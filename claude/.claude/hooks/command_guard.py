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
    r"/(?:\s|$|\*)",          # rm -rf /  or  /*
    r"~/?(?:\s|$|\*)",        # rm -rf ~  or  ~/*
    r"\$HOME\b/?(?:\s|$|\*)", # rm -rf $HOME
    r"/(?:home|etc|usr|var|boot|bin|sbin|lib(?:64)?|opt|root|srv|sys|proc|dev)\b/?(?:\s|$|\*)",
)

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

    for pattern, reason in RULES:
        if pattern.search(command):
            print(f"command-guard: {reason}. Command: {command!r}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
