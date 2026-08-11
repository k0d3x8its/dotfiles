#!/usr/bin/env python3
"""PostToolUse detective hook for the code-mode Gate-3-skip pattern.

Root cause (diagnosed .work/GATES.md TASK 8, this repo, 2026-07-19):
self-grading is STRUCTURAL, not a wording gap. A model that reads its own
Gate-2 evidence and writes a Gate-3 conclusion cannot notice the omission
from inside the pass that produced it — three SKILL.md wording hardenings
already failed to fix this. Advisor's prescribed fix class: a hook cannot
MECHANIZE delegation (hooks can't call Agent/advisor), but it CAN detect,
after the fact, that a Gate-3-or-later conclusion landed in GATES.md with
no Agent/advisor tool_use anywhere earlier in the transcript, and force
the model to look at it.

Contract (Claude Code PostToolUse):
  stdin  — JSON: {"tool_name", "tool_input", "transcript_path", "cwd", ...}
  exit 0 — quiet (also on any parse error: fail-open)
  exit 2 — stderr text fed back to the model as required follow-up
"""

import json
import os
import re
import sys

GATE_LINE_RE = re.compile(
    r"gate\s*[3-9]\d*\b.*\bclosed\b|current gate:\s*[3-9]\d*\b", re.IGNORECASE
)
# Names as they actually appear in transcript tool_use blocks. advisor confirmed
# live 2026-07-20 (see gate.md TASK 9 G6) as name "advisor". "Agent"/"Task" are
# both included since the subagent tool's transcript name wasn't confirmed live
# in this session (no Agent call occurred) — permissive on purpose, since a
# missed name here reproduces the exact bug this hook just shipped with.
DELEGATE_TOOL_NAMES = {"Agent", "Task", "advisor"}
# Real transcripts use "tool_use" for normal tools and "server_tool_use" for
# advisor specifically (confirmed live 2026-07-20) — match both.
TOOL_USE_TYPES = {"tool_use", "server_tool_use"}


def read_stdin():
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def added_text(tool_name, tool_input):
    """Best-effort extraction of the NEW text this call is writing."""
    if tool_name == "Write":
        return tool_input.get("content", "") or ""
    if tool_name == "Edit":
        return tool_input.get("new_string", "") or ""
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", []) or []
        return "\n".join(e.get("new_string", "") or "" for e in edits)
    return ""


def has_new_gate3_plus(text):
    return any(GATE_LINE_RE.search(line) for line in text.splitlines())


RECENT_TOOL_USE_WINDOW = 40


def transcript_has_delegation(transcript_path):
    """Was Agent/advisor called among the last RECENT_TOOL_USE_WINDOW tool_use
    blocks in the transcript?

    Scanning the WHOLE session defeats the point: the diagnosed skip lands
    late in long, multi-task sessions where an earlier, unrelated advisor
    call (for a different task's Gate 3, turns ago) would otherwise mask a
    current self-graded skip. Bounding to a recent window means a delegation
    call only counts if it happened close to the conclusion it's supposed to
    have attacked.
    """
    if not transcript_path:
        return True  # fail-open: can't verify, don't false-positive-block
    try:
        tool_uses = []
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                content = obj.get("message", {}).get("content", [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if isinstance(block, dict) and block.get("type") in TOOL_USE_TYPES:
                        tool_uses.append(block.get("name"))
        recent = tool_uses[-RECENT_TOOL_USE_WINDOW:]
        return any(name in DELEGATE_TOOL_NAMES for name in recent)
    except Exception:
        return True  # fail-open on any read/parse trouble


def main():
    data = read_stdin()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""

    if not file_path.endswith("GATES.md"):
        return 0

    text = added_text(tool_name, tool_input)
    if not has_new_gate3_plus(text):
        return 0

    if transcript_has_delegation(data.get("transcript_path", "")):
        return 0

    sys.stderr.write(
        "GATE-3-SKIP DETECTOR: GATES.md just recorded a Gate 3+ conclusion "
        "(a 'G3'/'G4'/... log line), but no Agent or advisor tool_use call "
        "was found anywhere earlier in this session's transcript. Code-mode "
        "Gate 3 requires a DELEGATED adversarial attack (advisor() or a "
        "spawned Agent) — self-reviewing your own Gate-2 evidence does not "
        "satisfy it, even if the write-up reads as thorough. Before treating "
        "this gate as passed: call advisor() or spawn an Agent to actually "
        "attack the conclusion, then update GATES.md with what it found."
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
