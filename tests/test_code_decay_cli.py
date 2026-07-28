#!/usr/bin/env python3
"""Deterministic-core integration test for code-decay's CLI entrypoint
(SKILL.md). Chains the real scripts (shallow_guard, file_universe, churn,
complexity, scorer, labeler, report_renderer) against a real temp git repo,
in the exact order SKILL.md's Pipeline section documents, and proves the
whole chain makes zero network/model calls (FR-11). Also greps SKILL.md
itself so the prose orchestration can't silently drift from what this test
proves works — an integration test that hand-wires the functions beside the
shipped prose, instead of against it, would prove the wrong thing."""

import importlib.machinery
import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = (
    Path(__file__).parent.parent / "claude" / ".claude" / "skills" / "code-decay"
)
SCRIPTS = SKILL_DIR / "scripts"
SKILL_MD = SKILL_DIR / "SKILL.md"


def load_module(name):
    mod_name = name.replace(".", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(SCRIPTS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


shallow_guard = load_module("shallow_guard.py")
file_universe = load_module("file_universe.py")
churn_mod = load_module("churn.py")
complexity_mod = load_module("complexity.py")
scorer = load_module("scorer.py")
labeler = load_module("labeler.py")
report_renderer = load_module("report_renderer.py")


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


def commit_file(repo: Path, rel_path: str, content: str, message: str) -> None:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    run_git(repo, "add", rel_path)
    run_git(repo, "commit", "-q", "-m", message)


def run_deterministic_pipeline(repo_path: str) -> Path:
    """Mirrors SKILL.md's Pipeline steps 1-7 and 9 exactly (step 8, the
    Interpret Pass, is flag-gated and the only step allowed to touch a
    model — deliberately excluded here)."""
    shallow_warning = shallow_guard.is_shallow(repo_path)  # step 1
    paths = file_universe.resolve_files(repo_path)  # step 2
    churn = churn_mod.extract_churn(repo_path)  # step 3

    rows = {}
    for path in paths:  # steps 4-5
        cx = complexity_mod.complexity(os.path.join(repo_path, path)).value
        rows[path] = (churn.get(path, 0), cx)

    # step 6 (score_files) is not called here directly: render_report loads
    # scorer.py as a sibling and calls the same function internally, so
    # there is exactly one `score = churn * cx` implementation, not two.
    labels = labeler.label_files(rows)  # step 7

    return report_renderer.render_report(  # step 9
        repo_path, rows, labels, shallow_warning=shallow_warning
    )


class DeterministicPipelineTests(unittest.TestCase):
    def test_full_pipeline_writes_a_ranked_report_from_a_real_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "target-repo"
            repo.mkdir()
            init_repo(repo)
            commit_file(repo, "hot.py", "def f():\n" + "    if x:\n" * 20, "add hot")
            commit_file(repo, "cold.py", "x = 1\n", "add cold")
            for touch in range(3):
                commit_file(
                    repo,
                    "hot.py",
                    "def f():\n" + "    if x:\n" * (21 + touch),
                    "touch",
                )

            report_path = run_deterministic_pipeline(str(repo))
            content = report_path.read_text()

            self.assertTrue(report_path.exists())
            self.assertLess(content.index("hot.py"), content.index("cold.py"))

    def test_pipeline_makes_zero_network_calls(self) -> None:
        # FR-11: everything but the flag-gated Interpret Pass must run with
        # no network/model access. Patch the socket layer so any attempt at
        # a real connection fails loudly instead of silently succeeding.
        original_socket = socket.socket

        def blocked_socket(*args, **kwargs):
            raise AssertionError("deterministic pipeline attempted a network call")

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "target-repo"
            repo.mkdir()
            init_repo(repo)
            commit_file(repo, "a.py", "x = 1\n", "add a")

            socket.socket = blocked_socket
            try:
                report_path = run_deterministic_pipeline(str(repo))
            finally:
                socket.socket = original_socket

            self.assertTrue(report_path.exists())

    def test_second_repo_ranks_its_own_files_not_a_merge(self) -> None:
        # NFR-01: single-repo scope — running against a second repo must
        # not carry over or merge anything from the first run.
        with tempfile.TemporaryDirectory() as tmp:
            repo_a = Path(tmp) / "repo-a"
            repo_a.mkdir()
            init_repo(repo_a)
            commit_file(repo_a, "only_in_a.py", "x = 1\n", "add a")
            run_deterministic_pipeline(str(repo_a))

            repo_b = Path(tmp) / "repo-b"
            repo_b.mkdir()
            init_repo(repo_b)
            commit_file(repo_b, "only_in_b.py", "y = 2\n", "add b")
            report_path = run_deterministic_pipeline(str(repo_b))
            content = report_path.read_text()

            self.assertIn("only_in_b.py", content)
            self.assertNotIn("only_in_a.py", content)


class SkillMdOrchestrationTests(unittest.TestCase):
    """Cross-checks that the shipped prose in SKILL.md actually names the
    same call sequence this test proves works, and carries the guarantees
    FR-11/NFR-01/FR-05 require — not a directory-existence check that could
    never fail (the NFR-03 mistake this branch already caught once)."""

    def setUp(self) -> None:
        self.text = SKILL_MD.read_text()

    def test_skill_md_exists(self) -> None:
        self.assertTrue(SKILL_MD.exists())

    def test_pipeline_names_every_deterministic_function_in_order(self) -> None:
        ordered_calls = [
            "shallow_guard.is_shallow",
            "file_universe.resolve_files",
            "churn.extract_churn",
            "complexity.complexity",
            "scorer.score_files",
            "labeler.label_files",
            "report_renderer.render_report",
        ]
        positions = [self.text.index(call) for call in ordered_calls]
        self.assertEqual(positions, sorted(positions))

    def test_states_single_repo_scope_no_multi_repo_affordance(self) -> None:
        self.assertIn("Exactly one repo per", self.text)
        self.assertNotIn("--repos", self.text)
        self.assertNotIn("--paths", self.text)

    def test_states_interpret_pass_is_the_only_model_call(self) -> None:
        self.assertIn("only step in the entire pipeline that touches a", self.text)

    def test_states_shallow_warning_reaches_the_report(self) -> None:
        self.assertIn("shallow_warning=", self.text)


if __name__ == "__main__":
    unittest.main()
