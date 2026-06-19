# Design: Statusline burn-bars — data source (5hr + weekly limit indicators)

> Brainstorm output, 2026-06-16. Pipeline: /brainstorm → /grill-me → /write-plan.
> Status: draft — not yet grilled.

## Problem

The Claude Code statusline needs two token-burn indicators: one for the **5-hour
rolling limit**, one for the **weekly limit**. The V6 visual is already settled
(one-line dual layout, 10 discrete ticks/bar, inline %, color bands, ⚠ at ≥80% —
see `dotfiles/claude/.claude/hooks/_statusline-bars-proto.NOTES.md`). What is *not*
settled is where each bar's number comes from. Both bars need a **percentage against
a ceiling**, and no local file or documented API exposes the true 5hr/weekly
subscription-limit % — only Anthropic's OAuth subscription backend knows it.

## Context & constraints

- **Confirmed via the claude-api skill:** there is *no documented public endpoint* for
  the Claude Code 5hr/weekly *subscription* limits. The only rate-limit surface Anthropic
  documents is per-request response headers (`retry-after`, `x-ratelimit-*`) and those are
  **API-key RPM/TPM/TPD**, not the OAuth subscription windows the statusline cares about.
- **The statusline already runs `ccusage statusline`** (ccusage 20.0.5, npm, actively
  maintained) inside `combined-statusline.sh`. ccusage exposes raw tokens, 5hr session
  blocks (`ccusage blocks`), burn rate, and per-week token totals (`ccusage weekly`).
  It does **not** emit a limit-% — there is no ceiling layer in ccusage.
- **`kos-burn-bar` reimplemented the ceiling layer** in JS: p90 of completed 5hr-block
  totals as the detected limit (`kos-burn-bar/main.js:335 detectTokenLimit`), plus 5hr
  block grouping. This is the %-against-ceiling logic the statusline would want.
- **kos-burn-bar shows wrong outputs today, and its correctness is unvalidated.** Its own
  `TODOS.md` carries **4 open `[BLOCKER][INVESTIGATE]` items** plus a `[DECISION]` —
  including *"Log what detectTokenLimit() returns vs known plan ceiling"* and
  *"Evaluate p90 algorithm vs alternatives"*. The exact ceiling logic the statusline would
  reuse is the part that's never been proven correct. Reusing its code inherits that debt.
- **5hr vs weekly are asymmetric.** The 5hr bar maps cleanly onto a session-block + p90
  ceiling. The weekly bar has *no* ceiling concept — `ccusage weekly` groups by calendar
  week, which likely does not match CC's real weekly reset cadence (rolling 7-day vs
  calendar). Whatever weekly ceiling exists must be derived or supplied, not detected the
  same way.
- Refresh cadence and the V6 fold into `combined-statusline.sh` are downstream of this
  decision; the proto must be deleted once the winner is wired.

## Approaches

### A — Offline consumption proxy, sourced direct from ccusage (recommended)

Compute each bar as `consumed ÷ detected_ceiling` using **`ccusage` as the only data
source**, and write a *fresh, minimal* ceiling layer in the statusline hook. 5hr bar:
current active block tokens (`ccusage blocks --active`) ÷ p90 of completed blocks. Weekly
bar: current-week tokens (`ccusage weekly`) ÷ a derived weekly ceiling (see Open
questions). **Does not depend on kos-burn-bar's code** — only on the maintained npm tool
plus a small, owned ceiling calc.

**Tradeoffs:** Offline, no network, already half-wired (ccusage is in the statusline
today). Not blocked on kos-burn-bar's open BLOCKERs — its bug debt stays its own problem.
Approximate by nature: a detected ceiling is an estimate, not the real subscription cap,
so the % can drift from truth. Weekly ceiling derivation is unsolved (the one real open
question). Cost: writing + owning a fresh ceiling calc (small, but it's new code to test).

### A′ — Offline proxy, reusing kos-burn-bar's p90 logic (blocked alt)

Same proxy concept, but lift `detectTokenLimit()` / block-grouping from
`kos-burn-bar/main.js` instead of writing fresh.

**Tradeoffs:** Less new code *if it worked* — but it currently shows wrong outputs and its
ceiling logic sits behind 4 unresolved `[BLOCKER][INVESTIGATE]` items. Adopting it now
imports an unvalidated, known-buggy dependency into the statusline and couples two repos'
correctness. **Blocked** until kos-burn-bar closes those BLOCKERs. Revisit only if/when it
does; not viable as the v1 path.

### B — Real subscription limits via Anthropic's usage feed

Query the undocumented internal endpoint the Claude Code client uses to read OAuth
subscription 5hr/weekly consumption. Ground truth — the only source that knows the real %.

**Tradeoffs:** Accurate if reachable. But undocumented (no contract, can change/break
without notice), network-dependent (statusline runs on every prompt — adds latency + a
failure mode), needs OAuth token handling from a shell hook, and may not even be reachable
from the statusline context. High fragility for a surface that must render fast and never
hang. Not justified when an offline proxy gets "good enough" for a glance-only bar.

## Recommendation

**A — offline proxy sourced direct from ccusage, fresh ceiling layer.** It is the only
path that is simultaneously (1) offline/fast — mandatory for a per-prompt statusline,
(2) not blocked on kos-burn-bar's open correctness debt, and (3) built on a maintained
upstream (ccusage) rather than an unvalidated reimplementation. The bars are glance-only
with the exact % printed inline (per V6), so "approximate but stable" beats "accurate but
fragile/blocked". B's ground-truth accuracy doesn't earn its fragility for this surface;
A′ is the same idea as A but saddled with kos-burn-bar's bug debt — demote it to "revisit
if those BLOCKERs close."

## Open questions → for /grill-me

- **Weekly ceiling derivation** — A handles the 5hr ceiling via p90-of-completed-blocks,
  but weekly has no ceiling concept. Pick one: (a) p90 of completed *weeks* (needs enough
  history; cold-start weak), (b) 5hr-ceiling × a scaling constant, (c) user-supplied fixed
  weekly cap in settings, or (d) ship **5hr-only in v1** and defer the weekly bar until a
  trustworthy weekly source exists (V6 degrades to one bar).
- **`ccusage weekly` window vs CC's real weekly reset** — ccusage groups by calendar week;
  CC's weekly limit is likely a rolling 7-day window on its own reset cadence. How far does
  that mismatch push the weekly % off, and is it tolerable for a glance bar — or does it
  force option (c)/(d) above?
- **Refresh cadence** — `ccusage blocks`/`weekly` on every statusline render adds latency.
  Cache interval? (ccusage statusline already has hybrid time+file caching — reuse it, or
  add our own TTL?)
- **Ceiling cold-start** — with few completed blocks/weeks, p90 returns a bad ceiling
  (kos-burn-bar's `fallbackLimit: 44000`). What fallback does the statusline show, and how
  is a clearly-untrustworthy bar signalled vs hidden?
