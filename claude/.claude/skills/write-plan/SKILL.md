---
name: write-plan
description: Convert a grilled design doc plus .work/FINDINGS.md into .work/PLAN.md using the Goal / Micro-Goal / Task structure that /sync-trello and /dev-brief consume unchanged. Every Task carries a verify sub-bullet — the command that proves it. Use after /grill-me resolves a design, or when turning a design doc into an executable plan. Offers a /threat-model design review when the plan has a security surface, then /sync-trello at the end.
---

# Write Plan

**Trigger:** `/write-plan [design-doc path]`
**Purpose:** Design doc + resolved decisions in, executable `.work/PLAN.md` out.

**Pipeline:** `/brainstorm` → `/grill-me` → `/write-plan` → build.

---

## Step 1 — Gather inputs

- **Design doc:** the path argument, else the newest file in `docs/brainstorm/`. If
  neither exists, stop: recommend `/brainstorm` first — planning without a design doc
  skips the tradeoff work.
- **`.work/FINDINGS.md`:** read if present. Resolved decisions there override the design doc
  (they're newer).
- If the design doc still has unanswered **Open questions**, stop: recommend `/grill-me`
  first — every open question becomes a wrong guess baked into the plan.

## Step 2 — Emit .work/PLAN.md

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

If `.work/PLAN.md` already exists: append new Goals, never clobber existing Goals or
their `[trello:ID]` tags.

## Step 3 — Security gate (conditional offer)

The plan is the finished product before build starts — the last cheap moment to catch a
design-level security hole (an attacker roadmap costs nothing to fix on paper, a lot after
code exists). `/threat-model` is deliberate-trigger-only, so this is an **offer, never an
auto-run**, and only when the design has a security surface.

- **Fire the offer only if** the design doc or emitted plan implies either: an HTTP /
  network-reachable surface (server, API, endpoint, webhook, listener), OR handling of
  user / sensitive / regulated data (auth, PII, payments, credentials, tokens). A
  local-only CLI, a docs change, or a pure-logic library with none of these → **skip
  silently**, no prompt.
- **When it fires:**

  > This plan exposes a security surface ([one-line why — e.g. "adds an authenticated
  > HTTP endpoint touching user records"]). Recommend `/threat-model --design <design-doc>`
  > before building — plan-level STRIDE review while a fix is still just an edit. Skip if
  > the surface is already covered by an existing `docs/threat-model.md`.

- Never run `/threat-model` unprompted — surface the recommendation and let the user call it.

## Step 4 — Offer sync

> `.work/PLAN.md` written: [N] Goals, [M] Tasks. Recommend `/sync-trello` if this project
> tracks work on a board — it's idempotent and annotates Goals with card IDs. Skip it
> for small or local-only work; `/dev-brief` reads `.work/PLAN.md` either way.

Optional — never run `/sync-trello` unprompted.
