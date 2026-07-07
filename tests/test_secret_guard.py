#!/usr/bin/env python3
"""Tests for claude/.claude/hooks/secret_guard.py (S1 secret guard).

Two surfaces:
  - resolve_repo_cwd(): the hook fires BEFORE the command runs, so the
    payload cwd is the session cwd — `cd repo && git commit` or
    `git -C repo commit` target a different repo than the one gitleaks
    would scan. These tests pin the target-repo recovery (2026-07-07 fix).
  - main(): commit/push routing into gitleaks + fail-open behavior.
"""

import importlib.machinery
import importlib.util
import io
import json
import os
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


hook = load_hook("secret_guard.py")


class TestResolveRepoCwd(unittest.TestCase):
    """resolve_repo_cwd(command, session_cwd) → the repo gitleaks must scan."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = self._tmp.name  # exists → passes the isdir gate
        self.session = "/session/cwd"

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_cd_or_dash_c_falls_back_to_session_cwd(self):
        got = hook.resolve_repo_cwd("git commit -m 'x'", self.session)
        self.assertEqual(got, self.session)

    def test_cd_then_git_resolves_cd_target(self):
        got = hook.resolve_repo_cwd(f"cd {self.repo} && git commit -m x", self.session)
        self.assertEqual(got, self.repo)

    def test_git_dash_c_resolves_target(self):
        got = hook.resolve_repo_cwd(f"git -C {self.repo} commit -m x", self.session)
        self.assertEqual(got, self.repo)

    def test_dash_c_wins_over_cd(self):
        # git -C names the repo the git call actually runs against
        other = tempfile.mkdtemp()
        try:
            got = hook.resolve_repo_cwd(
                f"cd {other} && git -C {self.repo} commit -m x", self.session
            )
            self.assertEqual(got, self.repo)
        finally:
            os.rmdir(other)

    def test_double_quoted_cd_path(self):
        got = hook.resolve_repo_cwd(f'cd "{self.repo}" && git commit', self.session)
        self.assertEqual(got, self.repo)

    def test_single_quoted_dash_c_path(self):
        got = hook.resolve_repo_cwd(f"git -C '{self.repo}' push", self.session)
        self.assertEqual(got, self.repo)

    def test_quoted_path_with_spaces(self):
        spaced = os.path.join(self.repo, "my repo")
        os.mkdir(spaced)
        got = hook.resolve_repo_cwd(f'cd "{spaced}" && git commit', self.session)
        self.assertEqual(got, spaced)

    def test_tilde_expansion(self):
        with patch.dict(os.environ, {"HOME": self.repo}):
            got = hook.resolve_repo_cwd("cd ~/ && git commit", self.session)
        self.assertEqual(os.path.normpath(got), os.path.normpath(self.repo))

    def test_relative_path_joined_onto_session_cwd(self):
        sub = os.path.join(self.repo, "proj")
        os.mkdir(sub)
        got = hook.resolve_repo_cwd("cd proj && git commit", self.repo)
        self.assertEqual(got, sub)

    def test_nonexistent_dir_falls_back_to_session_cwd(self):
        got = hook.resolve_repo_cwd("cd /no/such/dir && git commit", self.session)
        self.assertEqual(got, self.session)

    def test_cd_after_git_ignored(self):
        # only a cd BEFORE the git call changes where git runs
        got = hook.resolve_repo_cwd(f"git commit -m x && cd {self.repo}", self.session)
        self.assertEqual(got, self.session)

    def test_last_cd_before_git_wins(self):
        first = tempfile.mkdtemp()
        try:
            got = hook.resolve_repo_cwd(
                f"cd {first} && cd {self.repo} && git commit", self.session
            )
            self.assertEqual(got, self.repo)
        finally:
            os.rmdir(first)


def _run_main(command, cwd="/session/cwd", gitleaks_result=(0, ""), which=True):
    """Run hook.main() with the subprocess boundary mocked.

    Returns (exit_code, stderr_text, gitleaks_calls) where gitleaks_calls is
    the list of (args, cwd) run_gitleaks received.
    """
    payload = json.dumps({"tool_input": {"command": command}, "cwd": cwd})
    calls = []

    def fake_gitleaks(args, cwd):
        calls.append((args, cwd))
        return gitleaks_result

    err = io.StringIO()
    with patch("sys.stdin", io.StringIO(payload)), \
         patch("sys.stderr", err), \
         patch.object(hook.shutil, "which", return_value="/usr/bin/gitleaks" if which else None), \
         patch.object(hook, "run_gitleaks", side_effect=fake_gitleaks), \
         patch.object(hook, "has_upstream", return_value=True), \
         patch.object(hook, "resolve_repo_cwd", side_effect=lambda c, s: s):
        code = hook.main()
    return code, err.getvalue(), calls


class TestMainRouting(unittest.TestCase):
    def test_non_git_command_never_scans(self):
        code, _, calls = _run_main("ls -la")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [])

    def test_git_status_never_scans(self):
        code, _, calls = _run_main("git status")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [])

    def test_commit_scans_staged(self):
        code, _, calls = _run_main("git commit -m 'x'")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(["git", "--pre-commit", "--staged"], "/session/cwd")])

    def test_push_with_upstream_scans_unpushed_range(self):
        code, _, calls = _run_main("git push")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(["git", "--log-opts=@{u}..HEAD"], "/session/cwd")])

    def test_first_push_without_upstream_scans_last_20(self):
        payload = json.dumps({"tool_input": {"command": "git push -u origin main"}, "cwd": "/s"})
        calls = []
        with patch("sys.stdin", io.StringIO(payload)), \
             patch("sys.stderr", io.StringIO()), \
             patch.object(hook.shutil, "which", return_value="/usr/bin/gitleaks"), \
             patch.object(hook, "run_gitleaks", side_effect=lambda a, c: calls.append((a, c)) or (0, "")), \
             patch.object(hook, "has_upstream", return_value=False), \
             patch.object(hook, "resolve_repo_cwd", side_effect=lambda c, s: s):
            code = hook.main()
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(["git", "--log-opts=-n 20"], "/s")])

    def test_findings_block_commit_with_reason(self):
        code, err, _ = _run_main("git commit -m x", gitleaks_result=(1, "leak: aws-key file.py:3"))
        self.assertEqual(code, 2)
        self.assertIn("commit blocked", err)
        self.assertIn("leak: aws-key file.py:3", err)

    def test_findings_block_push(self):
        code, err, _ = _run_main("git push origin main", gitleaks_result=(1, "leak"))
        self.assertEqual(code, 2)
        self.assertIn("push blocked", err)


class TestFailOpen(unittest.TestCase):
    """A broken scanner must never brick every commit — the deny is about
    leaks, not tooling health."""

    def test_gitleaks_not_installed_allows_with_note(self):
        code, err, calls = _run_main("git commit -m x", which=False)
        self.assertEqual(code, 0)
        self.assertEqual(calls, [])
        self.assertIn("fail-open", err)

    def test_gitleaks_config_error_allows_with_note(self):
        code, err, _ = _run_main("git commit -m x", gitleaks_result=(3, "config parse error"))
        self.assertEqual(code, 0)
        self.assertIn("scan skipped", err)

    def test_gitleaks_crash_allows(self):
        payload = json.dumps({"tool_input": {"command": "git commit -m x"}, "cwd": "/s"})
        with patch("sys.stdin", io.StringIO(payload)), \
             patch("sys.stderr", io.StringIO()), \
             patch.object(hook.shutil, "which", return_value="/usr/bin/gitleaks"), \
             patch.object(hook, "run_gitleaks", side_effect=OSError("boom")), \
             patch.object(hook, "resolve_repo_cwd", side_effect=lambda c, s: s):
            self.assertEqual(hook.main(), 0)

    def test_malformed_json_allows(self):
        with patch("sys.stdin", io.StringIO("not json{{{")), patch("sys.stderr", io.StringIO()):
            self.assertEqual(hook.main(), 0)

    def test_non_string_command_allows(self):
        payload = json.dumps({"tool_input": {"command": 42}, "cwd": "/s"})
        with patch("sys.stdin", io.StringIO(payload)), patch("sys.stderr", io.StringIO()):
            self.assertEqual(hook.main(), 0)


class TestAddAndCommitLimitation(unittest.TestCase):
    """DOCUMENTED LIMITATION: for `git add secret.txt && git commit` in ONE
    Bash call, the hook fires before the command runs, so the `git add` has
    not happened yet — the staged scan inspects the PRE-add index and cannot
    see the file being added. The guard still catches it one call later
    (the commit of an already-staged secret) and at push time. This test
    pins the current behavior so any future fix consciously flips it."""

    def test_add_and_commit_single_call_scans_pre_add_index(self):
        code, _, calls = _run_main("git add secret.txt && git commit -m x")
        # scan runs (commit detected) but against --staged as of hook time
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(["git", "--pre-commit", "--staged"], "/session/cwd")])


if __name__ == "__main__":
    unittest.main()
