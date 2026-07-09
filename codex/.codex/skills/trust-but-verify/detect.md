# Resolving the verify command

Project-agnostic resolution, first hit wins. State the resolved command + which level
produced it before the first run. Cache per session per project.

## 1. Explicit declaration (preferred)

Project `AGENTS.md` or `KNOWLEDGE.md` (project root or `.codex/`): a line declaring the
verify command, e.g.

```
Verify command: `shellcheck install.sh && bats --tap tests/`
```

Grep for `verify command` (case-insensitive). If found, use it verbatim — no inference.

## 2. Build-runner targets

- **Makefile / justfile:** targets named `test`, `check`, `verify`, `lint` — prefer
  `check`/`verify` (usually a superset), else `test`.
- **package.json:** `scripts.test` (skip if it's the npm placeholder
  `"echo \"Error: no test specified\""`), plus `scripts.lint` if present. Join with `&&`.

## 3. CI workflows

Parse `run:` lines from `.github/workflows/*.yml`, in step order, joined with `&&` —
**skipping setup/install steps**:

- Step `name:` matching install / setup / checkout / cache / deps (case-insensitive)
- Commands led by a package manager install: `apt-get`, `apt`, `brew`, `npm install`,
  `npm ci`, `pip install`, `uv sync`, `bundle install`, `cargo fetch`
- `uses:` steps (no `run:` to take)

Keep lint/test/check commands only. Multi-line `run: |` blocks: apply the same filter
per line.

## 4. Tool-presence fallback

No declaration, no runner, no CI — infer from what's in the repo, combining all that apply:

| Present | Command |
|---|---|
| `tests/*.bats` + `bats` on PATH | `bats --tap tests/` |
| `*.sh` at root + `shellcheck` on PATH | `shellcheck <those files>` |
| `pytest.ini` / `pyproject.toml [tool.pytest]` | `pytest` |
| `tests/test_*.py` without pytest config | `python3 -m unittest discover -s tests -p "test_*.py"` |
| `Cargo.toml` | `cargo test` |
| `go.mod` | `go test ./...` |

## Nothing resolves

Report it honestly. Recommend the user add a level-1 declaration — one line in the
project's KNOWLEDGE.md makes every future resolution instant and exact. Until then,
every completion claim stays unproven.
