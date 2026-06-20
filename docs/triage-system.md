# Triage System

Zero-token TODOS.md → TRIAGE-BLOCK.md pipeline. No Claude API calls — runs entirely in the harness.

---

## Pipeline

```
TODOS.md (per project)
    ↓  update-cache <project> <path>
~/dev/.triage-cache          (pointer registry)
    ↓  update-triage
~/dev/TRIAGE-BLOCK.md        (rendered output for /dev-brief)
```

`refresh_triage.py` (PostToolUse hook) triggers the full pipeline automatically whenever a `TODOS.md` is edited in Claude Code. Run manually anytime:

```bash
update-triage
```

---

## Scripts

### `update-cache <project> <todos_path>`

Writes or updates one project's block in `~/.triage-cache`. Stores a path + mtime pointer rather than copying content — `/dev-brief`'s read-skip checks the mtime to decide whether re-reading is needed.

### `update-triage`

Reads `~/.triage-cache`, loads each live `TODOS.md`, and renders `~/dev/TRIAGE-BLOCK.md` sorted by tier and urgency. Also reads `~/.triage-dates` for first-seen timestamps to compute stale age.

### `rotate-log <log_path> [N]`

Keeps the newest N session blocks in `SESSION-LOG.md`; moves older blocks to `ARCHIVE-LOG.md`. Default N=8. Matches both `## Session Handoff` and `## Session Checkpoint` block types — missing either causes silent block loss.

---

## Tier system

Items are classified into five tiers based on tags in the TODO line:

| Tier | Tags | Color |
|------|------|-------|
| CRITICAL | `[BROKEN]`, `[TEST]`, `[VERIFY]` | 🔴 red |
| HIGH | `[BLOCKER]`, `urgent` keyword | 🟥 dark red |
| MEDIUM | (default — no priority tag) | 🔶 orange |
| LOW | `[LOW]` | 🟡 yellow |
| BACKLOG | `[BACKLOG]` | 🔵 blue |

Within each tier, urgent items sort first, then alphabetically by project name.

---

## Stale age bands

Items with a known first-seen date get a colored inline marker once they exceed the minimum threshold. Comparison is strictly greater than (`>`):

| Age | Color | Marker |
|-----|-------|--------|
| >30 days | `#ff1a1a` (red) | `[stale since YYYY-MM-DD]` |
| >14 days | `#ff6600` (orange) | `[stale since YYYY-MM-DD]` |
| >7 days | `#ffd700` (yellow) | `[stale since YYYY-MM-DD]` |
| ≤7 days | — | (no marker) |

First-seen dates are seeded from `~/.triage-dates`. Override retroactively by adding a `[since: YYYY-MM-DD]` tag to the TODO line — it overwrites the cached date and is stripped from display.

---

## Data files

| File | Purpose | Committed? |
|------|---------|-----------|
| `~/dev/.triage-cache` | Pointer registry: project → path + mtime | No — runtime artifact |
| `~/dev/.triage-dates` | First-seen timestamps keyed by item hash | No — runtime artifact |
| `~/dev/TRIAGE-BLOCK.md` | Rendered output consumed by `/dev-brief` | No — runtime artifact |
| `~/dev/SESSION-LOG.md` | Session narratives written by `/checkpoint` | Yes — git-crypt encrypted |
| `~/dev/ARCHIVE-LOG.md` | Overflow blocks rotated out by `rotate-log` | No — not committed |
