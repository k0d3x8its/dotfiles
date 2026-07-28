#!/usr/bin/env python3
"""File Universe Resolver: git ls-files intersected with on-disk, minus deny-list."""

from __future__ import annotations

import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

# Lockfiles/minified/vendored/generated skew churn+cx signal without being
# code anyone edits by hand — excluded so hotspot ranking isn't diluted.
DEFAULT_DENY_PATTERNS: tuple[str, ...] = (
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "Gemfile.lock",
    "composer.lock",
    "*.lock",
    "*.min.js",
    "*.min.css",
    "*.min.map",
    "*.map",
    "vendor/*",
    "node_modules/*",
    "third_party/*",
    "dist/*",
    "build/*",
    "*.generated.*",
    "__pycache__/*",
    "*.pyc",
    # Prose: proxy backend counts branch keywords, so a .md with "if" scores as code.
    "*.md",
    ".work/*",
)


def resolve_files(
    repo_path: str, deny_patterns: tuple[str, ...] = DEFAULT_DENY_PATTERNS
) -> list[str]:
    tracked = subprocess.run(
        ["git", "-C", repo_path, "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    root = Path(repo_path)
    universe = [
        rel_path
        for rel_path in tracked
        # `is_file()` drops paths git still tracks but that are gone from disk
        # (staged deletes, deleted-after-rename).
        if (root / rel_path).is_file()
        and not any(fnmatch(rel_path, pattern) for pattern in deny_patterns)
    ]
    # Stable order so two runs on unchanged repo state diff cleanly — later
    # scoring depends on deterministic input ordering.
    return sorted(universe)


if __name__ == "__main__":
    for path in resolve_files(sys.argv[1] if len(sys.argv) > 1 else "."):
        print(path)
