#!/usr/bin/env python3
"""
KOS Session Timer Hook
Tracks elapsed session time and warns at 45 minutes to run /handoff.

Hook events used:
  SessionStart → record session start time
  Stop         → check elapsed time and print warning if needed

Install: ~/.claude/hooks/session_timer.py
"""

import sys
import os
import json
import time
from pathlib import Path

# Where we store the session start timestamp
TIMING_DIR = Path.home() / ".claude" / "session_timing"
TIMESTAMP_FILE = TIMING_DIR / "session_start.txt"

# Warn at 45 minutes (2700 seconds), remind again at 55 minutes (3300 seconds)
WARN_THRESHOLD  = 45 * 60   # 45 min
URGENT_THRESHOLD = 55 * 60  # 55 min


def session_start():
    """Record the session start time."""
    TIMING_DIR.mkdir(parents=True, exist_ok=True)
    TIMESTAMP_FILE.write_text(str(time.time()))


def check_elapsed():
    """
    Called on every Stop event (after each Claude response).
    Reads elapsed time and prints a warning if past thresholds.
    """
    if not TIMESTAMP_FILE.exists():
        # No timestamp — write one now as a fallback
        session_start()
        return

    start = float(TIMESTAMP_FILE.read_text().strip())
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    # Always print elapsed time so it's visible in every response
    print(f"\n⏱  Session time: {minutes}m {seconds}s", flush=True)

    # 45 min warning
    if WARN_THRESHOLD <= elapsed < URGENT_THRESHOLD:
        print(
            "⚠️  45 minutes elapsed — consider running /handoff soon to preserve cache.",
            flush=True
        )

    # 55 min urgent warning
    elif elapsed >= URGENT_THRESHOLD:
        print(
            "🚨 55 minutes elapsed — run /handoff NOW. Cache TTL expires in ~5 minutes.",
            flush=True
        )


def reset():
    """Reset the session timer (useful when starting a new task in the same terminal)."""
    session_start()
    print("✓ Session timer reset.", flush=True)


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
