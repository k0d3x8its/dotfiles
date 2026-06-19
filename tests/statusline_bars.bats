#!/usr/bin/env bats
#
# Tests for claude/.claude/hooks/statusline-bars.sh — the 5hr + weekly burn bars.
# Sources the hook (its dispatch is guarded by BASH_SOURCE) and exercises the
# functions directly. ccusage is never called: the JSON extractors are fed fixtures.

setup() {
    HOOK="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/claude/.claude/hooks/statusline-bars.sh"
    export STATUSLINE_BARS_CACHE="$BATS_TEST_TMPDIR/cache"
    # shellcheck source=/dev/null
    source "$HOOK"
}

# ── bars_pct (D4 clamp + na) ─────────────────────────────────────────────────

@test "bars_pct: normal ratio" {
    [ "$(bars_pct 50 100)" -eq 50 ]
}

@test "bars_pct: clamps over 100" {
    [ "$(bars_pct 250 100)" -eq 100 ]
}

@test "bars_pct: na denominator -> na (never fabricate)" {
    [ "$(bars_pct 5 na)" = "na" ]
}

@test "bars_pct: zero denominator -> na" {
    [ "$(bars_pct 5 0)" = "na" ]
}

# ── config readers (D7) ──────────────────────────────────────────────────────

@test "bars_5h_cap: set value passes through" {
    STATUSLINE_5H_CAP=12345 run bars_5h_cap
    [ "$output" = "12345" ]
}

@test "bars_5h_cap: unset -> na" {
    unset STATUSLINE_5H_CAP
    [ "$(bars_5h_cap)" = "na" ]
}

@test "bars_weekly_cap: unset -> na" {
    unset STATUSLINE_WEEKLY_CAP
    [ "$(bars_weekly_cap)" = "na" ]
}

# ── weekly reset anchor (D2) ─────────────────────────────────────────────────

@test "bars_weekly_reset_epoch: lands on the configured day + time, at/before now" {
    local epoch
    epoch="$(bars_weekly_reset_epoch)"
    [ "$epoch" -le "$(date +%s)" ]
    [ "$(TZ=America/New_York date -d "@$epoch" +%u)" -eq 6 ]      # Saturday
    [ "$(TZ=America/New_York date -d "@$epoch" +%H:%M)" = "17:59" ]
}

# ── ccusage JSON extraction (D5 metric, D6 json) ─────────────────────────────

FIXTURE='{"blocks":[
  {"startTime":"2026-06-16T17:00:00.000Z","isActive":true,"isGap":false,"tokenCounts":{"inputTokens":100,"outputTokens":50,"cacheCreationInputTokens":25,"cacheReadInputTokens":99999}},
  {"startTime":"2026-06-14T00:00:00.000Z","isActive":false,"isGap":false,"tokenCounts":{"inputTokens":1000,"outputTokens":500,"cacheCreationInputTokens":250,"cacheReadInputTokens":0}},
  {"startTime":"2026-06-10T00:00:00.000Z","isActive":false,"isGap":false,"tokenCounts":{"inputTokens":9999,"outputTokens":0,"cacheCreationInputTokens":0,"cacheReadInputTokens":0}}
]}'

@test "bars_active_from_json: sums input+output+cacheCreation, EXCLUDES cache-read (D5)" {
    # 100 + 50 + 25 = 175; the 99999 cacheRead must not appear
    [ "$(printf '%s' "$FIXTURE" | bars_active_from_json)" -eq 175 ]
}

@test "bars_weekly_from_json: sums only non-gap blocks at/after the reset (D2)" {
    # reset = Sat 2026-06-13 17:59 EDT = 2026-06-13T21:59:00Z
    local reset; reset=$(date -d '2026-06-13T21:59:00Z' +%s)
    # in-window: active (175) + 06-14 (1750) = 1925; 06-10 excluded
    [ "$(printf '%s' "$FIXTURE" | bars_weekly_from_json "$reset")" -eq 1925 ]
}

# ── render (V6 + D4 placeholders) ────────────────────────────────────────────

@test "bars_render: absent cache -> dimmed placeholders, no fabricated number" {
    rm -f "$STATUSLINE_BARS_CACHE"
    run bars_render
    [[ "$output" == *"--%"* ]]
    [[ "$output" != *"0%"* ]]
}

@test "bars_render: na values render as placeholders" {
    printf 'na na\n' > "$STATUSLINE_BARS_CACHE"
    run bars_render
    [[ "$output" == *"5h"* ]]
    [[ "$output" == *"wk"* ]]
    [[ "$output" == *"--%"* ]]
}

@test "bars_render: numeric values show % and the warn glyph at >=80" {
    printf '45 85\n' > "$STATUSLINE_BARS_CACHE"
    run bars_render
    [[ "$output" == *"45%"* ]]
    [[ "$output" == *"85%"* ]]
    [[ "$output" == *"⚠"* ]]      # 85 >= 80 triggers the warning glyph
}

@test "bars_render: below 80 shows no warn glyph" {
    printf '10 20\n' > "$STATUSLINE_BARS_CACHE"
    run bars_render
    [[ "$output" != *"⚠"* ]]
}
