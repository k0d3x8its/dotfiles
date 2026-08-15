#!/usr/bin/env python3
"""Tests for claude/.claude/hooks/standards_guard.py.

Contract under test:
  PreToolUse (Edit|Write) — main(["pre"]) reads a payload on stdin, returns
    0 (allow) or 2 (block, missing paths on stderr).
  PostToolUse (Read)      — main(["post"]) records a references/code/ read
    into a per-session marker file; always exits 0, silent stdout.
Fail-open on any error — a broken guard must never wedge editing.
"""

import importlib.machinery
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HOOKS = Path(__file__).parent.parent / "claude" / ".claude" / "hooks"


def load_hook(name):
    mod_name = name.replace(".", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(HOOKS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


hook = load_hook("standards_guard.py")

SESSION = "test-session-abc"


class GuardTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        marker_dir = Path(self._tmp.name) / "session_timing" / "standards_guard"
        self._patch = patch.object(hook, "MARKER_DIR", marker_dir)
        self._patch.start()
        self.addCleanup(self._patch.stop)

    def _pre(self, file_path, new_string="x" * 100, tool_name="Edit", content=None):
        tool_input = {"file_path": file_path}
        if tool_name == "Write":
            tool_input["content"] = content if content is not None else new_string
        else:
            tool_input["old_string"] = "old"
            tool_input["new_string"] = new_string
        payload = json.dumps(
            {"session_id": SESSION, "tool_name": tool_name, "tool_input": tool_input}
        )
        err = io.StringIO()
        with patch("sys.stdin", io.StringIO(payload)), patch("sys.stderr", err):
            code = hook.main(["pre"])
        return code, err.getvalue()

    def _post(self, file_path):
        payload = json.dumps(
            {
                "session_id": SESSION,
                "tool_name": "Read",
                "tool_input": {"file_path": file_path},
            }
        )
        out = io.StringIO()
        with patch("sys.stdin", io.StringIO(payload)), patch("sys.stdout", out):
            code = hook.main(["post"])
        return code, out.getvalue()

    def _mark_read(self, *basenames):
        for b in basenames:
            self._post(str(hook.REFS_DIR / b))


class TestBlocksWithoutRead(GuardTestCase):
    def test_py_edit_without_read_blocks(self):
        code, err = self._pre("/repo/foo.py")
        self.assertEqual(code, 2)
        self.assertIn("CODE-STANDARD.md", err)
        self.assertIn("PYTHON.md", err)

    def test_non_code_path_allowed(self):
        code, _ = self._pre("/repo/TODOS.md")
        self.assertEqual(code, 0)

    def test_unmapped_extension_allowed(self):
        code, _ = self._pre("/repo/data.json")
        self.assertEqual(code, 0)


class TestAllowsAfterRead(GuardTestCase):
    def test_py_edit_after_reading_both_allows(self):
        self._mark_read("CODE-STANDARD.md", "PYTHON.md")
        code, _ = self._pre("/repo/foo.py")
        self.assertEqual(code, 0)

    def test_py_edit_partial_read_still_blocks(self):
        self._mark_read("CODE-STANDARD.md")
        code, err = self._pre("/repo/foo.py")
        self.assertEqual(code, 2)
        self.assertIn("PYTHON.md", err)

    def test_marker_scoped_per_session(self):
        self._mark_read("CODE-STANDARD.md", "PYTHON.md")
        payload = json.dumps(
            {
                "session_id": "other-session",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "/repo/foo.py",
                    "old_string": "old",
                    "new_string": "x" * 100,
                },
            }
        )
        err = io.StringIO()
        with patch("sys.stdin", io.StringIO(payload)), patch("sys.stderr", err):
            code = hook.main(["pre"])
        self.assertEqual(code, 2)


class TestTestFileRequiresTestingStandard(GuardTestCase):
    def test_test_file_without_testing_standard_blocks(self):
        self._mark_read("CODE-STANDARD.md", "PYTHON.md")
        code, err = self._pre("/repo/tests/test_foo.py")
        self.assertEqual(code, 2)
        self.assertIn("TESTING-STANDARD.md", err)

    def test_test_file_with_all_three_allows(self):
        self._mark_read("CODE-STANDARD.md", "PYTHON.md", "TESTING-STANDARD.md")
        code, _ = self._pre("/repo/tests/test_foo.py")
        self.assertEqual(code, 0)

    def test_star_test_suffix_basename_detected(self):
        self._mark_read("CODE-STANDARD.md", "PYTHON.md")
        code, err = self._pre("/repo/foo_test.py")
        self.assertEqual(code, 2)
        self.assertIn("TESTING-STANDARD.md", err)


class TestLanguageMapping(GuardTestCase):
    def test_bash_script_requires_bash_md(self):
        code, err = self._pre("/repo/install.sh")
        self.assertEqual(code, 2)
        self.assertIn("BASH.md", err)

    def test_typescript_requires_typescript_md(self):
        code, err = self._pre("/repo/app.tsx")
        self.assertEqual(code, 2)
        self.assertIn("TYPESCRIPT.md", err)

    def test_solidity_requires_solidity_md(self):
        code, err = self._pre("/repo/Token.sol")
        self.assertEqual(code, 2)
        self.assertIn("SOLIDITY.md", err)

    def test_bats_test_requires_bash_md_and_testing_standard(self):
        code, err = self._pre("/repo/tests/install.bats")
        self.assertEqual(code, 2)
        self.assertIn("BASH.md", err)
        self.assertIn("TESTING-STANDARD.md", err)

    def test_bats_outside_tests_dir_requires_only_bash_md(self):
        code, err = self._pre("/repo/scripts/helper.bats")
        self.assertEqual(code, 2)
        self.assertIn("BASH.md", err)
        self.assertNotIn("TESTING-STANDARD.md", err)


class TestTrivialEditThreshold(GuardTestCase):
    def test_tiny_new_string_allowed_without_read(self):
        code, _ = self._pre("/repo/foo.py", new_string="x")
        self.assertEqual(code, 0)

    def test_large_new_string_blocked_without_read(self):
        code, _ = self._pre("/repo/foo.py", new_string="x" * 200)
        self.assertEqual(code, 2)

    def test_write_tool_uses_content_length(self):
        code, _ = self._pre("/repo/foo.py", tool_name="Write", content="x")
        self.assertEqual(code, 0)
        code, _ = self._pre("/repo/foo.py", tool_name="Write", content="x" * 200)
        self.assertEqual(code, 2)


class TestFailOpen(GuardTestCase):
    def test_malformed_json_allows(self):
        with patch("sys.stdin", io.StringIO("not json{{")), patch(
            "sys.stderr", io.StringIO()
        ):
            self.assertEqual(hook.main(["pre"]), 0)

    def test_missing_file_path_allows(self):
        payload = json.dumps({"session_id": SESSION, "tool_input": {}})
        with patch("sys.stdin", io.StringIO(payload)), patch(
            "sys.stderr", io.StringIO()
        ):
            self.assertEqual(hook.main(["pre"]), 0)

    def test_unwritable_marker_dir_fails_open_on_post(self):
        with patch.object(hook, "MARKER_DIR", Path("/nonexistent-root-only/x/y")):
            code, out = self._post(str(hook.REFS_DIR / "PYTHON.md"))
            self.assertEqual(code, 0)
            self.assertEqual(out, "")

    def test_post_of_unrelated_file_does_not_satisfy_pre(self):
        self._post("/repo/README.md")
        code, _ = self._pre("/repo/foo.py")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
