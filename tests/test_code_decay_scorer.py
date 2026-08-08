#!/usr/bin/env python3
"""Unit tests for code-decay/scripts/scorer.py — score = churn x cx, absolute
units, no repo-relative rescale (FR-07/FR-08)."""

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


scorer = load_module("scorer.py")
score_files = scorer.score_files
churn_module = load_module("churn.py")
complexity_module = load_module("complexity.py")


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def init_repo(repo: Path) -> None:
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test")


def commit_file(repo: Path, rel_path: str, content: str, message: str) -> None:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    run_git(repo, "add", rel_path)
    run_git(repo, "commit", "-q", "-m", message)


def build_rows(repo: Path) -> dict[str, tuple[int, int]]:
    churn = churn_module.extract_churn(str(repo), since=None)
    return {
        path: (count, complexity_module.complexity(str(repo / path)).value)
        for path, count in churn.items()
    }


class ScoreFilesTests(unittest.TestCase):
    def test_score_is_churn_times_cx(self) -> None:
        result = score_files({"a.py": (4, 5)})

        self.assertEqual(result, {"a.py": 20})

    def test_score_repeated_calls_are_byte_identical(self) -> None:
        rows = {"a.py": (4, 5), "b.py": (10, 2)}

        first = score_files(rows)
        second = score_files(rows)

        self.assertEqual(first, second)

    def test_score_for_a_file_does_not_depend_on_other_files_present(self) -> None:
        alone = score_files({"a.py": (4, 5)})
        with_neighbor = score_files({"a.py": (4, 5), "b.py": (999, 999)})

        self.assertEqual(alone["a.py"], with_neighbor["a.py"])

    def test_zero_churn_or_zero_cx_scores_zero(self) -> None:
        result = score_files({"untouched.py": (0, 40), "trivial.py": (12, 0)})

        self.assertEqual(result, {"untouched.py": 0, "trivial.py": 0})


class ScoreFilesRealRepoTests(unittest.TestCase):
    """FR-08's own verify clause: run twice against an UNCHANGED repo state —
    real git history, real ast-grep complexity, not synthetic (churn, cx)
    pairs — and prove the unchanged file's score doesn't move."""

    def test_unchanged_repo_state_scores_byte_identical_across_two_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            commit_file(repo, "a.py", "if True:\n    pass\n", "add a")
            commit_file(
                repo, "a.py", "if True:\n    if False:\n        pass\n", "edit a"
            )

            first = score_files(build_rows(repo))
            second = score_files(build_rows(repo))

            self.assertEqual(first, second)
            self.assertEqual(first["a.py"], second["a.py"])


if __name__ == "__main__":
    unittest.main()
