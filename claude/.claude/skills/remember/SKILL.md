---
name: remember
description: Ad-hoc fact capture. Routes a fact to KNOWLEDGE.md (local or global), runs the 4-test promotion bar, deduplicates semantically, and confirms on write. Triggers on /remember <fact>. Flag overrides: --global forces global destination, --force bypasses the bar.
---

# Remember Skill

**Trigger:** `/remember <fact>` · `/remember --global <fact>` · `/remember --force <fact>`
**Purpose:** Capture a single fact into KNOWLEDGE.md without running a full /checkpoint session.

---

## Interface

| Invocation | Behavior |
|---|---|
| `/remember <fact>` | Auto-route, run bar. Write if passes. Explain if fails. |
| `/remember --global <fact>` | Force global destination (`~/.claude/KNOWLEDGE.md`). Still runs bar. |
| `/remember --force <fact>` | Bypass bar. Write regardless. Route auto-detected unless `--global` also given. |

---

## Claude Instructions (Read Before Executing)

**1.** Read `~/.claude/references/memory-standard.md` first — authoritative source for entry format, routing rules, deduplication, and the promotion bar.

**2.** Extract the fact from the argument. Strip `--global` and `--force` flags before processing.

**3.** Determine destination:
   - `--global` present → `~/.claude/KNOWLEDGE.md`
   - Otherwise → `KNOWLEDGE.md` in the current project root (walk up from cwd for `.git` marker); fall back to `~/.claude/KNOWLEDGE.md` if not in a project
   - Apply routing escalation from memory-standard.md: if fact is environment/toolchain-level or true across ≥2 projects, auto-escalate to GLOBAL and note it

**4.** Unless `--force`:
   - Run all 4 promotion bar tests (SETTLED · NON-OBVIOUS · NOT A RULE · DURABLE)
   - If any test fails: name the failing test(s), suggest the correct destination (TODOS.md for open work, CLAUDE.md for rules), stop — do not write
   - If all pass: continue

**5.** Read the target KNOWLEDGE.md. Check for semantic duplicates or overlap.
   - Exact duplicate → print "already captured" with the existing entry, stop
   - Overlap → propose a distilled entry that merges both; confirm before writing (or reject the update)
   - No overlap → proceed

**6.** Append (or update) the entry as a flat prose bullet per the entry format in memory-standard.md.

**7.** Print one-line confirmation:
   ```
   ✓ Captured to [local|global] KNOWLEDGE.md: "- {fact}"
   ```
   If auto-escalated: append `(auto-escalated: environment/toolchain fact)`
   If --force: append `(bar bypassed — force write)`
