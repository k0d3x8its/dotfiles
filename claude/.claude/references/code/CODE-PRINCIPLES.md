# CODE-PRINCIPLES

Language-agnostic principles this environment has committed to. Read at review
(`/code-crit`), not per-line writing — `CODE-STANDARD.md:112` and global `CLAUDE.md`
scope the write path to `CODE-STANDARD.md` + one language file only. This file selects
and locally interprets principles — it does not teach
them (they're in your priors). Per-language mechanics live in `CODE-STANDARD.md` and the
files it delegates to.

## Precedence (collision heuristics — not a ranked lattice)

These resolve _principle_ collisions; they are not themselves totally ordered. When
two of them conflict, **Surgical Scope is the outer gate**: no other rule may push an
edit outside the current diff — file it as `[CHORE]` instead. (Example: your diff adds
the _third_ occurrence of a look-alike but the first two live in untouched files —
rule of three does NOT license editing them; extract in-scope or file the `[CHORE]`.
Forcing the cross-file edit is shotgun surgery, the smell below.)

1. **Working beats elegant.** A verified, passing change outranks any cleanup. Never
   trade green tests for structure. Verify before claiming (see `/trust-but-verify`).
2. **KISS/YAGNI beat DRY — for look-alike code only.** Repeated _actions_ and repeated
   _knowledge_ always get extracted (that's what functions are for). But merging code
   that merely _looks similar_ waits for the _rule of three_: the third occurrence
   proves the pattern and reveals the abstraction's true shape. A wrong abstraction is
   costlier than duplication — especially for agents, which extend bad patterns
   confidently.
   - **Test for which bucket you're in:** could both call sites cite the _same name_
     for what they're doing, independent of the code — "compute a percentile,"
     "resolve a rename chain," "parse this header" — a name a domain expert would
     recognize without reading either implementation? That's _knowledge_: extract
     now, no wait, even at occurrence two. If the honest description is instead
     "these two blocks happen to do a similar-shaped thing" — same control flow,
     different domain purpose, or same shape today but no reason to expect they'd
     change together — that's a _look-alike_: hold for the third occurrence.
   - This is a judgment call, not a mechanical count — don't reach for whichever
     bucket happens to justify the extraction (or the duplication) you already
     wanted. If the honest test above is genuinely ambiguous, that ambiguity
     itself is the signal to wait for a third occurrence, not a coin flip.
3. **Surgical scope beats Boy Scout (outer gate).** Clean only what the current change
   already touches. Cleanups outside the diff become `[CHORE]` TODOs, not drive-by
   edits — this gate overrides the other three when they would reach outside the diff.
4. **Explicit beats implicit.** When simplicity and cleverness conflict, write the
   boring version a stranger can read without context.

## Committed principles

### TDD — main methodology

- Loop is **red-green**, one vertical slice at a time. Red before green, always.
- Refactoring is **not** part of the loop — it happens at the review stage
  (see Smells below). Do not overload implementation with restructuring.
- Workflow, tooling, and test-quality bars live in the `/tdd` skill — invoke it;
  do not restate its steps here or elsewhere.

### KISS — Keep It Simple

- The primary failure mode of coding agents is over-engineering. Default to the
  simplest design that passes the tests.
- No configuration options, parameters, or indirection that the current task
  does not exercise.

### YAGNI — You Aren't Gonna Need It

- Build for the requirement in front of you, not the one you can imagine.
- Speculative extension points are a smell (see _speculative generality_).
  Extensibility is earned by a second concrete consumer, not predicted.

### DRY — with the rule of three

- Repeated actions become a function immediately — code exists to prevent repeat actions.
- Knowledge (business rules, constants, formats) must have one authoritative home.
- Code _shape_ similarity alone is neither of the above. Extract look-alike code on the
  third occurrence, when the abstraction's real boundaries are visible.
- When an existing abstraction fights a new case, prefer inlining it back over
  adding flags to it.

### Boy Scout Rule — scoped

- Leave every file you _touch_ cleaner than you found it: better name, dead code
  removed, comment corrected — within the lines your change already visits.
- Anything wider than the current diff: record as `[CHORE]`, move on.

### SRP — Single Responsibility (module-level)

- Applies to modules/files/functions, not just classes: one reason to change each.
- Test: describe the module in one sentence without "and". If you can't, split it.

### SoC — Separation of Concerns (layer-level, cuts across modules)

- Distinct from SRP: SRP asks "does this one module have one reason to change";
  SoC asks whether _unrelated kinds of concern_ — IO/persistence, presentation,
  validation, policy-vs-mechanism — are sharing a layer at all, even inside a
  module small enough to still pass the SRP test.
- Config vs code is the recurring local instance: a global fallback config
  (env-wide default, e.g. `~/dev/eslint.config.js`) and a project's own config
  (project-specific policy) are different concerns and MUST NOT be collapsed
  into one file just because both are "eslint config" — see `TYPESCRIPT.md`.
- Policy (what rule applies) SHOULD be separable from mechanism (how the rule
  is enforced/executed) — the same discriminating question as the eslint case,
  generalized: can the _what_ change without touching the _how_, and vice versa?
- Not a license to split prematurely — a two-line script mixing IO and logic
  is not a violation until a second concern actually shows up (YAGNI still
  gates this, same as DRY's rule of three).

### DIP — Dependency Inversion (seams)

- Depend on seams, not concretions: pass collaborators in (the `wire{}` DI pattern
  in kodex-ide is the local idiom) rather than reaching out to globals or requiring
  deep into another module's internals.
- A seam exists so tests can substitute it. If a module can't be tested without the
  real world attached, it's missing a seam.
- Three seam types (Feathers): **Object seam** — inject a dependency as a parameter.
  **Link seam** — swap a module at load time via env or conditional import.
  **Preprocessing seam** — config/env changes behavior before code runs.

### Error handling — judgment layer

- Mechanical MUSTs (never swallow, log with context, boundary validation, no silent
  no-ops) live in `CODE-STANDARD.md` — this is the judgment underneath them.
- **Raise vs return-Result vs log-and-continue is a judgment call, not a rule**: raise/
  throw when the caller cannot meaningfully continue (a truly exceptional, rare
  condition); return a `Result`/`ok, err`/`nil, err`-shaped value when failure is a
  normal, expected outcome the caller is expected to branch on (a file that might not
  exist, a network call that might time out); log-and-continue only when the failure
  is genuinely non-fatal to the caller's goal AND the user needs to know it happened
  (this environment's own `watch()` no-op fixes are the local example — the caller
  now sees the boolean and decides, rather than the module silently absorbing it).
- Retries, timeouts, and circuit breakers are judgment, not a default to reach for.
  Add a retry only where the failure is plausibly transient (network, external
  service) — retrying a logic error just delays the same failure. A circuit breaker
  is justified only once a dependency's failure mode is observed to be _sustained_,
  not a one-off blip; building one speculatively is the same YAGNI violation as any
  other unearned abstraction.
- **Prefer the fix that makes a failure OBSERVABLE over the fix that guesses at
  recovery.** When in doubt between "swallow and hope" and "surface it, let the
  caller (or user) decide" — surface it. Recovery logic invented without evidence
  the failure mode is real is speculative generality wearing a different hat.

### Depth — prefer deep modules

- Small interface, large implementation: callers get leverage; they gain a lot of
  behavior for little interface complexity.
- At review, flag shallow modules — if the interface is nearly as complex as the
  implementation, the abstraction earns nothing and is often premature decomposition.
- Apply the **Deletion Test** when evaluating any module: "If I deleted this, where
  does the complexity go?" Complexity that vanishes → module hid nothing, delete it.
  Complexity that scatters → earns its keep. Complexity that consolidates → wrong
  location, move it.
- Full vocabulary with diagrams: `CODE-REFERENCE.md`

## Explicitly dropped — do not apply

- **OCP** (open/closed): invites speculative abstraction layers; contradicts YAGNI.
  Modify the code directly; extension points are earned (see YAGNI).
- **LSP / ISP**: class-hierarchy principles; this stack (Lua modules, bash, Solidity
  contracts, embedded C++) is not hierarchy-OOP. Where real subtyping appears
  (TypeScript, Python classes), plain SRP + small interfaces already cover it.

## Smells — the review-stage refactoring vocabulary

At review (`/code-crit` after green, per TDD above), check the diff against these
Fowler smells by name. Naming the smell is the trigger — flag it, then fix or file it.

- **Mysterious name** — name doesn't reveal intent (single-letter identifiers are
  banned outright in this environment; see CODE-STANDARD.md)
- **Duplicated code** — same knowledge in two homes (apply rule of three before extracting)
- **Long function / large module** — can't be described without "and"
- **Long parameter list** — more than 3-4 params; usually a missing object or wrong boundary
- **Boolean blindness** — call site reads `foo(true, false, true)`, flags opaque without the signature
- **Complex / nested conditional** — deep `if`/`else` nesting or a sprawling boolean expression
- **Data clumps** — same 3+ values traveling together; they want to be a structure
- **Primitive obsession** — domain concept passed around as bare string/number
- **Repeated switches** — same discriminator switched on in multiple places
- **Divergent change** — one module edited for many unrelated reasons (SRP breach)
- **Shotgun surgery** — one logical change forces edits across many modules
- **Feature envy** — function mostly manipulates another module's data
- **Message chains** — `a.b().c().d()` reaching through structure
- **Middle man** — module that only delegates
- **Speculative generality** — hooks/params/layers with no current caller (YAGNI breach)
- **Dead code / commented-out code** — delete it; git remembers

## Two-axis review — Standards vs Spec, never merged

A review has two independent axes: **Standards** (does the diff follow the project's
standards — `CODE-STANDARD.md` plus the Smells above) and **Spec** (does it do what the
task actually asked).
A change can pass one and fail the other:

- Follows every standard, implements the wrong thing → **Standards pass, Spec fail.**
- Does exactly what was asked, breaks conventions doing it → **Spec pass, Standards fail.**

Report the two separately. Merging them lets one mask the other — clean code hides a
missed requirement; a correct fix hides the mess it was written in.

## Related

- `/tdd` — the methodology this file commits to
- `/trust-but-verify` — the evidence gate behind precedence rule 1
- `CODE-STANDARD.md` — mechanical rules + per-language delegation
- `TESTING-STANDARD.md` — test-type decision layer; the error-handling judgment
  above is what a test asserting on failure behavior should actually check
- `CODE-REFERENCE.md` — vocabulary definitions (Ousterhout, Feathers), ADR format + gate, Quick-Check Questions
- `ANTI-PATTERNS.md` — full Fowler/Brown/Meszaros anti-pattern catalogue
- `DATA-STRUCTURES.md`/`ALGORITHMS.md` — scenario-first selection; the YAGNI/
  rule-of-three tone above governs their "escalate when" columns
- `/code-refactor` skill — acts on the smells this file names; code-crit reports,
  code-refactor fixes (deliberate split, no overlap)
- `codebase-design` skill — module/interface/depth/seam vocabulary; a module that
  forces callers to know its internals to use correctly (leaky abstraction) is
  that skill's smell to name, not a new row here
