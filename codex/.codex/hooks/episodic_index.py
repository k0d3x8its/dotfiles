#!/usr/bin/env python3
"""SessionEnd hook: append one episodic-index line when a session ends."""

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

    cwd = data.get("cwd") or os.getcwd()
    abscwd = os.path.realpath(cwd)

    try:
        if os.path.commonpath([abscwd, DEV]) != DEV:
            return
    except ValueError:
        return

    devnull = subprocess.DEVNULL
    subprocess.run(["update-episodic", abscwd], stdout=devnull, stderr=devnull)


if __name__ == "__main__":
    main()
