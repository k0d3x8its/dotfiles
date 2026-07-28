#!/usr/bin/env python3
"""Tests for code-decay/scripts/ast_grep_backend.py — real `ast-grep` CLI
calls (not mocked) so the branch-kind names and containment-depth algorithm
are proven against the real tree-sitter grammars, and the exit-code-1-means-
no-matches distinction (a real bug caught by hand, not by a test) stays
locked."""

import importlib.machinery
import importlib.util
import os
import shutil
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


ast_grep_backend = load_module("ast_grep_backend.py")
compute = ast_grep_backend.compute
AstGrepBackendError = ast_grep_backend.AstGrepBackendError

HAS_AST_GREP = shutil.which("ast-grep") is not None


@unittest.skipUnless(HAS_AST_GREP, "ast-grep binary not on PATH")
class ComputeTests(unittest.TestCase):
    def test_flat_branches_have_depth_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "flat.py"
            target.write_text(
                "def f(x):\n"
                "    if x:\n"
                "        pass\n"
                "    for i in range(3):\n"
                "        pass\n"
                "    while True:\n"
                "        break\n"
            )
            result = compute(str(target), "python")

            self.assertEqual(result.branch_count, 3)
            self.assertEqual(result.nesting_depth, 1)

    def test_nested_branches_measure_containment_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested.py"
            target.write_text(
                "def f(x):\n"
                "    if x:\n"
                "        for i in range(3):\n"
                "            while True:\n"
                "                break\n"
            )
            result = compute(str(target), "python")

            self.assertEqual(result.branch_count, 3)
            self.assertEqual(result.nesting_depth, 3)

    def test_file_with_no_branches_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "flat_no_branch.py"
            target.write_text("x = 1\ny = 2\n")

            result = compute(str(target), "python")

            self.assertEqual(result.branch_count, 0)
            self.assertEqual(result.nesting_depth, 0)

    def test_lua_for_statement_kind_covers_numeric_and_generic_for(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "loops.lua"
            target.write_text(
                "local function f(x)\n"
                "  for i=1,3 do end\n"
                "  for k,v in pairs(x) do end\n"
                "end\n"
            )
            result = compute(str(target), "lua")

            self.assertEqual(result.branch_count, 2)

    def test_bash_uses_kind_based_matching_never_metavariable_pattern(self) -> None:
        # FR-12: `$A=$B` doesn't match bash assignments; this backend must
        # only ever invoke ast-grep with --kind, never --pattern. Live check
        # on the module source, not an assertion against BRANCH_KINDS (kind
        # names could never contain "--pattern" regardless of correctness).
        source = (SCRIPTS / "ast_grep_backend.py").read_text()
        self.assertNotIn("--pattern", source)
        self.assertIn('"--kind"', source)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "script.sh"
            target.write_text('if [ "$1" = "x" ]; then\n  echo hi\nfi\n')

            result = compute(str(target), "bash")

            self.assertEqual(result.branch_count, 1)

    def test_ino_extension_routes_through_cpp_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sketch.ino"
            target.write_text("void loop() { if (true) {} }\n")

            result = compute(str(target), "cpp")

            self.assertEqual(result.branch_count, 1)


class AstGrepMissingBinaryTests(unittest.TestCase):
    def test_missing_binary_fails_loud(self) -> None:
        # 2026-07-27 decision: fail loud, never silently degrade to the
        # proxy backend. Simulate a broken install with an empty PATH.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.py"
            target.write_text("x = 1\n")

            env_backup = os.environ.get("PATH")
            os.environ["PATH"] = ""
            try:
                with self.assertRaises(AstGrepBackendError):
                    compute(str(target), "python")
            finally:
                if env_backup is not None:
                    os.environ["PATH"] = env_backup


class MatchRangesReturnCodeTests(unittest.TestCase):
    @unittest.skipUnless(HAS_AST_GREP, "ast-grep binary not on PATH")
    def test_real_ast_grep_no_match_exit_code_is_not_an_error(self) -> None:
        # ast-grep exits 1 on zero matches, which subprocess.run(check=True)
        # would treat as a crash — this pins the fix that stopped that.
        result = subprocess.run(
            [
                "ast-grep",
                "run",
                "--lang",
                "python",
                "--kind",
                "match_statement",
                "--json=compact",
                __file__,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), "[]")


if __name__ == "__main__":
    unittest.main()
