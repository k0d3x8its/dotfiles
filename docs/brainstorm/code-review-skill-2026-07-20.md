# Design: owned `/code-review` skill (replaces compound-engineering's ce-code-review roster)

> Brainstorm output, 2026-07-20. Pipeline: /brainstorm → /grill-me → /write-plan.
> Status: draft — not yet grilled.

## Problem

`compound-engineering` (the ce-* plugin) is scheduled for uninstall (TODOS.md line 35,
decision already made). Its code-review system — the `ce-code-review` orchestrator
plus ~22 persona agents — is the single most-used piece of that plugin and has no local
replacement. Build one owned `/code-review` skill that matches or beats it, before the
plugin comes out, so review capability doesn't regress. Closes TODOS.md line 70 (ce-*
reviewer-persona slice of the full roster triage). Line 37
(build-your-own-adversarial-reviewer) is NOT automatically closed by this design —
Gate 3 caught that the persona roster below has no adversarial member, and line 37's
actual ask ("wire it into the fable-mode attack gate AT LEAST") targets a broader
break-it reviewer than just one `/code-review` persona. See the top open question.

Two prior-art sources exist and were fully read this session (not from memory —
verbatim quotes and file paths below): the ce-code-review orchestrator + its full
persona roster, and Matt Pocock's `code-review` skill (`mattpocock/skills`), which the
user explicitly asked to be folded into the comparison rather than only cannibalized
for the two ideas (Fowler baseline, two-axis principle) already extracted into
`CODE-PRINCIPLES.md` this session.

## Context & constraints

- Already shipped locally, build on these, don't duplicate: `CODE-PRINCIPLES.md`
  (Fowler-smell vocabulary + the Standards-vs-Spec two-axis principle just added),
  `CODE-STANDARD.md` (mechanical per-language rules), `codebase-design` skill
  (module/interface/depth vocabulary for architecture-flavored findings), `code-sec`
  skill (security sweep — NOT the same as a diff-review security persona, but shares
  ground), `threat-model` skill (already absorbed `ce-security-lens-reviewer`).
- Skills in this environment live at `claude/.claude/skills/<name>/`, symlinked to
  `~/.claude/skills/` via `bash install.sh` — same convention `threat-model` and
  `codebase-design` used.
- CLAUDE.md's global config lists `/ce-code-review` under "External (not
  auto-surfaced)" — once this ships, that line moves to the main skills list as
  `/code-review`.
- Agent tool supports a `model` override (`sonnet`/`opus`/`haiku`/`fable`) per spawn —
  the local mechanism to replicate ce's cost-control lever (3 high-stakes personas on
  parent tier, rest forced mid-tier).

### Prior-art summary (full detail in `.work/GATES.md` G2 log + this session's subagent report, condensed here)

**ce-code-review orchestrator.** Parallel dispatch of selected personas (LLM reasons
over the diff to pick conditional ones, not keyword-matched). Fingerprint-based dedup
(`file + line±3 + normalized title`); cross-reviewer agreement on the same fingerprint
promotes confidence one step. **Anchor (confidence) and severity (impact) are
independent axes** — a 5-value behaviorally-anchored enum (0/25/50/75/100, each tied to
a concrete self-test, not a felt score) gates whether a finding surfaces at all;
severity orders it once it does. Confidence gate runs LATE, after promotion, so
borderline findings get a fair shot. Output is severity-grouped markdown tables with a
`Route` column and closing verdict.

Roster reality check: only ~13 of the ~22 agent files are actually wired into
`ce-code-review`'s dispatch table. The other 6 (`ce-security-sentinel`,
`ce-performance-oracle`, `ce-data-integrity-guardian`, `ce-architecture-strategist`,
`ce-code-simplicity-reviewer`, `ce-pattern-recognition-specialist`) are free-floating
generic-checklist duplicates from an earlier plugin generation, referenced only by
other ce-* meta-commands, never deleted. Treat these as "how not to do it" — skip
outright, don't port.

**Pocock rival.** Radically smaller: one skill file, exactly two `general-purpose`
sub-agents (Standards, Spec), a fixed 12-item Fowler baseline pasted into the prompt,
zero dedup/gating machinery ("do not merge or rerank findings" is explicit). Its
distinctive contribution — the two-axis split — is a REPORTING discipline, not an
architecture: nothing in ce's system currently checks "did this diff do what the task
actually asked" at all. Every ce persona checks code quality (Standards); none check
Spec compliance. That's a real capability gap in ce's design, not just a reporting gap.

**Known weakness to design around:** the promotion rule (2+ reviewers agree → anchor
50→75) has no signal distinguishing independently-reasoned agreement from two reviewers
sharing the same blind spot (e.g., both miss a guard clause defined outside the diff).
Files don't document a fix; this stays an open question below.

