# Design: Index+detail file split + Goal→Epoch hierarchy (Phase deferred)

> Brainstorm output, 2026-07-21. Pipeline: /brainstorm → /grill-me → /write-plan.
> Status: draft — not yet grilled.

## Problem

`.work/PLAN.md` (61K) and `.work/FINDINGS.md` (71K) have grown unbounded because they hold
full inline content for every Goal/decision ever recorded, across every initiative this repo
has built — including work closed months ago. `TODOS.md` mixes 13 different annotation tags
inline with no structural separation. `.work/GATES.md` and `.work/PROGRESS.md` are smaller
today but follow the same append-forever pattern. None of these files shrink; they only grow,
regardless of how much of their content is live vs. historical.

Splitting by tag (e.g. routing `[BUG]` items to a separate `TRIAGE.md`) was considered and
rejected: 13 tags exist, items commonly carry 2+ tags at once, and tag-split only fixes 2-3
of them — it doesn't address the root cause (files hold full content instead of pointers).

This repo's own memory system (`~/.claude/projects/.../memory/MEMORY.md` index +
`memory/<slug>.md` detail files) already proves a working alternative: a lean index with one
line per item, full content lives in a separate per-item file. This doc adapts that pattern to
`.work/` and `TODOS.md`, with Goal staying the top planning unit.

An elastic hierarchy layer above Goal came up mid-conversation — this repo's own
memory-architecture initiative ran 16 Goals in one flat block, and code-crit already ran 9
(one over the proposed cap, see Decision 7). This is portfolio-wide tooling, not a
dotfiles-only convenience — newer projects run bigger than anything built here so far. Epoch
stays in scope for that reason: it already has a real trigger inside this repo's own history.
Phase does not — no project anywhere in the portfolio has hit that scale yet — so Phase is
**deferred to its own future `/brainstorm`**, run against a project that actually needs it
(e.g. AvaPets), instead of speculatively designed here.

## Context & constraints

**Blast radius (confirmed by grep, not assumed):**

- TODOS.md is read/written by 15+ skill files: `/handoff`, `/handoff-return`, `/close`,
  `/checkpoint`, `/dev-brief`, `/remember`, `/consolidate`, `/diagnose`, `code-sec`,
  `harness-audit`, `mutation-testing`, `dev-setup`, `encrypt`, `ante-mortem`, `codebase-design`,
  `fable-mode`, plus global `CLAUDE.md`/`MEMORY-STANDARD.md`/`MEMORY-ARCHITECTURE.md`.
- PLAN.md/FINDINGS.md/GATES.md/PROGRESS.md are read/written by `/write-plan`, `/grill-me`,
  `/sync-trello`, `session-checkpoint`, `code-sec`, `dev-brief`, `dev-setup`, `encrypt`,
  fable-mode (GATES.md specifically), `trust-but-verify`.
- `/dev-brief` reads TODOS.md's shape across every `~/dev` project, not just this one —
  a format change here must not break cross-project reads (resolved: dotfiles-only pilot,
  see Decision 3 below).
- This repo's git-crypt `.gitattributes` uses a per-file allow-list, not a wildcard (confirmed
  by reading `.gitattributes` directly — `/TODOS.md`, `/.work/FINDINGS.md`, `/.work/PLAN.md`,
  etc. individually listed). Global CLAUDE.md's rule is "everything under `.work/`, no
  exceptions" — every new file/directory this build creates (`.work/todos/`, `.work/plan/`,
  `.work/archive/`) needs coverage or it commits as **plaintext**. See Decision 8 — this is
  not optional cleanup, it's a correctness requirement for the build itself.
- `claude/.claude/hooks/fable-mode-inject.sh:13` hardcodes `gates_file="$PWD/.work/GATES.md"`
  and runs on every prompt across every project. GATES.md is a single **current-task
  pointer**, not a historical ledger (one Task header, one `Current gate: N`) — it cannot move
  to a per-Epoch path without the hook going with it. See Decision 4.

