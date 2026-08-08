#!/usr/bin/env python3
"""fable-score.py — measure working-discipline habits from local Claude Code logs.

fable-mode's feedback loop. The skill claims to move a model toward Fable 5's
measured habits; this script is what proves or disproves that claim from your own
session files, so the answer is evidence, not vibes.

Two ways to use it:

  1. Compare two models (did the skill's target model close the gap?):
         python3 fable-score.py claude-opus-4-8 --baseline claude-fable-5

  2. Compare fable-mode ON vs OFF for one model (does the skill itself work?):
         python3 fable-score.py claude-opus-4-8 --split-fable
     A session counts as fable-mode ON when its log mentions the on-disk state the
     skill maintains (.work/.fable-active or .work/GATES.md) — that state is the
     only durable trace an activation leaves.

Habits measured (same definitions the public Fable analysis used, so numbers are
comparable in shape — absolute rates shift with the window scanned, so read the
gap between columns, not the raw percentages):

  beat level    reasoning present · reasoning before the first tool call ·
                re-evaluation after a tool result
  session level read before first edit · any check after an edit ·
                a real test/build/lint/typecheck after an edit
  error level   fraction of the model's own tool calls that returned is_error

A "beat" is one stretch where the model takes control: Claude Code splits a reply
across JSONL records (thinking, text, one per tool call), so a beat opens when the
model leads with thinking/text right after a boundary (a human message or a tool
result) and absorbs the tool-only continuation records that follow.

Reads raw session JSONL under ~/.claude/projects, streaming line by line — a
32 MB session never loads whole. Sessions are pre-filtered with grep so files
that cannot contain the model are never opened.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"

EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})

# What counts as "the real test" after an edit. Widen for your own stack — the
# point is to separate a genuine verification from a throwaway ls/echo.
REAL_TEST_PATTERN = re.compile(
    r"\b(pytest|jest|vitest|tsc|shellcheck|luacheck|ruff|eslint|stylua)\b"
    r"|\b(test|build|lint|typecheck)\b"
    r"|npm (run )?(test|build|lint)"
    r"|go (test|build|vet)"
    r"|cargo (test|build|clippy)"
    r"|forge (test|build)",
    re.IGNORECASE,
)

# Strings that only appear in a session where fable-mode was activated, because
# the skill writes this on-disk state on activation.
FABLE_MARKER_PATTERN = re.compile(r"\.fable-active|\.work/GATES\.md")


@dataclass
class HabitTally:
    """Counters for one corpus of sessions; rates derived at print time."""

    beats: int = 0
    beats_with_reasoning: int = 0
    beats_with_action: int = 0
    reasoned_before_action: int = 0
    reeval_opportunities: int = 0
    reeval_done: int = 0
    tool_results: int = 0
    tool_errors: int = 0
    sessions: int = 0
    sessions_with_edit: int = 0
    sessions_read_before_edit: int = 0
    sessions_check_after_edit: int = 0
    sessions_test_after_edit: int = 0


@dataclass
class _Beat:
    """One model-controlled stretch: ordered block kinds + attributed results."""

    kinds: list[str] = field(default_factory=list)
    opened_after_result: bool = False
    results: int = 0
    errors: int = 0


def find_sessions(model_id: str) -> list[Path]:
    """Sessions that contain at least one turn by this model, via cheap grep."""
    completed = subprocess.run(
        ["grep", "-rl", f'"model":"{model_id}"', str(PROJECTS_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    return [Path(line) for line in completed.stdout.splitlines() if line.strip()]


def session_mentions_fable(session_path: Path) -> bool:
    """True when the log carries fable-mode's on-disk activation state."""
    with session_path.open(encoding="utf-8", errors="replace") as handle:
        return any(FABLE_MARKER_PATTERN.search(line) for line in handle)


