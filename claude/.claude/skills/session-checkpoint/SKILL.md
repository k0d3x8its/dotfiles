---
name: checkpoint
description: Durable end-of-work-session checkpoint. Writes a narrative block to .memory/SESSION-LOG.md, syncs TODOS.md, rotates the log, refreshes the triage pipeline, and prints a re-entry prompt. Triggers on /checkpoint. Use at end of day or end of a multi-hour work session — not for quick mid-session forks (use /handoff for those).
---

# Session Checkpoint Skill

**Trigger:** `/checkpoint`
**Purpose:** Durably close a work session — capture the _why_ (decisions, gotchas) to `.memory/SESSION-LOG.md`, sync open work to `TODOS.md`, refresh the triage pipeline, print a re-entry prompt.

**Not this skill:** quick mid-session tangent fork → `/handoff`. Merging tangent findings back → `/handoff-return`. Checkpoint is the heavy, durable one — run it when real decisions were made or at end of a work session.

---

## When to Use

- End of day / end of a multi-hour work session
- Real decisions made this session that a future session must not re-litigate
- Significant context worth preserving as narrative (not just open TODOs)

For a cheap mid-session fork that does **not** need durable narrative, use `/handoff` (~400 tok) instead of this (~2K tok).

---

## Output Format

Appended to `.memory/SESSION-LOG.md`:

```markdown
---
## Session Checkpoint — {YYYY-MM-DD hh:MM AM/PM}

### Goal

{1–2 sentence description of what this work session set out to accomplish}

### Completed

- [x] {Item finished and removed from TODOS.md}

### Decisions Made

- **{Decision}** — {why, so you don't re-litigate it next session}

### Files Touched

- `path/to/file` — {what changed and why}

<!-- Machine-greppable summary line — /recall Layer 1 filters on this. One line, no wrapping. -->
Files: path/to/file, path/to/other | Tags: [FEAT] [BUG] {annotation tags from CLAUDE.md describing this session's work}

### Gotchas / Notes

- {Tech debt, edge cases, token-cost observations, things to watch out for}

### Re-Entry Prompt

> "{Compact summary: project, what was built, where you left off, first action next session.
> Read `.memory/SESSION-LOG.md`, `TODOS.md`, and `KNOWLEDGE.md` (local + global) — if any reads as git-crypt ciphertext, unlock first per `~/.claude/references/git-crypt-lock-check.md` (the manual fetch→unlock pipe, run from inside the repo). For what's next across projects, read `.memory/TRIAGE-BLOCK.md`.
> First action: {step}}"

---
```

No `### Incomplete / Next Steps` block — open work lives in `TODOS.md` only.

---

## Claude Instructions (Read Before Executing)

**1.** Execute immediately. No clarifying questions. Fill every field — never leave a section blank.

**2.** Read:

- `TODOS.md` in the project root (canonical open work)
- The **most recent block only** of `.memory/SESSION-LOG.md` (for Goal/Decisions context). Do not read the whole file.
- `KNOWLEDGE.md` in the project root (if it exists) — needed for dedup in Step 7
- `~/.claude/KNOWLEDGE.md` (global knowledge) — same reason
- If `TODOS.md` does not exist: create it with this header, then scan all prior `### Incomplete / Next Steps` blocks in `.memory/SESSION-LOG.md` and migrate every unchecked `- [ ]` item into it (one-time, deduplicated):
  ```markdown
  # {project} TODOS

  > Canonical open TODO list. Maintained by /handoff + /checkpoint. Never duplicate into `.memory/SESSION-LOG.md`.
  > Last updated: {YYYY-MM-DD}

  ---
  ```

**3.** Update `TODOS.md` in-place. **Format detection:** check
`~/.claude/references/planning-format-detect.md` (`test -d .work/plan`) first.

