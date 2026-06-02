---
name: session-handoff
description: Lean mid-session fork. Spins off a focused tangent from the main session — emits a reason-first re-entry prompt (why it forked + scope + first action) so you can open a fresh, clean-context session to chase a side-issue. Does NOT write SESSION-LOG narrative. Triggers on /handoff [focus]. When the tangent is done, use /handoff-return to merge findings back. For durable end-of-day wrap-up, use /checkpoint.
argument-hint: "What will the tangent session focus on? (optional — Claude will infer from conversation if omitted)"
---

# Session Handoff Skill (push / fork)

**Trigger:** `/handoff`
**Purpose:** Fork a *tangent* off the current session. Print a focused re-entry prompt so a fresh session can chase a side-issue with clean context — then `/handoff-return` merges its findings back into the still-alive main session.

**Mental model — push/pop:** `/handoff` pushes a tangent; `/handoff-return` pops it back with findings. This is lightweight context-passing between adjacent sessions, **not** durable memory. For end-of-work-session narrative, use `/checkpoint`.

---

## When to Use

- Main session hits a side-issue worth chasing in isolation (a chore, a bug, an investigation)
- You want clean context for the tangent without losing the main thread
- The main session usually **stays open** — you'll paste findings back into it via `/handoff-return`

**Crash-safety:** re-entry prompt is saved to `/tmp/handoff-{timestamp}.md` — survives terminal crash or accidental tab exit. File is not project-specific and will be cleaned up by OS on reboot.

---

## Claude Instructions (Read Before Executing)

**1.** Execute immediately. No clarifying questions. Determine the tangent's focus:
   - If arguments were passed to `/handoff`, use them as the declared focus.
   - Otherwise, extract the reason from the current conversation — do not ask.

**2.** Light TODOS touch only:
   - If the tangent corresponds to an existing `TODOS.md` item, note it.
   - If forking reveals a new open item, append it to `TODOS.md` with tags from `~/.claude/CLAUDE.md` (`- [ ]` + tags; untagged = Medium). Update the `Last updated:` date.
   - Do **not** write a SESSION-LOG narrative block. That is `/checkpoint`'s job.

**3.** Refresh triage (only for logs under `~/dev/`):
   ```bash
   update-triage 2>/dev/null || echo "(update-triage failed — run manually)"
   ```

**4.** Build the **Tangent Re-Entry Prompt**:

   ```
   ── Tangent fork ──────────────────────────────
   Reason: {why this forked off the main session — the trigger}
   Scope:  {what the tangent should accomplish, bounded}
   First action: {single concrete step}

   Suggested skills: {1-3 skills relevant to this tangent, e.g. /diagnose for bugs, /tdd for tests, /investigate for audits}

   At session start: read TODOS.md. For what's next across projects, read TRIAGE-BLOCK.md.
   When done, run /handoff-return to merge findings back into the main session.
   ──────────────────────────────────────────────
   ```

   - **Reason-first** — the reason is the parameter passed down; lead with it.
   - Keep it tight. No top-5, no narrative, no decisions log.
   - Suggested skills: pick from skills relevant to the tangent's type (bug → `/diagnose`, test gap → `/tdd`, open sweep → tag `[INVESTIGATE]`, etc.). 1-3 max.

**5.** Save re-entry prompt to `/tmp`:
   ```bash
   HANDOFF_FILE="/tmp/handoff-$(date +%Y-%m-%dT%H-%M).md"
   # write the prompt block to $HANDOFF_FILE
   echo "Saved to $HANDOFF_FILE"
   ```
   - Do not save anything else to `/tmp` — no narrative, no TODOS.

**6.** Print the re-entry prompt to terminal (paste convenience), then print closing message:
   ```
   ✓ Tangent prompt ready — saved to /tmp/handoff-{timestamp}.md (no SESSION-LOG written — this is a fork, not a checkpoint)
   → Open a new session and paste the Tangent Re-Entry Prompt above
   → Main session can stay open; /handoff-return merges findings back when you're done
   ```

**7.** Do not run `/clear` automatically.

---

## Related

- `/handoff-return` — pop: summarize the tangent's findings and sync them to `TODOS.md`
- `/checkpoint` — durable end-of-work-session wrap-up with full narrative
