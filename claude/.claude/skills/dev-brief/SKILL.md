---
name: dev-brief
description: Morning/context-switch brief across all projects in ~/dev. Reads TODOS.md or SESSION-LOG.md per project, surfaces open TODOs, live git state, gotchas, decisions, branch, and release-pending signals. Auto-reconciles TODOs against live git state. Triggers on /dev-brief or /dev-brief <project>.
---

# Dev Brief Skill

**Trigger:** `/dev-brief` or `/dev-brief <project>` or `/dev-brief triage`
**Purpose:** Produce a fast, high-signal brief across every project in `~/dev` so you can orient in under 60 seconds — what's open, what's dirty, what will burn you if you forget.

---

## Modes

### Default — `/dev-brief`
Full sweep of all projects in `~/dev`. One block per project with a session-log. Orphaned projects (no session-log) listed at the bottom.

### Deep-dive — `/dev-brief <project>`
Single project. Full re-entry prompt, all TODOs, all gotchas, all decisions, full git state. Use before starting a session on that project. **OPEN TODOs are tiered by priority (severity descending: Critical → High → Medium → Low → Backlog) and tag-grouped within each tier** — apply the same Step-6 tier assignment used by the Triage Block, but render it inside this single project's block (see Step 7 / deep-dive template). This is distinct from the cross-project Triage Block, which deep-dive still skips.

### Triage-only — `/dev-brief triage`
**Primary use: cache repair.** Runs full discovery + TODO collection + git reconciliation when `.triage-cache` is stale, corrupted, or missing project blocks. Skips printing project blocks and orphans; outputs only the Triage Block to terminal. After terminal output, calls `update-triage` (see instruction 14) to regenerate `~/dev/TRIAGE-BLOCK.md`. Under normal operation, `TRIAGE-BLOCK.md` is maintained by the `update-triage` shell script after every `/handoff` — run `/dev-brief triage` only when the cache needs a manual rebuild.

---

## What Claude Will Do

### Step 1 — Discover projects

Run:
```bash
find ~/dev -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
```

For each directory, check:
- Does `TODOS.md`, `SESSION-LOG.md`, or `session-log.md` exist? → active project
- None of the above? → orphan, collect for summary at end

**Also check for machine-level log:**
```bash
[ -f ~/dev/SESSION-LOG.md ] || [ -f ~/dev/session-log.md ] && echo "EXISTS"
```
If `~/dev/SESSION-LOG.md` or `~/dev/session-log.md` exists, treat it as a special project named `[machine]` with no git state. Apply the same session parsing, reconciliation, TODO flagging, and staleness rules. Show it as the first block in the brief. In deep-dive mode, `/dev-brief machine` targets this file.

### Step 2 — Per active project, gather data

**Cache gate first (mtime read-skip) — see the Triage Cache section below.**
For each active project (and `[machine]`), decide whether to READ the log or trust the cache:
```bash
live=$(stat -c %Y "$log" 2>/dev/null)              # log's modification time (epoch seconds)
cached=$(awk -v want="$proj" '/^## /{cur=substr($0,4);next} /^mtime:/&&cur==want{sub(/^mtime:[[:space:]]*/,"");print;exit}' ~/dev/.triage-cache 2>/dev/null)
```
- `live` empty → **GONE** (log deleted; drop the project's cache block, omit from brief)
- `cached` empty → **READ** (cold: never cached)
- `live > cached` → **READ** (log changed since last brief)
- `live <= cached` → **HIT** (nothing changed; skip the log read)

**On HIT:** load the project's open-TODO lines verbatim from its `## {project}` block in `~/dev/.triage-cache`. **Do NOT read the session-log.** (Gotchas/Decisions/re-entry are not cached — they're only needed for deep-dive mode, which always READs its single target project.)

