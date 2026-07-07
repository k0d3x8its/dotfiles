#!/usr/bin/env python3
"""PreToolUse secret guard for git commit/push (S1).

Runs gitleaks before a `git commit` or `git push` leaves the machine:
  - commit → scan the STAGED diff (`gitleaks git --pre-commit --staged`)
  - push   → scan UNPUSHED commits (`--log-opts=@{u}..HEAD`); if the
             branch has no upstream yet (first push), scan the last 20
             commits as a bounded approximation.

Exit 2 (block) only when gitleaks reports findings (its exit code 1).
Any other gitleaks failure — not installed, config error, not a git
repo — fails OPEN with a stderr note: a broken scanner must not brick
every commit, and the deny is about leaks, not tooling health.

Findings are printed with --redact so the secret itself never lands in
the session transcript (which is itself a file on disk).
"""

import json
import os
import re
import shutil
import subprocess
import sys

COMMIT_RE = re.compile(r"\bgit\b[^|;&]*\bcommit\b")
PUSH_RE = re.compile(r"\bgit\b[^|;&]*\bpush\b")
# The hook fires BEFORE the command runs, so payload cwd is the session cwd —
# a `cd repo && git commit` targets a different repo than the one gitleaks
# would scan. Recover the real target from `git -C <path>` or the last
# `cd <path>` preceding the git call.
GIT_C_RE = re.compile(r"\bgit\s+-C\s+(?:\"([^\"]+)\"|'([^']+)'|(\S+))")
CD_RE = re.compile(r"\bcd\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s;|&]+))")


def resolve_repo_cwd(command, session_cwd):
    """Best-effort target-repo resolution; falls back to session cwd."""
    git_c = GIT_C_RE.search(command)
    if git_c:
        path = next(g for g in git_c.groups() if g)
    else:
        git_pos = command.find("git")
        cds = [m for m in CD_RE.finditer(command) if m.start() < git_pos]
        if not cds:
            return session_cwd
        path = next(g for g in cds[-1].groups() if g)
    path = os.path.expanduser(os.path.expandvars(path))
    if not os.path.isabs(path):
        path = os.path.join(session_cwd or ".", path)
    return path if os.path.isdir(path) else session_cwd


def run_gitleaks(args, cwd):
    """Returns (exit_code, output). gitleaks: 0 clean, 1 leaks, else error."""
    proc = subprocess.run(
        ["gitleaks"] + args + ["--redact", "--no-banner", "--exit-code", "1"],
        cwd=cwd or None,
        capture_output=True,
        text=True,
        timeout=45,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def has_upstream(cwd):
    return (
        subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "@{u}"],
            cwd=cwd or None,
            capture_output=True,
        ).returncode
        == 0
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
        cwd = payload.get("cwd", "")
    except Exception:
        return 0

    if not isinstance(command, str):
        return 0

    is_commit = bool(COMMIT_RE.search(command))
    is_push = bool(PUSH_RE.search(command))
    if not (is_commit or is_push):
        return 0

    cwd = resolve_repo_cwd(command, cwd)

    if not shutil.which("gitleaks"):
        print("secret-guard: gitleaks not on PATH — scan skipped (fail-open)", file=sys.stderr)
        return 0

    try:
        if is_commit:
            code, out = run_gitleaks(["git", "--pre-commit", "--staged"], cwd)
        else:
            log_opts = "@{u}..HEAD" if has_upstream(cwd) else "-n 20"
            code, out = run_gitleaks(["git", f"--log-opts={log_opts}"], cwd)
    except Exception as exc:
        print(f"secret-guard: gitleaks failed to run ({exc}) — scan skipped", file=sys.stderr)
        return 0

    if code == 1:
        action = "commit" if is_commit else "push"
        print(
            f"secret-guard: gitleaks found potential secrets — {action} blocked.\n"
            f"{out}\n"
            "Remove/rotate the secret or add a gitleaks allowlist entry "
            "(.gitleaks.toml) if it is a confirmed false positive.",
            file=sys.stderr,
        )
        return 2

    if code not in (0, 1):
        print(f"secret-guard: gitleaks error (exit {code}) — scan skipped:\n{out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
