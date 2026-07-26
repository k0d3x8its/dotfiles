---
name: consolidate
description: Episodic-to-semantic promotion ("sleep" phase). Sweeps .memory/SESSION-LOG.md and .memory/EPISODIC-INDEX.md entries since the last consolidation marker, runs the 4-bar promotion gate (SETTLED · NON-OBVIOUS · NOT A RULE · DURABLE), and routes approved facts through /remember's dedup logic into KNOWLEDGE.md. Use when running /consolidate manually or when reviewing a .memory/CONSOLIDATION-INBOX.md written by a scheduled run. Never auto-writes — always requires explicit approval.
---

# Consolidate Skill

**Trigger:** `/consolidate`
**Purpose:** Promote durable facts from episodic memory (SESSION-LOG, EPISODIC-INDEX) into semantic memory (KNOWLEDGE.md). The "sleep" phase — what /checkpoint's Step 7 does for one session, this does across many sessions since the last consolidation.

**Never auto-writes.** Every candidate requires explicit user approval before touching KNOWLEDGE.md.

---

## Modes

| Mode          | How triggered                                         | Writes where                              | User present? |
| ------------- | ----------------------------------------------------- | ----------------------------------------- | ------------- |
| **Manual**    | `/consolidate` in a live session                      | KNOWLEDGE.md directly (on approval)       | Yes           |
| **Scheduled** | `/schedule` (cloud cron) or system cron — NOT `/loop` | `CONSOLIDATION-INBOX.md` (proposals only) | No            |

`/loop` is in-session only and cannot produce an inbox for a future session. Use `/schedule` or system cron for unattended runs.

---

## The Consolidation Marker

Tracks where the last consolidation ended. File: `~/dev/.consolidation-marker`

Format (mirrors `.triage-cache`):

```json
{ "<project-name>": "<ISO-8601 timestamp>" }
```

- **Read** at start: determines sweep range (entries newer than the marker for the in-scope project).
- **Missing marker** = first run — sweep everything.
- **Advance** the marker to the current ISO timestamp on completion (after all candidates resolved).
- Multi-project: each project has its own key; keys are additive.

---

## Claude Instructions — Manual Mode (Read Before Executing)

**1.** Execute immediately. No clarifying questions.

**2.** Read `~/.claude/references/MEMORY-STANDARD.md` — authoritative source for the promotion bar, entry format, routing, and dedup rules. This step is mandatory before running any bar test.

**3.** Determine sweep scope:

