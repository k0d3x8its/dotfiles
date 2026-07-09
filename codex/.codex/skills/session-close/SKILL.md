---
name: session-close
description: Lightweight session close. Emits a resume-focused re-entry prompt (working on + left off + open items) so you can start a fresh session and pick up exactly where you left off. No SESSION-LOG narrative. Use when you're done for now but didn't make major architectural decisions (those warrant /checkpoint). Triggers on /close.
---

# Session Close Skill (close + resume)

**Trigger:** `/close`
**Purpose:** Close the current session cleanly and emit a resume-focused re-entry prompt so the next session starts with full context. Lightweight — no narrative, no rotate-log, no update-cache.

**Mental model:** Neither a fork (/handoff) nor a durable close (/checkpoint). Use when: wrapping up, no live main session to return to, didn't make decisions worth narrating. The re-entry prompt is the artifact.

---

## When to Use

- Done for now, want to resume later from exactly here
- No live main session to merge findings into (that's /handoff-return)
- Didn't make major architectural decisions this session (those warrant /checkpoint)

---

## Codex Instructions (Read Before Executing)

**1.** Execute immediately. No clarifying questions. Extract working context from the conversation.

**2.** Light TODOS touch only:
   - New open items discovered this session → append to `TODOS.md` with tags from `~/.codex/AGENTS.md`. Update `Last updated:` date.
   - Completed items → **remove** them. Do not leave `[x]` lines.
   - Do **not** write a SESSION-LOG narrative block. That is `/checkpoint`'s job.

**3.** Refresh triage (only for logs under `~/dev/`):
   ```bash
   update-triage 2>/dev/null || echo "(update-triage failed — run manually)"
   ```

**4.** Build the **Resume Re-Entry Prompt**:

   ```
   ── Session resume ─────────────────────────────
   Working on: {project/focus of this session — one line}
   Left off: {last concrete action or current state — specific enough to orient a cold session}
   Open items this session: {new TODOs added, or "none — check ~/dev/.memory/TRIAGE-BLOCK.md"}

   At session start: read TODOS.md and KNOWLEDGE.md (local + global) — if either is git-crypt ciphertext, unlock first per `~/.codex/references/git-crypt-lock-check.md`. For what's next, read `~/dev/.memory/TRIAGE-BLOCK.md`.
   ──────────────────────────────────────────────
   ```

   - No "scope" or "suggested skills" — this is a resume, not a bounded tangent.
   - No "run /handoff-return" — there is no live main session.
   - "Left off" must be specific: last file edited, last decision made, last command run.

**5.** Save re-entry prompt to `/tmp`:
   ```bash
   CLOSE_FILE="/tmp/close-$(date +%Y-%m-%dT%H-%M).md"
   # write the prompt block to $CLOSE_FILE
   echo "Saved to $CLOSE_FILE"
   ```

**6.** Print re-entry prompt to terminal, then print closing message:
   ```
   ✓ Session closed — saved to /tmp/close-{timestamp}.md (no SESSION-LOG written — use /checkpoint when real decisions were made)
   → Open a new session and paste the Resume Re-Entry Prompt above to continue
   ```

**7.** Do not run `/clear` automatically.

---

## Related

- `/handoff` — push: fork a tangent off a still-alive main session
- `/handoff-return` — pop: merge a tangent's findings back into the main session
- `/checkpoint` — durable end-of-work-session close with full narrative + SESSION-LOG
