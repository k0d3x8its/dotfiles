#!/usr/bin/env python3
"""Tests for code-decay/scripts/complexity.py — the Dispatcher's routing by
extension, including the `.ino` -> cpp special case that needs no separate
language-mapping config."""

import importlib.machinery
import importlib.util
import shutil
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


complexity_module = load_module("complexity.py")
complexity = complexity_module.complexity

HAS_AST_GREP = shutil.which("ast-grep") is not None


class RoutingTests(unittest.TestCase):
    def test_unsupported_extension_routes_to_proxy_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.rb"
            target.write_text("if x\n  y\nend\n")

            # Proxy backend counts "if" as a branch keyword; ast-grep has no
            # .rb entry in EXTENSION_TO_LANG so this can only be the proxy.
            result = complexity(str(target))

            self.assertEqual(result.branch_count, 1)

    def test_unknown_extension_never_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.unknownext"
            target.write_text("plain text, no code\n")

            result = complexity(str(target))

            self.assertEqual(result.branch_count, 0)

    @unittest.skipUnless(HAS_AST_GREP, "ast-grep binary not on PATH")
    def test_python_extension_routes_to_ast_grep_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.py"
            target.write_text("def f(x):\n    if x:\n        pass\n")

            result = complexity(str(target))

            self.assertEqual(result.branch_count, 1)

    @unittest.skipUnless(HAS_AST_GREP, "ast-grep binary not on PATH")
    def test_ino_extension_routes_to_cpp_backend_with_no_mapping_config(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sketch.ino"
            target.write_text("void loop() { if (true) {} }\n")

            result = complexity(str(target))

            self.assertEqual(result.branch_count, 1)

    def test_cx_value_is_branch_count_plus_nesting_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.rb"
            target.write_text("a\n  if x\n    b\n")

            result = complexity(str(target))

            self.assertEqual(result.value, result.branch_count + result.nesting_depth)

    @unittest.skipUnless(HAS_AST_GREP, "ast-grep binary not on PATH")
    def test_cx_never_reads_repo_wide_distribution(self) -> None:
        # No repo-relative rescale, ever: a fixed fixture's cx must be
        # identical whether it sits alone or beside a large, complex sibling.
        content = "def f(x):\n    if x:\n        for i in range(3):\n            pass\n"

        with tempfile.TemporaryDirectory() as tmp_alone:
            alone = Path(tmp_alone) / "f.py"
            alone.write_text(content)
            result_alone = complexity(str(alone))

        with tempfile.TemporaryDirectory() as tmp_crowded:
            target = Path(tmp_crowded) / "f.py"
            target.write_text(content)
            sibling = Path(tmp_crowded) / "huge.py"
            sibling.write_text("\n".join(f"if x == {i}:\n    pass" for i in range(200)))
            result_crowded = complexity(str(target))

        self.assertEqual(result_alone, result_crowded)


if __name__ == "__main__":
    unittest.main()
