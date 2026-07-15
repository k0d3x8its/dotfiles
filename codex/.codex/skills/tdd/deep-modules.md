# Deep Modules

*(Ousterhout — A Philosophy of Software Design)*

Full vocabulary reference: `~/.codex/references/code/CODE-REFERENCE.md`

## The principle

**Deep module** = small interface + large implementation

```
┌─────────────────┐
│ Small Interface │  ← few functions, simple parameters
├─────────────────┤
│                 │
│  Deep Impl      │  ← complex logic hidden inside
│                 │
└─────────────────┘
```

**Shallow module** = large interface + thin implementation (avoid)

```
┌──────────────────────────────┐
│      Large Interface         │  ← many functions, complex params
├──────────────────────────────┤
│ Thin Implementation          │  ← mostly passes through
└──────────────────────────────┘
```

A shallow module adds indirection without adding value — callers could almost have
done the work themselves.

## Application to TDD

When designing interfaces before writing tests, ask:

- Can I reduce the number of public functions?
- Can I simplify the parameters?
- Can I hide more complexity inside the module?

A deep module is easier to test: fewer entry points, each covering more behavior.
A shallow module forces many small tests that all break together when internals change.

## Recognising shallow modules during refactor

After the RED→GREEN cycle, look for:

- Functions that do one trivial thing (pass-through, single assignment)
- Modules with more public methods than lines of real logic
- Callers that must call three functions to accomplish one conceptual thing

Combine or absorb these. Fewer, deeper modules = fewer tests, more stable tests.

## Deletion test

> "If I deleted this module, where does the complexity go?"

- Complexity **vanishes** → module was hiding nothing; delete it
- Complexity **scatters** → module is earning its keep
- Complexity **moves to one place** → module is in the wrong place; move it there
