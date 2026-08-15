# PYTHON — language standard

Scope: Python apps and tooling (kos-capture Textual TUI, flask_app, kos scripts).
Strength vocabulary per `CODE-STANDARD.md`.

## Naming & casing

| Kind                     | Casing                | Example              |
| ------------------------ | --------------------- | -------------------- |
| variables / functions    | `snake_case`          | `transcribe_batch`   |
| constants                | `UPPER_SNAKE`         | `DEFAULT_MODEL_NAME` |
| classes                  | `PascalCase`          | `CaptureScreen`      |
| modules / packages       | `snake_case`          | `session_log.py`     |
| "private" module members | `_leading_underscore` | `_parse_header`      |

## Rules

- MUST type-hint all public function signatures (params + return). Internal helpers
  SHOULD be hinted; untyped code is AVOID.
- MUST use f-strings — never `%` or `.format()`.
- MUST NOT use mutable default arguments (`def f(items=[])` — the classic trap);
  default to `None`, create inside.
- MUST use `pathlib.Path` over `os.path` string juggling.
- Exceptions: MUST catch the narrowest type that handles the case; bare `except:`
  is banned; `except Exception` requires a logged reason. Errors never pass silently
  (universal hygiene rule).
- Context managers (`with`) MUST guard files, locks, connections.
- SHOULD prefer dataclasses (or `NamedTuple`) over dict-shaped records passed around
  (primitive-obsession smell).
- Imports: stdlib / third-party / local, three blocks, no wildcard imports.
- AVOID module-level side effects — importing a module must be safe.

## File layout (SHOULD — top to bottom)

1. Imports — stdlib / third-party / local, three blocks
2. Constants (`UPPER_SNAKE`)
3. Types — dataclasses, NamedTuples, enums, type aliases
4. Functions / classes — newspaper order: public high-level first, `_helpers` below
5. Entry wiring at the bottom: `if __name__ == "__main__":` guard (the only
   module-level side effect allowed)

## Directory structure (canonical minimum)

Ecosystem-standard shape. An existing repo's layout always wins over this — check
before creating directories.

```
<project>/
├── pyproject.toml          # metadata + deps + tool config (ruff/pytest) — one file
├── README.md
├── <package_name>/         # the import package (snake_case)
│   ├── __init__.py
│   ├── main.py             # entry: thin — bootstrap only
│   ├── core/               # pure logic — importable with NO UI/framework imports
│   └── <ui layer>/         # framework-facing code (screens/, routes/, templates/)
└── tests/                  # pytest mirror of the package
```

- Minimum viable: `pyproject.toml` + `<package_name>/__init__.py` + `tests/`.
- The load-bearing rule regardless of framework: **pure logic separated from the
  UI/framework layer** so it's testable without the framework attached.
- `requirements.txt` acceptable in legacy repos; new projects use `pyproject.toml`.

## Async (Textual apps — kos-capture pattern)

- pytest runs `asyncio_mode = auto` — async tests are plain `async def test_*`.
- MUST NOT block the event loop: no `time.sleep`, no sync I/O in handlers —
  `asyncio.sleep`, executors, or Textual workers.
- Fire-and-forget tasks MUST be held in a reference and cancelled on teardown —
  orphaned tasks die silently with the loop.

## Data structures & algorithms

Scenario names match `DATA-STRUCTURES.md`/`ALGORITHMS.md` — this is the concrete API only.

- Membership test / set ops: `set`.
- Key → value: `dict` (insertion-ordered since 3.7 — no separate ordered-map type needed).
- FIFO/LIFO: `collections.deque` (O(1) both ends; a plain `list` is O(n) on `pop(0)`).
- LRU / bounded cache: `functools.lru_cache` (function-level) or `functools.cache`;
  hand-roll only if the cache needs eviction callbacks the decorator can't express.
- Priority / smallest-next: `heapq` (min-heap on tuples; negate for max-heap).
- Ordered + unique / binary search: `bisect` over a sorted `list`.
- Sort + sort-key: `sorted(iterable, key=...)` / `list.sort(key=...)`.
- Dedup preserving order: `dict.fromkeys(iterable)`.

## Testing

- pytest, tests under `tests/`, red-green per `/tdd`.
- SHOULD test pure logic separated from UI (same SM/renderer split as Lua standard).

## Tooling

- No ruff/black/mypy config exists in the Python repos yet — `[CHORE]` candidate
  (recommended: ruff for format+lint, pyright for types). Until then: PEP 8 defaults,
  4-space indent, match the file you're in.
