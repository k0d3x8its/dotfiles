#!/usr/bin/env python3
"""
KOS Session Timer Hook
Suggests a handoff when the session runs long (45m / 55m) OR the context window
fills up (40% / 55%) — whichever happens first — and recommends WHICH handoff
tool to reach for.

Hook events used:
  SessionStart → record session start time, clear one-shot warning markers
  Stop         → check elapsed time + context fill; surface a one-shot suggestion
                 when a threshold is first crossed

Two independent trigger axes, OR'd together (whichever fires first wins):
  TIME    — wall-clock since SessionStart
  CONTEXT — % of the model context window consumed, read from the live transcript
            (last assistant turn's input + cache_creation + cache_read tokens).
  Rationale: a short-but-dense session can blow the context budget well before
  the hour mark, and an idle-but-long session burns cache TTL before it fills
  context. Watching only one axis misses half the handoff-worthy moments.

Handoff recommendation (feature 1):
  The hook can't read the conversation, so it infers session weight from git
  state since SessionStart (baseline HEAD stored in $CWD/.episodic-baseline):
    commits since start          → /checkpoint (real decisions to persist)
    only uncommitted churn        → /close      (work, but no narrative yet)
    clean tree / no baseline      → /close      (light session)
  /handoff is always offered as the tangent option — git can't detect a tangent.

Visibility note (the whole reason this file emits JSON, not print()):
  Plain stdout from a Stop hook only reaches Claude Code's debug log — it is NOT
  shown in the normal UI. The reliable user-facing channel from a Stop hook is the
  JSON `systemMessage` field, which Claude Code renders to the user. The
  persistent, always-visible elapsed clock lives in the statusline
  (combined-statusline.sh); this hook fires the one-shot suggestion popups.

Install: ~/.claude/hooks/session_timer.py
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Where we store the session start timestamp + one-shot warning markers
TIMING_DIR = Path.home() / ".claude" / "session_timing"
TIMESTAMP_FILE = TIMING_DIR / "session_start.txt"
WARNED_SUGGEST = TIMING_DIR / "warned_suggest.flag"
WARNED_URGENT = TIMING_DIR / "warned_urgent.flag"

# ── Trigger thresholds ────────────────────────────────────────────────────────
# Suggest a handoff at the FIRST of: 45 min elapsed OR 40% of context consumed.
TIME_SUGGEST = 45 * 60      # 45 min
CONTEXT_SUGGEST_PCT = 40    # 40% of the context window
# Escalate (stronger nudge) at the first of: 55 min OR 45% context.
TIME_URGENT = 55 * 60
CONTEXT_URGENT_PCT = 45

# Model context window. Opus/Sonnet ship a 200k window; 40% ≈ 80k tokens.
CONTEXT_WINDOW = 200_000


def emit_system_message(msg):
    """
    Surface a message to the USER from a Stop hook.
    Stop-hook plain stdout is swallowed to the debug log; the JSON `systemMessage`
    field is the only channel Claude Code renders to the user.
    """
    print(json.dumps({"systemMessage": msg}), flush=True)


def session_start():
    """Record the session start time and clear one-shot warning markers."""
    TIMING_DIR.mkdir(parents=True, exist_ok=True)
    TIMESTAMP_FILE.write_text(str(time.time()))
    # Fresh session: clear markers so the suggestion popups fire again.
    WARNED_SUGGEST.unlink(missing_ok=True)
    WARNED_URGENT.unlink(missing_ok=True)


def read_hook_stdin():
    """
    Stop hooks receive a JSON blob on stdin (session_id, transcript_path, cwd, …).
    Return it as a dict, or {} on any problem. Guard against a TTY so a manually
    invoked `reset` (no piped stdin) never blocks waiting on a read.
    """
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def context_pct(transcript_path):
    """
    Percent of the context window consumed, from the live transcript.

    The transcript is JSONL; each assistant turn carries message.usage. The
    window currently in use ≈ the LAST turn's input_tokens + cache_creation +
    cache_read (output is not part of the next turn's input context). We scan
    the file's tail backwards for the most recent usage and divide by the window.

    Returns an int 0-100, or None if it can't be determined (no path, no usage,
    parse error) — callers must treat None as "context axis unknown", never 0.
    """
    if not transcript_path:
        return None
    try:
        p = Path(transcript_path)
        if not p.exists():
            return None
        # Read only the tail — the latest usage line sits near the end, and
        # transcripts can grow to many MB over a long session.
        size = p.stat().st_size
        with p.open("rb") as f:
            if size > 512 * 1024:
                f.seek(-512 * 1024, os.SEEK_END)
                f.readline()  # drop the partial first line after the seek
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
    """Run a git command in cwd, return stripped stdout or '' on any failure."""
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def recommend_handoff(cwd):
    """
    Recommend which session tool to reach for, inferred from git state since
    SessionStart. Returns a short single-line recommendation string.

    The session-start HEAD lives in $CWD/.episodic-baseline (written by the
    SessionStart hook). commits since then = durable decisions worth a narrative
    → /checkpoint. Uncommitted-only churn = work without a narrative yet → /close.
    Clean tree / unknown = light session → /close. /handoff covers tangents, which
    git cannot detect, so it is always offered as the alternative.
    """
    if not cwd or not Path(cwd).exists():
        return "Recommend → /close (light) or /checkpoint (if decisions made). Tangent? /handoff."

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
        return (
            f"Recommend → /checkpoint ({commits} commit{plural} this session — "
            f"persist the why). Tangent? /handoff. Light wrap? /close."
        )
    if dirty_files >= 3:
        return (
            f"Recommend → /checkpoint ({dirty_files} files changed, uncommitted — "
            f"capture the decisions). Tangent? /handoff. Light wrap? /close."
        )
    if dirty_files >= 1:
        return "Recommend → /close (light session, no commits). Tangent? /handoff."
    return "Recommend → /close (no changes this session). Tangent? /handoff."


def check_elapsed():
    """
    Called on every Stop event (after each Claude response). Surfaces a one-shot
    suggestion the first time EITHER axis (time or context) crosses a threshold.
    One-shot (marker-gated) so the user gets a single popup per tier instead of a
    nag on every Stop — the statusline already shows elapsed time persistently.
    """
    if not TIMESTAMP_FILE.exists():
        # No timestamp — write one now as a fallback, nothing to warn yet.
        session_start()
        return

    data = read_hook_stdin()
    cwd = data.get("cwd") or os.getcwd()
    pct = context_pct(data.get("transcript_path"))

    start = float(TIMESTAMP_FILE.read_text().strip())
    elapsed = time.time() - start
    mins = int(elapsed // 60)

    # Which axis (or both) tripped — drives the human-readable reason.
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
            emit_system_message(
                f"🚨 Hand off NOW — {reason(time_urgent, ctx_urgent)}. "
                f"{recommend_handoff(cwd)}"
            )
            WARNED_URGENT.touch()
            WARNED_SUGGEST.touch()  # urgent supersedes the softer suggestion
    elif time_suggest or ctx_suggest:
        if not WARNED_SUGGEST.exists():
            emit_system_message(
                f"⚠️  Time to hand off — {reason(time_suggest, ctx_suggest)}. "
                f"{recommend_handoff(cwd)}"
            )
            WARNED_SUGGEST.touch()


def reset():
    """Reset the session timer (useful when starting a new task in the same terminal)."""
    session_start()
    emit_system_message("✓ Session timer reset.")


if __name__ == "__main__":
    # Claude Code passes the event name as the first argument
    event = sys.argv[1] if len(sys.argv) > 1 else ""

    if event == "session_start":
        session_start()
    elif event == "stop":
        check_elapsed()
    elif event == "reset":
        reset()
    # Silently ignore unknown events — never crash the hook
