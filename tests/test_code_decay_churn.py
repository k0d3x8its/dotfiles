#!/usr/bin/env python3
"""Integration tests for code-decay/scripts/churn.py — real git repos so the
rename-fold logic is proven against git's actual `-M --name-status` output,
not a hand-built fixture of it."""

import importlib.machinery
import importlib.util
import os
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


churn = load_module("churn.py")
extract_churn = churn.extract_churn


def run_git(repo: Path, *args: str, when: str | None = None) -> None:
    env = os.environ.copy()
    if when is not None:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, env=env
    )


def init_repo(repo: Path) -> None:
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test")


def commit_file(
    repo: Path, rel_path: str, content: str, message: str, when: str | None = None
) -> None:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    run_git(repo, "add", rel_path)
    run_git(repo, "commit", "-q", "-m", message, when=when)


class ExtractChurnTests(unittest.TestCase):
    def test_counts_one_touch_per_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit_file(repo, "a.py", "x = 1\n", "add a")
            commit_file(repo, "a.py", "x = 2\n", "edit a")

            self.assertEqual(extract_churn(str(repo), since=None), {"a.py": 2})

    def test_rename_folds_churn_onto_new_path_not_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit_file(repo, "old.py", "x = 1\n", "add old")
            commit_file(repo, "old.py", "x = 2\n", "edit old")
            run_git(repo, "mv", "old.py", "new.py")
            run_git(repo, "commit", "-q", "-m", "rename old to new")
            commit_file(repo, "new.py", "x = 3\n", "edit new")

            result = extract_churn(str(repo), since=None)

            self.assertEqual(result, {"new.py": 4})
            self.assertNotIn("old.py", result)

    def test_unrelated_file_churn_stays_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit_file(repo, "a.py", "x = 1\n", "add a")
            commit_file(repo, "b.py", "x = 1\n", "add b")
            commit_file(repo, "a.py", "x = 2\n", "edit a")

            self.assertEqual(
                extract_churn(str(repo), since=None), {"a.py": 2, "b.py": 1}
            )

    def test_since_window_excludes_older_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit_file(
                repo, "a.py", "x = 1\n", "old commit", when="2020-01-01T00:00:00"
            )
            commit_file(repo, "a.py", "x = 2\n", "recent commit")

            self.assertEqual(extract_churn(str(repo), since="12.months"), {"a.py": 1})

    def test_merge_commit_counts_every_branch_commit_individually(self) -> None:
        # Regression lock: --first-parent was tried here and reverted because
        # it collapses a feature branch's whole history into the merge
        # commit's single diff, undercounting a file edited 3x on the branch
        # down to 1. Default git log walks each branch commit individually
        # and must keep doing so.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit_file(repo, "main.py", "a = 1\n", "init")
            base_branch = subprocess.run(
                ["git", "-C", str(repo), "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            run_git(repo, "checkout", "-q", "-b", "side")
            commit_file(repo, "side.py", "y = 1\n", "side 1")
            commit_file(repo, "side.py", "y = 2\n", "side 2")
            commit_file(repo, "side.py", "y = 3\n", "side 3")
            run_git(repo, "checkout", "-q", base_branch)
            run_git(repo, "merge", "--no-ff", "-q", "-m", "merge side", "side")

            self.assertEqual(
                extract_churn(str(repo), since=None), {"main.py": 1, "side.py": 3}
            )

    def test_all_history_overrides_since_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit_file(
                repo, "a.py", "x = 1\n", "old commit", when="2020-01-01T00:00:00"
            )
            commit_file(repo, "a.py", "x = 2\n", "recent commit")

            self.assertEqual(
                extract_churn(str(repo), since="12.months", all_history=True),
                {"a.py": 2},
            )


if __name__ == "__main__":
    unittest.main()