## Approaches

### A — Full port: replicate ce's architecture near-verbatim

Keep all ~13 wired personas, the JSON-schema'd finding format, fingerprint dedup, the
5-value anchor enum, and the interactive per-finding triage UX (apply/defer/skip,
ticket-filing fallback, bulk-preview).

**Tradeoffs:** Highest capability parity with the incumbent (zero regression risk).
But the interactive triage UX is a large fraction of the source file (Stages 5b,
`walkthrough.md`, `tracker-defer.md`, `bulk-preview.md`) built for a team/ticket-tracker
context this solo dotfiles environment doesn't have — `/review-response` and the
`[VERIFY]`/`[CHORE]` TODO-tag system already cover "what happens after a finding lands"
locally. Porting it verbatim duplicates existing machinery and is the highest build
cost of the three approaches.

### B — Pocock-style minimal: two-agent Standards/Spec split

One skill file, two sub-agents (Standards checks Fowler smells + CODE-STANDARD.md +
CODE-PRINCIPLES.md; Spec checks the diff against the task/plan/ticket). No dedup, no
anchor gating, flat prose output grouped by axis.

**Tradeoffs:** Fast to build, trivial to maintain solo, directly reuses the two-axis
principle already shipped. But it throws away the single most-praised mechanism from
the research (anchor/severity independent-axis confidence gating) and loses every
persona's specialized territory (security exploit-tracing, migration schema-drift,
frontend race conditions, Swift concurrency) — those aren't generic Fowler-smell
catches, a generalist Standards agent will miss them.

### C — Hybrid: trimmed persona roster + anchor/severity gate + Spec as a persona (recommended)

Port the anchor/severity independent-axis gating mechanism and fingerprint dedup
(the standout piece), but trim the roster to the personas with genuinely distinct
territory: the 4 always-on ce personas (correctness, maintainability, testing,
project-standards) plus a NEW always-on **spec-compliance persona** (Pocock's missing
piece — checks the diff against the task description / `.work/PLAN.md` entry / ticket,
using the exact two-axis wording already in `CODE-PRINCIPLES.md`), plus the conditional
personas with real distinct territory (security, performance, reliability,
api-contract, data-migration, frontend-races if this environment ever touches
Stimulus/Turbo, swift-ios if it ever touches Swift — both currently speculative for
this stack, see open questions). Drop the 6 confirmed-dead duplicates outright. Use
the `Agent` tool's `model` param to replicate the cost-tier split (correctness/
security/spec-compliance on parent tier, everything else mid-tier). Final report groups
findings by the Standards-vs-Spec axis (Pocock) AND by severity within each axis (ce).
**Unresolved (flagged at Gate 3, not settled by this doc):** ce partitions personas by
_territory_ (correctness, security, performance...); Pocock partitions findings by
_contract type_ (Standards, Spec). A correctness bug (null deref) or a security bug
(SQLi) is neither a Fowler-Standards quality issue nor a Spec mismatch — it's a bug. How
the axis grouping and the territory-based roster overlay is NOT shown to compose cleanly
here; it's the top open question below, not an assumed-solved design detail. Whether an
adversarial/break-it persona belongs in this roster at all, vs. staying a standalone
fable-mode Gate 3 attacker (or both), is also unresolved — see open questions.

**Tradeoffs:** Captures the best-praised mechanism from both sources without porting
either source's dead weight (ce's unused duplicates, ce's team-oriented triage UX,
Pocock's total lack of confidence gating). Requires deciding the promotion-rule
weakness (open question below) rather than inheriting ce's unexamined answer.
Moderate build cost — more than B, meaningfully less than A.

## Recommendation

**C — Hybrid**, confirmed by user before this doc was written. Rationale: it is the
only option that doesn't throw away a mechanism the research flagged as genuinely
best-in-class (anchor/severity independent axes) while also closing the one real
capability gap the research surfaced (no persona checks Spec compliance at all today).
A and B each optimize one axis of the tradeoff and lose the other.

## Open questions → for /grill-me

Ordered by how load-bearing each is to the Recommendation above — the first two can
invalidate the choice of Hybrid itself if resolved the "wrong" way; the rest are
implementation detail within Hybrid.

- **[LOAD-BEARING] Dispatch ↔ promotion-rule coupling.** The cross-reviewer promotion
  (anchor 50→75 on 2-reviewer agreement) is the _main reason Hybrid beats Approach B_ —
  it's the mechanism the recommendation leans on. It only means anything with genuinely
  independent parallel subagents. If cost/complexity pushes dispatch to a single
  sequential prompt instead (cheaper, no subagent overhead), "agreement" between
  personas sharing one context isn't independent at all, and Hybrid quietly collapses
  toward "Approach B plus a checklist" — the headline justification evaporates. Decide
  dispatch mechanism and the promotion rule TOGETHER, not as two separate questions.
