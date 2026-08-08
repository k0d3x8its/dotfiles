#!/usr/bin/env python3
"""Integration tests for code-decay/scripts/file_universe.py — real git repos,
real disk, pins the ls-files ∩ disk ∩ not-denied intersection so a deleted-
but-tracked or denied path never leaks into the ranked hotspot table."""

import importlib.machinery
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = (
    Path(__file__).parent.parent
    / "claude"
    / ".claude"
    / "skills"
    / "code-decay"
    / "scripts"
)


def load_module(name):
    mod_name = name.replace(".", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(SCRIPTS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


file_universe = load_module("file_universe.py")
resolve_files = file_universe.resolve_files


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def init_repo(repo: Path) -> None:
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test")


def write_and_commit(repo: Path, rel_path: str, content: str, message: str) -> None:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    run_git(repo, "add", rel_path)
    run_git(repo, "commit", "-q", "-m", message)


class ResolveFilesTests(unittest.TestCase):
    def test_returns_tracked_files_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_and_commit(repo, "app.py", "print(1)\n", "add app.py")

            self.assertEqual(resolve_files(str(repo)), ["app.py"])

    def test_excludes_tracked_file_deleted_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_and_commit(repo, "gone.py", "x = 1\n", "add gone.py")
            # Unstaged delete: still in the index, gone from the working tree
            # — a real state `git ls-files` still reports.
            (repo / "gone.py").unlink()

            self.assertEqual(resolve_files(str(repo)), [])

    def test_excludes_denied_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_and_commit(repo, "app.py", "print(1)\n", "add app.py")
            write_and_commit(repo, "package-lock.json", "{}\n", "add lockfile")

            self.assertEqual(resolve_files(str(repo)), ["app.py"])

    def test_excludes_denied_vendored_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_and_commit(repo, "app.py", "print(1)\n", "add app.py")
            write_and_commit(repo, "vendor/lib.py", "x = 1\n", "add vendored file")

            self.assertEqual(resolve_files(str(repo)), ["app.py"])

    def test_excludes_denied_prose_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_and_commit(repo, "app.py", "print(1)\n", "add app.py")
            write_and_commit(repo, "NOTES.md", "if this then that\n", "add notes")

            self.assertEqual(resolve_files(str(repo)), ["app.py"])

    def test_excludes_denied_work_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_and_commit(repo, "app.py", "print(1)\n", "add app.py")
            write_and_commit(repo, ".work/plan.txt", "if x then y\n", "add work file")

            self.assertEqual(resolve_files(str(repo)), ["app.py"])

    def test_returns_sorted_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_and_commit(repo, "zebra.py", "x = 1\n", "add zebra")
            write_and_commit(repo, "alpha.py", "x = 1\n", "add alpha")

            self.assertEqual(resolve_files(str(repo)), ["alpha.py", "zebra.py"])


if __name__ == "__main__":
    unittest.main()
