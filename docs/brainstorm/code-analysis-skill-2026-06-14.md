# Design: code-analysis skill

> Brainstorm output, 2026-06-14. Pipeline: /brainstorm → /grill-me → /write-plan.
> Status: draft — not yet grilled.

## Problem

Build a `code-analysis` skill that ranks the hotspots in a repo — the files most worth
refactoring — by combining **behavioral** signals from git history (churn, age,
co-change) with **structural** signals (complexity), then names each hotspot through the
kos-code-reference.md vocabulary (God Class, Shotgun Surgery, Deep/Shallow Module, Lava
Flow, etc.). v2+ dimensions deferred: static analysis (lint/type errors), coverage gaps
vs churn, dependency-graph coupling.

## Context & constraints

- Skill lives in `dotfiles/claude/.claude/skills/code-analysis/` (symlinked to `~/.claude`).
- Interpretive lens already exists: `references/kos-code-reference.md` + `anti-patterns.md`.
- `ast-grep` 0.43.0 (`sg`) on PATH. **Verified** it supports every language in play:
  Python, JS, TS/TSX, Lua, Bash, C, C++, **Solidity** — all built-in (tested with real
  files; an earlier stdin-based probe falsely reported Solidity unsupported).
- kodex-ide treesitter/LSP config defines the working language set (python, c, cpp, js,
  ts, html, css, solidity, lua, bash, yaml, json, arduino).
- Pipeline mandates `/prototype` before `/write-a-skill`, and `/tdd` on any delegated
  script — so the deterministic core must be unit-testable.
- Precedent: dev-brief triage moved rendering OUT of the model into zero-token scripts
  (see dotfiles/KNOWLEDGE.md). Same instinct applies here — keep the model off the
  always-on path.

## Locked decisions

These were resolved during brainstorm (each chosen over named alternatives):

### D1 — Target scope: single repo (cwd)
Analyzes the current git repo only. churn/co-change are per-repo by nature; a
multi-project sweep can't meaningfully merge git histories or co-change graphs across
repos. *(Rejected: multi-project sweep; single-repo + path arg.)*

### D2 — Output: dedicated dated file
Write to `docs/code-analysis/<repo>-YYYY-MM-DD.md`. Persists, no collision (vs
findings.md shared scratch), and dated snapshots **diff over time → hotspot trend**.
*(Rejected: ephemeral terminal; findings.md.)*

### D3 — Ranking: churn × complexity
`score = churn × complexity`. age + co-change render as **annotations**, not score
inputs. Multiplication enforces the AND — a file ranks high only if it is *both*
volatile AND complex (Tornhill crime-scene heuristic), which is the genuinely dangerous
quadrant. *(Rejected: weighted normalized sum — arbitrary weights, opaque; lexicographic
tiers — no blending, churn-dominated.)*

### D4 — Interpretation: hybrid, model-confirm behind a flag
The script emits the ranked number table **plus heuristic-suggested kos labels** (e.g.
co-change ratio > T → Shotgun Surgery; fn-count > N + high churn → God Class). This core
is deterministic, /tdd-testable, zero-token, always-on. An optional `--interpret` flag
adds a model pass that reads the top-N files and confirms / corrects / drops the
suggested labels with real code understanding. *(Rejected: script-only — can't read
intent; model-only — not testable, breaks dated-diff determinism, tokens every run.)*

### D5 — Complexity: pluggable backend, ast-grep for all v1 languages
Complexity is computed behind one swappable `complexity(file)` interface with two
backends:
- **ast-grep backend** — per-language AST metrics (nesting depth, branch count, fn
  length/count). Covers all v1 languages (Python, JS, TS/TSX, Lua, Bash, C, C++,
  Solidity), since all are ast-grep built-ins.
- **agnostic proxy backend** — language-neutral metrics (line count, max indent depth,
  regex fn-count). Universal fallback for any language without an ast-grep rule set.

No v1 language needs the fallback; it exists so an unknown/exotic file still ranks
(cruder cx) instead of producing zero output. *(Rejected: Python-only; agnostic-only —
both contradict the "cover the languages I actually use" goal that ast-grep already
satisfies.)*

## Architecture sketch

```
/code-analysis [--interpret] [path]
  │
  ├─ behavioral.sh   git log → churn, age, co-change per file   (testable)
  ├─ complexity()    per file: ast-grep backend | agnostic proxy (testable)
  ├─ rank            score = churn × cx; annotate age, co-change  (testable)
  ├─ label           heuristic kos-vocab suggestions             (testable)
  ├─ render          docs/code-analysis/<repo>-DATE.md           (testable)
  └─ [--interpret]   model reads top-N, confirms/corrects labels (flag only)
```

Deterministic core = everything except the flagged model pass → unit-testable via /tdd.

## Open questions → for /grill-me

- **churn window** — full git history vs a `--since` window? (Note the P1 dev-brief
  `--since` gap lesson: a window can miss older signal.) If windowed, what default?
- **complexity normalization** — ast-grep cx and proxy cx must land on a comparable
  scale, else a repo mixing supported + fallback languages ranks apples vs oranges. How
  is each backend's cx number defined and normalized so `churn × cx` is consistent?
- **label thresholds** — exact heuristic cutoffs (God Class fn-count N, Shotgun Surgery
  co-change ratio T, Shallow Module iface≈impl). Tune empirically in /prototype, or fix
  now?
- **--interpret top-N** — how many files does the model read? Token budget per run.
- **edge cases** — non-git repo, empty repo, shallow clone (no full history → churn
  wrong); binary/vendored/generated exclusion (node_modules, .min.js, lockfiles).
- **arduino `.ino`** — map to the cpp backend or let it fall to the agnostic proxy?
- **bash node quirk** — tree-sitter-bash parses `x=1` as a `command`, not an assignment;
  per-language complexity patterns need verification, not assumption.
