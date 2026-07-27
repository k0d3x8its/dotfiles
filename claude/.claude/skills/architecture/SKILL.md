---
name: architecture
description: Design the system that satisfies docs/REQUIREMENTS.md — components, interfaces, data flow — as a living docs/ARCHITECTURE.md, edited in place with bidirectional FR/NFR traceability. Use after /requirements produces a spec, or standalone when a system needs a design doc before /write-plan. Hands off to /write-plan.
---

# Architecture

**Trigger:** `/architecture [feature note]`
**Purpose:** `docs/REQUIREMENTS.md` in, living `docs/ARCHITECTURE.md` out — every
`FR-NN`/`NFR-NN` traced to a component.

**Pipeline:** `/brainstorm` → `/grill-me` → `/requirements` → `/architecture` →
`/write-plan` → build.

---

## Step 1 — Gather inputs

Read, don't ask, whatever these already answer:

- **`docs/REQUIREMENTS.md`** — required. Not present? Stop: recommend `/requirements`
  first — designing a system with no spec to trace against defeats the point of this
  skill.
- **`docs/ARCHITECTURE.md`**, if it already exists — read it whole before touching
  anything. Unlike REQUIREMENTS.md this is a **living document, edited in place, not
  appended** (see Step 4). Note every existing Traceability row so revisions don't
  silently drop coverage.
- **`.work/FINDINGS.md`** — resolved decisions from `/grill-me` that bear on system
  design (not just requirements framing). **Format detection:** check
  `~/.claude/references/planning-format-detect.md` (`test -d .work/plan`) first.
  FLAT-FORMAT: read directly. NEW-FORMAT: read the index, then the specific
  `.work/findings/<cluster-slug>.md` detail file(s) relevant to this feature.

## Step 2 — Encryption gate (before any write)

`docs/ARCHITECTURE.md` is written encrypted by convention, same rule as
`docs/REQUIREMENTS.md`. Before writing or revising:

1. Check the repo's `.gitattributes` for a `docs/ARCHITECTURE.md filter=git-crypt`
   (or equivalent wildcard) pattern.
2. **Present, matching pattern:** proceed to Step 3.
3. **Absent:** stop. Do not write a plaintext file the user will believe is
   encrypted. Recommend `/encrypt` first, or, if the user explicitly wants this repo's
   spec plaintext, confirm that out loud before writing — a deliberate exception, not
   a default.

## Step 3 — Design, gaps only

Diff the requirements' FR/NFR set against what's already covered in an existing
Traceability table (if any). Design only what's new or changed — don't redesign
components that already satisfy an unchanged FR/NFR.

- **Hard gate — do not write a design decision into Components/Interfaces/Failure
  Behavior as settled unless it's forced.** For each design choice: either (a) cite the
  specific `FR-NN`/`NFR-NN` text or `.work/FINDINGS.md` line that forces it, or (b) ask
  the user, one question at a time, recommended approach + one-line why first (matches
  brainstorm/grill-me/requirements interview style). A choice that's neither forced nor
  asked goes in Open Technical Questions with a stated recommendation, not into the
  body as if decided — same gate `/requirements` Step 3 uses for Overview/Problem
  Statement/Users, applied here to design decisions.
- **Interfaces must cover external boundaries**, not just inter-component contracts —
  third-party APIs and services outside your control are where architecture actually
  rots. If a requirement touches one, name it here explicitly.
- Every new or touched component must be traceable to at least one `FR-NN`/`NFR-NN`.
  A component with no citation is scope creep the requirements never asked for — either
  find the FR/NFR it serves or cut it.

## Step 4 — Write/revise `docs/ARCHITECTURE.md`

Use `~/.claude/skills/architecture/templates/ARCHITECTURE.md`, substituting `{{DATE}}`.

- **File doesn't exist:** write it fresh from the template, covering every `FR-NN`/
  `NFR-NN` currently `[active]` in `docs/REQUIREMENTS.md`.
- **File exists — living doc, edited in place, NOT appended.** This is the opposite
  rule from `/requirements`' append-only ledger, and it's asymmetric on purpose:
  REQUIREMENTS.md numbers are permanent citations; ARCHITECTURE.md is one current
  system view. Appending a new Components entry while System Design's diagram still
  shows the old component count makes the doc self-contradictory — and it's
  `/write-plan`'s authoritative input. Revise System Design, Components, Interfaces,
  Data & State in place so the doc stays internally consistent as a snapshot of _now_.
- Update the `Last updated:` line on every write.
- **Traceability gate is bidirectional** — before finishing:
  1. Every `FR-NN`/`NFR-NN` `[active]` in `docs/REQUIREMENTS.md` appears as a row here.
  2. Every row here cites a real `FR-NN`/`NFR-NN` that exists in `docs/REQUIREMENTS.md`.
     One-way checking lets orphan components accumulate silently — check both directions
     every time, not just on first write.
  3. Every row cites an actual **component name**, never a document section (e.g.
     "System Design"). A constraint-type NFR that no single component owns still has an
     enforcer — usually the entrypoint that would have to accept the disallowed input
     for the constraint to break (e.g. a single-repo-scope NFR traces to the component
     whose argument parsing rejects a second repo, not to the diagram it's described in).
- Deployment section: omit for repo-local tooling; fill in once the project has a
  deploy target.
- Key Decisions: only where a real tradeoff was debated — omit rather than pad.

## Step 5 — Hand off

> `docs/ARCHITECTURE.md` [written|revised]: [N] component(s), [M] `FR`/`NFR` row(s)
> traced. Traceability gate: [pass|N orphan(s) — list]. Next: `/write-plan` — it slices
> this into Goal/Micro-Goal/Task, citing `FR-NN`/`NFR-NN` directly on the tasks that
> satisfy them.

Prose pointer, not an auto-invocation.

---

## Boundaries

- **Does not formalize requirements** — WHAT must be true is `/requirements`' job.
  This skill only designs HOW to satisfy an existing spec.
- **Does not plan tasks** — Goal/Micro-Goal/Task breakdown is `/write-plan`'s job.
- **Distinct from `docs/adr/`** — ADRs are one frozen decision + rejected alternatives,
  point-in-time. `docs/ARCHITECTURE.md` is the current whole-system design, updated as
  the system evolves. A tradeoff worth freezing permanently belongs in an ADR; the
  Key Decisions section here is a lighter pointer, not a replacement.
- **Never appends** — see Step 4. Appending here is the wrong-file failure mode;
  append-only behavior belongs to `docs/REQUIREMENTS.md` only.
- **Never writes a plaintext `docs/ARCHITECTURE.md` by default** — see Step 2.
- **Doesn't render a diagram export by default** — the System Design mermaid fence
  is the default; `/diagram` is reachable by hand for a polished swimlane/DFD export,
  not wired in automatically (a rendered artifact beside a living doc drifts).
