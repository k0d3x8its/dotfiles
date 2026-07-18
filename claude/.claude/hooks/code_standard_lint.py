#!/usr/bin/env python3
"""PostToolUse Layer-2 check (Edit|Write|MultiEdit) — CODE-STANDARD.md
code-marker rules, the two checks that are actually tool-authoritative
(no false positives from strings/comments, unlike identifier/casing
regex, which stays /code-review's job):

  1. Marker keyword missing its required trailing colon
     (TODO: not TODO/TODO ) — CODE-STANDARD.md "Comments" section.
  2. Marker with a TODOS.md tag counterpart whose text isn't mirrored
     anywhere in TODOS.md — best-effort substring match.

PostToolUse can't block (the edit already landed) — this only prints
a stderr note fed back into context as a nudge, per the standard's
"tool-checkable" tier. Everything judgment-level stays with
/code-review. No LLM calls.
"""

import json
import os
import re
import sys

EXCLUDE_PATH_PARTS = (".work/", ".memory/", "/KNOWLEDGE.md", "/TODOS.md", "/CLAUDE.md")

# keyword -> requires trailing colon; tag_group groups aliases that share
# one TODOS.md tag counterpart (None = inline-only, no tag expected).
MARKERS = {
    "TODO": "TODO",
    "BUG": "BUG",
    "FIXME": "BUG",
    "HOTFIX": "CHORE-or-VERIFY",
    "HACK": None,
    "NOTE": None,
    "WARN": None,
    "PERFORMANCE": "PERFORMANCE",
    "PERF": "PERFORMANCE",
    "OPTIMIZE": "PERFORMANCE",
    "SECURITY": "SECURITY",
    "TEST": "TEST",
    "TESTING": "TEST",
    "PASSED": "TEST",
    "FAILED": "TEST",
}

KEYWORD_RE = re.compile(r"\b(" + "|".join(MARKERS.keys()) + r")\b(:?)")


def find_todos_md(start_dir):
    d = os.path.abspath(start_dir)
    for _ in range(6):
        candidate = os.path.join(d, "TODOS.md")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        file_path = payload.get("tool_input", {}).get("file_path", "")
    except Exception:
        return 0

    if not file_path or not os.path.isfile(file_path):
        return 0
    if any(part in file_path for part in EXCLUDE_PATH_PARTS):
        return 0
    if os.path.splitext(file_path)[1].lower() not in (
        ".lua",
        ".py",
        ".sh",
        ".bash",
        ".sol",
        ".ino",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
    ):
        return 0

    try:
        with open(file_path, "r", errors="ignore") as fh:
            lines = fh.readlines()
    except Exception:
        return 0

    todos_path = find_todos_md(os.path.dirname(file_path))
    todos_text = ""
    if todos_path:
        try:
            with open(todos_path, "r", errors="ignore") as fh:
                todos_text = fh.read()
        except Exception:
            pass

    missing_colon = []
    unmirrored = []

    for lineno, line in enumerate(lines, start=1):
        for match in KEYWORD_RE.finditer(line):
            keyword, colon = match.group(1), match.group(2)
            if not colon:
                missing_colon.append((lineno, keyword, line.strip()))
                continue

            tag_group = MARKERS[keyword]
            if tag_group is None or not todos_path:
                continue

            trailing = line[match.end() :].strip()
            if trailing and trailing not in todos_text:
                unmirrored.append((lineno, keyword, trailing))

    if not missing_colon and not unmirrored:
        return 0

    report = [f"code_standard_lint: {file_path}"]
    for lineno, keyword, text in missing_colon:
        report.append(
            f"  L{lineno}: `{keyword}` marker missing trailing colon — {text!r}"
        )
    for lineno, keyword, text in unmirrored:
        report.append(
            f"  L{lineno}: `{keyword}:` not found in {todos_path} — mirror it or it doesn't exist"
        )

    print("\n".join(report), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