**FLAT-FORMAT** (no `.work/plan/` — today's behavior, unchanged):

- Items **completed this session** → remove from `TODOS.md`; add to `### Completed` with `[x]`
- **New open items** → append with tags from the TODO Tags system in `~/.claude/CLAUDE.md`. Every item begins `- [ ]` then tags. Untagged = Medium.
- All other items → leave verbatim, do not reorder
- Update the `Last updated:` date in the header

**NEW-FORMAT** (`.work/plan/` exists): `TODOS.md` is a lean index — sync against
it, never against `.work/archive/legacy-todos.md` (that's the archived pre-cutover
state, not live). Items **completed this session** → remove BOTH the index line
and its detail file in `.work/todos/` if one exists (mirrors this same
remove-not-mark rule already in place today); add to `### Completed` with `[x]`.
**New open items** → append an index line (`- [ ]` + tags + title + pointer);
if the item's body exceeds ~150 words, write the full body to
`.work/todos/<slug>.md` and point the index line at it (conditional spill,
shorter items stay inline with no detail file). All other items → leave verbatim.

**4.** For **Decisions Made**: capture the _why_, not just the _what_.

**5.** For **Gotchas / Notes**: flag anything worth knowing — bugs, edge cases, token-cost observations, things the user didn't ask about but should know.

**5b.** Emit the machine-greppable `Files:` / `Tags:` line under **Files Touched** — a single unwrapped line listing the files this session touched and the annotation tags (`[FEAT]`/`[BUG]`/… from `CLAUDE.md`) that classify the work. This is the curated counterpart to the auto-captured `.memory/EPISODIC-INDEX.md` line; `/recall` Layer 1 filters on it.

**6.** Append the narrative block to `.memory/SESSION-LOG.md` at the project root.

- If `.memory/` does not exist, create it first (`mkdir -p .memory`).
- If `.memory/SESSION-LOG.md` does not exist, create it first:
  ```markdown
  # Session Log

  > Auto-generated by session skills. Do not edit manually mid-session.

  ---
  ```

**7.** KNOWLEDGE.md promotion gate — scan `### Decisions Made` and `### Gotchas / Notes` from the block just written for facts eligible for KNOWLEDGE.md.

First, read `~/.claude/references/MEMORY-STANDARD.md` — authoritative source for the promotion bar, entry format, routing, and dedup rules.

For each candidate, run all 4 bar tests (SETTLED · NON-OBVIOUS · NOT A RULE · DURABLE). Discard failures. For passing candidates, check against the KNOWLEDGE.md files read in Step 2 for semantic duplicates — skip already-known entries.

If candidates remain:

- Present them numbered in one block, each pre-routed LOCAL or GLOBAL per routing rule in MEMORY-STANDARD.md:
  ```
  KNOWLEDGE.md candidates:
  1. [LOCAL] "- {proposed entry}"  ← {which tests it passed}
  2. [GLOBAL] "- {proposed entry}" ← {why escalated to global}
  ```
- Accept: `a`/`approve` (approve all) · `d`/`deny` (deny all) · `1 2 …` (approve by number) · `r1 global` (re-route item 1) · `e1 new text` (edit item 1)
- When printing the options line to the user, always include the parenthesized labels — never bare shortcuts like "Reply `a` / `d`"
- On approval: write entries to target KNOWLEDGE.md, following distill-on-write (update existing entry on overlap, no blind-append)
- On denial: skip silently
- No candidates pass bar: skip this step silently

**8.** Refresh the triage pipeline (only for logs under `~/dev/`):

- Project name = `basename` of the log's grandparent dir (log lives at `<root>/.memory/SESSION-LOG.md`)
- TODOS path = `{log_dir}/../TODOS.md` (TODOS.md stays at project root, not in .memory/)

```bash
update-cache '{project}' '{todos_path}'
rotate-log '{log_path}' 8
update-cache '{project}' '{todos_path}'
update-triage 2>/dev/null || echo "(update-triage failed — run manually to refresh .memory/TRIAGE-BLOCK.md)"
```

All calls idempotent. If any fails, note it but don't block the checkpoint.

**9.** Changelog: use `/changelog` manually if this session produced changelog-worthy changes. Do not auto-update inline — CLAUDE.md delegates this to `/changelog`.

**10.** Print the **Re-Entry Prompt** to the terminal (same text written into the log block). It must include:

- Directive for next session to read `.memory/SESSION-LOG.md`, `TODOS.md`, and `KNOWLEDGE.md` (local + global) at start
- Pointer: "for what's next across projects, read `~/.memory/TRIAGE-BLOCK.md`" (do **not** embed a top-5 — TRIAGE-BLOCK is the single source for what's next)
- A single "first action" line

**11.** Print closing message:

```
✓ Checkpoint written to .memory/SESSION-LOG.md
✓ TODOS.md + .memory/TRIAGE-BLOCK.md updated
→ Run /clear now to reset the cache
→ Paste the Re-Entry Prompt above as your first message in the new session
```

**12.** Do not run `/clear` automatically — the user does this manually.

---

## Cache Optimization Notes

Works around Claude Code's **1-hour cache TTL**. Cached tokens cost ~10% of normal input; let them expire and you pay full price again.

**Rule of thumb:** End of work session → `/checkpoint` → `/clear` → paste re-entry. For mid-session momentum, prefer the lean `/handoff`.

---

## Integration With Other Skills

- Planning files present: read `.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md` first; sync completed/open between `.work/PLAN.md` and `TODOS.md`.
- Project-level `.claude/CLAUDE.md` exists: note conventions relevant to open items; don't reproduce it.
- Skill routing for new `TODOS.md` items: `[BUG]` → "start next session with `/diagnose`"; `[TEST]` → "use `/tdd`"; `[FEAT]` early-stage → "consider `/prototype` before building".