- **[LOAD-BEARING] Adversarial-reviewer placement (TODOS line 37).** Gate 3 caught: the
  persona roster below has no adversarial/break-it member, so this design does NOT
  close line 37 as originally claimed. Line 37's actual ask is "wire it into the
  fable-mode attack gate AT LEAST (possibly wider break-it review)" — broader than one
  `/code-review` persona. Three shapes to pick from: (a) standalone agent, called only
  by fable-mode Gate 3, out of scope for this doc entirely; (b) one more persona in
  this roster (conditional, high-risk diffs); (c) both — a shared adversarial-attack
  core with two thin call sites. Resolve before `/write-plan`, not after.
- **Axis-vs-territory composition.** The doc asserts Standards-vs-Spec (axis) and
  severity (ce) are "complementary, not competing," but only spec-compliance feeds the
  Spec bucket — the other ~9 personas all feed Standards, INCLUDING correctness and
  security findings that are neither a Fowler-Standards quality issue nor a Spec
  mismatch (they're bugs). Show how a null-deref or a SQLi finding routes through the
  axis grouping before building the report-format code, or drop the axis-grouping claim
  down to "Spec is its own top-level section, everything else stays severity-grouped
  like ce today" (simpler, doesn't force a category that doesn't fit).
- **KISS gate on the ported machinery itself.** Every question below this one is about
  _how_ to implement the anchor/severity/promotion system; none ask _whether_ a 5-value
  behaviorally-anchored confidence enum + late-gating + cross-reviewer promotion earns
  its complexity for a SOLO user reviewing their own diffs — this is noise-reduction
  machinery built for team/multi-reviewer volume. CODE-PRINCIPLES.md's own KISS section
  says "the primary failure mode of coding agents is over-engineering." Let grill-me
  weigh, per mechanism, whether a simpler binary confidence flag (verified / unverified)
  gets 80% of the benefit at a fraction of the build+maintenance cost.
- **Security-persona territory vs. existing security tooling — RESOLVED, shipped.**
  `code-crit/personas/SECURITY.md` (§ Territory) draws the boundary explicitly:
  diff-local exploit/regression only, not "is this repo secure" (`/code-sec`), not
  reachability (`/bounty-hunter`), not design-level STRIDE (`/threat-model`) — those
  three routed to as follow-ups, not substitutes. All 12 `code-crit/personas/*.md`
  ship a `## Territory` section on the same pattern.
- Persona set: confirm final list. Always-on = correctness, maintainability, testing,
  project-standards, spec-compliance (5, pending the adversarial-placement and
  security-territory questions above). Conditional = security (pending territory
  question), performance, reliability, api-contract, data-migration (5, all have clear
  local drivers). Drop entirely for now (no local driver, confirmed by grep across all
  of `~/dev`, zero Swift/Stimulus files): frontend-races, swift-ios. Also drop or fold:
  deployment-verification-agent (migration-gated, maybe fold into data-migration
  instead of separate persona), previous-comments-reviewer (PR-comment-thread checking
  — only meaningful with a live PR, may belong in `/review-response` instead of
  `/code-review`). Confirm each. **Also confirm:** ce's other two always-on personas
  (`ce-agent-native-reviewer`, `ce-learnings-researcher`) are dropped from this roster
  with no rationale stated yet — agent-native's action-parity check is plausibly
  relevant here specifically, since this whole repo is agent tooling. Intentional drop
  or oversight?
- Output format: keep ce's severity-grouped pipe-table format (machine-parseable,
  matches `ReportFindings`-style structured output already used elsewhere in this
  harness) vs Pocock's freeform prose-per-axis (more readable, less structured)?
- Fingerprint dedup: port ce's exact `file + line±3 + normalized-title` fingerprint, or
  simplify given the smaller persona count (less finding-volume, less need for
  aggressive dedup)?
- Model-tier assignment: which personas inherit parent-session model vs get forced to
  a cheaper tier? Draft: correctness + security + spec-compliance on parent tier
  (highest-stakes per ce's own reasoning); maintainability + testing + standards +
  performance + reliability + api-contract + data-migration on a fixed cheaper tier.
  Confirm the specific model names to hardcode (or leave inheriting parent tier
  entirely, skipping this cost lever for v1 — simpler, revisit if cost becomes real).
- Naming/location: `claude/.claude/skills/code-review/`, command `/code-review` — any
  conflict with `ce-code-review`'s alias while both are still installed during the
  transition period? (They coexist until the plugin uninstall step, line 35.)
- Scope for v1: build the full persona set in one `/write-plan` pass, or ship the
  4 always-on + spec-compliance first (v1, closes the core capability), conditional
  personas as a fast-follow (v1.1)?
