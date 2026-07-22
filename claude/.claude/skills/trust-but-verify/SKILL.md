---
name: trust-but-verify
description: Evidence gate for completion claims. Before saying done/works/fixed, before git push, a PR, or any handoff or session close — run the project's verify command FRESH, read the exit code, only then claim. Unproven claims become [VERIFY] TODOs. Maps to the [VERIFY] TODO tag.
---

# Trust But Verify

**Trigger:** `/trust-but-verify` — but mostly reflexive: the gate fires on its own at the
points below (encoded as a session rule in `~/.claude/CLAUDE.md`).
**Purpose:** A claim is permitted only by fresh evidence from this session. "Should work",
"tests passed earlier", and a green run from before the last edit are not evidence.

---

## Gate points

Run the verify command FRESH, read the exit code, **before**:

- Any **done / works / fixed / complete** claim — to the user or inside a TODO/plan update
- **`git push`**
- Opening a **PR**
- Any **subagent or user handoff** — including `/close`, `/checkpoint`, `/handoff`,
  `/handoff-return`

**NOT before commits.** Commits are cheap WIP checkpoints; gating them kills granularity.

## Procedure

1. **Resolve the verify command** via `~/.claude/skills/trust-but-verify/detect.md`.
   Resolve once per session per project and cache the result; re-resolve only if the
   command stops existing or build files changed.
2. **Run it fresh** — after the last edit, not from memory of an earlier run.
3. **Read the exit code.** Exit 0 → claim permitted; cite the evidence ("`bats tests/`
   exit 0, 82 tests"). Non-zero → no claim. Fix it, or write the TODO below.
4. **Per-task evidence:** if the task in `.work/PLAN.md` carries a `verify:` sub-bullet
   (see `/write-plan`), that command gates that task's checkbox — run it, not just the
   project-wide command.

## When the claim can't be proven

- **Verify command failed or wasn't run** → the claim becomes a TODO in `TODOS.md`:

  ```
  [VERIFY] <the claim> — <command> exited <code> (or: claimed without fresh run)
  ```

  `[VERIFY]` is always Critical — an unverified "done" is a lie with a delay.

  **Format detection:** check `~/.claude/references/planning-format-detect.md`
  (`test -d .work/plan`) first. FLAT-FORMAT (no `.work/plan/` — today's behavior,
  unchanged): append the `[VERIFY]` bullet above directly. NEW-FORMAT
  (`.work/plan/` exists): append an index line (`- [ ]` + `[VERIFY]` + title) to
  `TODOS.md`; spill to `.work/todos/<slug>.md` with a pointer only past ~150
  words.

- **Machine-unverifiable** (visual result, UX flow, external service) → do NOT mark done
  and do NOT loop on `[VERIFY]`. Write a `[UX]` checklist instead: steps + success
  criteria, hand off to the user.

## Routing

- Verify command fails because **tests are missing or broken** → `[TEST]`, close with `/tdd`.
- Verify command exposes a **real defect** → `[BUG]`, close with `/diagnose`.
- No verify command resolvable at all → say so explicitly, recommend adding one to the
  project's CLAUDE.md/KNOWLEDGE.md (detect.md priority 1), and treat all claims as
  unproven until then.
