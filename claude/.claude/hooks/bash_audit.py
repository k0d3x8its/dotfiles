#!/usr/bin/env python3
"""PostToolUse audit log for Bash commands (S5).

Appends every executed Bash command + cwd + timestamp to
~/.claude/logs/bash-audit.log — a forensics trail for reconstructing
what an agent session actually ran. Append-only, fail-silent: logging
must never break tool execution.
"""

import json
import os
import sys
from datetime import datetime, timezone

LOG_DIR = os.path.expanduser("~/.claude/logs")
LOG_FILE = os.path.join(LOG_DIR, "bash-audit.log")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
        cwd = payload.get("cwd", "")
        if not command:
            return 0
        os.makedirs(LOG_DIR, exist_ok=True)
        stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        # One JSON object per line: survives newlines inside commands.
        line = json.dumps({"ts": stamp, "cwd": cwd, "command": command})
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass  # never block or noise the session over a logging failure
    return 0


if __name__ == "__main__":
    sys.exit(main())
