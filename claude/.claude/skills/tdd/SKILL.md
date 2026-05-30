---
name: tdd
description: Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development. Maps to the [TEST] TODO tag.
---

# Test-Driven Development

> Examples throughout use Python/pytest. The patterns apply universally — adapt to
> your stack's test runner (Go's `testing`, Node's `vitest`, etc.).

## Philosophy

**Core principle:** Tests verify behavior through public interfaces, not implementation
details. Code can change entirely; tests should not.

**Good tests** are integration-style: they exercise real code paths through public APIs.
They describe *what* the system does, not *how*. A good test reads like a specification.
See `~/.claude/skills/tdd/tests.md` for examples.

**Bad tests** are coupled to implementation. They mock internal collaborators, test
private methods, or assert on call order. The warning sign: your test breaks when you
refactor but behavior hasn't changed.

See `~/.claude/skills/tdd/mocking.md` for mocking guidelines.

## Anti-Pattern: Horizontal Slices

**Do not write all tests first, then all implementation.**

This produces tests that verify the *shape* of things rather than user-facing behavior.
Tests become insensitive to real changes — they pass when behavior breaks, fail when
behavior is fine.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
```

One test → one implementation → repeat. Each test responds to what you learned from
the previous cycle.

## Workflow

### 1. Planning

Before writing any code:

- Confirm with user what interface changes are needed
- Confirm which behaviors to test (prioritise — you can't test everything)
- Design interfaces for testability (see `~/.claude/skills/tdd/interface-design.md`)
- Identify opportunities for deep modules (see `~/.claude/skills/tdd/deep-modules.md`)
- List the behaviors to test (not implementation steps)
- Get user approval on the plan

Ask: "What should the public interface look like? Which behaviors matter most?"

### 2. Tracer Bullet

Write ONE test that confirms ONE thing about the system:

```python
# RED: write test for first behavior → fails
def test_user_can_checkout_with_valid_cart():
    cart = Cart()
    cart.add(product)
    result = checkout(cart, payment_method)
    assert result.status == "confirmed"
```

```python
# GREEN: write minimal code to pass → passes
def checkout(cart, payment):
    return Result(status="confirmed")
```

Proves the path works end-to-end. Minimal code only — don't anticipate future tests.

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:
- One test at a time
- Only enough code to pass the current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After all tests pass, look for candidates (see `~/.claude/skills/tdd/refactoring.md`):

- Extract duplication
- Deepen modules (move complexity behind simple interfaces)
- Apply SOLID principles where natural
- Consider what new code reveals about existing code
- Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.

## Checklist Per Cycle

- [ ] Test describes behavior, not implementation
- [ ] Test uses public interface only
- [ ] Test would survive an internal refactor
- [ ] Code is minimal for this test only
- [ ] No speculative features added
