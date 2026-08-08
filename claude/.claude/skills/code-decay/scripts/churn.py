#!/usr/bin/env python3
"""Churn Extractor: single-pass `git log -M --name-status`, renames folded onto
the current path so a 100%-similarity rename combines churn instead of
splitting it across old/new names."""

from __future__ import annotations

import subprocess
import sys

COMMIT_MARKER = "--commit--"
DEFAULT_SINCE = "12.months"


def _run_git_log(repo_path: str, since: str | None) -> list[str]:
    # `--reverse` walks oldest-first so renames fold forward onto the path a
    # file has *now*, not backward onto a name nothing references anymore.
    cmd = [
        "git",
        "-C",
        repo_path,
        "log",
        "--reverse",
        "-M",
        # No --first-parent: default git log already walks every individual
        # commit reachable through a merge and shows each one's own diff, so
        # a file edited N times on a feature branch counts N, not 1.
        # --first-parent was tried and reverted — verified empirically it
        # collapses a branch's whole history into the merge commit's single
        # diff against its first parent, undercounting real edits.
        "--name-status",
        f"--pretty=format:{COMMIT_MARKER}",
    ]
    if since is not None:
        cmd.append(f"--since={since}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.splitlines()


def extract_churn(
    repo_path: str, since: str | None = DEFAULT_SINCE, all_history: bool = False
) -> dict[str, int]:
    lines = _run_git_log(repo_path, None if all_history else since)

    # alias[old] -> new lets a later touch of `old` resolve to wherever the
    # file lives today, without rewriting every prior alias entry.
    alias: dict[str, str] = {}
    churn: dict[str, int] = {}

    def resolve(path: str) -> str:
        seen = []
        while path in alias:
            seen.append(path)
            path = alias[path]
        # Path compression: next lookup for any name in this chain is O(1).
        for stale in seen:
            alias[stale] = path
        return path

    for line in lines:
        if not line or line == COMMIT_MARKER:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")):
            old_path, new_path = resolve(parts[1]), resolve(parts[2])
            # Merge whatever churn the old name accumulated into the new
            # name's bucket, then credit this rename commit itself.
            churn[new_path] = churn.pop(old_path, 0) + churn.get(new_path, 0) + 1
            alias[old_path] = new_path
        else:
            path = resolve(parts[1])
            churn[path] = churn.get(path, 0) + 1

    return churn


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    for path, count in sorted(extract_churn(target).items(), key=lambda kv: -kv[1]):
        print(f"{count}\t{path}")