def score_session(session_path: Path, model_id: str, tally: HabitTally) -> None:
    """Stream one session once, updating the tally for the given model."""
    tally.sessions += 1

    beats: list[_Beat] = []
    open_beat: _Beat | None = None
    # What the model would be reacting to if it takes control now:
    # "user" = fresh human message, "result" = tool output (the re-evaluate moment).
    boundary: str | None = "user"
    beat_by_uuid: dict[str, int] = {}

    saw_edit = False
    saw_read = False
    read_before_first_edit = False
    check_after_edit = False
    test_after_edit = False

    for record in _iter_json_lines(session_path):
        record_type = record.get("type")

        if record_type == "assistant":
            message = record.get("message") or {}
            if message.get("model") != model_id:
                continue  # another model's turn; boundary state is unaffected
            blocks = [
                block
                for block in (message.get("content") or [])
                if isinstance(block, dict)
                and block.get("type") in ("thinking", "text", "tool_use")
            ]
            leads_with_reasoning = bool(blocks) and blocks[0]["type"] != "tool_use"

            # A new beat opens at a boundary when the model leads with reasoning
            # or text; tool-only continuation records extend the open beat, so a
            # single think-then-many-tools reply counts as ONE beat, not many.
            if open_beat is None or (leads_with_reasoning and boundary is not None):
                open_beat = _Beat(opened_after_result=(boundary == "result"))
                beats.append(open_beat)
            record_uuid = record.get("uuid")
            if record_uuid:
                beat_by_uuid[record_uuid] = len(beats) - 1
            boundary = None

            for block in blocks:
                open_beat.kinds.append(block["type"])
                if block["type"] != "tool_use":
                    continue
                tool_name = block.get("name")
                if tool_name == "Read":
                    saw_read = True
                elif tool_name in EDIT_TOOLS:
                    if not saw_edit:
                        read_before_first_edit = saw_read
                    saw_edit = True
                elif tool_name == "Bash" and saw_edit:
                    check_after_edit = True
                    command = (block.get("input") or {}).get("command", "") or ""
                    if REAL_TEST_PATTERN.search(command):
                        test_after_edit = True
            continue

        if record_type == "user":
            if _is_tool_result(record):
                owner_index = beat_by_uuid.get(record.get("parentUuid", ""))
                if owner_index is not None:
                    beats[owner_index].results += 1
                    if _result_is_error(record):
                        beats[owner_index].errors += 1
                boundary = "result"
            else:
                boundary = "user"
                open_beat = None

    if saw_edit:
        tally.sessions_with_edit += 1
        tally.sessions_read_before_edit += int(read_before_first_edit)
        tally.sessions_check_after_edit += int(check_after_edit)
        tally.sessions_test_after_edit += int(test_after_edit)

    for beat in beats:
        tally.beats += 1
        has_reasoning = "thinking" in beat.kinds
        tally.beats_with_reasoning += int(has_reasoning)
        if "tool_use" in beat.kinds:
            tally.beats_with_action += 1
            if has_reasoning and beat.kinds.index("thinking") < beat.kinds.index("tool_use"):
                tally.reasoned_before_action += 1
        if beat.opened_after_result:
            tally.reeval_opportunities += 1
            tally.reeval_done += int(has_reasoning)
        tally.tool_results += beat.results
        tally.tool_errors += beat.errors


