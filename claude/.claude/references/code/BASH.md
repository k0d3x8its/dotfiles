# BASH — language standard

Scope: shell scripts (`scripts/`, tooling, hooks) and sourced libraries
(trueline.sh prompt lib). The two kinds have DIFFERENT rules — know which you're
writing. Strength vocabulary per `CODE-STANDARD.md`.

## Naming & casing

| Kind | Casing | Example |
|---|---|---|
| variables (script-local) | `snake_case` | `retry_count` |
| environment / exported | `UPPER_SNAKE` | `KODEX_IDE` |
| constants | `UPPER_SNAKE`, `readonly` | `readonly MAX_ATTEMPTS=3` |
| functions | `snake_case` | `parse_session_log` |
| sourced-library functions | `_prefix` with lib name | `_trueline_font_style` |
| files | `kebab-case.sh` or extensionless executables | `batch-transcribe.sh` |

## Executable scripts — MUSTs

- First lines: `#!/usr/bin/env bash` then `set -euo pipefail`. Existing `scripts/`
  lack this — retrofit when touched (Boy Scout, in-scope).
- EVERY expansion quoted: `"$variable"`, `"$(command)"`, `"$@"`. Unquoted is the
  #1 bash defect class.
- MUST use `[[ ]]` over `[ ]`; `$(...)` over backticks.
- Arguments: `local` inside functions; positional params named immediately
  (`local input_file="$1"`) — bare `$1` used deep in a function violates naming rules.
- Temp files via `mktemp`, cleaned by a `trap ... EXIT`.
- MUST NOT parse `ls`; glob or `find -print0 | while read -d ''` for filenames
  (filenames contain spaces/newlines — assume it).
- Exit codes are the API: 0 success only; failures exit nonzero with a message
  to stderr (`>&2`). Silent failure = swallowed error (universal hygiene rule).
- SHOULD guard `cd` (`cd "$dir" || exit 1`) even under `set -e` (pipelines/subshells
  escape it).

## Sourced libraries — the exception

- `set -e`/`set -u` MUST NOT appear in a file meant to be sourced (it would kill or
  break the parent shell — why trueline.sh has none). Defensive `${var:-default}`
  expansions instead.
- Everything is namespaced (`_libname_fn`) — a sourced file pollutes the caller's
  namespace; act like a guest.
- Top-of-file `# shellcheck disable=` directives with a reason are the accepted
  way to document deliberate deviations (existing trueline.sh pattern).

## File layout (SHOULD — top to bottom)

1. Shebang + `set -euo pipefail` (executables only)
2. Header comment: what + usage line
3. Constants / defaults (`readonly`, `UPPER_SNAKE`)
4. Functions — newspaper order: high-level first, helpers below… *(bash has no
   hoisting inside a call, but functions defined before `main` runs is what matters)*
5. `main "$@"` invocation (or the argument-parsing + dispatch block) — at the bottom
- A script long enough to need sections is a script that SHOULD have a `main()`.

## Directory structure (canonical minimum)

Shell projects rarely need structure; when one does:

```
<project>/
├── <tool>            # or bin/<tool> — executable entry
├── lib/              # sourced helpers (no set -e, namespaced fns)
└── tests/            # bats tests, if the logic warrants them
```

- One-off automation stays a single file in the repo's `scripts/`.
- A bash file past ~300 lines or needing data structures SHOULD become Python.

## Tooling

- shellcheck is the authoritative linter — a script isn't done until shellcheck
  passes or every disable-directive carries a reason. shfmt for format.
