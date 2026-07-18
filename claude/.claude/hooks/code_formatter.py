#!/usr/bin/env python3
"""PostToolUse formatter dispatch (Edit|Write|MultiEdit).

Runs the per-language formatter in place on whatever file was just
written. No LLM calls — local binaries only. Fails open (prints a
stderr note, exit 0) on any missing tool or formatter error: a broken
formatter must not block editing.

Foundry (`forge`) installs to ~/.foundry/bin, which a non-interactive
hook subprocess won't pick up from ~/.bashrc — PATH is extended
explicitly below rather than relying on shell rc sourcing.
"""

import json
import os
import shutil
import subprocess
import sys

os.environ["PATH"] = (
    os.environ.get("PATH", "") + os.pathsep + os.path.expanduser("~/.foundry/bin")
)

# Paths that are git-crypt'd by convention or otherwise not code —
# formatters must never touch these regardless of extension.
EXCLUDE_PATH_PARTS = (".work/", ".memory/", "/KNOWLEDGE.md", "/TODOS.md", "/CLAUDE.md")

FORMATTERS = {
    ".lua": ["stylua"],
    ".py": ["black", "-q"],
    ".sh": ["shfmt", "-w"],
    ".bash": ["shfmt", "-w"],
    ".sol": ["forge", "fmt"],
    ".ino": ["clang-format", "-i"],
    ".c": ["clang-format", "-i"],
    ".h": ["clang-format", "-i"],
    ".cpp": ["clang-format", "-i"],
    ".hpp": ["clang-format", "-i"],
    ".js": ["prettier", "--write"],
    ".jsx": ["prettier", "--write"],
    ".ts": ["prettier", "--write"],
    ".tsx": ["prettier", "--write"],
    ".json": ["prettier", "--write"],
    ".yaml": ["prettier", "--write"],
    ".yml": ["prettier", "--write"],
    ".css": ["prettier", "--write"],
    ".html": ["prettier", "--write"],
    ".md": ["prettier", "--write"],
}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        file_path = payload.get("tool_input", {}).get("file_path", "")
    except Exception:
        return 0

    if not file_path or not os.path.isfile(file_path):
        return 0

    if any(part in file_path for part in EXCLUDE_PATH_PARTS):
        return 0

    ext = os.path.splitext(file_path)[1].lower()
    cmd = FORMATTERS.get(ext)
    if not cmd:
        return 0

    binary = cmd[0]
    if not shutil.which(binary):
        print(
            f"code_formatter: {binary} not on PATH — skipping format of {file_path}",
            file=sys.stderr,
        )
        return 0

    try:
        proc = subprocess.run(
            cmd + [file_path], capture_output=True, text=True, timeout=30
        )
        if proc.returncode != 0:
            print(
                f"code_formatter: {binary} failed on {file_path}:\n{proc.stderr}",
                file=sys.stderr,
            )
    except Exception as exc:
        print(
            f"code_formatter: {binary} errored on {file_path}: {exc}", file=sys.stderr
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