- Read `~/dev/.consolidation-marker` (JSON). Extract the timestamp for the current project (key = `basename` of cwd's project root).
- Missing key or missing file = first run: sweep from the beginning of time.
- Otherwise: sweep only entries with a timestamp newer than the stored value.

**4.** Read sources in this order:

- `<project-root>/.memory/EPISODIC-INDEX.md` — filter to lines with timestamps newer than the marker
- `<project-root>/.memory/SESSION-LOG.md` — find `## Session` blocks whose date header is newer than the marker
- For each qualifying SESSION-LOG block, scan `### Decisions Made` and `### Gotchas / Notes` sections for candidate facts (same sections /checkpoint's Step 7 scans)

**5.** Read dedup targets:

- `<project-root>/KNOWLEDGE.md` (if it exists)
- `~/.claude/KNOWLEDGE.md`

**6.** Run the promotion gate — identical to /checkpoint Step 7:

For each candidate fact, run all 4 bar tests:

- **SETTLED** — not open work. Verbs like "implement", "fix", "add", "build", "update" → TODOS.md, not here.
- **NON-OBVIOUS** — cannot be derived in 30 seconds by reading the repo.
- **NOT A RULE** — empirical observation, not a normative instruction (rules → CLAUDE.md).
- **DURABLE** — unlikely to go stale within ~3 months.

Discard any candidate that fails a test. Check survivors against KNOWLEDGE.md files (Step 5) for semantic duplicates — skip already-known entries.

**7.** If candidates remain, present them numbered in one block, each pre-routed LOCAL or GLOBAL per routing rules in MEMORY-STANDARD.md:

```
KNOWLEDGE.md candidates:
1. [LOCAL] "- {proposed entry}"  ← {which tests it passed}
2. [GLOBAL] "- {proposed entry}" ← {why escalated to global}
```

Accept grammar (same as /checkpoint Step 7):

- `a` / `approve` — approve all
- `d` / `deny` — deny all
- `1 2 …` — approve by number
- `r1 global` — re-route item 1 to global
- `e1 new text` — edit item 1's text before writing

When printing the options line, always include the parenthesized labels — never bare shortcuts like "Reply `a` / `d`". Precede the list with a recommendation + one-line why (per MEMORY-STANDARD.md § Recommendations).

**8.** On approval: write entries to the target KNOWLEDGE.md following distill-on-write (update existing entry on overlap, no blind-append). Route through `/remember`'s dedup check — exact duplicate → "already captured", overlap → propose merged entry.

**9.** For candidates that fail the bar:

- SETTLED failure (open work) → append to `TODOS.md` with appropriate tags and note: "(rejected by /consolidate — not yet settled)"
- NOT A RULE failure → suggest adding to `CLAUDE.md` (do not write automatically)
- Other failures → drop silently

**10.** Advance the marker: write the current ISO timestamp for this project to `~/dev/.consolidation-marker`.

```json
{ "<project>": "2026-06-19T14:32:00Z" }
```

Merge with any existing keys — do not clobber other projects' entries.

**11.** Print closing message:

```
✓ Consolidation complete — marker advanced to {ISO timestamp}
✓ {N} fact(s) promoted to KNOWLEDGE.md
✓ {M} item(s) routed to TODOS.md (open work)
→ Run /recall <query> to verify promoted facts are retrievable
```

If no candidates passed the bar: "No new facts to promote — marker advanced."

---

## Claude Instructions — Scheduled Mode

When running unattended (via `/schedule` or system cron), follow Steps 1–6 above, then:

**S7.** Instead of presenting candidates interactively, write them to `.memory/CONSOLIDATION-INBOX.md` in the project root:

```markdown
# Consolidation Inbox — {ISO timestamp}

> Review these candidates. Reply `a` / `d` / `1 2` / `r1 global` / `e1 new text` in a live session.
> Run /consolidate to process this inbox, or delete the file to skip.

## Candidates

1. [LOCAL] "- {proposed entry}" ← {tests passed}
2. [GLOBAL] "- {proposed entry}" ← {why global}
```

**S8.** Do NOT advance the marker until a live session processes the inbox.

**S9.** Notify (print to stdout / send to configured notifier): "Consolidation inbox written — {N} candidates pending review."

**Live session processes inbox:** When a user runs `/consolidate` and `.memory/CONSOLIDATION-INBOX.md` exists, read it first and process its candidates instead of re-sweeping from the marker. On completion: delete `.memory/CONSOLIDATION-INBOX.md`, advance the marker.

---

## Differs From /checkpoint Step 7

| Dimension | /checkpoint Step 7                                          | /consolidate                                  |
| --------- | ----------------------------------------------------------- | --------------------------------------------- |
| Scope     | Current session's `### Decisions Made` + `### Gotchas` only | All sessions since consolidation marker       |
| Trigger   | Automatic at session end                                    | Manual or scheduled                           |
| Mode      | Always interactive                                          | Manual (interactive) or scheduled (inbox)     |
| Marker    | None — single session                                       | `~/dev/.consolidation-marker` tracks progress |

Gate logic, grammar, and dedup behavior are identical.

---

## Related

- `/remember` — single-fact ad-hoc capture (dedup + bar; routing logic reused here)
- `/recall` — retrieve facts from episodic + semantic memory
- `/checkpoint` — durable session close; Step 7 is the per-session precursor to this skill
- `/schedule` — set up unattended scheduled consolidation runs
