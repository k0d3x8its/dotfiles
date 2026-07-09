---
name: mutation-testing
description: Perform mutation testing on the codebase. Introduces deliberate bugs one at a time, checks whether the test suite catches each one, and reports on test suite gaps. Survived mutations become [TEST] TODOs in TODOS.md — close them with /tdd.
argument-hint: "[file, directory, or description of what to focus on]"
disable-model-invocation: true
---

# Mutation Testing

You are now in mutation testing mode. Your job is to assess the strength of the
project's test suite by introducing deliberate bugs (mutations) into the source
code, one at a time, and checking whether any test fails. A mutation that the
tests don't catch reveals a gap in coverage.

## Scope

$ARGUMENTS

- If the user names specific files or directories, restrict mutations to those.
- If no argument is given, look at the project's source layout and use
  `AskUserQuestion` to agree on a starting scope. Don't try to mutate
  everything at once — pick a module or package and work through it.
- Test files themselves are out of scope for mutation. Only mutate production
  code.
- Prioritise code that has meaningful logic (branching, arithmetic, state
  changes) over boilerplate, config, or trivial accessors.

## Pre-flight

Before mutating anything:

1. **Clean working tree.** Run `git status` on the files in scope. If there are
   uncommitted changes to any file you plan to mutate, stop and ask the user to
   commit or stash first. You need a clean baseline so every mutation can be
   reverted cleanly with `git checkout -- <file>`.
2. **Find the test runner.** Look for: `pytest.ini`, `pyproject.toml
   [tool.pytest]`, `setup.cfg [tool:pytest]`, `tox.ini`, `package.json`
   (scripts.test), `Makefile` test target, `go.mod`, `Cargo.toml`, a `tests/`
   or `spec/` directory, or any CI config that reveals the test command. Ask
   the user if you can't determine how to run tests. Confirm that the test suite
   passes on the unmodified code before starting — if it doesn't, stop and tell
   the user.
3. **Map the code.** Read the files in scope. Build a mental model of each
   module's structure and data flow so you can choose mutations that are
   meaningful rather than trivially dead.

## Workflow

Work through the files in scope one at a time. For each file:

1. **Choose mutations.** Read the file and identify 3–8 candidate mutations
   using the catalogue below. Prefer mutations that test interesting behaviour
   — a bug a real developer might introduce — over mechanical operator swaps
   on dead code. For each candidate, write a one-line description of what the
   mutation does and what behaviour it should break.

2. **Apply, test, revert.** For each mutation:
   a. Apply the mutation using `Edit`. Change as little as possible — usually a
      single line.
   b. Run the test suite (or the relevant subset if the suite is large). Use a
      timeout — if the tests hang, that still counts as "caught" (the mutation
      broke something).
   c. Record the result:
      - **Killed** — a test failed. Note which test, and briefly assess how
        helpful the failure message is. Would a developer reading this failure
        immediately understand what went wrong, or would they have to dig?
      - **Survived** — no test failed. This is a gap. Note what behaviour is
        untested.
   d. Revert the mutation: `git checkout -- <file>`. Confirm the file is back
      to its original state before moving on.

3. **Never leave a mutation in place.** After each test run, revert immediately.
   If something goes wrong and you're unsure of the file state, run
   `git diff <file>` to check, and `git checkout -- <file>` to restore.

Use `TaskCreate` to track progress across files when there are more than a
handful.

## Mutation Catalogue

Choose mutations from these categories, ordered roughly from most to least
likely to reveal meaningful test gaps.

### 1. Delete or skip a side effect

Remove or comment out a line that modifies state — an assignment, a method
call that updates an object, an append to a list, a cache write, a database
call. This tests whether the suite verifies that the side effect actually
happened.

```python
# Original
self.count += 1
results.append(item)

# Mutation: delete the line entirely
```

### 2. Negate or invert a condition

Flip a boolean condition: `if x` → `if not x`, `x > 0` → `x <= 0`,
`x and y` → `x or y`, `x is None` → `x is not None`.

```python
# Original
if user.is_active and user.has_permission:

# Mutation
if user.is_active or user.has_permission:
```

### 3. Change a boundary or comparison

Off-by-one and boundary errors: `<` → `<=`, `>=` → `>`, `== 0` → `== 1`,
`range(n)` → `range(n - 1)`.

```python
# Original
if retry_count < max_retries:

# Mutation
if retry_count <= max_retries:
```

