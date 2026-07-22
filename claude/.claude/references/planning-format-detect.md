# Planning-file format detection

Before a skill reads or writes `TODOS.md`, `.work/PLAN.md`, or `.work/FINDINGS.md`,
determine which format the current repo uses. Two formats coexist across `~/dev`
during the index+detail pilot (dotfiles-only as of 2026-07-22 — see
`docs/brainstorm/planning-file-hierarchy-2026-07-21.md` and dotfiles `.work/PLAN.md`
Goal 29 / `.work/archive/legacy-plan.md` Goal 29 for the design).

## Detect

```bash
test -d .work/plan && echo NEW-FORMAT || echo FLAT-FORMAT
```

`.work/plan/` existing is the sole marker. Its presence means `TODOS.md`,
`.work/PLAN.md`, `.work/FINDINGS.md` are lean indexes (checkbox/status + title +
pointer) with real content living in `.work/plan/`, `.work/findings/`, `.work/todos/`
detail files. Its absence means those three files hold full content directly, as
they always have.

## On NEW-FORMAT

- `TODOS.md` line: `[ ]`/`[x]` + tags + title + pointer to `.work/todos/<slug>.md`
  (spill to a detail file only past ~150 words per item; shorter items stay inline).
- `.work/PLAN.md` line: status (`open`/`in-progress`/`done`) + Goal number/title +
  Epoch tag (if assigned) + pointer to `.work/plan/<goal-slug>.md` (flat) or
  `.work/plan/<epoch-slug>/<goal-slug>.md` (nested, Epoch'd Goals only).
- `.work/FINDINGS.md` line: status + decision-cluster title + pointer to
  `.work/findings/<cluster-slug>.md`.
- Detail filenames are `<id>-<topic-slug>.md` (ID-first, both ID and topic in the name).
- Read the index first; open a detail file only when its content is actually needed
  (a TODO's full body, a Goal's Micro-Goals/Tasks, a decision cluster's rationale).

## On FLAT-FORMAT

Behave exactly as before this pilot: read/write `TODOS.md`, `.work/PLAN.md`,
`.work/FINDINGS.md` directly, full content inline, no detail-file indirection.

## Why a shared helper, not per-skill logic

Every skill that touches these three files (write-plan, grill-me, sync-trello, the
four closing skills, dev-brief, fable-mode, brainstorm, and TODOS.md-appenders like
diagnose/consolidate/remember/code-sec/etc.) needs the identical branch. Duplicating
the test-and-branch in each SKILL.md risks drift — one skill's detection logic
diverging from another's. This file is the single source; skills reference it by
name rather than re-deriving the check.
