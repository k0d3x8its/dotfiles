#!/usr/bin/env python3
"""Shallow-Clone Guard: detects truncated git history before churn is trusted."""

from __future__ import annotations

import subprocess
import sys

SHALLOW_WARNING = (
    "WARNING: this is a shallow clone — churn history is truncated. "
    "Ranking continues on the available history (2026-07-27 decision: "
    "warn-and-continue, matching the pipeline's never-errors philosophy)."
)


def is_shallow(repo_path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--is-shallow-repository"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == "true"


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    if is_shallow(target):
        print(SHALLOW_WARNING, file=sys.stderr)