### 4. Swap or hardcode a return value

Replace a computed return value with a constant, or swap two return paths in
a conditional. This tests whether callers actually use and verify the return
value.

```python
# Original
return calculated_score

# Mutation
return 0
```

### 5. Delete an early return or guard clause

Remove a guard clause (`if bad_input: return/raise`) to see whether the
suite has a test for the guarded condition.

```python
# Original
def process(items):
    if not items:
        return []
    ...

# Mutation — delete the guard
def process(items):
    ...
```

### 6. Change an operator

Swap arithmetic or string operators: `+` → `-`, `*` → `/`, `//` → `/`,
`+` → `` (concatenation removed). Use sparingly — only when the operation
has a testable effect on output.

### 7. Modify a default argument or constant

Change a default parameter value, a class constant, or a module-level
constant. This tests whether any test exercises the default path.

```python
# Original
def connect(host, port=5432):

# Mutation
def connect(host, port=5433):
```

### 8. Swap the order of arguments or operands

Reverse argument order in an internal call, or swap operands around a
non-commutative operator. This tests whether the suite is sensitive to
argument semantics rather than just arity.

```python
# Original
result = divide(numerator, denominator)

# Mutation
result = divide(denominator, numerator)
```

## Assessing test failures

When a mutation is killed, briefly rate the diagnostic quality of the failure:

- **Clear** — the test name and failure message immediately point to the bug.
  A developer would fix this in minutes.
- **Indirect** — a test failed, but the failure message describes a symptom
  rather than the root cause. A developer would need to investigate. Consider
  whether a more targeted test would help.
- **Cascading** — many tests failed, making it hard to locate the root cause.
  This suggests the code under test is a dependency of many things but may
  lack focused unit tests of its own.

Record the rating alongside the mutation result.

## Reporting

After completing all mutations for the scope, produce a summary table:

```
| # | File           | Mutation                     | Result   | Diagnostic | Notes               |
|---|----------------|------------------------------|----------|------------|---------------------|
| 1 | pipeline.py    | Negate active check          | Killed   | Clear      | test_inactive_user  |
| 2 | pipeline.py    | Delete cache write           | Survived | —          | No cache test       |
| 3 | scoring.py     | Return 0 instead of score    | Killed   | Indirect   | Assertion on rank   |
```

Then provide:

1. **Mutation score**: killed / total (e.g. 6/8 = 75%).
2. **Uncaught mutations**: list each survived mutation with a sentence
   explaining what behaviour is untested and why it matters.
3. **Diagnostic quality**: note any killed mutations where the failure message
   was indirect or cascading, and suggest how the test could be improved.

## Writing TODOs for survived mutations

After presenting the report, write a `[TEST]` TODO to `TODOS.md` for each
survived mutation. These are critical priority — always tag `[TEST]`, and note
that they should be closed with `/tdd`.

Format each entry:

```
- [ ] [TEST] <file>:<function> — <one-line description of the behaviour that has no test> (mutation-testing survivor — close with /tdd)
```

If `TODOS.md` does not exist in the project root, create it with a minimal
header before writing. Append to the file; do not overwrite existing entries.

After writing the TODOs, tell the user: "Survived mutations written to TODOS.md
as [TEST] items. Use /tdd to close them."

Do not implement the missing tests inline. The /tdd skill runs the full
red-green-refactor loop with proper verification; ad-hoc test writing here
skips that discipline.

## Critical Rules

- **Always revert.** After every test run, revert the mutation before doing
  anything else. Never stack mutations. Never leave mutated code in the working
  tree.
- **Verify the revert.** Run `git diff <file>` after reverting to confirm the
  file is clean. If it's not, run `git checkout -- <file>` again.
- **Don't mutate test files.** Only mutate production code.
- **Don't mutate imports, type annotations, or docstrings.** These rarely
  reveal meaningful test gaps and produce noise.
- **Keep it targeted.** 3–8 mutations per file is enough. Prefer quality over
  quantity — a well-chosen mutation that reveals a real gap is worth more than
  ten trivial operator swaps.
- **Ask when uncertain.** If you're unsure whether a mutation is meaningful or
  whether a test failure constitutes "catching" it, use `AskUserQuestion`.
- **Respect the user's time.** If the test suite is slow, ask whether they
  want to run the full suite or a relevant subset for each mutation.
