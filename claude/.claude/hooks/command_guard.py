#!/usr/bin/env python3
"""PreToolUse guard for Bash commands (S2 command-guard hook).

Blocks command classes that the settings.json deny globs cannot reliably
match (deny patterns are literal-ish globs — `Bash(curl * | bash)` misses
`wget | sh`, `curl | zsh`, etc.). This hook regex-matches the whole class.

Contract (Claude Code PreToolUse):
  stdin  — JSON: {"tool_name": "Bash", "tool_input": {"command": "..."}}
  exit 0 — allow (also on any parse error: fail-open so a malformed
           payload can't brick every Bash call; the permission system
           is still underneath us)
  exit 2 — block; stderr text is fed back to the model as the reason
"""

import json
import re
import sys

# Shell binaries that turn piped text into execution.
SHELLS = r"(?:ba|z|da|k|fi)?sh"

# Filesystem roots where a recursive force-delete is never a sane
# agent action. $HOME/~ included: losing the home dir is unrecoverable.
DANGEROUS_RM_TARGETS = (
    r"/(?:\s|$|\*)",  # rm -rf /  or  /*
    r"~/?(?:\s|$|\*)",  # rm -rf ~  or  ~/*
    r"\$HOME\b/?(?:\s|$|\*)",  # rm -rf $HOME
    r"/(?:home|etc|usr|var|boot|bin|sbin|lib(?:64)?|opt|root|srv|sys|proc|dev)\b/?(?:\s|$|\*)",
)

# A heredoc redirect: `<<[-]DELIM`, optionally quoted (quoting only disables
# variable expansion inside, doesn't change body detection here).
HEREDOC_START = re.compile(r"<<-?\s*([\"']?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _strip_heredoc_bodies(command: str) -> str:
    """Blank out heredoc BODIES before rule matching — a body is data the
    shell never executes as a command, so patterns appearing only in a body
    (e.g. this file's own docstring pasted into a `cat >> log <<EOF` entry)
    must not trigger a rule meant for executed text. Exception: if the
    command reading the heredoc is itself a shell (`bash <<EOF ... EOF`),
    the body IS executed — don't strip it."""
    spans = []
    for match in HEREDOC_START.finditer(command):
        line_start = command.rfind("\n", 0, match.start()) + 1
        prefix = command[line_start : match.start()]
        segment = re.split(r"[;&|]+", prefix)[-1].strip()
        cmd_name = segment.split()[0].rsplit("/", 1)[-1] if segment else ""
        if re.fullmatch(SHELLS, cmd_name):
            continue  # heredoc body is real, executed shell input

        body_line_start = command.find("\n", match.end())
        if body_line_start == -1:
            continue  # malformed (no body/terminator) — leave untouched
        body_line_start += 1

        delimiter = match.group(2)
        terminator = re.compile(rf"^[ \t]*{re.escape(delimiter)}[ \t]*$", re.MULTILINE)
        end_match = terminator.search(command, body_line_start)
        if not end_match:
            continue  # unterminated heredoc — leave untouched

        spans.append((body_line_start, end_match.start()))

    if not spans:
        return command

    result = []
    cursor = 0
    for start, end in spans:
        result.append(command[cursor:start])
        result.append("<heredoc-body-stripped>")
        cursor = end
    result.append(command[cursor:])
    return "".join(result)


RULES = [
    (
        # Fetch-and-execute: network content piped straight into a shell.
        re.compile(
            rf"\b(?:curl|wget|fetch)\b[^|;&\n]*\|\s*(?:sudo\s+)?(?:env\s+\S+\s+)?{SHELLS}\b"
        ),
        "pipe-to-shell (fetch piped into a shell) is blocked — download to a file, inspect it, then run it explicitly",
    ),
    (
        # Obfuscated execution: base64 decode piped into a shell or eval.
        re.compile(
            rf"base64\b[^|;&\n]*(?:-d|--decode)[^|;&\n]*\|\s*(?:sudo\s+)?{SHELLS}\b"
            # optional quote: eval "$(...)" is the common spelling and must
            # not slip past on the quote character (regression 2026-07-07)
            rf"|(?:eval|{SHELLS})\s*[\"']?\s*(?:\$\(|`)[^)`]*base64"
        ),
        "base64-decode-into-shell is blocked — decode to a file and inspect before executing",
    ),
    (
        # Recursive force-delete of a root-ish path. Both flag orders and
        # combined flags (-rf, -fr, -r -f) are covered.
        re.compile(
            r"\brm\s+(?:-[a-zA-Z]+\s+)*"
            r"(?:-[a-zA-Z]*(?:r[a-zA-Z]*f|f[a-zA-Z]*r)[a-zA-Z]*|"
            r"(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+)+-[a-zA-Z]*[rf][a-zA-Z]*)\s+"
            r"(?:" + "|".join(DANGEROUS_RM_TARGETS) + r")"
        ),
        "recursive force-delete of a root-level or home path is blocked",
    ),
    (
        # World-writable perms: 777/666 (optionally octal-prefixed, -R).
        re.compile(r"\bchmod\s+(?:-[a-zA-Z]+\s+)*0?(?:777|666)\b"),
        "chmod 777/666 is blocked — grant the narrowest permission that works (e.g. 755/644, or u+x)",
    ),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
    except Exception:
        return 0  # fail-open: never brick Bash on a bad payload

    if not isinstance(command, str) or not command:
        return 0

    scannable = _strip_heredoc_bodies(command)

    for pattern, reason in RULES:
        if pattern.search(scannable):
            print(f"command-guard: {reason}. Command: {command!r}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
