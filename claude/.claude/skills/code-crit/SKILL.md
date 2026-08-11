---
name: code-crit
description: Structured code review using parallel Agent-spawn personas, binary verified/unverified confidence, and a Spec-plus-severity report. Two modes — fast (default, Sonnet-tier mega-spawn) and thorough (every persona fully isolated). Use for "review this diff/branch/PR", "code review", "review my changes", "thorough code-crit" — NOT the built-in `/code-review ultra` command (different tool, do not confuse).
---

# code-crit

**Not `/code-review` or `/code-review ultra`** — those are built-in Claude Code
commands (cloud ultrareview). This skill is `/code-crit`, a local peer, not a
replacement wired to that name.

## Mode detection

Two modes. Detect in this order, first match wins; default when nothing
matches:

1. **Explicit arg**: the literal token `thorough` anywhere in the invocation
   args → thorough; strip it before diff-resolution. Every other arg (PR#,
   branch name, or nothing) is diff-resolution input, not a mode signal —
   `/code-crit thorough 42` and `/code-crit 42 thorough` both mean "thorough
   mode, diff = PR 42." No `thorough` token anywhere → fast.
2. **Natural-language keyword**: invocation text contains "thorough" or
   "deep" alongside a review request (e.g. "run a thorough code-crit", "do a
   deep review") → thorough. Deliberately excludes "full" — "review the full
   diff"/"full changeset" is ordinary fast-mode phrasing, not a thoroughness
   signal, and step 3 forbids guessing thorough from ambiguous wording.
3. **Default**: **fast**. Never guess thorough from ambiguous phrasing —
   thorough is real token cost (isolated per-persona), so an unclear
   invocation must fall through to fast, not silently spend the expensive
   mode.

State which mode ran at the top of the Report (below).

- **fast** — Sonnet-tier personas run as one mega-spawn (cheap, some
  cross-persona blind-spot-correlation risk accepted — CR-D16). This is the
  common-path default; Goal 28's whole purpose is paying this cost instead
  of the isolated one.
- **thorough** — every persona (Opus 4 + Sonnet 8, 12 total) runs as its own
  fully isolated spawn, no shared context anywhere. Strictly more thorough:
  isolation means one persona's blind spot can't propagate to or suppress
  another's finding, which shared-context batching can't guarantee. Real
  cost: ~12 separate spawns instead of 5 (4 Opus + 1 mega). Use when you
  want maximum coverage and are willing to pay for it (e.g. a pre-release
  pass), not as the everyday mode.

## Quick start

1. Resolve mode (above).
2. Resolve the diff: explicit PR#/branch arg, else `git diff` against the
   diff-base (default: the branch's merge-base with `main`).
3. Spawn all 5 always-on personas + any conditional personas whose trigger
   matches (Dispatch, below) — dispatch shape depends on mode.
4. Run the Stage-2 Opus advisor pass (Synthesis, below).
5. Emit the report (Report, below).

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

**Opus frontline (4 separate isolated spawns, both modes, identical):**
**correctness, security, spec-compliance, adversarial** —
miss-is-unrecoverable territory (SQLi, null-deref, a Spec mismatch that
ships the wrong thing). Context never shared across these 4, so
cross-persona agreement at Stage 2 reflects independent reasoning, not
shared framing.

- `prompt`: the diff + the full contents of that persona's file + this
  instruction: "Set your own `confidence: verified | unverified` per your
  file's self-test criteria. Return findings as `file:line | severity | issue
| confidence | fix`." Personas never set `route` — that's assigned at Stage
  2 synthesis, once the merged finding is placed relative to the other tools
  it might belong to (`/code-sec`, `/diagnose`, etc). Personas don't self-tag
  `persona` — the orchestrator already knows which persona name each spawn
  was (see Synthesis's canonical-record step).
- `model: opus`, `run_in_background: false` — wait for all 4 before Stage 2.

**Sonnet tier — dispatch shape forks on mode.** Whichever of
maintainability, testing, project-standards, performance, reliability,
api-contract, data-migration, agent-native matched (3-8 of the 8, per-diff).

**fast mode — one Agent mega-spawn call, not one-per-persona.** All matched
persona files' full contents are concatenated into a single `Agent` prompt
alongside the diff, pasted once — not once per persona. This is a real,
accepted coverage tradeoff, not a free lunch: batching these personas into
one shared context trades some cross-persona blind-spot-correlation risk (a
finding that only surfaces from one persona's isolated framing may never
come up when all matched personas reason in the same shared context) for
real token savings (diff pasted once instead of up to 8x). Stage-2 dedup
does NOT recover a finding this mega-spawn never generated in the first
place — dedup only removes duplicates among findings that exist. The
tradeoff is accepted because the 4 Opus-frontline personas — the
miss-is-unrecoverable ones — stay fully isolated regardless of mode; this
tier is where a miss is comparatively low-consequence.

- `prompt`: the diff + the full contents of every matched Sonnet-tier
  persona file, each clearly labeled by persona name + instructed to tag its
  own findings with `persona: <name>` + set its own `confidence:
verified | unverified` per that persona's self-test criteria. Also
  instructs: write the full findings (one JSON object per finding — `file`,
  `line`, `title`, `persona`, `severity`, `confidence`, `fix`) to
  `.work/scratch/code-crit-sonnet-findings.json`, and return ONLY that file
  path in the spawn's response — never the findings text itself. This keeps
  the mega-spawn's own response cheap regardless of how many findings the
  matched personas produce.
- `model: sonnet`, `run_in_background: false`.
- If the mega-spawn's response isn't a valid path to a parseable JSON file
  (malformed write, spawn error, etc.), do not retry — proceed to Synthesis
  with the Sonnet tier marked failed (see Report, below). No retry: a second
  attempt in a fresh context is no more likely to succeed than the first,
  and retrying silently would hide a real failure from the report.
- **CWD note:** the mega-spawn's scratch path is repo-relative
  (`.work/scratch/...`). code-crit runs against whatever repo the caller's
  CWD is in — the mega-spawn and the orchestrator share that CWD, so the
  relative path round-trips within a single run. This is per-run scratch,
  gitignored in every repo the same way (add `/.work/scratch/` to that
  repo's `.gitignore` if code-crit is run there for the first time and the
  entry is missing).

**thorough mode — one isolated Agent spawn per matched persona** (identical
shape to the Opus frontline, just `model: sonnet`): each matched persona
gets its own spawn, `prompt` = diff + that persona's file contents + the
same confidence/pipe-format instruction as the Opus frontline above, no
concatenation, no shared context, no scratch file. `run_in_background:
false` for all. This is the maximally-isolated shape — no Sonnet-tier
mega-spawn step exists in this mode, so the JSON-scratch-file path and its
failure-marker (below) never apply.

## Synthesis (Stage 2 — Opus advisor pass)

One final `Agent` spawn, `model: opus`, after every persona spawn returns.

**Canonical record — build this first, before grouping, from whichever raw
shapes this run produced.** `fingerprint_group.py`'s `Finding` needs `file`,
`line`, `title`, `persona` (script's own field names). The raw spawn outputs
don't already agree on this shape, so the orchestrator normalizes every
finding into `(file, line, title, persona, severity, confidence, fix)`
before anything else:

- **Any isolated spawn's output** (Opus frontline, both modes; Sonnet tier
  in thorough mode) — inline pipe rows, field named `issue`, no `persona`
  field. Map `issue` → `title`; set `persona` to that spawn's own known
  persona name (the orchestrator dispatched it, so this is never
  ambiguous — no self-tagging needed).
- **Sonnet mega-spawn JSON** (fast mode only) — already carries `title` and
  `persona` per object; use as-is.

Only after this normalization does grouping happen.

**Input:** the 4 Opus-frontline canonical records (both modes) + the
Sonnet-tier canonical records — from 8 isolated spawns in thorough mode, or
from `.work/scratch/code-crit-sonnet-findings.json` in fast mode (the
mega-spawn's own response is just that path, never the findings text) —
EXCEPT `spec-compliance`'s (spec-compliance findings never enter
dedup/synthesis — they go straight to the Report's Spec section, untouched).
Build `scripts/fingerprint_group.py`'s candidate-dupe clusters over that
same subset (`file + line±3 + normalized-title` — a pre-grouping HINT, not a
decision) from the canonical records; keep the full records for the report
table.

If running in fast mode and the Sonnet-tier JSON file is missing or fails to
parse (mega-spawn failure, see Dispatch above), proceed with only the 4
Opus-frontline findings as input — do not block Synthesis on a failed tier,
and do not fabricate Sonnet-tier findings. Carry the failure forward into
the Report (below) as an explicit marker, never a silent empty section. This
failure mode does not exist in thorough mode (no mega-spawn to fail).

**Responsibilities:**

1. Refine the Sonnet-tier findings (maintainability, testing,
   project-standards, performance, reliability, api-contract, data-migration,
   agent-native) — rerank, prune weak ones, and may revise their `confidence`
   flag if the advisor's own read differs. **In both modes** — this step's
   trigger is model tier (Sonnet is the lower-trust model, checked
   regardless of isolation), not shared-vs-isolated context. Pre-Goal-28
   thorough-equivalent behavior refined these findings even though every
   persona was already isolated; fast mode's shared context is an additional
   reason for scrutiny on top of that, not the only reason.
2. Semantically dedup/merge all remaining personas' findings (everything
   except spec-compliance) into one list — catch cross-persona semantic
   dupes the fingerprint hint misses (e.g. a maintainability finding and a
   correctness finding describing the same line in different words).
3. **Never alter or prune** the 4 Opus-frontline findings' substance OR their
   `confidence` flag, in either mode — fold them into the merged structure
   unchanged. Frontline confidence is set once, at spawn time, and is final.

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

   State the mode that ran (fast or thorough) at the top of the report. In
   **fast** mode, if the Sonnet-tier mega-spawn failed to parse (Dispatch
   above), the Findings section opens with an explicit line — "Sonnet-tier
   mega-spawn failed — the N matched Sonnet-tier personas are not
   represented this run" (N = however many personas matched this diff, not
   a fixed count) — never an indistinguishable empty section; a failed tier
   and a clean tier must never look the same to the reader. This failure
   mode cannot occur in **thorough** mode (no mega-spawn exists there).

## References

- `references/ADVERSARIAL-TECHNIQUES.md` — shared attack-technique spec, used
  by `personas/ADVERSARIAL.md` AND by code-mode's Gate 3 (separate
  call site, see that skill). Read it before writing/using the adversarial
  persona.
- `personas/` — one file per persona (territory, what it flags,
  what it defers, its own confidence self-test, model tier).
- `scripts/fingerprint_group.py` — the dedup pre-grouping helper (Stage 2
  input, never the decision-maker).
