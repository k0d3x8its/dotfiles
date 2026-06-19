#!/usr/bin/env bats
#
# Tests for claude/.claude/hooks/statusline-bars.sh — the 5hr + weekly usage bars.
# Sources the hook (its dispatch is guarded by BASH_SOURCE) and exercises the
# functions directly. No ccusage, no caps, no cache: the bars read the
# server-authoritative .rate_limits.* percentages straight out of the statusline
# stdin JSON, so the extractor is fed fixture JSON.

setup() {
    HOOK="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/claude/.claude/hooks/statusline-bars.sh"
    # shellcheck source=/dev/null
    source "$HOOK"
}

# ── bars_round (CC sends floats; round to whole percent; junk -> na) ──────────

@test "bars_round: float rounds half-up to int" {
    [ "$(bars_round 28.999999)" -eq 29 ]
}

@test "bars_round: integer passes through" {
    [ "$(bars_round 26)" -eq 26 ]
}

@test "bars_round: empty -> na (never fabricate)" {
    [ "$(bars_round '')" = "na" ]
}

@test "bars_round: null -> na" {
    [ "$(bars_round null)" = "na" ]
}

@test "bars_round: non-numeric -> na" {
    [ "$(bars_round abc)" = "na" ]
}

# ── bars_clamp (0-100; na passes through) ────────────────────────────────────

@test "bars_clamp: in-range passes through" {
    [ "$(bars_clamp 50)" -eq 50 ]
}

@test "bars_clamp: over 100 clamps to 100" {
    [ "$(bars_clamp 250)" -eq 100 ]
}

@test "bars_clamp: negative clamps to 0" {
    [ "$(bars_clamp -5)" -eq 0 ]
}

@test "bars_clamp: na passes through" {
    [ "$(bars_clamp na)" = "na" ]
}

# ── bars_extract (the real data path: read .rate_limits.<window>.used_percentage) ─

FIXTURE='{"rate_limits":{"five_hour":{"used_percentage":26,"resets_at":1781840400},"seven_day":{"used_percentage":28.999999999999996,"resets_at":1781992800}}}'

@test "bars_extract: five_hour pulls the server percent" {
    [ "$(bars_extract "$FIXTURE" five_hour)" -eq 26 ]
}

@test "bars_extract: seven_day rounds the float" {
    [ "$(bars_extract "$FIXTURE" seven_day)" -eq 29 ]
}

@test "bars_extract: missing rate_limits -> na (older CC / no published limits)" {
    [ "$(bars_extract '{"cost":{"total_cost_usd":1.23}}' five_hour)" = "na" ]
}

@test "bars_extract: malformed json -> na" {
    [ "$(bars_extract 'not json' five_hour)" = "na" ]
}

# ── render (V6 + na placeholders) ─────────────────────────────────────────────

@test "bars_render: na values render as dimmed placeholders, no fabricated number" {
    run bars_render na na
    [[ "$output" == *"5h"* ]]
    [[ "$output" == *"wk"* ]]
    [[ "$output" == *"--%"* ]]
    [[ "$output" != *"0%"* ]]
}

@test "bars_render: missing args default to placeholders" {
    run bars_render
    [[ "$output" == *"--%"* ]]
}

@test "bars_render: numeric values show % and the warn glyph at >=80" {
    run bars_render 45 85
    [[ "$output" == *"45%"* ]]
    [[ "$output" == *"85%"* ]]
    [[ "$output" == *"⚠"* ]]      # 85 >= 80 triggers the warning glyph
}

@test "bars_render: below 80 shows no warn glyph" {
    run bars_render 10 20
    [[ "$output" != *"⚠"* ]]
}

# ── end-to-end: stdin JSON -> rendered bars ───────────────────────────────────

@test "end-to-end: piping statusline JSON renders both percents" {
    run bash "$HOOK" <<< "$FIXTURE"
    [[ "$output" == *"26%"* ]]
    [[ "$output" == *"29%"* ]]
}
