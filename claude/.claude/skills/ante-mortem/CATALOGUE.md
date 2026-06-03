# Fragility Catalogue

These are the patterns to look for when reading code in ante-mortem mode.
This list is not exhaustive — use judgement to spot anything that would
surprise a future editor. For each pattern found, ask: "What change would a
reasonable developer make here that would break this?"

### 1. Implicit ordering dependencies

Code that must run in a specific order but doesn't enforce it. Setup methods
that must be called before other methods. List processing that assumes elements
arrive sorted. Initialization sequences where step 3 silently depends on
step 1 having run.

*Future edit:* Someone reorders the calls, adds a new step between existing
ones, or calls a method before the object is fully initialized.

### 2. Semantic coupling through shared mutable state

Two components that communicate through a shared object (a dict, a list, a
module-level variable, an attribute on a passed-in object) rather than through
explicit arguments and return values. The reader of component A might not
realise that component B is reading or writing the same state.

*Future edit:* Someone modifies one component's use of the shared state without
realising the other depends on it. Or someone adds caching/memoization that
prevents the shared state from updating.

### 3. Stringly-typed contracts

Logic that depends on the exact value of strings — dict keys, status fields,
format strings, column names, error messages. These create invisible contracts
between producers and consumers that aren't enforced by any type checker or
test.

*Future edit:* Someone renames a status string, adds a new enum variant that
existing match/if-elif chains don't handle, or changes a dict key in one place
but not another.

### 4. Assumptions baked into data transformations

A function that processes data assuming a particular shape, range, or
distribution — e.g. assuming a list is non-empty, a value is positive, a string
matches a pattern, or a column contains no nulls. These assumptions might be
true today because of how the data is produced upstream, but nothing enforces
them.

*Future edit:* Someone changes the upstream data source, adds a new code path
that feeds different data into the function, or relaxes validation at the
system boundary.

### 5. Coincidental correctness

Code that produces the right result for the wrong reason. A condition that
happens to work because two variables are always equal today. A loop that
doesn't handle the empty case but is never called with an empty input. An
exception handler that catches too broadly but currently only encounters one
exception type.

*Future edit:* The coincidence stops holding. The input space widens, a new
exception type appears, or the previously-equal variables diverge.

### 6. Non-atomic compound operations

A sequence of operations that should be atomic but isn't — e.g. "check then
act" patterns, multi-step state updates with no rollback, or file operations
that assume no concurrent access. Includes anything where a failure or
interruption between steps leaves the system in an inconsistent state.

*Future edit:* Someone adds concurrency, moves the code to a context where
interruption is possible, or adds an early return between the steps.

### 7. Invisible invariants

Relationships between pieces of data that must be maintained but are enforced
only by convention — e.g. "this list and that dict always have the same keys",
"this counter equals len(that list)", "this field is non-None whenever that
flag is True". No assertion, type, or test enforces the invariant.

*Future edit:* Someone updates one side of the invariant but not the other,
especially when the two sides are in different functions or files.

### 8. Load-bearing defaults

Default values (function parameters, config settings, class attributes,
environment variables) that the code subtly depends on. The default doesn't
just provide convenience — the code would behave incorrectly or dangerously
with a different value, and nothing documents this constraint.

*Future edit:* Someone changes the default to something that seems equally
reasonable, or a caller starts passing an explicit value that nobody anticipated.

### 9. Implicit resource lifecycle

Resources (connections, file handles, locks, temporary files, background
threads) that are created but whose cleanup depends on a particular control
flow. No context manager or finalizer guarantees cleanup.

*Future edit:* Someone adds an early return, raises an exception, or refactors
the function into smaller pieces, and the cleanup code is no longer reached.

### 10. Version-coupled assumptions

Code that depends on the behaviour of a specific version of a dependency,
runtime, or protocol — e.g. relying on dict ordering (pre-3.7), assuming a
library function's undocumented side effect, or depending on the exact format
of an error message from a third-party library.

*Future edit:* The dependency is upgraded, the runtime version changes, or the
API's undocumented behaviour shifts.

### 11. Security fragility

Auth checks that depend on call order or implicit context. Permission logic
spread across multiple layers with no single enforcement point. Input that
reaches sensitive operations without validation at the boundary. Secrets or
credentials passed through shared state rather than explicit parameters.

This category is distinct: a fragility here isn't just a future bug — it may
be an exploitable vulnerability. See "Security fragility path" in SKILL.md.
