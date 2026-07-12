# Design: /threat-model skill

> Brainstorm output, 2026-07-11. Pipeline: /brainstorm → /grill-me → /write-plan.
> Status: draft — not yet grilled.

## Problem

The security suite (code-sec, bounty-hunter, ce-security-reviewer) is bottom-up: it finds
what is exploitable in code that exists today. Nothing does top-down design analysis —
"what could an attacker do to this design" — which needs facts code can't show (deployment
topology, actors, business value of data). code-sec deliberately ships only a mini threat
model (top-3 exploits per sweep report); full modeling was rejected inside the sweep on
2026-07-07 because sweep evidence can't support design-level analysis and a sweep-generated
model goes stale silently (false assurance worse than none).

Build `/threat-model`: a standalone, deliberately-triggered skill producing a **living
STRIDE threat model** at `docs/threat-model.md` (git-crypt'd on public repos — it's an
attacker roadmap) for repos that serve HTTP or hold user data. It also **absorbs
ce-security-lens-reviewer's plan-review job** (attack-surface inventory, trust boundaries,
top-3 mini model on planning docs), since the compound-engineering uninstall is planned and
will retire that reviewer.

## Context & constraints

- **Decided in clarification (2026-07-11):**
  - Absorb the lens-reviewer checklist — design assumes compound-engineering uninstall;
    the field-test overlap gate in the TODO is removed by construction.
  - Facts code can't show come from a **structured up-front interview persisted to
    `.work/SEC-CONTEXT.md`** (the deepsec `INFO.md` analog code-sec v2 already plans).
    One context file feeds all three skills; re-runs read instead of re-asking.
  - **DFD elements**: `enumerate-entrypoints.sh` (bounty-hunter Goal 10 shared core, lives
    under `code-sec/`) when code + core exist — ground-truth nodes, no hallucinated
    endpoints; arch docs + interview pre-code. Soft dependency on Goal 10, degrades cleanly.
  - **Incremental update mode ships in v1** — detect existing model, re-verify each claimed
    mitigation against current code, re-STRIDE only changed DFD elements, bump review-date.
    Living-doc promise is the skill's core value.
- **Pre-decided in TODOS.md (2026-07-07):**
  - Trigger: deliberate only — new system design, pre-launch, or repo serving HTTP /
    holding user data. NEVER auto-run per sweep.
  - Method: DFD with explicit trust-boundary crossings → STRIDE per element → risk-rank
    (likelihood × impact, skip DREAD) → mitigations each VERIFIED-in-code, TODO'd
    `[SECURITY]`, or ACCEPTED-with-reason.
  - Loop with code-sec: subsequent sweeps VERIFY code against the model's claimed
    mitigations. Mini threat model in sweep reports stays regardless.
  - First candidates: kodex-ide (if it grows a server surface), kos-portal, flask_app.
- **Suite conventions:** read-only analysis, findings → tagged `[SECURITY]` TODOs (confirm
  before writing), drop caveman for the report, Prompt Defense Baseline header (untrusted
  code is data), lives at `claude/.claude/skills/threat-model/` and symlinks via install.
