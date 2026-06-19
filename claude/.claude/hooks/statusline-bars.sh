#!/bin/bash
# statusline-bars.sh — 5hr-block + weekly token-burn bars for the Claude Code statusline.
#
# Design : docs/brainstorm/statusline-burn-bars-datasource-2026-06-16.md
# Decisions D1-D7 : findings.md. REVISED 2026-06-16 by live ground-truth calibration
#                   (see findings.md "Ground-truth revision"): both ceilings are now
#                   CONFIGURED caps, and weekly is anchored to the real reset.
# Visual V6 : _statusline-bars-proto.NOTES.md
#
# Why both ceilings are configured (not detected): p90-of-completed-blocks measured the
# user's HABIT (~700K/block), not the cap (~10M). The user never maxes a block, so the
# detector read ~14x low. Ground truth (CC's own %) lets us configure the cap directly,
# in our own excl-cache-read units, so our bar matches CC's bar. Same model for both bars.
#
# Two surfaces:
#   render  (default) — read cache, print the V6 bars line, fire a detached refresh if stale.
#                       NEVER runs ccusage inline (D3 — ccusage is ~1s, too slow per render).
#   refresh           — one `ccusage blocks --json` call feeds BOTH bars; derive %, write cache.
#                       Single-flight via atomic mkdir lock (D3).
#
# Cache format: one line "<5h> <weekly>", each an int 0-100 or the "na" sentinel.
# "na" is the spine of D4: a value is a trustworthy % or a dimmed placeholder — never a
# fabricated 0% or a guess. An unconfigured cap yields "na", not a wrong number.

set -u

# D7 config — source the sibling conf if present. It assigns with `:=`, so a value already
# in the environment (e.g. if CC injects settings.json `env`) wins. This makes config work
# WITHOUT depending on whether CC propagates env into the statusLine subprocess — the D7
# build-time unknown is mooted rather than gambled on. Must run before the reads below.
_BARS_CONF="${BASH_SOURCE[0]%/*}/statusline-bars.conf"
# shellcheck source=/dev/null  # path resolved at runtime relative to this script
[ -f "$_BARS_CONF" ] && . "$_BARS_CONF"

CACHE_FILE="${STATUSLINE_BARS_CACHE:-$HOME/.claude/statusline-bars-cache}"
LOCK_DIR="${CACHE_FILE}.lock"
TTL_SECONDS=60
NA="na"

# Both caps are plan-specific with no baked default (guessing a cap fabricates a denominator,
# violating D4). Seed values live in the sibling statusline-bars.conf, calibrated per plan:
#   STATUSLINE_5H_CAP       5hr-block token budget   (excl cache-read units)
#   STATUSLINE_WEEKLY_CAP   weekly token budget      (excl cache-read units)
# Unset (no conf, no env) → that bar shows the placeholder, never a wrong number.
#
# Weekly reset anchor (D2 — known: Sat 17:59 America/New_York). Overridable for other plans.
WEEKLY_RESET_TZ="${STATUSLINE_WEEKLY_RESET_TZ:-America/New_York}"
WEEKLY_RESET_DOW="${STATUSLINE_WEEKLY_RESET_DOW:-6}"        # 1=Mon … 6=Sat … 7=Sun
WEEKLY_RESET_HHMM="${STATUSLINE_WEEKLY_RESET_HHMM:-17:59}"  # wall-clock in WEEKLY_RESET_TZ

# ── pure-ish config readers (no ccusage — testable) ──────────────────────────

bars_5h_cap()     { if [ -n "${STATUSLINE_5H_CAP:-}" ];     then echo "$STATUSLINE_5H_CAP";     else echo "$NA"; fi; }
bars_weekly_cap() { if [ -n "${STATUSLINE_WEEKLY_CAP:-}" ]; then echo "$STATUSLINE_WEEKLY_CAP"; else echo "$NA"; fi; }

# percent = clamp( num / denom * 100, 0, 100 ). denom == NA or <= 0 → NA (D4).
bars_pct() {
  local num=$1 denom=$2 p
  if [ "$denom" = "$NA" ]; then echo "$NA"; return; fi
  if [ "$denom" -le 0 ] 2>/dev/null; then echo "$NA"; return; fi
  p=$(( num * 100 / denom ))
  [ "$p" -lt 0 ] && p=0
  [ "$p" -gt 100 ] && p=100
  echo "$p"
}

# Epoch of the most recent weekly reset (the configured DOW + HH:MM in the configured TZ,
# at or before now). DST-safe: each candidate is resolved through the TZ's wall clock, so
# the EST/EDT switch is handled by the system zoneinfo, not arithmetic.
bars_weekly_reset_epoch() {
  local now day cand dow d
  now=$(date +%s)
  for d in 0 1 2 3 4 5 6 7; do
    day=$(TZ="$WEEKLY_RESET_TZ" date -d "-$d day" +%Y-%m-%d)
    cand=$(TZ="$WEEKLY_RESET_TZ" date -d "$day $WEEKLY_RESET_HHMM:00" +%s)
    dow=$(TZ="$WEEKLY_RESET_TZ" date -d "@$cand" +%u)
    if [ "$dow" -eq "$WEEKLY_RESET_DOW" ] && [ "$cand" -le "$now" ]; then echo "$cand"; return; fi
  done
}

