#!/usr/bin/env python3
"""SessionEnd hook: append one episodic-index line when a session ends.

Wired to `SessionEnd` (NOT `Stop`). Stop fires every time the model finishes a
response — using it would append a line per turn and bloat the index. SessionEnd
fires once, when the session terminates, which is the cadence we want.

Runs in the harness (not the model) so it costs zero model tokens. All output is
suppressed — emitting to stdout would inject text back into the model context and
defeat the point.

The SessionEnd payload carries `cwd` (and `reason`); it does NOT carry the
PostToolUse-style `tool_input.file_path`. We hand `cwd` to update-episodic, which
derives the project from it and computes files-touched from git itself.
"""
import json
import os
import subprocess
import sys

DEV = os.path.realpath(os.path.expanduser("~/dev"))


def main() -> None:
    # Hook input arrives as JSON on stdin. Any parse failure = do nothing.
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    cwd = data.get("cwd") or os.getcwd()
    abscwd = os.path.realpath(cwd)

    # Only act on sessions under ~/dev — anything else is out of scope.
    try:
        if os.path.commonpath([abscwd, DEV]) != DEV:
            return
    except ValueError:
        return  # different drive / unrelated path

    devnull = subprocess.DEVNULL
    subprocess.run(["update-episodic", abscwd], stdout=devnull, stderr=devnull)


if __name__ == "__main__":
    main()
