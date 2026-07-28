#!/usr/bin/env python3
"""Unit tests for code-decay/scripts/percentile.py — linear-interpolation
percentile, shared by Labeler and the Interpret Pass selector."""

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


percentile_module = load_module("percentile.py")
percentile = percentile_module.percentile


class PercentileTests(unittest.TestCase):
    def test_empty_list_returns_zero(self) -> None:
        self.assertEqual(percentile([], 0.9), 0.0)

    def test_single_value_returns_that_value_at_any_target(self) -> None:
        self.assertEqual(percentile([7], 0.0), 7)
        self.assertEqual(percentile([7], 0.5), 7)
        self.assertEqual(percentile([7], 1.0), 7)

    def test_p0_returns_minimum(self) -> None:
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0.0), 1)

    def test_p100_returns_maximum(self) -> None:
        self.assertEqual(percentile([1, 2, 3, 4, 5], 1.0), 5)

    def test_p50_of_odd_length_returns_middle_value(self) -> None:
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0.5), 3)

    def test_interpolates_between_two_ranks(self) -> None:
        # rank = (4 values - 1) * 0.5 = 1.5 -> halfway between index 1 (2) and
        # index 2 (3).
        self.assertEqual(percentile([1, 2, 3, 4], 0.5), 2.5)

    def test_input_order_must_already_be_sorted(self) -> None:
        # percentile() trusts its caller to have sorted the input already —
        # an unsorted list silently produces a wrong answer rather than
        # raising, so this test documents the contract explicitly.
        self.assertNotEqual(percentile([5, 1, 3, 2, 4], 0.0), 1)


if __name__ == "__main__":
    unittest.main()
