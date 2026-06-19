---
name: write-plan
description: Convert a grilled design doc plus findings.md into task_plan.md using the Goal / Micro-Goal / Task structure that /sync-trello and /dev-brief consume unchanged. Every Task carries a verify sub-bullet — the command that proves it. Use after /grill-me resolves a design, or when turning a design doc into an executable plan. Offers /sync-trello at the end.
---

# Write Plan

**Trigger:** `/write-plan [design-doc path]`
**Purpose:** Design doc + resolved decisions in, executable `task_plan.md` out.

**Pipeline:** `/brainstorm` → `/grill-me` → `/write-plan` → build.

---

## Step 1 — Gather inputs

- **Design doc:** the path argument, else the newest file in `docs/brainstorm/`. If
  neither exists, stop: recommend `/brainstorm` first — planning without a design doc
  skips the tradeoff work.
- **findings.md:** read if present. Resolved decisions there override the design doc
  (they're newer).
- If the design doc still has unanswered **Open questions**, stop: recommend `/grill-me`
  first — every open question becomes a wrong guess baked into the plan.

## Step 2 — Emit task_plan.md

Reuse the structure of `~/.claude/skills/dev-setup/templates/task_plan.md`, exactly the
hierarchy `/sync-trello` parses:

```markdown
## Goal: [Outcome-level chunk of work]

### Micro-Goal: [Milestone within the goal]
- [ ] Task — small, completable, verifiable
  - verify: `command that proves this task`
```

Rules:

- **Tasks MUST sit under a Micro-Goal** — orphan tasks are ignored by `/sync-trello`.
- **Every Task carries a `verify:` sub-bullet** — indented, no checkbox, so
  `/sync-trello` never sends it to Trello (it only parses `- [ ]`/`- [x]` lines) and
  `/trust-but-verify` reads it to close the task. No machine command possible →
  `- verify: manual — [UX] checklist`.
- Goals map to outcomes, Micro-Goals to milestones, Tasks to single sittings.

If `task_plan.md` already exists: append new Goals, never clobber existing Goals or
their `[trello:ID]` tags.

## Step 3 — Offer sync

> task_plan.md written: [N] Goals, [M] Tasks. Recommend `/sync-trello` if this project
> tracks work on a board — it's idempotent and annotates Goals with card IDs. Skip it
> for small or local-only work; `/dev-brief` reads task_plan.md either way.

Optional — never run `/sync-trello` unprompted.
