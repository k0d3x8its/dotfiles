---
name: code-decay
description: Hotspot-ranking CLI skill — churn (git log) × complexity (ast-grep/proxy) → a dated Markdown report inside the target repo. Use for "/code-decay", "find hotspots", "which files are decaying", "churn times complexity", "rank files by risk". Single-repo scope per run (NFR-01); zero model calls outside `--interpret` (FR-11).
---

# code-decay

Ranks every tracked file in a target repo by `score = churn × cx` (churn from
`git log`, `cx` from AST/regex complexity), labels outliers heuristically, and
writes a dated report. Traces to `docs/REQUIREMENTS.md` FR-01–15/NFR-01–03 and
`docs/ARCHITECTURE.md`'s component list — this file is the CLI entrypoint
component; every stage below already exists as a tested script under
`scripts/`. This file only orchestrates them in order — no new ranking logic
lives here.

## Invocation

```
/code-decay [path] [--interpret[=N]] [--all-history]
```

- **`path`** — the repo to analyze. Default: cwd. **Exactly one repo per
  run — never merge or aggregate more than one repo's history or scores in a
  single run (NFR-01).** There is no flag that accepts a second path or a
  list of repos.
- **`--interpret[=N]`** — send the top files above the score floor to a model
  review pass (default `N=10`). Omit entirely to skip the model pass — the
  base report is always complete without it (Failure Behavior, below).
- **`--all-history`** — churn window is full history instead of the
  `--since=12.months` default.

## Pipeline

Run every stage below, in this order, for every invocation — regardless of
whether `--interpret` is passed. Stop only on an unrecoverable error from a
stage that has no defined fallback (none currently exist; every stage below
either succeeds or degrades per Failure Behavior).

1. **Shallow-Clone Guard** — `shallow_guard.is_shallow(path)`. If `True`,
   carry the warning forward to the Report stage (below); do not stop the
   run (FR-05, warn-and-continue).
2. **File Universe Resolver** — `file_universe.resolve_files(path)` → list of
   repo-relative paths (FR-02).
3. **Churn Extractor** — `churn.extract_churn(path, all_history=<flag>)` →
   `{repo_relative_path: churn_count}` (FR-03, FR-04).
4. **Complexity Dispatcher** — for each path from step 2, call
   `complexity.complexity(os.path.join(path, repo_relative_path))` → `Cx`;
   read `.value` (`branch_count + nesting_depth`) for the scalar `cx` (FR-06,
   FR-07). A path with no churn entry (untouched in the window) still gets a
   `cx` — it scores `0` in step 5, not an error.
5. **Build `rows`** — `{repo_relative_path: (churn, cx)}` for every path
   from step 2, defaulting missing churn to `0`. This is the shared input
   shape every downstream stage takes.
6. **Scorer** — `scorer.score_files(rows)` → `{path: score}` (FR-08).
7. **Labeler** — `labeler.label_files(rows)` → `{path: label | None}`
   (FR-09, FR-15).
8. **Interpret Pass (flag-gated)** — only when `--interpret` was passed:
   1. `interpret_selection.select_for_interpretation(rows, top_n=<N>)` →
      up to `N` paths clearing the score floor (deterministic, zero model
      calls — `interpret_selection.py` never touches a model).
   2. **This is the only step in the entire pipeline that touches a
      model.** For each selected path: read the file, compare its current
      content against the Labeler's suggested label and the Scorer's score,
      and confirm / correct / drop the label based on what the code
      actually shows (a heuristic percentile threshold can mislabel a file
      whose complexity is justified — e.g. a generated parser). Record the
      verdict per path.
   3. **Apply the verdicts before rendering** — for every path with a
      verdict, overwrite that path's entry in `labels` (step 7's dict) with
      the corrected label, or `None` if dropped; a "confirmed" verdict
      leaves the existing entry unchanged. A verdict that never reaches
      `labels` is indistinguishable from a pass that changed nothing —
      FR-10 requires the model's corrections to actually land in the
      report, not just run. Pass the selected-paths list to the Report
      stage as `interpreted_paths` regardless of how many verdicts were
      confirmed vs. corrected vs. dropped — the report states the count
      _sent_, not the count _changed_.
9. **Report Renderer** — `report_renderer.render_report(path, rows,
<labels, with step 8.3's verdicts applied if `--interpret` ran>,
interpreted_paths=<step 8.1 list or None>, shallow_warning=<step 1
bool>)` → writes `docs/code-decay/<repo>-<date>.md` **inside the target
   repo**, never inside `dotfiles` (FR-14, NFR-03).

## Failure Behavior

- **Shallow clone** — warn (visible in the report body, not just the
  terminal), continue on truncated history. Never stops the run.
- **Unsupported language** — the Complexity Dispatcher's Agnostic Proxy
  Backend guarantees a non-error `cx` for anything the ast-grep backend
  doesn't cover. Never a crash.
- **Missing/older `ast-grep` binary for a v1-covered language** — fails
  loud. This is the one deliberate exception to "never errors": a broken
  install must not silently degrade into a proxy-backend accuracy problem
  (2026-07-27 decision, `docs/ARCHITECTURE.md` ast-grep Backend).
- **`--interpret` model call fails or is unreachable** — the base report
  (steps 1–7, 9) is already complete before step 8 runs. Emit the report
  without an `interpreted_paths` line rather than blocking on the model
  step; state in the response to the user that the interpret pass did not
  complete, don't silently omit it.
- **`--interpret` floor undershoot** — fewer than `N` files clear the score
  floor: the report states the actual count sent, never pads to `N`.

## Deterministic-core guarantee (FR-11)

Steps 1–7 and 9 make zero network/model calls — every function they call
(`shallow_guard.is_shallow`, `file_universe.resolve_files`,
`churn.extract_churn`, `complexity.complexity`, `scorer.score_files`,
`labeler.label_files`, `report_renderer.render_report`) is a pure/local-I/O
function covered by its own unit test suite. Step 8.2 is the **only** place
in this skill that spends that guarantee on an actual model call — nothing
upstream or downstream of it touches one. `tests/test_code_decay_cli.py`
exercises steps 1–7 and 9 end-to-end against a real temp git repo and
asserts zero model access.

## Report

Markdown table, columns `File | Churn | Cx | Score | Label`, ranked
descending by score. A shallow-clone warning (if any) appears before the
table. An `--interpret` summary line (if the flag was used) appears after
the table, stating the actual count of files sent for review.

## Verify

- Run against `kodex-ide`: confirm `docs/code-decay/kodex-ide-<date>.md`
  lands with a ranked table (FR-01).
- Re-run against a second, unrelated repo: confirm it ranks that repo's own
  files, not a merge with the first run (FR-01, NFR-01).
- `tests/test_code_decay_cli.py` — deterministic-core integration suite,
  zero model calls (FR-11).
