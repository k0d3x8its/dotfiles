#!/usr/bin/env python3
"""PostToolUse hook: refresh TRIAGE-BLOCK.md when a TODOS.md is edited."""

import json
import os
import subprocess
import sys

DEV = os.path.realpath(os.path.expanduser("~/dev"))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    path = data.get("tool_input", {}).get("file_path", "")
    if not path or os.path.basename(path) != "TODOS.md":
        return

    abspath = os.path.realpath(path)
    parent = os.path.dirname(abspath)

    try:
        if os.path.commonpath([abspath, DEV]) != DEV:
            return
    except ValueError:
        return

    project = "machine" if parent == DEV else os.path.basename(parent)

    devnull = subprocess.DEVNULL
    subprocess.run(["update-cache", project, path], stdout=devnull, stderr=devnull)
    subprocess.run(["update-triage"], stdout=devnull, stderr=devnull)


if __name__ == "__main__":
    main()