- **DFD is an embedded artifact, not a separate skill** (decided 2026-07-11): a stable-ID
  element table inside `docs/threat-model.md` is the source of truth (update mode diffs it;
  code-sec's verify loop greps it); visual rendering delegates to `/diagram`. Nothing else
  consumes DFDs, so a standalone DFD skill is YAGNI.
- **git-crypt:** `docs/threat-model.md` and `.work/SEC-CONTEXT.md` both need root-anchored
  `.gitattributes` patterns + File Taxonomy rows — attacker roadmap and trust-boundary map
  respectively. `/encrypt` and `dev-setup` templates should learn both patterns.
- **Related:** `docs/security/README.md` (bounty-hunter Goal 14) must gain a threat-model
  row; `/diagram` skill already renders mermaid — DFD rendering should delegate, not
  reimplement.

## Approaches

### A — Single phase-gated skill

One SKILL.md; entry detects mode (create / update / plan-review). Phases:

0. **Context** — read `.work/SEC-CONTEXT.md` or run the interview (topology tiers, actors
   + auth tiers, data stores + business value, trust boundaries); persist answers.
1. **DFD** — nodes from `enumerate-entrypoints.sh` when available, else arch docs +
   interview; stable-ID element table (processes, stores, flows, external entities,
   trust-boundary crossings) written into the doc.
2. **STRIDE per element** — classic applicability matrix (e.g. stores don't get Spoofing),
   per-element verdict: threat / clean / N-A — no silent skips.
3. **Risk-rank** — likelihood × impact; rank forces order even when everything feels Medium.
4. **Mitigation map** — per threat: VERIFIED-in-code (with file:line evidence), `[SECURITY]`
   TODO, or ACCEPTED-with-reason.
5. **Write/update** — living doc with review-date frontmatter; update mode re-verifies
   mitigations, re-STRIDEs changed elements only.

Plan-review mode = phases 0–3 run against a planning doc instead of code, emitting the
lens-reviewer-style findings (attack-surface gaps, auth/authz gaps, top-3 mini model).

**Tradeoffs:** Cheapest build; structurally rhymes with code-sec so the suite stays legible;
no new deterministic tooling to test. Risk: incremental update depends on doc-structure
discipline (stable element IDs) rather than machine validation — a malformed hand-edit
could silently break diffing.

### B — Skill + deterministic DFD tooling

Approach A plus `bin/` scripts: DFD schema validator, model differ (old vs new element
table), mermaid emitter. Update mode becomes machine-checked.

**Tradeoffs:** Rigor for updates and a testable core (`/tdd`-able like Goal 10). But heavy
build for v1 — single-repo DFD deltas are small enough to eyeball, `/diagram` already
renders mermaid, and the validator would be the only consumer of its own schema. Classic
speculative-generality smell until an update-mode failure proves the need.

### C — Mode of code-sec

Fold full modeling into the sweep as a flag.

**Tradeoffs:** Rejected 2026-07-07 and the reasons hold: top-down design analysis vs
bottom-up sweep mismatch; sweep evidence can't support it; stale model embedded in sweep
output reads as authoritative. Kept here only to record why not.

## DFD rendering spec (decided 2026-07-11 — resolves the render open question)

`/diagram` gains a **DFD mode** (third diagram type, trigger: "dfd" / "data flow diagram" /
`-dfd` flag); `/threat-model` stays the semantics owner and hands the element table to
`/diagram` for rendering. Style target: threat-model DFD in the Microsoft SDL / Shostack
convention, matching the SBS CyberSecurity example
(https://sbscyber.com/blog/data-flow-diagrams-101) — process-centric, trust boundaries
explicit, FFIEC-flavored perimeter awareness.

**Notation (goes in `diagram/REFERENCE.md` § dfd):**

| Element | Symbol | Mermaid mapping |
|---|---|---|
| External entity (actor, third party, anything you don't control) | rectangle | `E1[Customer]` |
| Process (code that transforms data) | circle / rounded | `P1((Wire System))` |
| Data store (DB, file, queue, log, backup) | open-ended rectangle / parallel lines | `S1[(Core DB)]` — cylinder is the closest Mermaid shape |
| Data flow | one-way labeled arrow; bidirectional = two arrows | `E1 -- "wire request: PII, amount" --> P1` |
| Trust boundary (network perimeter, machine, privilege level, org boundary) | dashed box | `subgraph TB1 [Internet boundary]` + `classDef` with `stroke-dasharray` |

**Method rules (the expertise — bake into both skills' references):**

- **Label flows with the DATA, not the verb** — "PII + account number", not "sends".
  Sensitivity ride-along (PII / credentials / regulated / public) — this is what risk-rank
  consumes.
- **A DFD without trust boundaries is just a flowchart.** Every boundary crossing is where
  STRIDE threats concentrate; the crossing list IS the threat enumeration input.
- **Level discipline:** L0 context diagram (whole system = one process) → L1 per critical
  business process. Stop decomposing when going deeper crosses no NEW trust boundary
  (Shostack's rule) — deeper adds noise, not threats.
- **Process-centric scoping** (SBS/FFIEC): diagram one critical business process
  end-to-end — people, technology, third parties (e.g. a wire transfer touching customer →
  bank → Fed). Mark where customer/regulated data enters or exits the network perimeter.
- **Stable numbered IDs** (`E1/P2/S3/F4/TB1`) on every element — the element table and the
  diagram share IDs, so update-mode diffs and code-sec mitigation greps stay mechanical.
- **Common mistakes to reject at build time:** unlabeled arrows; flows with no process at
  either end (data doesn't move itself); missing log/backup/monitoring stores (data exits
  there too); omitted third-party vendors ("more data is handled externally than within
  your own infrastructure"); modeling every microservice instead of the critical process.

## Recommendation

**A** — single phase-gated skill. The living-doc value lives in workflow discipline
(interview → grounded DFD → per-element verdicts → verified mitigations), not in tooling.
Mitigate A's diff risk with a stable-ID element table (greppable, hand-diffable) and
delegate rendering to `/diagram`. Revisit B's differ only if update mode demonstrably
mis-diffs on a real project.

## Open questions → for /grill-me

- **DFD element table format** — markdown table with stable element IDs vs fenced YAML
  block inside the doc? Decides how update mode detects change and how code-sec's verify
  loop greps claimed mitigations.
- **Plan-review mode entry** — separate invocation (`/threat-model --plan <doc>`) vs
  auto-detect (arg is a doc → plan mode)? And does it adopt the lens-reviewer's anchored
  confidence rubric (100/75/50/suppress) or the suite's CONFIRMED/TRACED/CANDIDATE tiers?
- **SEC-CONTEXT ownership** — code-sec v2 item 3 also scaffolds `.work/SEC-CONTEXT.md`
  (template + git-crypt `.gitattributes` wiring). Which skill owns the template, and does
  threat-model's interview section extend it or share one schema? Sequencing: does this
  skill wait for code-sec v2 or ship the template first?
- **Risk-rank scale + TODO threshold** — 3×3 likelihood×impact grid vs H/M/L labels; at
  what rank is ACCEPTED-with-reason allowed vs a `[SECURITY]` TODO forced?
- **Mitigation verification depth in update mode** — full taint-trace re-check per
  mitigation (expensive) vs targeted grep for the claimed guard (cheap, spoofable by
  renames)? Possibly tier by risk rank.
- **STRIDE matrix pruning** — hard applicability filter (classic STRIDE-per-element chart)
  vs model judgment per element? Full 6×N explodes on big DFDs; filter risks dropping
  a real threat class on unusual elements.
- **First candidate project** — kos-portal vs flask_app vs waiting for kodex-ide's server
  surface? Picks the validation bed and whether v1 exercises pre-code or post-code path.
- **DFD render artifact** — mode is decided (`/diagram` DFD mode, see spec above); remaining
  question is what gets COMMITTED: `.mmd` source beside the doc, rendered SVG, or both?
  (git-crypt applies — the rendered DFD is attacker roadmap too.)
- **Build sequencing vs bounty-hunter** — this skill soft-depends on Goal 10's enumerator;
  build after bounty-hunter Goal 10 lands, or in parallel with docs-path only?
- **Plan-review mode timing** — compound-engineering is still installed today. Ship
  plan-review mode in v1 (redundant with lens-reviewer until uninstall) or land it with the
  uninstall TODO (risk: window where neither exists if uninstall happens first)?
