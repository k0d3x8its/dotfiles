#!/usr/bin/env python3
"""Unit tests for code-decay/scripts/labeler.py — heuristic labels from
percentile thresholds of the CURRENT call's own distribution, display-only,
never a score input (FR-09/FR-15). Cutoffs and priority order per
`.work/findings/code-decay-label-percentile-cutoffs.md`."""

import importlib.machinery
import importlib.util
import sys
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


labeler = load_module("labeler.py")
label_files = labeler.label_files


def make_distribution() -> dict[str, tuple[int, int]]:
    # 10 files spanning a real spread so p50/p75/p90 land on distinct values,
    # mirroring the shape measured against kodex-ide (a few extreme outliers,
    # most files low on both axes).
    return {
        "dormant.py": (2, 200),  # high cx, low churn
        "god_class.py": (50, 200),  # high cx, high churn
        "shotgun.py": (50, 1),  # high churn, low cx
        "quiet_1.py": (1, 1),
        "quiet_2.py": (1, 2),
        "quiet_3.py": (2, 3),
        "quiet_4.py": (3, 4),
        "quiet_5.py": (4, 5),
        "quiet_6.py": (5, 6),
        "quiet_7.py": (6, 7),
    }


class LabelFilesTests(unittest.TestCase):
    def test_high_cx_low_churn_is_dormant_complexity(self) -> None:
        labels = label_files(make_distribution())

        self.assertEqual(labels["dormant.py"], "Dormant Complexity")

    def test_high_cx_high_churn_is_god_class(self) -> None:
        labels = label_files(make_distribution())

        self.assertEqual(labels["god_class.py"], "God Class")

    def test_high_churn_low_cx_is_shotgun_surgery(self) -> None:
        labels = label_files(make_distribution())

        self.assertEqual(labels["shotgun.py"], "Shotgun Surgery")

    def test_unremarkable_file_gets_no_label(self) -> None:
        labels = label_files(make_distribution())

        self.assertIsNone(labels["quiet_4.py"])

    def test_labels_are_mutually_exclusive(self) -> None:
        labels = label_files(make_distribution())

        # Each of the three named labels appears at most once in this fixture
        # — no file satisfies two label predicates at once.
        for name in ("Dormant Complexity", "God Class", "Shotgun Surgery"):
            self.assertLessEqual(list(labels.values()).count(name), 1)

    def test_changing_the_input_file_set_shifts_label_boundaries(self) -> None:
        # Same file (cx=10, churn=10) reads as top-of-distribution in a mostly
        # quiet repo, but unremarkable once genuinely hot files join the set —
        # percentiles come from THIS call's rows, never a hardcoded constant.
        small_quiet_repo = {
            "target.py": (10, 10),
            "peer_1.py": (1, 1),
            "peer_2.py": (1, 1),
        }
        large_busy_repo = {
            "target.py": (10, 10),
            **{f"hot_{i}.py": (50, 200) for i in range(9)},
        }

        quiet_label = label_files(small_quiet_repo)["target.py"]
        busy_label = label_files(large_busy_repo)["target.py"]

        self.assertNotEqual(quiet_label, busy_label)

    def test_changing_the_input_file_set_never_changes_a_files_score(self) -> None:
        # Labels shift (previous test); the score a Scorer would compute for
        # the same (churn, cx) pair MUST NOT — labels never feed back into it.
        scorer = load_module("scorer.py")
        rows_a = {"target.py": (10, 10), "peer.py": (1, 1)}
        rows_b = {"target.py": (10, 10), **{f"hot_{i}.py": (50, 200) for i in range(9)}}

        score_a = scorer.score_files(rows_a)["target.py"]
        score_b = scorer.score_files(rows_b)["target.py"]

        self.assertEqual(score_a, score_b)

    def test_empty_input_returns_empty_labels(self) -> None:
        self.assertEqual(label_files({}), {})

    def test_zero_variance_cx_does_not_mass_label_the_whole_universe(self) -> None:
        # A doc/config-heavy universe where every file's cx floors at 0: p90(cx)
        # is also 0, and `cx >= 0` is trivially true for everyone. Without the
        # `high_cx > 0` guard this would label the entire set God Class/Dormant
        # Complexity — a real failure mode, not a hypothetical (measured on a
        # low-variance slice of dotfiles' own universe). Churn still varies in
        # this fixture, so Shotgun Surgery (which only needs churn variance)
        # correctly still fires on the genuinely high-churn files.
        rows = {f"doc_{i}.md": (i % 5, 0) for i in range(20)}

        labels = label_files(rows)

        self.assertNotIn("God Class", labels.values())
        self.assertNotIn("Dormant Complexity", labels.values())


if __name__ == "__main__":
    unittest.main()