**On READ/cold:**
- If `TODOS.md` exists: read all `- [ ]` lines from it for TODOs. Read SESSION-LOG.md/session-log.md (latest block only) for session date, Gotchas, Decisions, and Re-Entry Prompt.
- Else: parse SESSION-LOG.md or session-log.md (latest block only) for all of the below.
- Session date/time (from `## Session Handoff — {date}` header — parse every block's date and take the NEWEST by date; do NOT assume position. Logs vary: the machine log is newest-at-top, kos is newest-at-bottom)
- All unchecked TODOs: lines matching `- [ ]` (from TODOS.md if it exists, else from Incomplete section)
- Gotchas section: all bullet lines under `### Gotchas / Notes`
- Decisions section: first 3 bullet lines under `### Decisions Made`
- Re-entry prompt: full block under `### Re-Entry Prompt` (used in deep-dive mode). **Splice on render:** this section stores prose + first-action with a pointer to TODOS.md (or `### Incomplete / Next Steps` for legacy logs). When printing the deep-dive RE-ENTRY PROMPT box, expand that pointer — inline every unchecked `- [ ]` item from TODOS.md (or the same block's Incomplete section) so the printed paste is self-contained.

**After a READ, refresh the cache — MANDATORY, runs in triage mode too:**
- For **TODOS.md projects**: call `update-cache <project> <todos_path>` — the script stats TODOS.md and writes a pointer block. Do this after any Step-3 self-heal write to TODOS.md.
- For **legacy session-log projects**: rewrite that project's `## {project}` block in `~/dev/.triage-cache` with the verbatim open-TODO lines just parsed and `mtime:` = a FRESH `stat -c %Y` of the log taken *after* any Step-3 self-heal write.
In both cases, re-`stat` the tracked file and confirm the written `mtime:` equals live; an unrefreshed block re-reads forever. **Why this is not optional:** skipping the refresh is the #1 cache bug. Triage mode is output-minimal but MUST still do this write-back. (Write-through: `/handoff` does the same — see session-handoff.)

**Run git commands (from that project's directory):**
```bash
git -C ~/dev/<project> branch --show-current 2>/dev/null
git -C ~/dev/<project> status --short 2>/dev/null | wc -l
git -C ~/dev/<project> log @{u}.. --oneline 2>/dev/null | wc -l
```
If not a git repo, show `not a git repo`.
If no upstream set, show `no upstream`.

**Check for pending release:**
```bash
[ -s ~/dev/<project>/RELEASE-NOTES.md ] && echo "RELEASE PENDING"
```

**Check for task_plan.md:**
If `task_plan.md` exists, extract unchecked items (`- [ ]`) from it and merge into TODOs, labeled `[plan]`.

### Step 3 — Reconcile session-log against live git state

For each project, compare live git output against its open TODOs (loaded from the cache on a HIT, from the log on a READ). Git state is **always live** — never cached; `git log @{u}..` / `status` output is tiny.

**Self-healing on HIT:** if reconciliation resolves a TODO, write the change (per the rules below). That write bumps the file's mtime. **Immediately after the write, refresh this project's cache block** (call `update-cache` for TODOS.md projects; inline awk for legacy) — so the block stays a HIT next brief instead of self-invalidating into a needless cold re-READ of an otherwise-unchanged file. A HIT therefore never strands a resolved TODO *and* never forces the next brief to re-read it.

**Reconciliation rules:**

| Condition | Matches TODO containing | Action |
|---|---|---|
| `git log @{u}..` = 0 commits | `push`, `git push`, `unpushed`, `commits ahead`, `push to remote`, `push origin`, `ahead of origin` | Auto-resolve |
| `git status --short` = 0 files | `uncommitted`, `not yet committed`, `stage`, `dirty`, `git add`, `commit changes` | Auto-resolve |

**Auto-resolve means:**
1. **TODOS.md project**: remove the matched `- [ ]` line from `TODOS.md`; call `update-cache <project> <todos_path>`. **Legacy session-log project**: change the matched `- [ ]` line to `- [x]` in `SESSION-LOG.md` or `session-log.md` and append ` *(auto-resolved by dev-brief {YYYY-MM-DD})*`
2. In the brief output: show the item with a `✓` prefix instead of `·` and label `(auto-resolved)`
3. Do NOT auto-resolve if the TODO text is ambiguous — e.g. "consider committing X" or "decide whether to push". Only resolve when the intent is clearly a push/commit action that live git confirms is done.
4. Only modify TODOs within the latest session block. Never touch earlier session entries.
5. After writing, report how many TODOs were auto-resolved at the bottom of the project block.

**Step 3b — Fix-commit reconcile (FLAG-ONLY, never auto-resolve):**

The push/commit rules above only catch TODOs whose intent *is* "push/commit". They miss the common stale-after-fix case: a `[BUG]`/`[FEAT]`/`[RELEASE]` TODO whose underlying work was already done by a normal fix commit. This pass surfaces those for human verification — it **never** writes to any file and **never** changes `- [ ]` to `- [x]`. It is advisory output only, recomputed every run (like git state and tiers — never cached).

Run this pass only for open TODOs in the **latest session block** that are tagged `[BUG]`, `[FEAT]`, or `[RELEASE]` (the work-producing tags). Skip `[DECISION]`/`[INVESTIGATE]`/`[CHORE]`/`[DOCS]` — those don't close via a code commit.

1. **Candidate commits.** Collect recent commit subjects + changed paths since the block was written:
   ```
   git -C ~/dev/<repo> log --since="<latest-block-date>" --no-merges --pretty='%h %s' --name-only 2>/dev/null
   ```
   - For a normal project's own TODOs: scan that project's repo.
   - For `[machine]` TODOs: machine/config work lands in `~/dev/dotfiles` (and occasionally other repos), **not** in the machine log's own (absent) git. So scan `~/dev/dotfiles` plus any repo the TODO text names. This cross-repo scan is the whole point — cause #1 of the RCA was the fix-repo ≠ TODO-repo gap.
2. **Match (conservative).** Tokenize the TODO text (strip tags, strip stopwords). Flag a TODO against a commit only on **high-signal** overlap:
   - a **filename or path** named in the TODO appears in that commit's changed paths (strongest), OR
   - **≥2 distinctive content words** (skill name, function, feature noun — not generic words like "fix"/"add"/"update") shared between TODO text and commit subject.
   Prefer precision over recall — a missed flag is cheap (status quo), a noisy flag erodes trust.
3. **Output.** Prefix the matched TODO line with `⚑` and append ` — possibly resolved by <hash>(<repo>) — verify`. Show under the project block. Never modify the log.
4. **De-dup.** Skip any TODO the push/commit rules already auto-resolved this run.
5. Report the flag count at the bottom of the project block, separate from the auto-resolved count.

> **P2 (stable TODO IDs `[#id]` → exact commit reconcile + carry-forward dedup) is deferred to `[BACKLOG]`**, gated on P1's false-positive rate proving insufficient. Do not build the ID system unless fuzzy flagging proves too noisy in practice.

### Step 4 — Flag urgent TODOs

Scan each TODO line (case-insensitive) for the urgent keywords in the **Keyword Flag Reference** below — the single canonical list. Flag matched lines with a `⚠` prefix in output.

### Step 5 — Calculate staleness

Compute days since last session:
- Parse date from `## Session Handoff — {date}` header
- Compare to today's date
- `0d` = today, `1d` = yesterday, etc.
- Mark projects not touched in >7 days with `[STALE]`

### Step 6 — Build priority triage

After collecting all open TODOs across all projects (post-reconciliation), assign each to one of five tiers using tag-first detection, falling back to keyword heuristics for untagged items. **Tiers are recomputed fresh every run — never cached** (tag→tier rules still evolve; a cached tier would serve stale priority). The cache stores only mtime + raw TODO lines.

**Tag-first rules (mechanical — no judgment needed):** map priority tags to tiers per the **TODO Tags** table in `~/.claude/CLAUDE.md` (`[BROKEN]`→Critical, `[BLOCKER]`→High, `[LOW]`→Low, `[BACKLOG]`→Backlog, untagged→Medium). dev-brief-specific rule: if both `[BROKEN]` and `[BLOCKER]` are present, the item is Critical.

**Keyword fallback (for untagged TODOs):**

**Critical** — TODO was ⚠-flagged AND text contains: `broken`, `failing`, `can't work`, `not working`, `crashed`, `down`

**High** — any of:
- TODO was flagged `⚠` (matched urgent keyword list in Step 4) and not Critical
- TODO text contains: `blocker`, `blocks`, `blocked`, `blocking`, `critical`
- Project is `[STALE]` and has open TODOs

**Low** — TODO text contains: `consider`, `evaluate`, `low priority`, `nice to have`, `when ready`, `no rush`

**Backlog** — TODO text contains: `someday`, `eventually`, `future`, `parked`, `long-term`, `backlog`

**Medium** — everything else (default: concrete action items, RELEASE PENDING TODOs, decisions pending, implementation tasks)

**Annotation tags** — the set (`[BUG]`, `[FEAT]`, `[CHORE]`, `[TEST]`, `[RELEASE]`, `[DECISION]`, `[INVESTIGATE]`) is defined in `~/.claude/CLAUDE.md`. They do not affect tier assignment. Display them inline between the project name and TODO text so the work type is visible at a glance.

**Formatting rules:**
- One line per TODO: `  [project]  {annotation tags} {truncated todo text — 70 chars max}`
- Truncate with `…` if text exceeds 70 chars
- Sort within each tier: ⚠/`[BROKEN]` items first, then alphabetically by project name
- Omit any tier that has no items
- Do not include auto-resolved (✓) items
- Strip priority tags (`[BROKEN]`, `[BLOCKER]`, `[LOW]`, `[BACKLOG]`) from displayed text — tier already communicates that. Keep annotation tags visible.

**Deep-dive application (single-project OPEN TODOs):** in deep-dive mode, render that one project's OPEN TODOs with the SAME tier assignment as above — tier headers `CRITICAL → HIGH → MEDIUM → LOW → BACKLOG` top-to-bottom (omit empty tiers), and **within each tier group by annotation tag** (`[BUG]`, `[FEAT]`, `[CHORE]`, `[TEST]`, `[RELEASE]`, `[DECISION]`, `[INVESTIGATE]`, `[DOCS]`, …). Within a tag group, ⚠/⚑-marked items first, then source order. An item with multiple annotation tags files under its first tag. Untagged items group under `[misc]`. Keep the `⚠`/`⚑` prefixes; strip priority tags from text (tier shows it). Auto-resolved `✓` items are listed once at the bottom, untiered. This replaces the old flat verbatim OPEN TODOs list — full-context deep-dive now reads severity-first.

### Step 7 — Print output

See Output Format below.

---

## Output Format

- **Default mode** — see `templates/format-default.md`
- **Deep-dive mode** — see `templates/format-deep-dive.md`
- **Triage-only mode** — header: `TRIAGE — {YYYY-MM-DD}` · `{Y} open TODOs across {N} projects`. Then Triage Block (same structure as end of default format). No project blocks, no orphans. Then run `update-triage` via Bash (see instruction 14) — do not generate HTML directly.

---

## Claude Instructions (Read Before Executing)

Steps 1–7 above define the behavior. These add constraints not already stated there (don't restate the steps):

1. **Execute immediately** — no clarifying questions.
2. **Cache gate before any log read** — `stat` every session-log and decide READ/HIT/GONE against `~/dev/.triage-cache` (see Step 2 + Triage Cache section). Only READ logs that are cold or changed; trust the cache on a HIT. **Refresh each READ project's cache block is MANDATORY — including in triage mode — and verified (`stat` after write == live mtime); an unrefreshed block re-reads forever.** After any Step-3 self-heal write to a log, re-refresh that block with the post-write mtime. Deep-dive mode always READs its single target (skip the gate there).
3. Run all git commands in parallel to keep output fast.
4. **Latest session only** — block ordering is NOT consistent across logs (machine log is newest-at-top; kos is newest-at-bottom). Parse the date in every `## Session Handoff — {date}` header and select the block with the newest date as the active one. Never assume position (top or bottom) = latest. All other blocks are history.
5. If a project has zero open TODOs, show `· (no open TODOs)` — never skip silently.
6. If project has no `TODOS.md` and `SESSION-LOG.md`/`session-log.md` has no `### Incomplete / Next Steps` section, note `· (no TODO section found)`.
7. **Orphans** — list every *directory* in `~/dev/` lacking `TODOS.md`, `SESSION-LOG.md`, or `session-log.md`. Root files are never listed (except `~/dev/SESSION-LOG.md` or `~/dev/session-log.md`, handled as `[machine]`).
8. Print output as plain markdown — no code-block wrapper around the brief.
9. Dev dir is always `~/dev/` — never prompt for a path.
10. **Auto-reconcile before printing** — write resolved items to `TODOS.md` (TODOS.md projects) or `SESSION-LOG.md`/`session-log.md` (legacy) first, then render with `✓` markers. When in doubt, leave `- [ ]` untouched.
11. **task_plan.md reconciliation** — apply the same push/commit reconciliation to `task_plan.md` open items if present.
12. **Fix-commit flags are advisory-only (Step 3b)** — `⚑ possibly resolved` items are NEVER written to any log and NEVER auto-closed; they are recomputed every run from live git, like git state and tiers. They surface a `[BUG]`/`[FEAT]`/`[RELEASE]` TODO whose work a normal commit may have already done (the stale-after-fix gap, RCA 2026-05-30). Bias to precision: skip a doubtful match rather than emit a noisy flag.
13. **Triage Block** — emit after the orphans list, before the footer. Omit empty tiers. Default mode only — skip in deep-dive.
14. **Visual triage write (triage mode only)** — after terminal output, run `update-triage` via Bash to regenerate `~/dev/TRIAGE-BLOCK.md`. The shell script reads `.triage-cache` (just refreshed this run) and writes the HTML-colored file — no need for Claude to generate the HTML directly. Do not write in default or deep-dive mode.

---

## Keyword Flag Reference

Flag a TODO with `⚠` if it contains any of (case-insensitive):

```
failing, broken, not yet, do not, DO NOT, warning, stale, never, never committed,
bug, error, unresolved, critical, missing, haven't, has not, hasn't
```

---

## Triage Cache — `~/dev/.triage-cache`

A single machine-wide cache that lets the brief skip reading unchanged session-logs. On a quiet day every log is a HIT and the brief reads only this ~0.5 KB file instead of ~175 KB of logs.

**Format** — one block per *active* project (logged dirs only; orphans are never cached). Two formats, both valid:
```
<!-- triage-cache v1 | dev-brief read-skip | "## <project>" then "mtime: <epoch>" then
     "path: <todos>" (pointer — TODOS.md projects) or verbatim "- [ ]" lines (legacy) -->

## [machine]           ← pointer format (TODOS.md project)
mtime: 1780324513
path: /home/k0d3x/dev/TODOS.md

## batctrl             ← legacy format (session-log.md project)
mtime: 1780189650
- [ ] [BUG] ...
```

**Rules:**
- `mtime:` = `stat -c %Y` of the tracked file (TODOS.md for pointer projects; session-log for legacy).
- **Pointer format**: `path:` line points to TODOS.md; `parse_cache` (in update-triage) reads that file for TODO lines.
- **Legacy format**: TODO lines are verbatim `- [ ]` lines from the latest session block.
- Stores **only** mtime + source pointer or raw lines. **Never** caches tiers (recomputed each run) or git state (always live).
- **Writers:** dev-brief refreshes a block after a READ; session-handoff calls `update-cache` for TODOS.md projects (write-through, keeps it a HIT next brief). Cache is idempotent derived state — safe to delete; cold rebuild costs one full read pass.
- **GONE:** if a cached `## {project}` has no live file (TODOS.md or session-log), drop the block.
- `[machine]` → `~/dev/TODOS.md` (or `~/dev/SESSION-LOG.md` / `~/dev/session-log.md` for legacy); project logs → `~/dev/{project}/TODOS.md` (or session-log).

---

## Integration Notes

- **session-handoff** writes `SESSION-LOG.md` and `TODOS.md` that this skill reads. Run `/handoff` at end of every session to keep briefs accurate.
- **planning-with-files** writes `task_plan.md`. This skill merges open items from it automatically if present.
- Run `/dev-brief <project>` immediately before starting a session on that project — re-entry prompt is ready to paste after `/clear`.
- When a Triage Block item carries `[BUG]`, append `→ /diagnose` to the line in output so the next session starts with the right skill.
- When a Triage Block item carries `[TEST]`, append `→ /tdd`.
