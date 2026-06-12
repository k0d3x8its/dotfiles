# Spec: Four Superpowers-derived skills

> Adapted (not copied) from `obra/superpowers`. Revised 2026-06-12 after gap analysis.
> Built on `feature/super-skills`. Commit + push, no PR.

## Pipeline

brainstorm → grill-me (existing) → write-plan → task_plan.md (existing format) →
sync-trello (existing, **optional**) → tdd/build → trust-but-verify (gate) +
review-response (rail) → /close | /checkpoint (existing).

Does NOT duplicate existing `tdd`, `diagnose`, `write-a-skill`, `grill-me`, `dev-brief`,
`sync-trello`, `session-*` skills.

## Conventions

- Skills live in `claude/.claude/skills/<name>/SKILL.md`, auto-discovered — no
  settings.json registration.
- Frontmatter: kebab-case `name` + verb-forward `description` with "Use when …" triggers;
  "Maps to the [TAG] TODO tag" where one applies. Voice mirrors `diagnose`/`sync-trello`.
- Sub-files referenced by backtick absolute path (`~/.claude/skills/<name>/detect.md`).
- Recommendation-first: every user choice leads with a recommendation + one-line why.
- Project-agnostic — no hardcoded dotfiles paths. Artifacts (design docs, plans, findings)
  land in the TARGET project.
- Build gotcha: Edit/Write refuse symlinks — write repo paths under
  `dotfiles/claude/.claude/`, never `~/.claude/`.

## The four skills

### 1. `brainstorm` (+ `templates/design-doc.md` — named to leave `DESIGN.md` free for future html/infographic work)

Generative design only. Explore context → clarifying questions ONE at a time
(recommendation-first) → 2-3 approaches with tradeoffs + recommendation → write
`docs/brainstorm/<topic>-YYYY-MM-DD.md` in the target project → self-review → hand off
to `/grill-me`. Never interrogates (grill-me's job). Template uses `{{TOKEN}}`
substitution (dev-setup style): Problem, Context, Approaches+tradeoffs, Recommendation,
Open questions → for grill-me.

**Disambiguation (revised):** `pm-product-discovery:brainstorm` = product ideation (no
overlap); `ce-brainstorm` = requirements doc, overlapping function but no pipeline.
Description must claim "entry point of the brainstorm → grill-me → write-plan pipeline;
technical design, not product ideation, not a requirements doc" so routing favors this
skill for design work.

### 2. `write-plan`

Reads design doc + `findings.md` → emits `task_plan.md` in Goal / Micro-Goal / Task
structure, reusing `~/.claude/skills/dev-setup/templates/task_plan.md` so `sync-trello`
and `dev-brief` consume it unchanged. Tasks MUST sit under a Micro-Goal.

**Prove-command convention (revised):** each Task carries an indented, non-checkbox
sub-bullet:

```markdown
- [ ] Task text
  - verify: `command that proves it`
```

sync-trello only parses `- [ ]`/`- [x]` lines, so verify sub-bullets never reach Trello —
zero sync-trello changes. trust-but-verify reads them per-task. Machine-unverifiable
tasks get `verify: manual — [UX] checklist`.

Ends by **offering** `/sync-trello` (optional, recommendation + why).

### 3. `trust-but-verify` (+ `detect.md`)

Gate: before any done/works/fixed claim, before `git push`, before a PR, before any
subagent/user handoff or `/close` | `/checkpoint` | `/handoff` | `/handoff-return`
(revised: real aliases, `/handoff-return` added) — run the project's verify command
FRESH, read exit code, only then claim. NOT before commits (cheap WIP). Unproven claim →
`[VERIFY]` TODO. Machine-unverifiable claim → `[UX]` checklist handoff (revised: escape
hatch, no eternal [VERIFY] loop).

`detect.md` resolves the verify command project-agnostically, priority order:

1. Project CLAUDE.md/KNOWLEDGE.md explicit command
2. Makefile / justfile / package.json scripts (test, check, lint, verify targets)
3. `.github/workflows/*.yml` `run:` lines — **skipping setup/install steps** (revised:
   step names matching install/setup/cache/checkout; commands led by apt-get, brew,
   npm install/ci, pip install)
4. Tool-presence fallback (bats/shellcheck, pytest/unittest, cargo, go)

**Caching (revised):** resolve once per session per project; re-resolve only on miss.

In the dotfiles repo this resolves at priority 1 (revised: explicit command added to repo-root
`KNOWLEDGE.md`): `shellcheck install.sh && bats --tap tests/ && python3 -m unittest
discover -s tests -p "test_*.py" -v`.

### 4. `review-response`

Rail for INCOMING review/CI feedback (counterpart to code-review, which GIVES review):
read fully without reacting → restate → verify each suggestion against actual code →
judge fit for THIS codebase → fix OR reasoned pushback (no performative "great point!") →
implement ONE item at a time. **Verification of each item goes through the
trust-but-verify gate** (revised: no duplicate verification logic). Routes: bugs →
`[BUG]`/`/diagnose`; test gaps → `[TEST]`/`/tdd`; fix-claimed-unverified → `[VERIFY]`
(revised: third route).

## CLAUDE.md changes (`claude/.claude/CLAUDE.md`)

- **Priority tag table (revised):** add `[VERIFY]` row, tier Critical — mirrors `[TEST]`
  ("claimed-but-unverified work is the same risk class"). Note line becomes: `[TEST]` and
  `[VERIFY]` are always Critical and override other priority tags.
- **Annotation tag table:** add `[VERIFY]` | Claimed-but-unverified work — needs fresh
  evidence before closing | Use `/trust-but-verify`.
- **Session rule (≤2 lines, revised):** trust-but-verify reflex — before
  done/push/PR/handoff claims, run detected verify command fresh; unproven →
  `[VERIFY]` TODO; unverifiable → `[UX]`. SKILL.md stays invokable (no
  disable-model-invocation).
- **Skills Available list (revised):** add `/brainstorm` `/write-plan`
  `/trust-but-verify` `/review-response`, backfill missing `/grill-me`.
- **File Taxonomy (revised):** add row — design docs (approaches + tradeoffs +
  recommendation) → `docs/brainstorm/<topic>-YYYY-MM-DD.md` via `/brainstorm`.

## Also

- Repo-root `KNOWLEDGE.md`: add explicit verify command entry (revised — makes detect.md
  priority 1 fire; avoids dirty global KNOWLEDGE.md).
- Dated `CHANGELOG.md` entry under `[Unreleased]`, `/changelog` convention, written after
  commits so hash links resolve (revised).

## Verify before pushing

1. Each SKILL.md frontmatter parses as YAML (python3 + yaml).
2. `grep '\[VERIFY\]'` shows it in priority table, annotation table, and session rule.
3. CI green: `shellcheck install.sh && bats --tap tests/ && python3 -m unittest discover
   -s tests -p "test_*.py" -v`.
4. `write-plan` output structure matches `dev-setup/templates/task_plan.md` hierarchy.

Then commit (one file per commit, conventional messages, no Co-Authored-By) on
`feature/super-skills` (revised: replaces conflicting `claude/brainstorm` /
`claude/superpowers-skills-review-5oyfw1` names; matches branch conventions) and push.
No PR.
