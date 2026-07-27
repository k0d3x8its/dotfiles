---
name: requirements
description: Formalize a resolved design into a numbered, testable FR/NFR spec at docs/REQUIREMENTS.md. Use after /grill-me resolves open questions, or standalone when a feature needs a formal requirements spec before architecture/planning. Hands off to /architecture.
---

# Requirements

**Trigger:** `/requirements [feature note]`
**Purpose:** Resolved design in, numbered testable FR/NFR spec out.

**Pipeline:** `/brainstorm` → `/grill-me` → `/requirements` → `/architecture` → `/write-plan` → build.

---

## Step 1 — Gather inputs

Read, don't ask, whatever these already answer:

- **`docs/brainstorm/*.md`** (newest file) — the WHAT.
- **`.work/FINDINGS.md`** — resolved decisions from `/grill-me`. These override the
  brainstorm doc where they conflict (they're newer). **Format detection:** check
  `~/.claude/references/planning-format-detect.md` (`test -d .work/plan`) first.
  FLAT-FORMAT (no `.work/plan/`): read `.work/FINDINGS.md` directly. NEW-FORMAT
  (`.work/plan/` exists): `.work/FINDINGS.md` is a lean index — read it, then open the
  specific `.work/findings/<cluster-slug>.md` detail file(s) relevant to this feature,
  not just the index line. Skipping the detail file re-asks what grill-me already
  resolved — the exact failure this step exists to prevent.
- **`docs/REQUIREMENTS.md`**, if it already exists — read every `FR-NN`/`NFR-NN` present
  to find the current max number. New requirements continue from next free — never
  restart at 1, never renumber or reuse a retired number.

Neither brainstorm nor grill-me ran? Fine — run cold, longer interview, build Overview /
Problem Statement / Users from scratch. Not a hard dependency on earlier stages.

## Step 2 — Encryption gate (before any write)

`docs/REQUIREMENTS.md` is written encrypted by convention. Before writing or appending:

1. Check the repo's `.gitattributes` for a `docs/REQUIREMENTS.md filter=git-crypt` (or
   equivalent wildcard) pattern.
2. **Present, matching pattern:** proceed to Step 3.
3. **Absent:** stop. Do not write a plaintext file the user will believe is encrypted.
   Recommend `/encrypt` first (it handles git-crypt init + `.gitattributes` + key
   storage), or, if the user explicitly wants this spec plaintext for this repo, confirm
   that out loud before writing — it's a deliberate exception, not a default.

## Step 3 — Interview, gaps only

Diff what Step 1 already answered against the template's sections. Ask about gaps only —
never re-ask something brainstorm or grill-me already resolved.

- One question at a time, recommended answer + one-line why first (matches
  brainstorm/grill-me style — never a flat Q&A dump).
- Every FR/NFR must be phrased **observably** — if it can't be phrased as a check someone
  could run or observe, it's not ready to number yet. Keep asking until it can.

## Step 4 — Write/append `docs/REQUIREMENTS.md`

Use `~/.claude/skills/requirements/templates/REQUIREMENTS.md`, substituting `{{DATE}}`.

- **Overview / Problem Statement / Users are PROJECT-scoped, not feature-scoped** — they
  describe the whole thing this repo builds, not whichever feature triggered this run.
  FR-NN/NFR-NN are the feature-scoped part. Writing an Overview that only describes the
  triggering feature bakes a wrong permanent header into an append-only file.
- **File doesn't exist:** write it fresh from the template. If the project itself has no
  single obvious identity yet (e.g. a tooling collection, not one product), say so in
  Overview rather than substituting the triggering feature's description.
- **File exists:** append new FRs/NFRs at next free number under the existing
  `<requirements>`/`<nfr>` blocks. Revise Overview/Problem Statement/Users **only if the
  project itself changed**, never to reflect the new feature. Update the `Last updated:`
  line. Never touch existing FR/NFR entries' numbers or text — a superseded requirement
  gets `[deprecated]` in its status field, the number itself is never reused.
- Every FR/NFR carries: number, `[active]`/`[deprecated]` status, the requirement text,
  and a `— verify:` clause (a command or a concretely observable check).
- `<requirements>`/`<nfr>` XML-style tags are load-bearing — `/architecture`'s
  Traceability section parses between them. Don't drop them.

## Step 5 — Hand off

> `docs/REQUIREMENTS.md` written: [N] new FR(s), [M] new NFR(s). Next: `/architecture` —
> it designs the system that satisfies this spec and traces every FR/NFR to a component.

Prose pointer, not an auto-invocation — `/architecture` may not exist yet in a repo mid
rollout of this pipeline.

---

## Boundaries

- **Does not design the system** — components, interfaces, data flow are `/architecture`'s
  job. This skill only formalizes WHAT must be true, never HOW.
- **Does not plan tasks** — Goal/Micro-Goal/Task breakdown is `/write-plan`'s job.
- **Never renumbers, never reuses a retired FR/NFR number** — downstream files
  (`docs/ARCHITECTURE.md` Traceability, `.work/PLAN.md` tasks) may cite a number directly;
  a renumber silently breaks every citation.
- **Never writes a plaintext `docs/REQUIREMENTS.md` by default** — see Step 2.
