#!/bin/bash
# Pipe Claude Code's stdin (session JSON) to ccusage, then build the bottom status row.
INPUT=$(cat)
echo "$INPUT" | ccusage statusline 2>/dev/null || true

# 5hr + weekly usage bars. Captured (not printed inline) so they can sit to the RIGHT of the
# caveman badge + session timer on a single bottom row instead of taking their own line.
# The bars read the server-authoritative .rate_limits.* percentages out of the SAME stdin
# JSON we already captured in $INPUT, so we forward it in. Pure jq read → instant, exact.
BARS=$(printf '%s' "$INPUT" | bash "$HOME/.claude/hooks/statusline-bars.sh" 2>/dev/null)

# Bottom row, left to right: caveman badge, session timer, burn bars.
# caveman-statusline.sh prints no trailing newline (and nothing when inactive), so the
# timer and bars append to the same line.
bash "$HOME/.claude/hooks/caveman-statusline.sh"

# Session elapsed timer — the persistent, always-visible surface for the /handoff nudge.
# Stop-hook stdout only reaches the debug log, so the statusline (not the hook's print) is
# what reliably shows the user how long the session has run.
TS_FILE="$HOME/.claude/session_timing/session_start.txt"
TIMER=""
if [ -f "$TS_FILE" ]; then
    start=$(cat "$TS_FILE" 2>/dev/null)
    start=${start%.*}   # strip float decimals for integer math
    if [ -n "$start" ]; then
        mins=$(( ( $(date +%s) - start ) / 60 ))
        if   [ "$mins" -ge 55 ]; then TIMER="🚨 ${mins}m — /handoff NOW (cache TTL ~5m)"
        elif [ "$mins" -ge 45 ]; then TIMER="⚠️  ${mins}m — run /handoff soon"
        else                          TIMER="⏱  ${mins}m"
        fi
    fi
fi

# Compose the remainder of the row after the caveman badge.
[ -n "$TIMER" ] && printf ' %s' "$TIMER"
[ -n "$BARS" ]  && printf '   %s' "$BARS"
printf '\n'
