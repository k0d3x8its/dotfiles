#!/usr/bin/env python3
"""Unit tests for code-decay/scripts/interpret_selection.py — the deterministic
front end of the Interpret Pass (FR-10/FR-11): which files clear the score
floor and make the top-N cut. The actual model call is the CLI entrypoint's
job, not this module's — this module never touches a model."""

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


interpret_selection = load_module("interpret_selection.py")
select_for_interpretation = interpret_selection.select_for_interpretation


def make_distribution() -> dict[str, tuple[int, int]]:
    # 9 quiet files (score 1-3) plus 3 real hotspots (score 500-900) — 3-of-12
    # is exactly the 25% the p75 floor needs above it, so the floor lands
    # cleanly between the two groups (measured: floor=127.25) rather than
    # inside the quiet cluster the way an unbalanced fixture would (p75 needs
    # real headroom above the top quartile's own count, not just a big gap in
    # raw score values).
    rows = {f"quiet_{i}.py": (1, i % 3 + 1) for i in range(9)}
    rows["hot_1.py"] = (10, 50)  # score 500
    rows["hot_2.py"] = (20, 40)  # score 800
    rows["hot_3.py"] = (30, 30)  # score 900
    return rows


class SelectForInterpretationTests(unittest.TestCase):
    def test_selects_only_files_above_the_score_floor(self) -> None:
        selected = select_for_interpretation(make_distribution(), top_n=10)

        self.assertEqual(set(selected), {"hot_1.py", "hot_2.py", "hot_3.py"})

    def test_sorted_descending_by_score(self) -> None:
        selected = select_for_interpretation(make_distribution(), top_n=10)

        self.assertEqual(selected, ["hot_3.py", "hot_2.py", "hot_1.py"])

    def test_caps_at_top_n_even_when_more_clear_the_floor(self) -> None:
        selected = select_for_interpretation(make_distribution(), top_n=2)

        self.assertEqual(selected, ["hot_3.py", "hot_2.py"])

    def test_never_pads_below_top_n_when_fewer_files_clear_the_floor(self) -> None:
        # Only 3 files clear the floor; asking for 10 must return exactly 3,
        # never padded with non-hotspots (FR-10's own "states actual count,
        # never pads" clause).
        selected = select_for_interpretation(make_distribution(), top_n=10)

        self.assertEqual(len(selected), 3)

    def test_empty_input_returns_empty_selection(self) -> None:
        self.assertEqual(select_for_interpretation({}, top_n=10), [])

    def test_floor_is_percentile_of_this_calls_own_distribution(self) -> None:
        # Same (churn, cx) pair for "target": reads as a hotspot in a quiet
        # repo, but the floor rises once the repo is genuinely busy — the
        # floor is never a hardcoded score constant. `busy_repo` also proves
        # the case out: all 9 "hot" files tie exactly at the p75 floor
        # (score 10000), and the >= comparison (not >) means a tied cluster
        # sitting AT the boundary is still eligible — top_n is what bounds the
        # output, not the tie itself.
        quiet_repo = {"target.py": (10, 10), "peer.py": (1, 1)}
        busy_repo = {
            "target.py": (10, 10),
            **{f"hot_{i}.py": (50, 200) for i in range(9)},
        }

        busy_selection = select_for_interpretation(busy_repo, top_n=10)

        self.assertIn("target.py", select_for_interpretation(quiet_repo, top_n=10))
        self.assertNotIn("target.py", busy_selection)
        self.assertIn("hot_0.py", busy_selection)
        self.assertEqual(len(busy_selection), 9)

    def test_tied_at_floor_files_are_included_via_ge_not_gt(self) -> None:
        # All 4 files share the exact same score, which lands exactly at p75
        # by construction (single-value distribution). None should be
        # excluded for merely tying the floor instead of clearing it.
        rows = {f"tied_{i}.py": (10, 10) for i in range(4)}

        selected = select_for_interpretation(rows, top_n=10)

        self.assertEqual(set(selected), set(rows))


if __name__ == "__main__":
    unittest.main()
