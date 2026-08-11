# ADR-0002: code-mode replaces fable-mode

- Status: accepted
- Date: 2026-08-10

## Context

`fable-mode` was a strong but artifact-agnostic method skill: a five-gate task loop
(spec → evidence → adversarial review → verification → report) plus standing habits,
applicable to any hard task. Alongside it, `chore/code-quality-refs` (merged into
`main`) built a large code-quality substrate — `references/code/` (standards,
principles, testing, anti-patterns, 12 language files), the `code-*` skill family
(`code-crit`, `code-decay`, `code-sec`), and a mechanical enforcement layer
(`standards_guard.py`, `code_standard_lint.py`, `code_formatter.py`,
`gate3_skip_detector.py`). The two were barely wired together.

fable-mode was already drifting code-ward on its own: its Gate 3 delegated to
`/code-crit` and borrowed `code-crit/references/ADVERSARIAL-TECHNIQUES.md` as its
attack core, and its Gate 4 was "deliberately stricter than the source" because
running the real test after an edit was Fable's weakest measured habit. That's a
coding habit, justified by coding evidence, sitting inside a general-purpose skill.

**Wording correction, carried from the source finding doc:** an earlier draft of
this rationale said "Fable 5 is retiring, so a skill built on its identity is not
the durable form." That misnamed the subject — it's the `fable-mode` **skill**
being retired by this decision (self-referential: replaced by code-mode), not the
Fable 5 **model**, which is live and unrelated. The independent evidence above
(Gate 3's `/code-crit` delegation, Gate 4's coding-specific habit data) holds either
way; the wording was simply wrong about what was ending.

## Decision

Replace `fable-mode` with `code-mode`: one method skill, gates rewritten around the
code lifecycle, routing into the code-quality/security substrate that already
exists, rather than restating it. `code-mode` is Claude-only (ADR-0001 permits
runtime-only skills) — no `codex/.codex/skills/code-mode/` counterpart exists.

**Single skill, not a sibling pair.** The two-skill split (a slim general-purpose
`fable-mode` kept alongside a new code-specific skill) was considered and rejected:
it costs description-boundary engineering (which skill fires on an ambiguous
prompt), duplicate markers/hooks/tests, and roughly 200 duplicated lines across the
two SKILL.md files — and buys only that non-code tasks skip about 1.5k tokens of
code-specific routing they'd otherwise load unused. `code-mode` instead carries a
short (~10-line) non-code fallback: the five gates still apply to docs/config/prose
work, skipping only the route table, red-green inner loop, and code-specific
smells. That fallback is cheap enough that a second skill isn't worth its
maintenance cost.

**Archive, not delete.** `fable-mode`'s dirs moved to `docs/archive/skills/`
(`fable-mode/` and `fable-mode-codex/`) rather than being deleted, so the prior
method skill can be compared against or restored if code-mode's coding-lifecycle
reorientation turns out to regress general-task handling. Archiving happened only
after code-mode was built, wired into the harness, and verified working
end-to-end — never before, so there was a working method skill live throughout the
transition.

## Consequences

- One method skill to maintain instead of two; no description-boundary ambiguity
  between "general hard task" and "coding task" triggers.
- Gate 4's three-rung ladder (`/trust-but-verify` → spec check → `/run`) is now
  named and required where fable-mode collapsed rungs 1–2 into one bullet and never
  mentioned rung 3 at all — the single largest behavioral change from the rewrite.
- Gate 1 gained a full route table (`/tdd`, `/diagnose`, `/code-refactor`,
  `/code-decay`, `/requirements`→`/architecture`, `/brainstorm`→`/grill-me`→
  `/write-plan`, `/threat-model`, `/prototype`) that fable-mode never had, since it
  wasn't scoped to code work specifically.
- Non-code tasks (docs, config, prose) get a thinner method-skill experience than
  fable-mode gave them — the ~10-line fallback, not the full general-purpose
  treatment. Accepted per the single-skill tradeoff above.
- `install.sh`'s claude/codex skill-symlink loops were add-only and never pruned a
  symlink whose skill dir was renamed or removed. This surfaced concretely during
  the transition: `code-mode`'s live symlink was never created, and `fable-mode`'s
  went dangling after archiving, until both were hand-patched mid-session. Fixed as
  part of this work (`install.sh`: dangling-only prune via `find -xtype l -delete`
  before each linking loop, deliberately never a "not in the tracked source list"
  prune — that broader rule would delete externally-managed links like `kos*`,
  `ast-grep`, `find-skills`, which `install.sh` doesn't own).
- The ownership manifest (`tests/test_skill_architecture.py`, per ADR-0001) required
  a two-part edit — add `code-mode` to `CLAUDE_ONLY`, drop `fable-mode` from
  `RUNTIME_SPECIFIC` — that could not land as one change: `fable-mode`'s directories
  were still physically live on both runtimes when `code-mode` was added, so
  applying both edits together would have failed the ownership-catalog assertion on
  both sides at once. The additive half (`code-mode` → `CLAUDE_ONLY`) landed
  immediately; the `fable-mode` removal was deferred to the same commit as the
  actual directory moves, where the manifest and the filesystem state changed
  together. A manifest edit must always describe physical reality at every commit,
  not physical reality once every other edit in a plan eventually lands.

## Alternatives considered

- **Two skills (general `fable-mode` + code-specific skill).** Rejected — see
  single-skill rationale above.
- **Edit `fable-mode` in place, no rename.** Rejected — the skill's identity and
  provenance (Fable-specific framing in `references/fable-patterns.md`, the AGPL
  boundary note, `fable-score.py`) don't describe what the rewritten gates actually
  are once every gate is reoriented around the code lifecycle. A rename makes the
  skill's scope legible from its name rather than its history.
- **Delete fable-mode outright instead of archiving.** Rejected — archiving costs
  nothing (git history retains it either way) and keeps a working fallback
  reachable during and immediately after the transition, before code-mode had been
  run against a real task.
