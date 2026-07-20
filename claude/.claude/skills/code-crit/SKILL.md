---
name: code-crit
description: Structured code review using isolated parallel Agent-spawn personas, binary verified/unverified confidence, and a Spec-plus-severity report. Use for "review this diff/branch/PR", "code review", "review my changes" — NOT the built-in `/code-review ultra` command (different tool, do not confuse).
---

# code-crit

**Not `/code-review` or `/code-review ultra`** — those are built-in Claude Code
commands (cloud ultrareview). This skill is `/code-crit`, a local peer, not a
replacement wired to that name.

## Quick start

1. Resolve the diff: explicit PR#/branch arg, else `git diff` against the
   diff-base (default: the branch's merge-base with `main`).
2. Spawn all 5 always-on personas + any conditional personas whose trigger
   matches (Dispatch, below).
3. Run the Stage-2 Opus advisor pass (Synthesis, below).
4. Emit the report (Report, below).

## Dispatch

**Always-on (5, every run):** `personas/CORRECTNESS.md`,
`personas/MAINTAINABILITY.md`, `personas/TESTING.md`,
`personas/PROJECT-STANDARDS.md`, `personas/SPEC-COMPLIANCE.md`.

**Conditional (7, LLM judgment against the diff, not keyword-match):**
`personas/SECURITY.md`, `personas/PERFORMANCE.md`,
`personas/RELIABILITY.md`, `personas/API-CONTRACT.md`,
`personas/DATA-MIGRATION.md`, `personas/ADVERSARIAL.md`,
`personas/AGENT-NATIVE.md`. Read each file's `trigger:` line and
decide per-diff whether it applies. Spawn only the ones that match — a
docs-only diff typically spawns zero of the 7.

**Per-spawn contract.** For each selected persona, one isolated `Agent` call —
context never shared across personas, so cross-persona agreement at Stage 2
reflects independent reasoning, not shared framing:

- `prompt`: the diff + the full contents of that persona's file + this
  instruction: "Set your own `confidence: verified | unverified` per your
  file's self-test criteria. Return findings as `file:line | severity | issue
| confidence | fix`." Personas never set `route` — that's assigned at Stage 2
  synthesis, once the merged finding is placed relative to the other tools it
  might belong to (`/code-sec`, `/diagnose`, etc).
- `model: opus` for the 4 frontline personas: **correctness, security,
  spec-compliance, adversarial** — miss-is-unrecoverable territory (SQLi,
  null-deref, a Spec mismatch that ships the wrong thing).
- `model: sonnet` for the other 8: maintainability, testing,
  project-standards, performance, reliability, api-contract, data-migration,
  agent-native.
- `run_in_background: false` — wait for all spawns before Stage 2 (nothing to
  do until findings are in).

## Synthesis (Stage 2 — Opus advisor pass)

One final `Agent` spawn, `model: opus`, after every persona spawn returns.

**Input:** all returned findings EXCEPT `spec-compliance`'s (spec-compliance
findings never enter dedup/synthesis — they go straight to the Report's Spec
section, untouched) + `scripts/fingerprint_group.py`'s candidate-dupe
clusters over that same subset (`file + line±3 + normalized-title` — a
pre-grouping HINT, not a decision).

**Responsibilities:**

1. Refine ONLY the 8 Sonnet-tier findings — rerank, prune weak ones, and may
   revise their `confidence` flag if the advisor's own read differs.
2. Semantically dedup/merge the remaining 11 personas' findings (everything
   except spec-compliance) into one list — catch cross-persona semantic
   dupes the fingerprint hint misses (e.g. a maintainability finding and a
   correctness finding describing the same line in different words).
3. **Never alter or prune** the 4 Opus-frontline findings' substance OR their
   `confidence` flag — fold them into the merged structure unchanged.
   Frontline confidence is set once, at spawn time, and is final.

This is the only place dedup decisions get made — `fingerprint_group.py` only
proposes candidate clusters, it never merges. Spec-compliance is exempt from
all of this: it's a different contract (Report section, above), not a
quality finding subject to severity-table dedup.

## Report

Two top-level sections, always in this order:

1. **Spec compliance** — from `personas/SPEC-COMPLIANCE.md` only.
   Prose or a small table. Never merged into Findings — it's a distinct
   contract (did the diff do what was asked), not a quality axis.
2. **Findings** — every other persona's output, deduped by Stage 2,
   severity-grouped (Critical / High / Medium / Low), pipe-table:

   | severity | file:line | persona(s) | issue | fix | confidence | route |
   | -------- | --------- | ---------- | ----- | --- | ---------- | ----- |

   `persona(s)` lists every persona that raised a deduped finding. `fix` is
   each persona's own remediation (merged/shortened by Stage 2 on dedup, never
   dropped). `route` is set BY Stage 2, never by a persona — it points
   elsewhere when relevant (`/code-sec` for repo-wide security, `/diagnose`
   for a confirmed bug worth its own session), else stays blank. No
   suppression — every finding surfaces with its `confidence` label; nothing
   is auto-hidden. A clean run still emits both sections ("no findings" is
   signal, not silence).

## References

- `references/ADVERSARIAL-TECHNIQUES.md` — shared attack-technique spec, used
  by `personas/ADVERSARIAL.md` AND by fable-mode's Gate 3 (separate
  call site, see that skill). Read it before writing/using the adversarial
  persona.
- `personas/` — one file per persona (territory, what it flags,
  what it defers, its own confidence self-test, model tier).
- `scripts/fingerprint_group.py` — the dedup pre-grouping helper (Stage 2
  input, never the decision-maker).