def print_report(
    left_label: str,
    left: HabitTally,
    right_label: str,
    right: HabitTally,
) -> None:
    """Markdown habit table, gap column included — paste-ready."""

    def rate(numerator: int, denominator: int) -> float:
        return 100.0 * numerator / denominator if denominator else 0.0

    rows = [
        ("beats containing reasoning",
         rate(left.beats_with_reasoning, left.beats),
         rate(right.beats_with_reasoning, right.beats)),
        ("reasons before the first action",
         rate(left.reasoned_before_action, left.beats_with_action),
         rate(right.reasoned_before_action, right.beats_with_action)),
        ("re-evaluates after a result",
         rate(left.reeval_done, left.reeval_opportunities),
         rate(right.reeval_done, right.reeval_opportunities)),
        ("reads the file before editing",
         rate(left.sessions_read_before_edit, left.sessions_with_edit),
         rate(right.sessions_read_before_edit, right.sessions_with_edit)),
        ("runs a check after editing",
         rate(left.sessions_check_after_edit, left.sessions_with_edit),
         rate(right.sessions_check_after_edit, right.sessions_with_edit)),
        ("runs the real test after editing",
         rate(left.sessions_test_after_edit, left.sessions_with_edit),
         rate(right.sessions_test_after_edit, right.sessions_with_edit)),
        ("tool error rate (lower is better)",
         rate(left.tool_errors, left.tool_results),
         rate(right.tool_errors, right.tool_results)),
    ]

    print(f"{left_label}: {left.beats} beats across {left.sessions} sessions "
          f"({left.sessions_with_edit} with edits)")
    print(f"{right_label}: {right.beats} beats across {right.sessions} sessions "
          f"({right.sessions_with_edit} with edits)")
    print("Rates shift with the window scanned — compare columns, not absolutes.\n")
    print(f"| Habit | {left_label} | {right_label} | gap |")
    print("|---|---|---|---|")
    for habit_name, left_rate, right_rate in rows:
        print(f"| {habit_name} | {left_rate:.0f}% | {right_rate:.0f}% "
              f"| {left_rate - right_rate:+.0f} |")


def _iter_json_lines(session_path: Path):
    """Yield one parsed object per JSONL line; malformed lines are skipped."""
    with session_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _is_tool_result(record: dict) -> bool:
    """A 'user' record that is actually tool output echoed back, not a human."""
    if record.get("toolUseResult") is not None:
        return True
    content = (record.get("message") or {}).get("content")
    return isinstance(content, list) and any(
        isinstance(block, dict) and block.get("type") == "tool_result"
        for block in content
    )


def _result_is_error(record: dict) -> bool:
    content = (record.get("message") or {}).get("content")
    if isinstance(content, list):
        return any(
            isinstance(block, dict)
            and block.get("type") == "tool_result"
            and block.get("is_error")
            for block in content
        )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score working-discipline habits from local Claude Code logs.",
    )
    parser.add_argument("model", help="model id to score, e.g. claude-opus-4-8")
    parser.add_argument(
        "--baseline",
        help="second model id to compare against, e.g. claude-fable-5",
    )
    parser.add_argument(
        "--split-fable",
        action="store_true",
        help="split the model's sessions into fable-mode ON vs OFF instead of "
             "comparing two models",
    )
    args = parser.parse_args()

    if args.baseline and args.split_fable:
        parser.error("--baseline and --split-fable are mutually exclusive")

    sessions = find_sessions(args.model)
    if not sessions:
        print(f"No sessions containing {args.model} under {PROJECTS_DIR}.")
        return 1

    if args.split_fable:
        fable_on, fable_off = HabitTally(), HabitTally()
        for session_path in sessions:
            target = fable_on if session_mentions_fable(session_path) else fable_off
            score_session(session_path, args.model, target)
        print(f"# {args.model} — fable-mode ON vs OFF\n")
        print_report("fable ON", fable_on, "fable OFF", fable_off)
        return 0

    model_tally = HabitTally()
    for session_path in sessions:
        score_session(session_path, args.model, model_tally)

    if not args.baseline:
        empty = HabitTally()
        print(f"# {args.model} — habit profile\n")
        print_report(args.model, model_tally, "(none)", empty)
        return 0

    baseline_tally = HabitTally()
    for session_path in find_sessions(args.baseline):
        score_session(session_path, args.baseline, baseline_tally)
    print(f"# {args.model} vs {args.baseline}\n")
    print_report(args.model, model_tally, args.baseline, baseline_tally)
    return 0


if __name__ == "__main__":
    sys.exit(main())
