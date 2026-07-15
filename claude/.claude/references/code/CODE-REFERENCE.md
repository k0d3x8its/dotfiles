# CODE-REFERENCE

> On-demand vocabulary and decision reference. Loaded by skills (diagnose, tdd,
> prototype, dev-setup) when evaluating architecture, writing tests, or recording
> decisions. Sources: Ousterhout (APOSD), Feathers (WEWLC), Fowler (Refactoring).

---

## Architectural Vocabulary

*(Ousterhout — A Philosophy of Software Design)*

### Module
Anything with an interface and an implementation. A function, class, file, service,
or script — if it has a surface others call and internals that do work, it's a module.

### Deep Module
Small interface, large implementation. Callers get a lot of behavior for a little
complexity on their end. The ideal shape.

```
┌─────────────────┐
│ Small Interface │  ← few functions, simple parameters
├─────────────────┤
│                 │
│  Deep Impl      │  ← complex logic hidden inside
│                 │
└─────────────────┘
```

### Shallow Module
Interface nearly as complex as the implementation. Offers little leverage — the
caller could almost have done the work itself. A warning sign worth noting.

```
┌──────────────────────────────┐
│      Large Interface         │  ← many functions, complex params
├──────────────────────────────┤
│ Thin Implementation          │  ← mostly passes through
└──────────────────────────────┘
```

### Depth
How much behavior a caller gets relative to the interface complexity they have to
understand. More depth = more leverage.

### Leverage
What callers gain from a module's depth. High-leverage modules simplify the
surrounding code; low-leverage modules just add an indirection layer.

### Locality
Change concentrated in one place. A module has good locality when fixing or
extending a behavior means editing one file, not six.

### Information Hiding
Internals that callers never need to know about. The more a module can hide, the
more its interface can stay stable while the implementation evolves.

---

## Seams

*(Feathers — Working Effectively with Legacy Code)*

### Seam
A place where behaviour can be altered without editing at that place. Seams are where
tests hook in, where dependencies get swapped, where behaviour gets extended safely.

**Types relevant to this environment:**
- **Object seam** — pass a dependency in rather than constructing it inside (dependency injection)
- **Link seam** — swap a module/import at load time (environment variable, conditional import)
- **Preprocessing seam** — config or environment variable changes behaviour before code runs

### Finding Seams
If a piece of code is hard to test or change, it usually lacks a seam. The fix is to
introduce one — extract the dependency, accept it as a parameter, or wrap the
external call.

---

## Anti-Pattern Taxonomy

*(Fowler — Refactoring; Mantyla; Brown et al — AntiPatterns; Meszaros — xUnit Test Patterns)*

Full taxonomy (70+ patterns across code, OO design, architecture, testing) lives in:
**`references/code/ANTI-PATTERNS.md`** — Read that file for the complete reference.

Most-encountered patterns for quick recall:

| Name | Symptom |
|---|---|
| **Feature Envy** | Method uses another module's data more than its own |
| **Shotgun Surgery** | One change requires edits across many files |
| **God Class** | One class accumulates all responsibility |
| **Speculative Generality** | Abstractions built for requirements that don't exist |
| **Lava Flow** | Dead code kept because no one knows if it's safe to delete |
| **Big Ball of Mud** | No discernible architecture; everything depends on everything |
| **Fragile Test** | Test breaks on internal refactor, not behavior change |
| **Golden Hammer** | Same familiar tool used regardless of fit |

---

## Deletion Test

A heuristic for evaluating whether an abstraction earns its keep:

> "If I deleted this module/class/function, where does the complexity go?"

- **Complexity vanishes** → the abstraction was hiding nothing; deleting it simplifies the system. Keep it deleted.
- **Complexity scatters** → callers would each have to re-implement pieces. The abstraction is earning its keep.
- **Complexity moves to one place** → the abstraction was in the wrong place. Move it to where the complexity would land.

---

## ADR Gate

*(Three-condition rule — all three must be true before creating an ADR)*

1. **Cost of change is meaningful** — reversing this decision later would require significant rework
2. **Future reader would wonder why** — without a record, someone reading the code will be confused by the choice
3. **Alternatives were genuinely considered** — at least one other approach was evaluated and rejected for specific reasons

If all three are true, write an ADR. If any one is false, a code comment or commit
message is sufficient.

---

## ADR Format

File location: `docs/adr/ADR-NNNN-short-title.md`

```markdown
# ADR-NNNN: Short Title

**Date:** YYYY-MM-DD
**Status:** Accepted | Superseded by ADR-NNNN | Deprecated

## Context
What situation or constraint forced this decision? What were the pressures?

## Decision
What was decided? State it as a direct, active sentence.

## Alternatives Considered
- **Option A** — why it was rejected
- **Option B** — why it was rejected

## Consequences
What becomes easier? What becomes harder? What is now locked in?

## Disproof
Under what condition would this decision be invalid or worth revisiting?
```

**Naming:** `ADR-0001-use-sqlite-for-local-cache.md`. Zero-padded 4-digit number.
Sequential. Never renumber.

**Superseding:** When an ADR is overturned, update its status to
`Superseded by ADR-NNNN` and write the new ADR explaining why the old decision
no longer holds. Never delete old ADRs.

---

## Quick-Check Questions

Use these when reviewing a module or deciding where to invest refactor effort:

1. Can I describe this module's purpose in one sentence without the word "and"?
2. Does the interface hide more than it exposes?
3. Would a new contributor know where to make this change without asking?
4. If I deleted this, where does the complexity go?
5. Does this module have a seam where tests can hook in?
6. Does this decision meet the three-condition ADR gate?
