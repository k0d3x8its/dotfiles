#!/usr/bin/env python3
"""Integration tests for code-decay/scripts/shallow_guard.py — real git repos,
including a real `--depth=1` clone, so the shallow-vs-full detection is
proven against git's actual behavior, not a mocked flag."""

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


shallow_guard = load_module("shallow_guard.py")
is_shallow = shallow_guard.is_shallow


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def init_repo_with_commits(repo: Path, count: int) -> None:
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test")
    for index in range(count):
        (repo / "file.txt").write_text(f"revision {index}\n")
        run_git(repo, "add", "file.txt")
        run_git(repo, "commit", "-q", "-m", f"revision {index}")


class IsShallowTests(unittest.TestCase):
    def test_full_clone_is_not_shallow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo_with_commits(repo, count=3)

            self.assertFalse(is_shallow(str(repo)))

    def test_depth_one_clone_is_shallow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            clone = Path(tmp) / "clone"
            source.mkdir()
            init_repo_with_commits(source, count=3)
            subprocess.run(
                ["git", "clone", "-q", "--depth=1", f"file://{source}", str(clone)],
                check=True,
                capture_output=True,
            )

            self.assertTrue(is_shallow(str(clone)))


if __name__ == "__main__":
    unittest.main()
