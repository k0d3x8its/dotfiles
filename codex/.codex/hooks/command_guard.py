#!/usr/bin/env python3
"""PreToolUse guard for Bash commands.

Blocks dangerous command classes that the settings.json deny globs cannot
reliably match. This hook regex-matches the whole command string.

Contract:
  stdin  - JSON: {"tool_name": "Bash", "tool_input": {"command": "..."}}
  exit 0 - allow (also on any parse error: fail-open so a malformed payload
           cannot brick every Bash call; the permission system is still
           underneath us)
  exit 2 - block; stderr text is fed back to the model as the reason
"""

import json
import re
import sys

SHELLS = r"(?:ba|z|da|k|fi)?sh"

DANGEROUS_RM_TARGETS = (
    r"/(?:\s|$|\*)",
    r"~/?(?:\s|$|\*)",
    r"\$HOME\b/?(?:\s|$|\*)",
    r"/(?:home|etc|usr|var|boot|bin|sbin|lib(?:64)?|opt|root|srv|sys|proc|dev)\b/?(?:\s|$|\*)",
)

RULES = [
    (
        re.compile(
            rf"\b(?:curl|wget|fetch)\b[^|;&\n]*\|\s*(?:sudo\s+)?(?:env\s+\S+\s+)?{SHELLS}\b"
        ),
        "pipe-to-shell (fetch piped into a shell) is blocked — download to a file, inspect it, then run it explicitly",
    ),
    (
        re.compile(
            rf"base64\b[^|;&\n]*(?:-d|--decode)[^|;&\n]*\|\s*(?:sudo\s+)?{SHELLS}\b"
            rf"|(?:eval|{SHELLS})\s*[\"']?\s*(?:\$\(|`)[^)`]*base64"
        ),
        "base64-decode-into-shell is blocked — decode to a file and inspect before executing",
    ),
    (
        re.compile(
            r"\brm\s+(?:-[a-zA-Z]+\s+)*"
            r"(?:-[a-zA-Z]*(?:r[a-zA-Z]*f|f[a-zA-Z]*r)[a-zA-Z]*|"
            r"(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+)+-[a-zA-Z]*[rf][a-zA-Z]*)\s+"
            r"(?:" + "|".join(DANGEROUS_RM_TARGETS) + r")"
        ),
        "recursive force-delete of a root-level or home path is blocked",
    ),
    (
        re.compile(r"\bchmod\s+(?:-[a-zA-Z]+\s+)*0?(?:777|666)\b"),
        "chmod 777/666 is blocked — grant the narrowest permission that works (e.g. 755/644, or u+x)",
    ),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
    except Exception:
        return 0

    if not isinstance(command, str) or not command:
        return 0

    for pattern, reason in RULES:
        if pattern.search(command):
            print(f"command-guard: {reason}. Command: {command!r}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
