---
name: dev-brief
description: Morning/context-switch brief across all projects in ~/dev. Reads session-log.md per project, surfaces open TODOs, live git state, gotchas, decisions, branch, and release-pending signals. Auto-reconciles session-log TODOs against live git state. Triggers on /dev-brief or /dev-brief <project>.
---

# Dev Brief Skill

**Trigger:** `/dev-brief` or `/dev-brief <project>` or `/dev-brief triage`
**Purpose:** Produce a fast, high-signal brief across every project in `~/dev` so you can orient in under 60 seconds — what's open, what's dirty, what will burn you if you forget.

---

## Modes

### Default — `/dev-brief`
Full sweep of all projects in `~/dev`. One block per project with a session-log. Orphaned projects (no session-log) listed at the bottom.

### Deep-dive — `/dev-brief <project>`
Single project. Full re-entry prompt, all TODOs, all gotchas, all decisions, full git state. Use before starting a session on that project.

### Triage-only — `/dev-brief triage`
Runs full discovery + TODO collection + git reconciliation, but skips printing project blocks and orphans. Outputs only the Triage Block. Use when you just need prioritized work order without the per-project narrative. Skips reading Gotchas/Decisions sections to reduce input tokens.

---

## What Claude Will Do

### Step 1 — Discover projects

Run:
```bash
find ~/dev -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
```

For each directory, check:
- Does `session-log.md` exist? → active project
- No `session-log.md`? → orphan, collect for summary at end

**Also check for machine-level log:**
```bash
[ -f ~/dev/session-log.md ] && echo "EXISTS"
```
If `~/dev/session-log.md` exists, treat it as a special project named `[machine]` with no git state. Apply the same session parsing, reconciliation, TODO flagging, and staleness rules. Show it as the first block in the brief. In deep-dive mode, `/dev-brief machine` targets this file.

### Step 2 — Per active project, gather data

**Parse session-log.md (latest session block only):**
- Session date/time (from `## Session Handoff — {date}` header — latest one at top)
- All unchecked TODOs: lines matching `- [ ]`
- Gotchas section: all bullet lines under `### Gotchas / Notes`
- Decisions section: first 3 bullet lines under `### Decisions Made`
- Re-entry prompt: full block under `### Re-Entry Prompt` (used in deep-dive mode)

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

For each project, compare live git output against open TODOs in the latest session block.

**Reconciliation rules:**

| Condition | Matches TODO containing | Action |
|---|---|---|
| `git log @{u}..` = 0 commits | `push`, `git push`, `unpushed`, `commits ahead`, `push to remote`, `push origin`, `ahead of origin` | Auto-resolve |
| `git status --short` = 0 files | `uncommitted`, `not yet committed`, `stage`, `dirty`, `git add`, `commit changes` | Auto-resolve |

**Auto-resolve means:**
1. In `session-log.md`: change the matched `- [ ]` line to `- [x]` and append ` *(auto-resolved by dev-brief {YYYY-MM-DD})*`
2. In the brief output: show the item with a `✓` prefix instead of `·` and label `(auto-resolved)`
3. Do NOT auto-resolve if the TODO text is ambiguous — e.g. "consider committing X" or "decide whether to push". Only resolve when the intent is clearly a push/commit action that live git confirms is done.
4. Only modify TODOs within the latest session block. Never touch earlier session entries.
5. After writing, report how many TODOs were auto-resolved at the bottom of the project block.

### Step 4 — Flag urgent TODOs

Scan each TODO line (case-insensitive) for the urgent keywords in the **Keyword Flag Reference** below — the single canonical list. Flag matched lines with a `⚠` prefix in output.

### Step 5 — Calculate staleness

Compute days since last session:
- Parse date from `## Session Handoff — {date}` header
- Compare to today's date
- `0d` = today, `1d` = yesterday, etc.
- Mark projects not touched in >7 days with `[STALE]`

### Step 6 — Build priority triage

After collecting all open TODOs across all projects (post-reconciliation), assign each to one of five tiers using tag-first detection, falling back to keyword heuristics for untagged items.

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

### Step 7 — Print output

See Output Format below.

---

## Output Format

- **Default mode** — see `templates/format-default.md`
- **Deep-dive mode** — see `templates/format-deep-dive.md`
- **Triage-only mode** — header: `TRIAGE — {YYYY-MM-DD}` · `{Y} open TODOs across {N} projects`. Then Triage Block (same structure as end of default format). No project blocks, no orphans.

---

## Claude Instructions (Read Before Executing)

Steps 1–7 above define the behavior. These add constraints not already stated there (don't restate the steps):

1. **Execute immediately** — no clarifying questions.
2. Run all git commands in parallel to keep output fast.
3. **Latest session only** — parse the topmost `## Session Handoff` block; earlier ones are history, not active state.
4. If a project has zero open TODOs, show `· (no open TODOs)` — never skip silently.
5. If `session-log.md` has no `### Incomplete / Next Steps` section, note `· (no TODO section found)`.
6. **Orphans** — list every *directory* in `~/dev/` lacking a `session-log.md`. Root files are never listed (except `~/dev/session-log.md`, handled as `[machine]`).
7. Print output as plain markdown — no code-block wrapper around the brief.
8. Dev dir is always `~/dev/` — never prompt for a path.
9. **Auto-reconcile before printing** — write resolved items to `session-log.md` first, then render with `✓` markers. When in doubt, leave `- [ ]` untouched.
10. **task_plan.md reconciliation** — apply the same push/commit reconciliation to `task_plan.md` open items if present.
11. **Triage Block** — emit after the orphans list, before the footer. Omit empty tiers. Default mode only — skip in deep-dive.

---

## Keyword Flag Reference

Flag a TODO with `⚠` if it contains any of (case-insensitive):

```
failing, broken, not yet, do not, DO NOT, warning, stale, never, never committed,
bug, error, unresolved, critical, missing, haven't, has not, hasn't
```

---

## Integration Notes

- **session-handoff** writes the `session-log.md` this skill reads. Run `/handoff` at end of every session to keep briefs accurate.
- **planning-with-files** writes `task_plan.md`. This skill merges open items from it automatically if present.
- Run `/dev-brief <project>` immediately before starting a session on that project — re-entry prompt is ready to paste after `/clear`.
- When a Triage Block item carries `[BUG]`, append `→ /diagnose` to the line in output so the next session starts with the right skill.
- When a Triage Block item carries `[TEST]`, append `→ /tdd`.
