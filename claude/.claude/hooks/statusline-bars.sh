#!/bin/bash
# statusline-bars.sh — 5hr-block + weekly usage bars for the Claude Code statusline.
#
# Design : docs/brainstorm/statusline-burn-bars-datasource-2026-06-16.md
# History: REWRITTEN 2026-06-18. The original derived both bars from ccusage token
#          counts against configured caps. That could never match CC's 5h % — the
#          server computes 5h/weekly usage on a non-public, model-weighted rate card
#          we don't see locally (findings I1: every ccusage-derived basis refuted).
#
# THE FIX (findings: "rate_limits in statusline stdin"): Claude Code pipes the
# server-authoritative numbers straight into the statusline hook's stdin JSON:
#   .rate_limits.five_hour.used_percentage   (matches CC exactly)
#   .rate_limits.seven_day.used_percentage
# So we read them, not reconstruct them. No ccusage, no caps, no cache, no lock,
# no weekly-reset anchor. The hook is now a pure jq read of stdin → instant + exact.
#
# Usage: the statusline JSON is piped on stdin (combined-statusline.sh forwards $INPUT).
#   bash statusline-bars.sh < statusline.json
#
# "na" sentinel (carried over from the original D4): if rate_limits is absent (older
# CC, or a plan with no published limits) a bar shows a dimmed placeholder + `--%`,
# never a fabricated 0%.

set -u

NA="na"

# ── extraction (pure-ish: feed JSON on $1, testable without a live statusline) ──

# Round a numeric string to an int; empty / "na" / "null" / non-numeric → na.
# CC sends floats (e.g. 28.999999); round half-up to the nearest whole percent.
bars_round() {
  local v=${1:-} out
  case "$v" in
    ""|na|null)  echo "$NA"; return ;;
    *[!0-9.+-]*) echo "$NA"; return ;;   # any non-numeric char → na (don't let printf emit a 0)
  esac
  # capture-then-echo: on a printf failure we emit na ONCE, never a partial number
  out=$(printf '%.0f' "$v" 2>/dev/null) && echo "$out" || echo "$NA"
}

# Clamp an int to 0-100; na passes through.
bars_clamp() {
  local p=${1:-na}
  [ "$p" = "$NA" ] && { echo "$NA"; return; }
  [ "$p" -lt 0   ] 2>/dev/null && p=0
  [ "$p" -gt 100 ] 2>/dev/null && p=100
  echo "$p"
}

# Pull .rate_limits.<window>.used_percentage from the stdin JSON, round + clamp.
# Missing key, null, no jq, or malformed JSON → na (never a fabricated number).
bars_extract() {
  local json=$1 window=$2 v
  v=$(printf '%s' "$json" | jq -r ".rate_limits.${window}.used_percentage // \"na\"" 2>/dev/null)
  bars_clamp "$(bars_round "$v")"
}

# ── render (V6 — unchanged from the original visual) ──────────────────────────

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

# One bar: label + 10 ticks + numeric %. NA → dimmed empty ticks + `--%` placeholder.
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

# Print the single V6 dual-bar line from two percents (each an int 0-100 or "na").
bars_render() {
  local p5=${1:-$NA} pw=${2:-$NA}
  _bars_one "5h" "$p5"
  _c $_DIM; printf '  ·  '; _r
  _bars_one "wk" "$pw"
  printf '\n'
}

# ── dispatch (skipped when sourced, e.g. by tests) ────────────────────────────

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  json=$(cat)
  p5=$(bars_extract "$json" five_hour)
  pw=$(bars_extract "$json" seven_day)
  bars_render "$p5" "$pw"
fi