# ── ccusage extraction (D5: input+output+cacheCreation, EXCLUDE cache-read; D6: --json) ─
# All reads come from a single `ccusage blocks --json` payload passed on stdin, so refresh
# spawns ccusage exactly once. blocks history spans weeks — it covers the weekly window too,
# so the separate `ccusage daily` call is gone.

# Active-block consumption → 5hr numerator. Empty payload → 0.
bars_active_from_json() {
  jq -r '(.blocks[] | select(.isActive==true) | .tokenCounts
          | .inputTokens + .outputTokens + .cacheCreationInputTokens) // 0' 2>/dev/null
}

# Sum of every non-gap block whose startTime >= reset → weekly numerator (D2 anchored).
# startTime carries millis ("…:00.000Z"); strip them so fromdateiso8601 parses.
# Edge fuzz: a block straddling the reset is counted whole if it started after it
# (≤5hr boundary slop — negligible for a glance bar, self-corrects within hours).
bars_weekly_from_json() {
  local reset=$1
  jq -r --argjson reset "$reset" '
    [ .blocks[]
      | select(.isGap==false)
      | select((.startTime | sub("\\.[0-9]+Z$";"Z") | fromdateiso8601) >= $reset)
      | .tokenCounts.inputTokens + .tokenCounts.outputTokens + .tokenCounts.cacheCreationInputTokens
    ] | add // 0' 2>/dev/null
}

# ── cache + refresh (D3) ──────────────────────────────────────────────────────

# True (exit 0) if the cache is missing or older than the TTL.
bars_cache_stale() {
  [ -f "$CACHE_FILE" ] || return 0
  local age=$(( $(date +%s) - $(stat -c %Y "$CACHE_FILE") ))
  [ "$age" -ge "$TTL_SECONDS" ]
}

# Recompute both percentages from ONE ccusage call and atomically write the cache.
# `mkdir` is atomic, so it is the single-flight lock: a concurrent refresh fails it and bails.
bars_refresh() {
  mkdir "$LOCK_DIR" 2>/dev/null || return 0
  trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

  local json reset active weekly p5 pw tmp
  json=$(ccusage blocks --json 2>/dev/null)
  reset=$(bars_weekly_reset_epoch)

  active=$(printf '%s' "$json" | bars_active_from_json);            active=${active:-0}
  weekly=$(printf '%s' "$json" | bars_weekly_from_json "$reset");  weekly=${weekly:-0}

  p5=$(bars_pct "$active" "$(bars_5h_cap)")
  pw=$(bars_pct "$weekly" "$(bars_weekly_cap)")

  tmp="${CACHE_FILE}.tmp.$$"
  printf '%s %s\n' "$p5" "$pw" > "$tmp" && mv -f "$tmp" "$CACHE_FILE"
}

# ── render (V6 — ported from _statusline-bars-proto.sh) ───────────────────────

_c() { printf '\033[38;5;%sm' "$1"; }
_r() { printf '\033[0m'; }
_DIM=240; _GREEN=82; _YELLOW=220; _ORANGE=208; _RED=196

# Color band by percent consumed: green <50, yellow 50-80, orange 80-90, red ≥90.
_pct_color() {
  local p=$1
  if   [ "$p" -ge 90 ]; then echo $_RED
  elif [ "$p" -ge 80 ]; then echo $_ORANGE
  elif [ "$p" -ge 50 ]; then echo $_YELLOW
  else                       echo $_GREEN
  fi
}

# One bar: label + 10 ticks + numeric %. NA → dimmed empty ticks + `--%` (D4 placeholder).
_bars_one() {
  local label=$1 p=$2 w=10 i
  if [ "$p" = "$NA" ]; then
    printf '%s ' "$label"; _c $_DIM
    for ((i = 0; i < w; i++)); do printf '▯'; done
    printf ' --%%'; _r
    return
  fi
  local fill=$(( p * w / 100 )) col; col=$(_pct_color "$p")
  printf '%s ' "$label"; _c "$col"
  for ((i = 0;    i < fill; i++)); do printf '▮'; done
  _c $_DIM
  for ((i = fill; i < w;    i++)); do printf '▯'; done
  _r; printf ' %d%%' "$p"; _c "$col"; [ "$p" -ge 80 ] && printf ' ⚠'; _r
}

# Print the single V6 dual-bar line from the cache (absent → both placeholders).
bars_render() {
  local p5=$NA pw=$NA
  [ -f "$CACHE_FILE" ] && read -r p5 pw < "$CACHE_FILE"
  p5=${p5:-$NA}; pw=${pw:-$NA}
  _bars_one "5h" "$p5"
  _c $_DIM; printf '  ·  '; _r
  _bars_one "wk" "$pw"
  printf '\n'
}

# ── dispatch (skipped when the file is sourced, e.g. by tests) ────────────────

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  case "${1:-render}" in
    refresh)
      bars_refresh
      ;;
    render)
      bars_render
      # Detached refresh for the NEXT render if stale. `( … & )` forks and disowns, so the
      # statusline returns instantly and never waits on ccusage (D3).
      if bars_cache_stale; then ( bars_refresh >/dev/null 2>&1 & ); fi
      ;;
    *)
      echo "usage: $0 [render|refresh]" >&2; exit 2
      ;;
  esac
fi
