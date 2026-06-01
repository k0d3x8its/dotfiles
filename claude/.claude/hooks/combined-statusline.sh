#!/bin/bash
# Pipe Claude Code's stdin (session JSON) to ccusage, then show caveman mode below
INPUT=$(cat)
echo "$INPUT" | ccusage statusline 2>/dev/null || true
bash "$HOME/.claude/hooks/caveman-statusline.sh"

# Session elapsed timer — the persistent, always-visible surface for the /handoff
# nudge. Stop-hook stdout only reaches the debug log, so the statusline (not the
# hook's print) is what reliably shows the user how long the session has run.
TS_FILE="$HOME/.claude/session_timing/session_start.txt"
if [ -f "$TS_FILE" ]; then
    start=$(cat "$TS_FILE" 2>/dev/null)
    start=${start%.*}   # strip float decimals for integer math
    if [ -n "$start" ]; then
        mins=$(( ( $(date +%s) - start ) / 60 ))
        if   [ "$mins" -ge 55 ]; then echo "🚨 ${mins}m — /handoff NOW (cache TTL ~5m)"
        elif [ "$mins" -ge 45 ]; then echo "⚠️  ${mins}m — run /handoff soon"
        else                          echo "⏱  ${mins}m"
        fi
    fi
fi
