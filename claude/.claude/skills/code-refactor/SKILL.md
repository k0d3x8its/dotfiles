---
name: code-refactor
description: Behavior-preserving code restructuring under a test safety net — micro-refactors (extract method, rename, decompose conditional, etc.) applied one at a time with a green test run between each. Use when the user says "refactor this", "clean this up", "reduce complexity here", or when picking up a [CHORE] TODO whose body names a code smell.
argument-hint: "[file, directory, or smell to target]"
---

# code-refactor

**Not `/code-crit`.** `/code-crit` _names_ smells (review-only, never edits).
`/code-refactor` _performs_ the transformation on a named smell — from a
code-crit finding, a `[CHORE]` TODO, or a direct ask. If no smell is named
yet, run or point at `/code-crit` first.

Smell vocabulary + Fowler catalogue: `~/.claude/references/code/CODE-PRINCIPLES.md`
§"Smells" and `ANTI-PATTERNS.md`. Full smell definitions live there — don't
restate them here. What's missing from both files, and what this skill
adds, is the **technique to fix each one**:

## Smell → technique map

| Smell (CODE-PRINCIPLES.md)                           | Technique                                                                                                                                                                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Mysterious name                                      | Rename Variable / Method / Field                                                                                                                                                                             |
| Duplicated code                                      | Extract Method, then Pull Up Method if duplicated across siblings                                                                                                                                            |
| Long function / large module                         | Extract Method / Extract Class                                                                                                                                                                               |
| Data clumps                                          | Introduce Parameter Object / Extract Class                                                                                                                                                                   |
| Primitive obsession                                  | Replace Primitive with Object (or Replace Type Code with Class)                                                                                                                                              |
| Repeated switches                                    | Replace Conditional with Polymorphism                                                                                                                                                                        |
| Divergent change                                     | Extract Class (split the unrelated responsibilities apart)                                                                                                                                                   |
| Shotgun surgery                                      | Move Method/Field to consolidate scattered logic; Inline Class if it collapses to one                                                                                                                        |
| Feature envy                                         | Move Method to the class it envies                                                                                                                                                                           |
| Message chains                                       | Hide Delegate, or Extract Method to name the traversal                                                                                                                                                       |
| Middle man                                           | Remove Middle Man (Inline Method)                                                                                                                                                                            |
| Speculative generality                               | Collapse Hierarchy / Inline Class or Method / delete unused params                                                                                                                                           |
| Dead code                                            | Delete outright — git remembers, no technique needed                                                                                                                                                         |
| Long parameter list                                  | Introduce Parameter Object; Replace Parameter with Method if a param is derivable inside the callee instead of passed in; Preserve Whole Object if you're already passing several fields off the same object |
| Boolean blindness                                    | Replace flag params with named constants/enum, or split the function into two named call sites                                                                                                               |
| Complex / nested conditional                         | Decompose Conditional; Replace Nested Conditional with Guard Clauses; Consolidate Conditional Expression when several conditions share one outcome                                                           |
| CQS violation (ANTI-PATTERNS.md, Data)               | Split into a Command (mutates, no return) and a Query (returns, no mutate)                                                                                                                                   |
| Circular dependency (ANTI-PATTERNS.md, Dependencies) | Extract a shared interface at the seam (Dependency Inversion), or merge the two modules if the split was never real                                                                                          |

## Scope

If a file, directory, or smell was named (as an argument or in the
request), restrict to that. Otherwise `AskUserQuestion` to agree scope
before starting (same pattern as `/mutation-testing`) — don't default to
"the whole repo."

- Duplicated-code or feature-envy smells often span files a text grep
  misses (renamed variables, reordered args). Use `ast-grep` to find
  every structural instance before deciding the batch — cheaper than
  discovering instance #4 mid-loop and re-scoping.

## Pre-flight (blocking — do not skip)

