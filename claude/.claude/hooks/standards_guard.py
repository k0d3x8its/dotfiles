#!/usr/bin/env python3
"""Standards-read guard for Edit|Write (mechanical enforcement of the
"read CODE-STANDARD.md + the matching language file before writing code"
rule — see ~/.claude/CLAUDE.md § Session Rules).

Rationale: the rule lived only in prose (global CLAUDE.md + an auto-memory
feedback file) and was missed 3x because both channels require noticing an
applicability condition mid-task. The harness runs hooks unconditionally;
that channel doesn't depend on attention. Full design:
.work/todos/standards-guard-hook.md.

Two modes, dispatched by argv[1] (mirrors session_timer.py):
  pre  — PreToolUse on Edit|Write. Blocks (exit 2) when the target is a
         code file and the required reference(s) haven't been read yet
         this session. Exit 0 (silent) otherwise.
  post — PostToolUse on Read. Records a references/code/ read into the
         session's marker. Always exits 0; never prints to stdout (stdout
         from a PostToolUse hook injects into model context).

Fail-open on any error — a broken guard must never wedge editing.
Fires once per session per required file (a marker, not a per-edit check).
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

REFS_DIR = Path.home() / ".claude" / "references" / "code"
MARKER_DIR = Path.home() / ".claude" / "session_timing" / "standards_guard"

# Extension -> language file basename (CODE-STANDARD.md's delegation table).
EXT_TO_LANG_FILE = {
    ".py": "PYTHON.md",
    ".lua": "LUA.md",
    ".ts": "TYPESCRIPT.md",
    ".tsx": "TYPESCRIPT.md",
    ".js": "TYPESCRIPT.md",
    ".jsx": "TYPESCRIPT.md",
    ".sol": "SOLIDITY.md",
    ".sh": "BASH.md",
    ".bash": "BASH.md",
    ".bats": "BASH.md",
    ".ino": "ARDUINO.md",
    ".cpp": "ARDUINO.md",
    ".c": "ARDUINO.md",
    ".h": "ARDUINO.md",
    ".hpp": "ARDUINO.md",
}

TESTING_STANDARD = "TESTING-STANDARD.md"
CODE_STANDARD = "CODE-STANDARD.md"

# A typo-sized edit shouldn't demand a standards read.
TRIVIAL_EDIT_CHARS = 40

TEST_BASENAME_RE = re.compile(
    r"^test_.*\.\w+$|.*_test\.\w+$|.*\.test\.\w+$|.*\.spec\.\w+$"
)


def read_payload() -> dict[str, Any]:
    return json.load(sys.stdin)


def is_test_file(path: Path) -> bool:
    if "tests" in path.parts:
        return True
    return bool(TEST_BASENAME_RE.match(path.name))


def required_files(path: Path) -> Optional[set[str]]:
    lang_file = EXT_TO_LANG_FILE.get(path.suffix)
    if lang_file is None:
        return None
    required = {CODE_STANDARD, lang_file}
    if is_test_file(path):
        required.add(TESTING_STANDARD)
    return required


def marker_path(session_id: str) -> Path:
    safe = session_id or "unknown"
    return MARKER_DIR / f"{safe}.json"


def read_marker(session_id: str) -> set[str]:
    try:
        return set(json.loads(marker_path(session_id).read_text()))
    except Exception:
        # Fail-open read: absent/corrupt marker == nothing read yet.
        return set()


def write_marker(session_id: str, read_set: set[str]) -> None:
    MARKER_DIR.mkdir(parents=True, exist_ok=True)
    marker_path(session_id).write_text(json.dumps(sorted(read_set)))


def run_pre() -> int:
    payload = read_payload()
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    session_id = payload.get("session_id", "")

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0

    path = Path(file_path)
    required = required_files(path)
    if not required:
        return 0

    if tool_name == "Write":
        edit_size = len(tool_input.get("content", "") or "")
    else:
        edit_size = len(tool_input.get("new_string", "") or "")
    if edit_size < TRIVIAL_EDIT_CHARS:
        return 0

    already_read = read_marker(session_id)
    missing = required - already_read
    if not missing:
        return 0

    lines = [f"standards-guard: read before editing {path.name}:"]
    for f in sorted(missing):
        lines.append(f"  Read {REFS_DIR / f}")
    print("\n".join(lines), file=sys.stderr)
    return 2


def run_post() -> int:
    payload = read_payload()
    tool_input = payload.get("tool_input", {})
    session_id = payload.get("session_id", "")

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0

    path = Path(file_path)
    try:
        under_refs = path.resolve().is_relative_to(REFS_DIR.resolve())
    except Exception:
        # Fail-open resolve: an unresolvable path was never a refs/code read.
        under_refs = False
    if not under_refs:
        return 0

    read_set = read_marker(session_id)
    read_set.add(path.name)
    write_marker(session_id, read_set)
    return 0


def main(argv: list[str]) -> int:
    mode = argv[0] if argv else ""
    try:
        if mode == "pre":
            return run_pre()
        if mode == "post":
            return run_post()
        return 0
    except Exception:
        # Fail-open: a broken guard must never wedge editing.
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
