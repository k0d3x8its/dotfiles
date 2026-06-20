---
name: recall
description: Progressive-disclosure memory retrieval. Greps EPISODIC-INDEX.md and KNOWLEDGE.md tiers for cheap Layer-1 hits, then expands on request. Use when searching past sessions, decisions, or facts — /recall <query> for current project scope, /recall --deep <query> to fan out across all ~/dev projects including scratchpad and archive. Never auto-expands in fan-out mode.
---

# Recall Skill

**Trigger:** `/recall <query>` · `/recall --deep <query>`
**Purpose:** Cue-driven retrieval across the memory system. Three layers of progressive disclosure — start cheap, expand only what you need.

---

## Layers

| Layer | What it reads | Cost | When |
|---|---|---|---|
| L1 — index | `EPISODIC-INDEX.md` + `KNOWLEDGE.md` tiers | ~50–100 tok | Always. Compact hit list. |
| L2 — context | Surrounding `SESSION-LOG` block or KNOWLEDGE neighbors | ~200–500 tok | After a L1 hit — user picks which to expand |
| L3 — full | Entire block or file | ~500–2K tok | Only when explicitly asked |

Never jump to L2/L3 automatically. Always present L1 first and let the user decide.

---

## Default Scope (`/recall <query>`)

- Current project: `SESSION-LOG.md`, `EPISODIC-INDEX.md`
- Local `KNOWLEDGE.md` (project root)
- Global `~/.claude/KNOWLEDGE.md`

Scratchpad (`~/.claude/projects/<hash>/memory/`) is **out of default scope** — it is per-machine, unvetted, and noisy.

---

## Deep Scope (`/recall --deep <query>`)

Fan out across all `~/dev` projects. **Layer-1 grep-only** — never auto-read full logs in fan-out. Emit index hits; expand only the one the user picks.

Additional sources available under `--deep`:
- `EPISODIC-ARCHIVE.md` per project (label hits `[archived]`)
- Scratchpad: `~/.claude/projects/<hash>/memory/` (label hits `[scratch]`)

---

## Claude Instructions (Read Before Executing)

**1.** Execute immediately. Extract the query from the argument. Note whether `--deep` was passed.

**2.** git-crypt guard (applies to every `KNOWLEDGE.md` read, critical under `--deep`):
   - Before grepping any `KNOWLEDGE.md`, detect lock state: check first bytes (`head -c 10 <file>` — ciphertext starts with non-UTF-8 bytes or the string `\x00GITCRYPT`), or use `file <path>` and inspect output.
   - If locked: skip the file and emit `[locked: <project-name>]` in results. Never grep ciphertext.
   - If unlocked: proceed normally.

**3.** Layer 1 — grep and present compact hit list:

   For **default scope**: grep the following in order:
   1. `<project-root>/EPISODIC-INDEX.md` — grep for query string; emit matching lines (already one-line format: ISO timestamp + fields)
   2. `<project-root>/KNOWLEDGE.md` — grep for query string; emit matching bullet(s)
   3. `~/.claude/KNOWLEDGE.md` — grep for query string; emit matching bullet(s)
   4. `<project-root>/SESSION-LOG.md` — grep for query string in section headers; emit matching `## Session` header lines only (not full blocks)

   For **`--deep` scope**: walk every direct subdirectory of `~/dev/` that looks like a project (contains `KNOWLEDGE.md`, `SESSION-LOG.md`, or `EPISODIC-INDEX.md`). For each:
   - Apply git-crypt guard before grepping `KNOWLEDGE.md`
   - Grep `EPISODIC-INDEX.md` (if present), `KNOWLEDGE.md` (if unlocked), `EPISODIC-ARCHIVE.md` (label `[archived]`)
   - Also grep scratchpad: enumerate `~/.claude/projects/*/memory/*.md` — label any hit `[scratch]`
   - Layer-1 only — emit matching lines, never full blocks

   Output format per hit:
   ```
   [source: <file-path>] {matching line or truncated to 100 chars}
   ```
   Group by source file. If no hits: "No matches found for '{query}'" — stop.

**4.** After presenting L1 hits, prompt:
   ```
   → Reply with a hit number to expand (Layer 2), or 'full <n>' for the complete block (Layer 3). 'done' to exit.
   ```

**5.** Layer 2 — expand on request:
   - For an `EPISODIC-INDEX.md` hit: find the ISO timestamp in the index, then search `SESSION-LOG.md` for the `## Session` block nearest that date. Read and print that block only (from its `## Session` header to the next `---` separator).
   - For a `KNOWLEDGE.md` hit: print the surrounding 5 bullets (2 before, the match, 2 after) for context.
   - For a `SESSION-LOG.md` header hit: read and print that full `## Session` block.
   - For an `[archived]` hit: read `EPISODIC-ARCHIVE.md` and print the matching line + its 2 surrounding lines.
   - For a `[scratch]` hit: print the matching content from the scratchpad file. Prepend: `[scratch — unvetted, skipped the bar]`

**6.** Layer 3 — full read on `full <n>` request:
   - For an episodic/session hit: read the complete `SESSION-LOG.md` block (or the full `EPISODIC-ARCHIVE.md` entry).
   - For a KNOWLEDGE.md hit: read the entire `KNOWLEDGE.md` file.
   - For a scratchpad hit: read the full scratchpad file. Repeat the `[scratch — unvetted]` label.

**7.** Continue the expand/full loop until user types `done` or moves on.

---

## Output Labels

| Label | Meaning |
|---|---|
| `[locked: <project>]` | KNOWLEDGE.md is git-crypt encrypted — skipped |
| `[archived]` | Hit came from EPISODIC-ARCHIVE.md (older than live index) |
| `[scratch]` | Hit came from auto-memory scratchpad — unvetted, skipped promotion bar |

---

## Related

- `/consolidate` — promote episodic facts to KNOWLEDGE.md (episodic→semantic)
- `/remember` — ad-hoc fact capture into KNOWLEDGE.md
- `/checkpoint` — writes structured `SESSION-LOG` blocks that `/recall` can expand
