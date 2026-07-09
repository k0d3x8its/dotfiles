#!/usr/bin/env python3
"""Session timer hook for Codex.

Suggests a handoff when the session runs long or the context window fills up.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

TIMING_DIR = Path.home() / ".codex" / "session_timing"
TIMESTAMP_FILE = TIMING_DIR / "session_start.txt"
WARNED_SUGGEST = TIMING_DIR / "warned_suggest.flag"
WARNED_URGENT = TIMING_DIR / "warned_urgent.flag"

TIME_SUGGEST = 45 * 60
CONTEXT_SUGGEST_PCT = 40
TIME_URGENT = 55 * 60
CONTEXT_URGENT_PCT = 45
CONTEXT_WINDOW = 200_000


def emit_system_message(msg):
    print(json.dumps({"systemMessage": msg}), flush=True)


def session_start():
    TIMING_DIR.mkdir(parents=True, exist_ok=True)
    TIMESTAMP_FILE.write_text(str(time.time()))
    WARNED_SUGGEST.unlink(missing_ok=True)
    WARNED_URGENT.unlink(missing_ok=True)


def read_hook_stdin():
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def context_pct(transcript_path):
    if not transcript_path:
        return None
    try:
        p = Path(transcript_path)
        if not p.exists():
            return None
        size = p.stat().st_size
        with p.open("rb") as f:
            if size > 512 * 1024:
                f.seek(-512 * 1024, os.SEEK_END)
                f.readline()
            chunk = f.read().decode("utf-8", errors="replace")

        for line in reversed(chunk.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            usage = (obj.get("message") or {}).get("usage")
            if not usage or "input_tokens" not in usage:
                continue
            used = (
                usage.get("input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
            )
            if used <= 0:
                return None
            return min(100, round(used / CONTEXT_WINDOW * 100))
    except Exception:
        return None
    return None


def _git(cwd, *args):
    try:
        out = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def recommend_handoff(cwd):
    if not cwd or not Path(cwd).exists():
        return "Recommend -> /close (light) or /checkpoint (if decisions made). Tangent? /handoff."

    baseline = ""
    bfile = Path(cwd) / ".episodic-baseline"
    if bfile.exists():
        try:
            baseline = bfile.read_text().strip()
        except Exception:
            baseline = ""

    commits = 0
    if baseline:
        n = _git(cwd, "rev-list", "--count", f"{baseline}..HEAD")
        commits = int(n) if n.isdigit() else 0

    dirty = _git(cwd, "status", "--porcelain")
    dirty_files = len([ln for ln in dirty.splitlines() if ln.strip()])

    if commits > 0:
        plural = "s" if commits != 1 else ""
        return f"Recommend -> /checkpoint ({commits} commit{plural} this session - persist the why). Tangent? /handoff. Light wrap? /close."
    if dirty_files >= 3:
        return f"Recommend -> /checkpoint ({dirty_files} files changed, uncommitted - capture the decisions). Tangent? /handoff. Light wrap? /close."
    if dirty_files >= 1:
        return "Recommend -> /close (light session, no commits). Tangent? /handoff."
    return "Recommend -> /close (no changes this session). Tangent? /handoff."


def check_elapsed():
    if not TIMESTAMP_FILE.exists():
        session_start()
        return

    data = read_hook_stdin()
    cwd = data.get("cwd") or os.getcwd()
    pct = context_pct(data.get("transcript_path"))

    start = float(TIMESTAMP_FILE.read_text().strip())
    elapsed = time.time() - start
    mins = int(elapsed // 60)

    time_urgent = elapsed >= TIME_URGENT
    ctx_urgent = pct is not None and pct >= CONTEXT_URGENT_PCT
    time_suggest = elapsed >= TIME_SUGGEST
    ctx_suggest = pct is not None and pct >= CONTEXT_SUGGEST_PCT

    ctx_str = f"ctx {pct}%" if pct is not None else "ctx n/a"

    def reason(time_hit, ctx_hit):
        if time_hit and ctx_hit:
            return f"{mins}m elapsed + {ctx_str}"
        if ctx_hit:
            return f"{ctx_str} ({mins}m elapsed)"
        return f"{mins}m elapsed ({ctx_str})"

    if time_urgent or ctx_urgent:
        if not WARNED_URGENT.exists():
            WARNED_URGENT.write_text("1")
            emit_system_message(
                f"Session getting long ({reason(time_urgent, ctx_urgent)}). {recommend_handoff(cwd)}"
            )
        return

    if time_suggest or ctx_suggest:
        if not WARNED_SUGGEST.exists():
            WARNED_SUGGEST.write_text("1")
            emit_system_message(
                f"Session is getting long ({reason(time_suggest, ctx_suggest)}). {recommend_handoff(cwd)}"
            )



def hook_event(data):
    for key in (
        "hook_event_name",
        "hookEventName",
        "event",
        "event_name",
        "eventName",
        "name",
    ):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("HOOK_EVENT") or ""


def main():
    data = read_hook_stdin()
    event = hook_event(data)
    if event == "SessionStart":
        session_start()
        return
    if event in {"Stop", "SessionEnd"}:
        check_elapsed()
        return

    # If Codex exposes a different hook payload shape, remain silent rather
    # than risk treating a non-session event as a timer tick.


if __name__ == "__main__":
    main()
