---
name: brainstorm
description: Generative design dialogue — explore context, ask clarifying questions, propose 2-3 approaches with tradeoffs and a recommendation, write a design doc to docs/brainstorm/. Entry point of the brainstorm → grill-me → write-plan pipeline. Technical design for something you're about to build — not product ideation, not a requirements doc. Use when starting a feature from a rough idea, or when asked to design or think through an implementation. Hands off to /grill-me.
---

# Brainstorm

**Trigger:** `/brainstorm [topic]`
**Purpose:** Turn a rough idea into a design doc with weighed approaches. Generative only —
this skill proposes and explores. It never interrogates; stress-testing is `/grill-me`'s job.

**Pipeline:** `/brainstorm` → `/grill-me` → `/write-plan` → build.

---

## Phase 1 — Explore

Understand before asking. Read what exists in the target project:

- `.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `KNOWLEDGE.md` if present
- The code the idea touches — entry points, existing patterns, constraints
- Prior design docs in `docs/brainstorm/` on related topics

Do not ask the user anything Phase 1 can answer.

## Phase 2 — Clarify

Ask clarifying questions **one at a time**. Wait for each answer before the next.

- Every question leads with a recommended answer + one-line why, then alternatives.
- If the codebase can answer it, explore instead of asking.
- Stop when you can state the problem in one paragraph the user would sign off on.

## Phase 3 — Approaches

Propose **2-3 approaches**. For each: what it is, tradeoffs (cost, risk, blast radius,
maintenance). Then state **one recommendation + why first** — never a neutral list.

## Phase 4 — Write the design doc

Write `docs/brainstorm/<topic>-YYYY-MM-DD.md` **in the target project** (create the
directory if needed) from `~/.codex/skills/brainstorm/templates/design-doc.md`, substituting
the `{{TOKEN}}` placeholders. Unresolved threads go under **Open questions** — that
section is `/grill-me`'s input, so phrase each as a decidable question, not a vague worry.

## Phase 5 — Self-review

Reread the doc once. Check: unstated assumptions, missing constraints, an approach
dismissed without a reason, open questions that are actually answerable from code.
Revise once. Do not loop.

## Phase 6 — Hand off

> Design doc written to `docs/brainstorm/<file>`. Recommend `/grill-me` next — it walks
> the Open questions one branch at a time and writes resolved decisions to `.work/FINDINGS.md`.

---

## Boundaries

- **Does NOT interrogate** — resolving decisions one-by-one is `/grill-me`.
- **Does NOT plan** — Goal/Micro-Goal/Task breakdown is `/write-plan`.
- **Does NOT do product ideation** — that's the pm-discovery skills. This is technical
  design: how to build a thing, not whether the market wants it.