**Prior art:** `~/.claude/projects/-home-k0d3x-dev-dotfiles/memory/MEMORY.md` — lean index,
each line links to `memory/<slug>.md`. Proven pattern, direct model for this design.

**Decisions already locked via clarifying dialogue (not open questions):**

1. **Archive lifecycle inherits each file's existing close-semantics**, not one uniform rule:
   - TODOS.md → closed item's detail file moves to `.work/archive/todos/`, index line removed.
   - PLAN.md / FINDINGS.md → closed items stay in place, marked done — index becomes the
     permanent completed-work ledger (index lines are cheap even at 30+ Goals; this is the
     actual fix for PLAN.md's bloat, since it currently pays full-content cost per closed Goal).
   - GATES.md → stays live at fixed root path always (hook untouched); on **Epoch** close
     (not every task — a bare TODO/task with no Epoch has no `<epoch-slug>` to archive into,
     so its GATES.md stays ephemeral and gets overwritten by the next task, current behavior
     unchanged), a **copy** archives to `.work/plan/<epoch-slug>/GATES.md` for historical
     record — see Decision 4.
   - PROGRESS.md → same Epoch-close-only copy pattern as GATES.md, for consistency (not
     hook-bound, but no reason to diverge).
2. **Migration = cutover, no backfill (Option B of three considered).** Existing PLAN.md,
   FINDINGS.md, TODOS.md get renamed to `.work/archive/legacy-<file>.md` as read-only history.
   New index+detail structure starts empty. Rejected full-migration (heavy, transcription risk
   for content whose only value is historical) and lazy-migration (two live formats to check
   simultaneously, worse than a clean cutover).
3. **Scope: dotfiles-only pilot**, not an immediate global CLAUDE.md convention change.
   `/dev-brief` keeps reading legacy-format TODOS.md in every other `~/dev` project unchanged.
   Global rollout is a deliberate follow-up once the pattern is proven here, not part of this
   build. (Skill _logic_ — e.g. hierarchy-depth decisioning in `/write-plan` — is still global,
   since skills are portfolio-wide tooling regardless of which repo's data they operate on.)
4. **GATES.md / PROGRESS.md do not get their own top-level index+detail split, and the live
   file never moves.** Both are narrative logs scoped to one active task/project already (not
   collections of discrete addressable items the way TODOS/PLAN/FINDINGS are). `.work/GATES.md`
   stays at its fixed root path permanently — `fable-mode-inject.sh` hardcodes that path and
   runs on every prompt, so moving the live file breaks the hook. Instead: on **Epoch** close
   only (bare non-Epoch tasks have no `<epoch-slug>` to archive into — their GATES.md stays
   ephemeral, overwritten by the next task, unchanged from today), a **copy** of both files
   archives into `.work/plan/<epoch-slug>/GATES.md` and `.work/plan/<epoch-slug>/PROGRESS.md`
   for historical record. No `.work/gates/` or `.work/progress/` top-level directory.
5. **TODOS.md items are always flat top-level** (`.work/todos/`), never nested under an Epoch
   folder — a TODO can predate any Epoch and graduates INTO one only when `/write-plan` builds
   it into a Goal.
6. **Split granularity:**
   - PLAN.md → one detail file per **Goal** (matches the unit Trello sync, gate logs, and
     hand-off prompts already key on — Micro-Goal-level splitting would fragment tightly
     coupled Task/verify-step context).
   - FINDINGS.md → one detail file per **decision cluster** (one `/grill-me` session's worth,
     e.g. `CR-D10–D18` together) — same reasoning, decisions within a cluster cross-reference
     each other constantly ("D5 supersedes D2").
7. **New hierarchy: Goal → Epoch, in scope. Phase deferred to a future `/brainstorm`.**
   - **Epoch** clusters Goals for a multi-Goal initiative (e.g. code-crit's 9 Goals, or what
     memory-architecture's 16-Goal run should have been split into 2 Epochs of). In scope for
     this build — code-crit already exceeded the proposed cap once in this repo's own history,
     and this tooling is portfolio-wide, not dotfiles-only; newer/bigger projects hit
     multi-Goal scale faster than anything built here so far.
   - **Phase** clusters Epochs, for genuinely large multi-domain projects (user's example:
     AvaPets, "typically four Phases"). **Deferred** — no project anywhere in the portfolio has
     reached that scale yet, so designing it now would be speculative. Raise a separate
     `/brainstorm` for Phase once run against a project (AvaPets or similar) that actually
     needs it; the Epoch-per-Goal mechanics below carry forward as a starting point.
   - Whether to use Epoch at all is decided **at plan time by AI recommendation, user
     confirms/overrides** (Option A of three considered) — not silent heuristic auto-detection
     (risks locking in the wrong shape early) and not organic grow-then-split (retrofitting a
     grouping tier onto a running Goal set is exactly the migration pain Decision 2 already
     ruled out avoiding).
   - **Soft cap: ~8 Goals per Epoch**, checked at plan time (recommend splitting into a second
     Epoch before writing) and re-checked at `/checkpoint`/`/handoff` time if scope creep
     pushes a live Epoch past the cap (never silently — Goal renumbering touches Trello card
     IDs and gate-log references). 8 chosen because memory-architecture's real 16-Goal run is
     the one concrete data point of what should have split — 8 sits at half that.
8. **Git-crypt wildcard backstop ships as part of this build, not a follow-up.** Global
   CLAUDE.md's rule ("everything under `.work/`, no exceptions") already prescribes the fix —
   add `/.work/**/* filter=git-crypt diff=git-crypt` to `.gitattributes` (per the `encrypt`
   skill's setup flow) before any new file under `.work/todos/`, `.work/plan/`, or
   `.work/archive/` is committed. Verify with BOTH `git check-attr filter -- .work/todos/<test-file>`
   (nested) AND `git check-attr filter -- .work/GATES.md` (top-level) returning `git-crypt` —
   a `/.work/**/*` pattern that matches nested paths but silently misses top-level files must
   be caught before the first real commit lands. Note this also retroactively encrypts files
   that are plaintext today (`.work/GATES.md`, `.work/DELEGATION-MAP.md` — confirmed via
   `ls .work/` against the current allow-list): intentional, correct per "no exceptions," but
   flag it explicitly rather than let it happen as a side effect. This was flagged as "out of
   scope" in an earlier draft and corrected — it's a precondition for the build, not cleanup.

## Approaches

### A — Full index+detail split, dotfiles-only pilot, Goal→Epoch hierarchy (Phase deferred)

Everything in "Context & constraints" above, built as one coherent system: TODOS.md,
PLAN.md, FINDINGS.md get lean indexes + per-item detail files; GATES.md/PROGRESS.md stay live
at their fixed root paths (hook-safe) with archive-copies nested per Epoch on close; new
Goal→Epoch grouping is elastic per-project (AI-recommends, user confirms), 8-Goal soft cap;
Phase is not built, reserved for a future `/brainstorm`; git-crypt wildcard backstop ships
as a precondition, not a follow-up.

**Tradeoffs:** More files to manage (one per Goal/decision-cluster/TODO instead of a handful
of monoliths) and a real migration touching 15+ skill files' read/write assumptions, plus a
`.gitattributes` change that must land before the first new file is committed. In exchange:
every root file stays index-sized regardless of total content volume, closed work stays a
cheap permanent ledger instead of dead weight, the fable-mode hook is untouched (live GATES.md
never moves), and multi-Goal projects (already happened once here, at code-crit's 9 Goals)
get a grouping unit that doesn't currently exist.

### B — Index+detail split only, no Epoch layer at all

Same TODOS/PLAN/FINDINGS split, same GATES/PROGRESS live-path decision, but Goal stays the
top planning unit — no Epoch, ever, anywhere. Simpler mental model, smaller build (skips the
hierarchy-decision logic in `/write-plan`, skips any future Trello-sync extension for
Epoch→board grouping).

**Tradeoffs:** Solves the file-bloat problem but not the "PLAN.md is actually N concatenated
unrelated initiatives" problem — a 16-Goal run like memory-architecture stays one flat
sequence with no way to say "these 8 Goals are one thing, those 8 are another." This isn't
hypothetical for a future project — code-crit already ran 9 Goals in this repo, one over the
proposed cap. Cheaper now, but the need is already demonstrated, not speculative.

### C — Prune/archive only, no structural split

Don't change the format at all — periodically move closed content out of PLAN.md/FINDINGS.md
into dated archive files (`.work/archive/PLAN-2026-Q2.md`), keep everything else as-is.
Minimal build, zero blast radius to other skills' read/write logic.

**Tradeoffs:** Cheapest option, but doesn't fix the root cause — files still hold full inline
content, they just get cut off periodically. Multi-tag TODOS.md items are still unaddressed.
No Epoch/Phase capability at all. This is closer to "delay the problem" than "solve it."

## Recommendation

**A** — B undersells a problem this repo's own PLAN.md history already demonstrates: 28 Goals
across three unrelated initiatives concatenated with no grouping, and one of those initiatives
(code-crit, 9 Goals) already exceeded the proposed 8-Goal cap. C doesn't touch the root cause
at all — files still hold full inline content, just truncated periodically. A's blast radius
is real (15+ skill files, a `.gitattributes` change, a live migration) but it's bounded
deliberately: dotfiles-only pilot, cutover-not-backfill, hook left untouched, Phase excluded
until a project actually needs it.

## Open questions → for /grill-me

- Exact index-line schema for each file type (TODOS.md: tags + title + pointer — what else?
  PLAN.md/FINDINGS.md: what fields beyond title + pointer + status?).
- Slug/filename convention for detail files (topic-derived vs. sequential ID vs. both).
- Exact `.work/` directory tree end-state (this doc describes the shape; `/write-plan` or a
  follow-up needs the literal paths nailed down, including where Epoch folders live relative
  to `.work/plan/` and how a Goal that hasn't been assigned an Epoch yet is filed).
- `/sync-trello`'s mapping needs an Epoch tier decision: does Epoch become a Trello list, a
  card-group, or stay untracked in Trello entirely (Goal stays the card unit)?
- Migration mechanics for the cutover itself: exact steps/script (if any) to rename existing
  files to `.work/archive/legacy-*.md`, add the `.gitattributes` wildcard, verify it with
  `git check-attr` before the first commit, and initialize the new empty structure — plus
  which skill (if any) is updated first vs. last to avoid a broken intermediate state.
- Does `/write-plan`'s AI-recommends-Epoch logic need an explicit sizing rubric (e.g. "under 3
  Goals: flat, 3+: recommend Epoch") or is prose judgment sufficient without a numeric table?
- Should the existing global CLAUDE.md File Taxonomy table get a forward-looking note now
  (without changing the convention itself) flagging that a dotfiles-only pilot is in flight,
  so a future session doesn't rediscover this from scratch?
- **Pilot-vs-Epoch-justification tension:** Decision 3 scopes this to a dotfiles-only pilot,
  and Decision 2 is cutover-no-backfill — code-crit's 9 existing Goals go to
  `legacy-archive`, not into a live Epoch. So the pilot can exercise, at most, single-Epoch
  containment (this build's own Goals, if `/write-plan` produces enough of them) — it cannot
  exercise the 8-Goal cap-split or multi-Epoch coordination, which ship on faith same as Phase
  does. Is cap-split logic actually in scope for this build, or does it defer alongside Phase
  until a real multi-Epoch case exists to test against?
- **Read-pattern sizing (unverified assumption):** the grep in Context & constraints proved
  these files are _touched_ by 15+ skills, not _how_ they're read. If a skill currently reads
  PLAN.md/FINDINGS.md whole rather than index-then-open-one-detail-file, its active-content
  reads gain indirection instead of shrinking. Before committing to the build, check how
  `/write-plan`, `/grill-me`, `session-checkpoint`, and `dev-brief` actually consume these
  files today, and size whether the bloat-avoidance win clears that cost.
