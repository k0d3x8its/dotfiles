#!/usr/bin/env python3
"""Tests for code-decay/scripts/proxy_backend.py — pins the never-errors
guarantee and the tab-indented non-zero nesting requirement."""

import importlib.machinery
import importlib.util
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


proxy_backend = load_module("proxy_backend.py")
compute = proxy_backend.compute


class ComputeTests(unittest.TestCase):
    def test_counts_branch_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.rb"
            target.write_text(
                "def f(x)\n"
                "  if x\n"
                "    for i in 1..3\n"
                "      x\n"
                "    end\n"
                "  end\n"
                "end\n"
            )
            result = compute(str(target))

            self.assertEqual(result.branch_count, 2)

    def test_stray_one_space_line_does_not_collapse_indent_unit(self) -> None:
        # Regression lock: a global min()-based detector reads a single
        # 1-space-indented comment/continuation line as the whole file's
        # indent unit, inflating a real depth of 2 to 8. The detector must
        # use the mode of deepening steps instead.
        target_content = (
            "def f\n"
            "    if x\n"
            "        y\n"
            "    end\n"
            "end\n"
            " # 1-space comment\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.rb"
            target.write_text(target_content)

            result = compute(str(target))

            self.assertEqual(result.nesting_depth, 2)

    def test_space_indent_nesting_uses_detected_unit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.rb"
            # 2-space indent unit; deepest line is 3 levels in.
            target.write_text("a\n  b\n    c\n      d\n")

            result = compute(str(target))

            self.assertEqual(result.nesting_depth, 3)

    def test_tab_indented_file_has_nonzero_nesting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.rb"
            target.write_text("a\n\tb\n\t\tc\n")

            result = compute(str(target))

            self.assertGreater(result.nesting_depth, 0)
            self.assertEqual(result.nesting_depth, 2)

    def test_missing_file_never_errors(self) -> None:
        result = compute("/nonexistent/path/does/not/exist.xyz")

        self.assertEqual(result.branch_count, 0)
        self.assertEqual(result.nesting_depth, 0)

    def test_empty_file_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "empty.xyz"
            target.write_text("")

            result = compute(str(target))

            self.assertEqual(result.branch_count, 0)
            self.assertEqual(result.nesting_depth, 0)


if __name__ == "__main__":
    unittest.main()
