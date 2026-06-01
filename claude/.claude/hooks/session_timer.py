#!/usr/bin/env python3
"""
KOS Session Timer Hook
Tracks elapsed session time and warns at 45 minutes to run /handoff.

Hook events used:
  SessionStart → record session start time, clear one-shot warning markers
  Stop         → check elapsed time and surface a warning if a threshold is crossed

Visibility note (the whole reason this file emits JSON, not print()):
  Plain stdout from a Stop hook only reaches Claude Code's debug log — it is NOT
  shown in the normal UI (only UserPromptSubmit/SessionStart stdout becomes
  visible context). The reliable user-facing channel from a Stop hook is the
  JSON `systemMessage` field, which Claude Code renders to the user. The
  persistent, always-visible elapsed clock lives in the statusline
  (combined-statusline.sh); this hook fires the one-shot 45m / 55m popups.

Install: ~/.claude/hooks/session_timer.py
"""

import sys
import json
import time
from pathlib import Path

# Where we store the session start timestamp + one-shot warning markers
TIMING_DIR = Path.home() / ".claude" / "session_timing"
TIMESTAMP_FILE = TIMING_DIR / "session_start.txt"
WARNED_45 = TIMING_DIR / "warned_45.flag"
WARNED_55 = TIMING_DIR / "warned_55.flag"

# Warn at 45 minutes (2700 seconds), remind again at 55 minutes (3300 seconds)
WARN_THRESHOLD = 45 * 60    # 45 min
URGENT_THRESHOLD = 55 * 60  # 55 min


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
    # Fresh session: clear markers so the 45m / 55m popups fire again.
    WARNED_45.unlink(missing_ok=True)
    WARNED_55.unlink(missing_ok=True)


def check_elapsed():
    """
    Called on every Stop event (after each Claude response).
    Surfaces a one-shot warning when a threshold is first crossed. One-shot
    (marker-gated) so the user gets a single popup at 45m and at 55m instead of
    a nag on every Stop — the statusline already shows elapsed time persistently.
    """
    if not TIMESTAMP_FILE.exists():
        # No timestamp — write one now as a fallback, nothing to warn yet.
        session_start()
        return

    start = float(TIMESTAMP_FILE.read_text().strip())
    elapsed = time.time() - start

    if elapsed >= URGENT_THRESHOLD:
        if not WARNED_55.exists():
            emit_system_message(
                "🚨 55 minutes elapsed — run /handoff NOW. Cache TTL expires in ~5 minutes."
            )
            WARNED_55.touch()
    elif elapsed >= WARN_THRESHOLD:
        if not WARNED_45.exists():
            emit_system_message(
                "⚠️  45 minutes elapsed — consider running /handoff soon to preserve cache."
            )
            WARNED_45.touch()


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
