---
name: session-handoff-return
description: Pop a tangent back into the main session. Summarizes what the forked /handoff tangent found, auto-syncs new findings into TODOS.md, refreshes triage, and prints a tight paste-back block for the still-alive main session. Triggers on /handoff-return. The counterpart to /handoff (push). For durable end-of-day wrap-up, use /checkpoint.
---

# Session Handoff Return Skill (pop / merge)

**Trigger:** `/handoff-return`
**Purpose:** Finish a tangent opened by `/handoff` and merge its findings upward. Auto-sync new findings to `TODOS.md`, then print a paste-back block to drop into the main session so it continues enriched.

**Mental model — push/pop:** `/handoff` pushed this tangent; `/handoff-return` pops it. The main session usually stayed alive — this skill produces the _return value_ (findings) to paste back into it. Not durable memory; for end-of-work-session narrative use `/checkpoint`.

---

## When to Use

- A tangent forked via `/handoff` is finished
- You have findings/results to carry back into the main session
- You want those findings captured in `TODOS.md` so they don't evaporate

---

## Claude Instructions (Read Before Executing)

**1.** Execute immediately. No clarifying questions. The tangent's findings are in the current conversation — extract them.

**2.** Auto-sync findings to `TODOS.md` (this is the point of the skill).
**Format detection:** check `~/.claude/references/planning-format-detect.md`
(`test -d .work/plan`) first.

**FLAT-FORMAT** (no `.work/plan/` — today's behavior, unchanged):

- Completed in the tangent → **remove** the matching `- [ ]` item entirely. Do not leave `[x]` lines — completed items belong in git history, not TODOS.md.
- New open items discovered → append with tags from `~/.claude/CLAUDE.md` (`- [ ]` + tags; untagged = Medium).
- Update the `Last updated:` date.

**NEW-FORMAT** (`.work/plan/` exists): completed in the tangent → remove BOTH the
matching index line and its detail file in `.work/todos/` if one exists. New
open items → append an index line (`- [ ]` + tags + title), spilling to
`.work/todos/<slug>.md` with a pointer only past ~150 words.

Do **not** write a SESSION-LOG narrative block either format. That is `/checkpoint`'s job.

**3.** Refresh triage (only for logs under `~/dev/`):

```bash
update-triage 2>/dev/null || echo "(update-triage failed — run manually)"
```

**4.** Print the **Paste-Back Block** to the terminal:

```
── Tangent findings (merge into main session) ──
Tangent was: {one line — what the fork chased}
Findings:
- {key result / decision / outcome}
- {…}
New TODOS added: {list, or "none"}
Resume main session at: {where it left off / next action there}
────────────────────────────────────────────────
```

- Tight. Findings + what changed in TODOS + where the main session resumes.

**5.** Print closing message:

```
✓ Findings synced to TODOS.md + .memory/TRIAGE-BLOCK.md
→ Paste the block above into your main session to continue
```

**6.** Do not run `/clear` automatically.

---

## Related

- `/handoff` — push: fork a tangent off the main session
- `/checkpoint` — durable end-of-work-session wrap-up with full narrative
