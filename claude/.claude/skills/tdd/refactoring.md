# Refactor Candidates

After all tests pass, look for these. Run tests after each individual refactor step —
never batch refactors before checking.

**Never refactor while RED.**

## Code-level

| Smell | Signal | Fix |
|---|---|---|
| **Duplication** | Same logic in 2+ places | Extract function or class |
| **Long function** | Hard to name without "and" | Extract sub-functions; keep tests on public interface |
| **Long parameter list** | More than 3–4 params | Introduce a data object or config struct |
| **Primitive obsession** | Raw string/int where a concept should be | Introduce a value type or enum |
| **Feature envy** | Function uses another module's data more than its own | Move function to where the data lives |
| **Data clumps** | Same group of variables always together | Extract into a class or named tuple |

## Module-level

| Smell | Signal | Fix |
|---|---|---|
| **Shallow module** | Interface as complex as implementation | Combine with caller or deepen |
| **Inappropriate intimacy** | Module reaches into another's internals | Enforce boundary; expose a method instead |
| **Middle man** | Module delegates almost everything | Inline it or give it real responsibility |
| **Dead code** | Function/class never called | Delete it — version control is the history |
| **Speculative generality** | Hooks for requirements that don't exist | Delete the abstraction |

## After refactoring

- [ ] All tests still pass
- [ ] No new public API surface added (tests still go through the same interface)
- [ ] Each refactor step was one logical change
- [ ] No dead code left behind

If new code reveals problems in *existing* code nearby, note them as
`[CHORE]` TODOs in session-log.md — don't refactor out of scope mid-cycle.
