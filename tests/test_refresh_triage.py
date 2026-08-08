#!/usr/bin/env python3
"""Tests for claude/.claude/hooks/refresh_triage.py"""

import importlib.machinery
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import call, patch

HOOKS = Path(__file__).parent.parent / "claude" / ".claude" / "hooks"
FAKE_DEV = "/fake/dev"


def load_hook(name):
    mod_name = name.replace(".", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(HOOKS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


hook = load_hook("refresh_triage.py")


def _run(payload: str) -> list:
    """Run hook.main() with payload on stdin; return subprocess.run call list."""
    calls = []
    with patch("sys.stdin", io.StringIO(payload)), patch(
        "subprocess.run", side_effect=lambda args, **kw: calls.append(args)
    ) as _mock, patch.object(hook, "DEV", FAKE_DEV):
        hook.main()
    return calls


def _json(path: str) -> str:
    return json.dumps({"tool_input": {"file_path": path}})


class TestPathGuard(unittest.TestCase):
    def test_invalid_json_no_subprocess_calls(self):
        calls = _run("not valid json{{{")
        self.assertEqual(calls, [])

    def test_empty_string_no_calls(self):
        calls = _run("")
        self.assertEqual(calls, [])

    def test_non_todos_file_ignored(self):
        calls = _run(_json(f"{FAKE_DEV}/TODOS.md.bak"))
        self.assertEqual(calls, [])

    def test_readme_ignored(self):
        calls = _run(_json(f"{FAKE_DEV}/proj/README.md"))
        self.assertEqual(calls, [])

    def test_empty_file_path_ignored(self):
        calls = _run(json.dumps({"tool_input": {"file_path": ""}}))
        self.assertEqual(calls, [])

    def test_missing_tool_input_ignored(self):
        calls = _run(json.dumps({"other_key": "value"}))
        self.assertEqual(calls, [])

    def test_todos_outside_dev_ignored(self):
        calls = _run(_json("/home/user/other-dir/TODOS.md"))
        self.assertEqual(calls, [])

    def test_todos_in_sibling_dir_ignored(self):
        # /fake/devother/TODOS.md is NOT under /fake/dev
        calls = _run(_json("/fake/devother/TODOS.md"))
        self.assertEqual(calls, [])

    def test_dev_root_todos_ignored(self):
        # ~/dev is not a project — only its subdirectories are
        calls = _run(_json(f"{FAKE_DEV}/TODOS.md"))
        self.assertEqual(calls, [])


class TestProjectDetection(unittest.TestCase):
    def test_subdir_todos_uses_folder_name(self):
        calls = _run(_json(f"{FAKE_DEV}/myproject/TODOS.md"))
        self.assertEqual(calls[0][1], "myproject")

    def test_nested_project_uses_immediate_parent(self):
        # ~/dev/proj/sub/TODOS.md — parent is "sub", not "proj"
        calls = _run(_json(f"{FAKE_DEV}/proj/sub/TODOS.md"))
        self.assertEqual(calls[0][1], "sub")


class TestSubprocessCalls(unittest.TestCase):
    def test_update_cache_called_first(self):
        calls = _run(_json(f"{FAKE_DEV}/proj/TODOS.md"))
        self.assertEqual(calls[0][0], "update-cache")

    def test_update_triage_called_second(self):
        calls = _run(_json(f"{FAKE_DEV}/proj/TODOS.md"))
        self.assertEqual(calls[1], ["update-triage"])

    def test_update_cache_receives_project_and_path(self):
        path = f"{FAKE_DEV}/proj/TODOS.md"
        calls = _run(_json(path))
        self.assertEqual(calls[0], ["update-cache", "proj", path])

    def test_exactly_two_calls_on_valid_todos(self):
        calls = _run(_json(f"{FAKE_DEV}/proj/TODOS.md"))
        self.assertEqual(len(calls), 2)

    def test_no_calls_on_ignored_file(self):
        calls = _run(_json(f"{FAKE_DEV}/proj/notes.md"))
        self.assertEqual(len(calls), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
