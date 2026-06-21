#!/usr/bin/env python3
"""PostToolUse hook: refresh .memory/TRIAGE-BLOCK.md when a TODOS.md is edited.

Wired to the Edit|Write tools. The matcher fires on every edit, so this
script is the path guard: it acts only when the edited file is a TODOS.md
under ~/dev, and exits silently otherwise. Runs in the harness (not the
model) so it costs zero model tokens. All output is suppressed — emitting
to stdout would inject text back into the model context and defeat that.

Flow on a TODOS.md edit:
  1. derive project name from path (~/dev/TODOS.md -> "machine";
     ~/dev/<proj>/TODOS.md -> "<proj>")
  2. update-cache <project> <path>   (bumps mtime pointer in .triage-cache
     so /dev-brief's read-skip sees the change)
  3. update-triage                   (re-renders .memory/TRIAGE-BLOCK.md from the
     live TODOS.md content the cache points at)
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

    path = data.get("tool_input", {}).get("file_path", "")
    if not path or os.path.basename(path) != "TODOS.md":
        return

    abspath = os.path.realpath(path)
    parent = os.path.dirname(abspath)

    # Only act on TODOS.md files under ~/dev — anything else is out of scope.
    if os.path.commonpath([abspath, DEV]) != DEV:
        return

    # ~/dev/TODOS.md is the [machine] project; subdir is named by its folder.
    project = "machine" if parent == DEV else os.path.basename(parent)

    devnull = subprocess.DEVNULL
    subprocess.run(["update-cache", project, path], stdout=devnull, stderr=devnull)
    subprocess.run(["update-triage"], stdout=devnull, stderr=devnull)


if __name__ == "__main__":
    main()