1. **Scope guard.** `git status`. Unrelated feature/bug changes in the tree
   → stop, ask user to separate them into their own commit/branch first.
   Refactoring mixed with functional change is explicitly banned
   (global CLAUDE.md: "not while fixing a bug or under a tight deadline").
2. **Safety-net gate.** Resolve the project's verify command via
   `~/.claude/skills/trust-but-verify/detect.md`, run it fresh, read the
   exit code. Suite must pass before touching anything.
3. **Exercised check** (existence, not % — this environment explicitly
   rejects line-coverage targets, see `TESTING-STANDARD.md` "Coverage
   stance"). Grep test files for the target symbol name **and** its
   direct callers — integration tests often reach a target only through
   a caller, never naming it directly. Neither appears → report exactly
   what was searched and let the user confirm before stopping; don't
   hard-block on a grep miss alone. Confirmed genuinely untested → route
   to `/tdd` for a characterization test first (locks in current
   behavior, not new behavior).
4. **Read the target.** Load `~/.claude/references/code/CODE-STANDARD.md`
   plus the one matching language file, per session rules.

## Loop — one micro-refactor at a time

For each smell being addressed:

1. Name the smell (from CODE-PRINCIPLES.md vocabulary) and the target
   technique (Extract Method, Rename, Decompose Conditional, Pull Up,
   Introduce Parameter Object, etc. — Fowler's catalogue, not reinvented
   here).
2. Apply **one** transformation. Smallest change that removes the smell.
   No drive-by cleanup, no bundling two smells into one step. Rename and
   Move techniques require a full call-site sweep (grep every reference) —
   the verify run only proves behavior-preservation where a test actually
   reaches the call site; an unswept caller is a silent break the suite
   won't catch.
3. Run the verify command fresh. Fail → revert this step (`git checkout`
   the file or `git revert`), re-attempt smaller, or stop and report —
   never leave the tree red between steps.
4. Pass → commit this file alone, message
   `refactor: <what and why in one line>` (per-file commit granularity,
   matches this repo's convention — confirmed via `git log`, `refactor:`
   prefix already in use alongside feat/fix/docs/chore).
5. Repeat for the next smell, or stop (see below).

## Stopping criteria

- **Rule of Three**: don't extract on first or second duplication, only
  the third (CODE-PRINCIPLES.md already states this — don't re-derive).
- Scope was N files / one module — finishing early because it's "close
  enough" is fine; expanding scope mid-task is not. If a fix reveals a
  bigger smell outside scope, log it as a new `[CHORE]` TODO, don't chase
  it now.
- Diminishing returns: if the next transformation trades one smell for
  another (e.g. Extract Method churns out a Middle Man), stop and say so
  rather than applying it.

## After the loop

- If the refactor was non-trivial (touched public interfaces, moved
  files, changed module boundaries), suggest `/code-crit` as a final pass
  before merge — different lens, catches what the refactor loop itself
  can't self-check.
- Suggest `/mutation-testing` on touched files: the exercised-check in
  pre-flight only proved a test _calls_ the target, not that it would
  catch a regression. Mutation testing is this environment's actual
  suite-strength signal (TESTING-STANDARD.md) — survived mutations become
  `[TEST]` TODOs, closed via `/tdd`.
- No CHANGELOG entry unless external behavior or public API surface
  changed — pure internal restructuring is not changelog-worthy.

## Related

- `/code-crit` — names smells (this skill fixes them)
- `/tdd` — characterization tests when the exercised-check fails
- `/trust-but-verify` — verify-command resolution + fresh-run discipline
- `ast-grep` — structural search for smell instances across files
- `/mutation-testing` — suite-strength confirmation after the loop
- `CODE-PRINCIPLES.md` / `ANTI-PATTERNS.md` — smell vocabulary this skill fixes
- `TESTING-STANDARD.md` — coverage stance behind the exercised-check gate
- `CODE-REFERENCE.md` — defines "seam" (Feathers), used by the Circular
  Dependency row above
