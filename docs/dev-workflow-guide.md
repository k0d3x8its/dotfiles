# K0d3x Dev Workflow Guide

> Claude Code · Session Management · Project Efficiency

---

## Part 1 — Install Everything

### 1. Dotfiles (bootstrap)

```bash
git clone git@github.com:k0d3x8its/dotfiles.git ~/dev/dotfiles
cd ~/dev/dotfiles
chmod +x install.sh
./install.sh
```

This wires:

- `bash/.bashrc` → `~/.bashrc`
- `git/.gitconfig`, `git/.gitignore_global` → `~/.gitconfig`, `~/.gitignore_global`
- `claude/.claude/CLAUDE.md`, `settings.json`, `hooks/`, `references/` → `~/.claude/`
- All skills in `claude/.claude/skills/*/` → `~/.claude/skills/`
- `scripts/update-triage`, `update-cache`, `rotate-log` → `~/.local/bin/`
- `scripts/trueline.sh` → `~/dev/trueline.sh`
- Ghostty sidebar config + autostart

Pass `--packages` to also install apt packages from `packages.txt`.

### 2. Manual steps after install

| Step            | Command                                                       |
| --------------- | ------------------------------------------------------------- |
| kos skills      | `npx skills install kos`                                      |
| Particle CLI    | `npm install -g particle-cli && particle login`               |
| Antigravity     | Has its own CLI installer — see https://antigravity.dev       |
| Ghostty sidebar | `sudo nala install xdotool` (required for window positioning) |

### 3. Plugins (inside a Claude Code session)

```bash
# Caveman (terse response mode) — active, heavy daily use

/plugin marketplace add JuliusBrussee/caveman
/plugin install caveman@caveman

# Compound engineering (code review agents) — active use

/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering@compound-engineering-plugin

# PM skills (5 plugins, one marketplace) — installed but currently DISABLED (unused)

/plugin marketplace add phuryn/pm-skills
/plugin install pm-toolkit@pm-skills
/plugin install pm-product-strategy@pm-skills
/plugin install pm-product-discovery@pm-skills
/plugin install pm-go-to-market@pm-skills
/plugin install pm-execution@pm-skills
```

### 4. Status Bar

`combined-statusline.sh` is already wired in `settings.json`. It outputs two lines on every response:

```
🤖 Sonnet 5 | 💰 $0.12 session / $0.84 today | 🔥 $0.08/hr | 🧠 18k (9%)
[CAVEMAN full] ⏱  23m   5hr ███░░░░░░░ 32%  wk ██░░░░░░░░ 18%
```

Line 1: live cost/burn/context from ccusage
Line 2: caveman badge (blank if off) + session elapsed timer + 5hr/weekly rate-limit
bars, all on one row — timer flips to `⚠️ 45m — run /handoff soon` at 45 min,
`🚨 55m — /handoff NOW (cache TTL ~5m)` at 55 min

---

## Part 2 — Global CLAUDE.md

Lives at `~/.claude/CLAUDE.md` (symlinked from `claude/.claude/CLAUDE.md` in this repo). Loaded every session globally. Edit the dotfiles source — changes sync automatically.

Sections it carries (read the file itself for current content — reproducing it here would just drift again):

- **Skills Available** — slash-alias index; full descriptions come from the harness's own per-session skill listing, not restated here
- **Session Rules** — session-timer/handoff-tool routing, standing read-first rules (`.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `KNOWLEDGE.md`), code-quality read-before-writing rule, trust-but-verify reflex, TDD-by-default for new features, ambiguity-handling rules
- **TODO Tags** — Priority tags (tier routing) + Annotation tags (which skill/mode a tag routes to)
- **My Conventions** — commit format/granularity, git-crypt commit-message rule, branch naming, Trello Kanban columns, comment policy
- **File Taxonomy** — the canonical "what fact goes where" table, including the index+detail planning-format note (see Part 4)

(Trello Sync Rules used to live here too — moved into `sync-trello/SKILL.md` 2026-08, so it's no longer one of this file's sections.)

---

## Part 3 — Skills Reference

Custom skills are authored under `dotfiles/claude/.claude/skills/<name>/` and symlinked to `~/.claude/skills/<name>/` by `install.sh` — a skill created loose under `~/.claude/skills/` directly is untracked and gets lost on reinstall. KOS-specific skills are installed separately via `npx skills install kos`.

### Design & Planning Pipeline

Idea → shippable plan, in order. Each stage hands off to the next; skip stages for small work.

| Skill           | Input                                | Output                                                                                 | Use when                                                                              |
| --------------- | ------------------------------------ | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `/brainstorm`   | rough idea                           | `docs/brainstorm/<topic>-YYYY-MM-DD.md` (2-3 approaches + tradeoffs + recommendation)  | Starting a feature from a vague idea; need to explore approaches before committing    |
| `/grill-me`     | a plan or design doc                 | resolved decisions in `.work/FINDINGS.md`                                              | Stress-testing a plan before building — resolves open branches one at a time          |
| `/requirements` | resolved design                      | numbered, testable FR/NFR spec at `docs/REQUIREMENTS.md` (git-crypt)                   | Formalizing a resolved design into a spec before architecture/planning                |
| `/architecture` | `docs/REQUIREMENTS.md`               | living `docs/ARCHITECTURE.md` (components, interfaces, data flow, FR/NFR traceability) | System needs a design doc before `/write-plan`; edited in place as the system evolves |
| `/write-plan`   | grilled design + `.work/FINDINGS.md` | `.work/PLAN.md` (Goal/Micro-Goal/Task, every Task carries a verify command)            | Turning a resolved design into an executable plan                                     |
| `/sync-trello`  | `.work/PLAN.md`                      | Trello cards/checklists/items                                                          | A Goal is ready to track on the board                                                 |

`/write-plan` offers a `/threat-model` design review mid-flow when the plan has a security surface, then offers `/sync-trello` at the end.

---

### Build & Verify Pipeline

Plan → shipped code, in order. Operates on a scoped Task from `.work/PLAN.md` — everything here assumes planning already happened. Splinters trigger off named conditions and either rejoin the spine or, when the output is unscoped signal rather than a scoped fix, exit to `/write-plan` instead.

**Pre-loop entries** — feed into `/write-plan`, before the spine starts:

```
                              ┌─────────────────────┐
┌───────────────────────┐     │     /prototype      │
│       /zoom-out       │     │ (spike UI look/feel │
│ (map unfamiliar code) │     │   or data model)    │
└───────────────────────┘     └─────────────────────┘
            │                            │
            └─────────────┬──────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ /write-plan │
                   └─────────────┘
```

**The spine** — a scoped Task runs straight through, left to right. Splinters (below) attach and rejoin at `/tdd`:

```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐     ┌─────────────────────┐     ┌─────────────┐     ┌───────────────────┐
│    /tdd     │     │  /code-crit   │     │  /code-refactor │     │  /trust-but-verify  │     │ commit / PR │     │ /review-response  │
│ (red-green, │ ──► │ (review only, │ ──► │  (fix smells,   │ ──► │  (fresh verify-cmd, │ ──► │             │ ──► │ (incoming PR/CI   │
│  per Task)  │     │   no edits)   │     │  test-gated)    │     │  exit code checked) │     │             │     │  feedback)        │
└─────────────┘     └───────────────┘     └─────────────────┘     └─────────────────────┘     └─────────────┘     └───────────────────┘
       ▲
       │  splinters below attach and rejoin here
```

**Splinter: `/diagnose`** — rejoins the spine at `/tdd`:

```
     ┌────────────────────────────┐
     │            /tdd            │
     │ (red-green loop, per Task) │
     └────────────────────────────┘
                    │  red test won't resolve,
                    │  or a [BUG] TODO
                    ▼
┌───────────────────────────────────────┐
│               /diagnose               │
│     (reproduce -> hypothesise ->      │
│ instrument -> fix -> regression test) │
└───────────────────────────────────────┘
                    │  regression test written
                    ▼
     ┌────────────────────────────┐
     │   /tdd  <-- rejoins here   │
     │ (red-green loop, per Task) │
     └────────────────────────────┘
```

**Splinter: `/mutation-testing`** — rejoins the spine at `/tdd`:

```
      ┌────────────────────────────┐
      │            /tdd            │
      │ (red-green loop, per Task) │
      └────────────────────────────┘
                     │  test suite goes green
                     ▼
         ┌──────────────────────┐
         │  /mutation-testing   │
         │ (introduces mutants, │
         │   finds survivors)   │
         └──────────────────────┘
                     │  emits [TEST] TODOs,
                     │  one per surviving mutation
                     ▼
┌──────────────────────────────────────────┐
│ /tdd  <-- rejoins here, fixes survivors  │
│       (red-green loop, per Task)         │
└──────────────────────────────────────────┘
```

**Splinter: `/code-decay` + `/ante-mortem`** — do NOT rejoin this loop. They trigger off shipped code, not off an in-flight Task, and their output is unscoped signal that needs a fresh planning pass:

```
               ┌───────────────────┐
               │    commit / PR    │
               │  (shipped code —  │
               │ periodic trigger, │
               │   not per-Task)   │
               └───────────────────┘
                         │
           ┌─────────────┴──────────────┐
           │                            │
┌─────────────────────┐      ┌─────────────────────┐
│     /code-decay     │      │    /ante-mortem     │
│ (churn x complexity │      │    (hypothetical    │
│  hotspot ranking)   │      │    post-mortems,    │
└─────────────────────┘      │ hardening findings) │
                              └─────────────────────┘
           │                            │
           └─────────────┬──────────────┘
                         │ unscoped signal,
                         │ needs triage
                         ▼
            ┌─────────────────────────┐
            │       /write-plan       │
            │    (new Goal/Task —     │
            │ starts a NEW spine run) │
            └─────────────────────────┘
```

| Skill               | Input                                                              | Output                                              | Use when                                                                                       |
| ------------------- | ------------------------------------------------------------------ | --------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `/zoom-out`         | unfamiliar file/module                                             | module map + caller graph                           | dropped into code you didn't write or haven't touched in a while — skip if you already know it |
| `/prototype`        | design question (logic OR UI look/feel)                            | throwaway spike, `_`-prefixed                       | unsure which data model or UI direction to commit to                                           |
| `/tdd`              | a Task from `.work/PLAN.md`                                        | failing test → passing code, red-green loop         | any `[TEST]` TODO or feature work needing coverage first                                       |
| `/diagnose`         | red test or `[BUG]` TODO                                           | root cause + fix + regression test                  | splinters from a failure; rejoins at `/tdd`                                                    |
| `/mutation-testing` | green test suite                                                   | `[TEST]` TODOs for surviving mutations              | after green, to verify coverage is meaningful not just present; rejoins at `/tdd`              |
| `/code-crit`        | a diff/branch/PR                                                   | Spec-vs-Standards severity report, no edits         | before merging non-trivial changes                                                             |
| `/code-refactor`    | a named smell (from `/code-crit`, a `[CHORE]` TODO, or direct ask) | one micro-refactor per commit, verify-gated         | "refactor this", "clean this up"                                                               |
| `/trust-but-verify` | a done/works/fixed claim                                           | fresh verify-command run, exit code checked         | automatic reflex before any completion claim, push, or PR                                      |
| `/review-response`  | incoming PR/CI feedback                                            | verified, judged, fixed or pushed back with reasons | handling review comments or CI failures                                                        |
| `/code-decay`       | git log + repo                                                     | churn × complexity hotspot ranking                  | prioritizing where to invest refactor effort; does not rejoin — feeds a future `/write-plan`   |
| `/ante-mortem`      | a file/module                                                      | hypothetical post-mortems, hardening TODOs          | pre-release or post-refactor audit; does not rejoin — feeds a future `/write-plan`             |

**Reads, not stages** — loaded _within_ a stage, never drawn as a box: `codebase-design` (deep-module vocabulary), `~/.claude/references/code/CODE-STANDARD.md` + the one matching language file, `CODE-PRINCIPLES.md` (judgment calls at `/code-crit` time), `TESTING-STANDARD.md`.

---

### Security Touchpoints

Not a parallel pipeline — three tools attach to the spine and planning table at different points, plus one that's out of scope for project work entirely.

**`/threat-model` — attaches at the planning table, before code exists:**

```
        ┌─────────────┐
        │ /write-plan │
        └─────────────┘
               │  security surface?
               │  offered mid-flow
               ▼
┌─────────────────────────────┐
│        /threat-model        │
│ (design-time STRIDE review, │
│     before code exists)     │
└─────────────────────────────┘
```

**`/code-sec` → `/bounty-hunter` — periodic / pre-release, re-enters the spine:**

```
┌────────────────────────────┐
│         /code-sec          │
│ (repo-wide sweep: secrets, │
│ deps, git-crypt coverage)  │
└────────────────────────────┘
               │  findings
               ▼
 ┌───────────────────────────┐
 │      /bounty-hunter       │
 │ (reachability filter over │
 │     /code-sec output)     │
 └───────────────────────────┘
               │  confirmed externally
               │  reachable subset
               ▼
┌────────────────────────────┐
│      [SECURITY] TODO       │
│ re-enters as a scoped Task │
│   -> back into THE SPINE   │
└────────────────────────────┘
```

**`/harness-audit` — excluded entirely, no arrows in or out:**

```
┌────────────────────────────────────┐
│           /harness-audit           │
│ excluded — audits ~/.claude itself │
│  (hooks, plugins, MCP, settings),  │
│   not a project repo. Never part   │
│         of this pipeline.          │
└────────────────────────────────────┘
```

| Skill            | Attaches at                                                               | Use when                                                                  |
| ---------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `/threat-model`  | planning table, offered by `/write-plan`                                  | plan has a security surface, before code exists                           |
| `/code-sec`      | periodic + pre-release, findings re-enter the spine as `[SECURITY]` TODOs | routine hygiene sweep — secrets, deps, git-crypt coverage                 |
| `/bounty-hunter` | after `/code-sec`, filters its output                                     | narrowing to what's actually externally reachable                         |
| `/harness-audit` | —                                                                         | never for project code; audits the harness that runs Claude, not the repo |

---

### Session Tools

These four skills manage context across sessions. Pick the right one based on what just happened.

| Skill             | Trigger           | Weight   | Use when                                                        |
| ----------------- | ----------------- | -------- | --------------------------------------------------------------- |
| `/handoff`        | `/handoff`        | ~400 tok | Spinning off a side-issue mid-session; main session stays alive |
| `/handoff-return` | `/handoff-return` | ~400 tok | Finishing a tangent; merging findings back into main session    |
| `/close`          | `/close`          | ~400 tok | Done for now; no major decisions made                           |
| `/checkpoint`     | `/checkpoint`     | ~2K tok  | End of work session; real decisions were made                   |

---

#### `/handoff` — Lean fork

Forks the current session into a focused tangent. Emits a reason-first re-entry prompt and saves it to `/tmp/handoff-{timestamp}.md` for crash safety. Writes nothing to `.memory/SESSION-LOG.md` — that is `/checkpoint`'s job.

When to use: a side-issue surfaces mid-session that needs clean context to chase. Open a fresh session, paste the prompt, work the tangent, then `/handoff-return` to merge findings back.

Output:

```
── Tangent fork ──────────────────────────────
Reason: {why this forked}
Scope:  {what the tangent should accomplish}
First action: {single concrete step}
Suggested skills: {1-3 relevant skills}
──────────────────────────────────────────────
```

---

#### `/handoff-return` — Merge tangent

Pops the tangent back into the main session. Summarizes what the forked session found, syncs any new items to `TODOS.md`, refreshes the triage pipeline, and prints a tight paste-back block to drop into the still-alive main session.

When to use: you've finished the tangent opened by `/handoff` and want to bring findings back without losing the main thread.

---

#### `/close` — Lightweight close

Emits a resume-focused re-entry prompt (what you were working on + where you left off + open items). No narrative block written, no log rotation, no triage pipeline. Run `/clear` after.

When to use: wrapping up but no major architectural decisions were made this session. Cheaper than `/checkpoint`; still gives a clean re-entry for next time.

---

#### `/checkpoint` — Durable close

Full end-of-work-session wrap-up. Writes a narrative block to `.memory/SESSION-LOG.md`, syncs completed/new items to `TODOS.md`, runs the triage pipeline (`update-cache` → `rotate-log` → `update-triage`), and prints a re-entry prompt. Run `/clear` after.

When to use: end of day, or any session where real decisions were made that a future session must not re-litigate.

`.memory/SESSION-LOG.md` block format:

```markdown
---
## Session Checkpoint — {YYYY-MM-DD hh:MM AM/PM}

### Goal

### Completed

### Decisions Made

### Files Touched

### Gotchas / Notes

### Re-Entry Prompt
---
```

Open work lives in `TODOS.md` only — there is no `### Incomplete / Next Steps` block.

---

### Dev Skills

#### `/diagnose` — Bug diagnosis loop

Disciplined feedback loop for hard bugs and performance regressions: reproduce → hypothesise → instrument → fix → regression test. Writes a `POST-MORTEM.md` at close and appends any new fragility findings to `TODOS.md` as `[BUG]` items.

When to use: any `[BUG]` TODO, a failing test you can't explain, or a performance regression. Do not jump straight to fixes — run `/diagnose` first.

---

#### `/tdd` — Test-driven development

Red-green-refactor loop. Writes a failing test, implements the minimal code to pass it, then refactors. Follows vertical slice discipline — one behavior at a time.

When to use: any `[TEST]` TODO, feature work that needs test coverage first, or when `/mutation-testing` surfaces survivors.

---

#### `/prototype` — Throwaway spike

Builds throwaway code to answer a design question before committing. Routes to either a terminal app (logic/state model) or switchable UI variants (look/feel). Output is prefixed `_` per naming convention to signal ephemeral status.

When to use: unsure which data model or architecture to commit to; want to see a UI idea before building it properly.

---

#### `/grill-me` — Plan stress-test

Interviews you relentlessly about every aspect of a plan — resolves decisions one branch at a time before building starts. Provides a recommended answer for each question. Appends resolved decisions to `.work/FINDINGS.md`.

When to use: moving from idea → foundation. Run this before `/dev-setup` or any significant build to surface hidden assumptions and lock in decisions.

---

#### `/ante-mortem` — Future bug audit

Imagines future post-mortems for the codebase as it stands today. Writes realistic incident reports for bugs that haven't happened yet, identifies fragile code and implicit assumptions. Hardening suggestions become tagged TODOs in `TODOS.md`. Security fragility gets `[SECURITY]` tags and a suggestion to run `/code-sec` or `/bounty-hunter`. Real bugs found in passing get `[BUG]` TODOs for `/diagnose`.

Reference catalogue of 11 fragility patterns lives in `ante-mortem/CATALOGUE.md`.

When to use: before a release, after a major refactor, or any time you want a pre-emptive audit of a file or module.

---

#### `/mutation-testing` — Test gap detection

Introduces deliberate one-line mutations into source code and checks whether the test suite catches each one. Reports surviving mutations (tests that didn't catch the change) as `[TEST]` TODOs in `TODOS.md`. Close those TODOs with `/tdd` — do not write tests inside this skill.

When to use: after writing a feature to verify test coverage is meaningful, not just present.

---

#### `/code-crit` — Structured code review

Parallel Agent-spawn persona review of a diff/branch/PR. Binary verified/unverified confidence, Spec-vs-Standards severity report. Fast mode (default) or thorough mode (every persona fully isolated). Report-only — never edits.

When to use: "review this diff/branch/PR", before merging non-trivial changes.

---

#### `/code-refactor` — Behavior-preserving restructuring

Applies a named fix (Extract Method, Rename, Decompose Conditional, etc.) to a named smell — from a `/code-crit` finding, a `[CHORE]` TODO, or a direct ask. One micro-refactor at a time, fresh verify-command run between each, per-file `refactor:` commits. Not `/code-crit` — that names smells, this fixes them.

When to use: "refactor this", "clean this up", or picking up a `[CHORE]` TODO that names a code smell.

---

#### `/code-decay` — Hotspot ranking

Ranks files by churn (git log) × complexity (ast-grep or a proxy metric) into a dated Markdown report inside the target repo. Zero model calls outside `--interpret`.

When to use: "find hotspots", "which files are decaying" — prioritizing where to invest refactor effort.

---

#### `/trust-but-verify` — Evidence gate

Before any done/works/fixed claim, `git push`, PR, or session close — runs the project's verify command fresh and reads the exit code. Unproven claims become `[VERIFY]` TODOs in `.work/VERIFY.md`.

When to use: automatically, per the global CLAUDE.md reflex — not opt-in. Run before claiming completion, not before every commit.

---

#### `/review-response` — Incoming feedback discipline

Counterpart to `/code-crit` (which gives review) — for receiving it. Reads all PR/CI feedback without reacting, restates it, verifies each claim against the actual code, judges fit for this codebase, then fixes or pushes back with reasons. No performative agreement.

When to use: handling PR review comments or CI failures.

---

#### `/threat-model` — STRIDE design review

Top-down threat model: DFD element table → STRIDE per element → likelihood×impact risk grid → mitigation map, written to `docs/threat-model.md` (git-crypt). Update mode re-verifies mitigations on changed elements; design-review mode runs against a planning doc before code exists. Sibling of `/code-sec` (bottom-up hygiene sweep) and `/bounty-hunter` (reachability filter).

When to use: pre-launch or new-system security design review, or when `/write-plan` flags a security surface. Deliberate trigger only — never auto-run.

---

### Project Skills

#### `/dev-setup` — Per-project wizard

Complete per-project setup in one guided run. Creates `README.md`, `.claude/CLAUDE.md`, `.claude/settings.json`, `CHANGELOG.md`, `.memory/SESSION-LOG.md`, `TODOS.md`, `.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `RELEASE-NOTES.md`, and `.gitignore`. Offers git init and GitHub repo creation. Safe to re-run — checks before overwriting.

When to use: starting any new project.

---

#### `/dev-brief` — Cross-project status brief

Morning or context-switch brief across all projects in `~/dev`. Reads `TODOS.md` (or `.memory/SESSION-LOG.md`) per project, surfaces open TODOs by tier, live git state, gotchas, decisions, and release-pending signals. Auto-reconciles open TODOs against recent git commits — flags items that may already be resolved.

When to use: first thing in a session to orient across projects, or before a context switch.

---

#### `/changelog` — Changelog entry generator

Reads git commits since the last versioned release and inserts a dated sub-block under `## [Unreleased]` in `CHANGELOG.md`. Groups commits by conventional-commit prefix (feat/fix/chore/etc.), applies the project's emoji format, deduplicates against existing entries.

When to use: manually, after a session that produced changelog-worthy changes. Do not run automatically — CLAUDE.md delegates this explicitly.

---

#### `/release-notes` — GitHub release prose

Reads the `## [Unreleased]` section of `CHANGELOG.md` and generates polished GitHub prose release notes. Optionally promotes `[Unreleased]` to a versioned entry. Writes output to `RELEASE-NOTES.md` (gitignored — clear after posting to GitHub).

When to use: before cutting a release. Run `/changelog` first to populate `[Unreleased]`, then run this.

---

#### `/sync-trello` — Trello sync

Reads `.work/PLAN.md` and for each Goal without a `[trello:ID]` tag: creates a card at the bottom of "Back Log", creates a checklist for each Micro-Goal, creates checklist items for each Task, then annotates the Goal line with `[trello:CARD_ID]`. Fully idempotent — re-running skips tagged Goals.

Board resolved in order: inline arg → `.claude/trello-board` file → interactive prompt.

When to use: when a Goal is ready to track on the Trello board.

---

#### `/trello-agent` — Trello board management

Direct Trello board management via `trello-cli`. Validates before acting, confirms destructive operations, never leaves the board in a broken state. Knows KOS board names. Defers to `trello <command> --help` for exact flags.

When to use: ad-hoc board operations outside the `/sync-trello` flow — moving cards, updating checklist items, bulk edits.

---

### Utility Skills

#### `/remember` — Ad-hoc fact capture

Captures a single fact into `KNOWLEDGE.md` (local or global) without running a full `/checkpoint`. Runs the 4-test promotion bar (SETTLED · NON-OBVIOUS · NOT A RULE · DURABLE), deduplicates semantically, and confirms on write. If a fact fails the bar, explains why and suggests the correct destination.

| Flag                        | Effect                                |
| --------------------------- | ------------------------------------- |
| `/remember <fact>`          | Auto-route + bar check                |
| `/remember --global <fact>` | Force global `~/.claude/KNOWLEDGE.md` |
| `/remember --force <fact>`  | Bypass bar, write regardless          |

When to use: mid-session fact worth preserving that doesn't need a full `/checkpoint`.

---

#### `/recall` — Progressive memory retrieval

Greps `.memory/EPISODIC-INDEX.md` and `KNOWLEDGE.md` tiers for cheap Layer-1 hits, then expands on request rather than dumping everything. `/recall <query>` scopes to the current project; `/recall --deep <query>` fans out across all of `~/dev` (never auto-expands in fan-out mode).

When to use: searching past sessions, decisions, or facts.

---

#### `/consolidate` — Episodic-to-semantic promotion

The "sleep" phase — sweeps `.memory/SESSION-LOG.md`/`.memory/EPISODIC-INDEX.md` entries since the last consolidation marker, runs the same 4-test promotion bar as `/remember`, and routes approved facts into `KNOWLEDGE.md`. Never auto-writes.

When to use: periodically, or when reviewing a scheduled-run `.memory/CONSOLIDATION-INBOX.md`.

---

#### `/encrypt` — git-crypt setup

Inits git-crypt on a repo, writes the root-anchored `.gitattributes` backstop for `KNOWLEDGE.md`/`TODOS.md`/`.memory/SESSION-LOG.md`/`.work/*`, adds `.gitignore` negations, and stores the binary key as base64 in Proton Pass.

When to use: setting up encryption for a new repo, or fixing a repo with plaintext session/planning files that should be encrypted.

---

#### `/diagram` — Diagram generation

Generates a diagram image (Mermaid flowchart by default; PlantUML UML activity diagram or Shostack/SDL data-flow diagram on request) as SVG/PNG/PDF, no editor dependency. `/threat-model` uses the DFD mode internally.

When to use: asked to draw a flowchart, decision tree, UML activity diagram, or DFD.

---

#### `/fable-mode` — Working-discipline loader

Loads a five-gate task loop + standing habits for any session, especially useful on tasks with many dependent steps or unknowns that could change approach mid-flight. Not a skill you "finish" — it's a mode; say "fable mode off" to deactivate.

When to use: a task keeps failing/stalling, or you want deliberate gated verification before a multi-step change lands.

---

#### `/code-mode` — Code-lifecycle five-gate loader

Loads the code-lifecycle discipline (five-gate task loop, red-green inner loop, code-specific gate-skip smells) and routes into the code-quality and security substrate (`CODE-STANDARD.md`, `SECURITY-STANDARD.md`, `/tdd`, `/diagnose`, `/code-refactor`, `/code-decay`, `/requirements`, `/architecture`, `/brainstorm`, `/grill-me`, `/write-plan`, `/threat-model`, `/prototype`, `/code-crit`, `/mutation-testing`, `/ante-mortem`, `/review-response`, `/trust-but-verify`, `/run`, `/changelog`). Not a skill you "finish" — it's a mode; say "code mode off" to deactivate.

When to use: starting real code work — new function/feature, bug fix, refactor, new system, diff review/cleanup, adding tests, debugging.

---

#### `/create-gdd` — Game Design Document

Creates or reviews a Game Design Document for any game type — digital, physical, hybrid, Web3, mobile, board/card game, tabletop RPG.

When to use: speccing a game system or documenting mechanics.

---

#### `codebase-design` — Deep-module vocabulary

Not a slash command — shared vocabulary (module, interface, depth, seam, adapter, leverage, locality) that other skills reference rather than re-deriving. `CODE-PRINCIPLES.md` points here for "is this a leaky abstraction" judgment calls — a module that forces callers to know its internals is this skill's smell to name, not a new catalogue row.

When to use: designing or improving a module's interface, deciding where a seam goes, or when another skill needs this vocabulary — invoked implicitly more often than by name.

---

#### `/zoom-out` — Codebase orientation

Maps an unfamiliar section of code — identifies modules, entry points, and how a given file or function fits into the broader system. Returns a module map and caller graph.

When to use: dropped into an unfamiliar codebase or a section you haven't touched in a while.

---

#### `/write-a-skill` — Skill authoring

Structured process for writing new Claude Code skills. Covers frontmatter, progressive disclosure, bundled resource files, and `disable-model-invocation` patterns. Walks through the skill anatomy step by step.

When to use: building a new custom skill.

---

### KOS Skills (installed separately)

Installed via `npx skills install kos`. Not tracked in dotfiles — reinstall after any `install.sh` run.

| Skill          | What it does                                                    |
| -------------- | --------------------------------------------------------------- |
| `/find-skills` | Discover and install agent skills via `npx skills find [query]` |
| `/kos-ingest`  | Ingest new notes/transcripts into the KOS vault                 |
| `/kos-query`   | Query the KOS vault                                             |
| `/kos-lint`    | Lint KOS vault entries                                          |
| `/kos-archive` | Archive KOS vault entries                                       |

Companion app (not a skill, standalone TUI, `~/dev/kos-capture`): transcribes
YouTube/podcast audio into files that land in `raw/` for `/kos-ingest` to pick up.

---

## Part 4 — Per-Project Setup

Run once when starting any new project:

```
/dev-setup
```

| Step                       | What it does                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Project name + description | Used in README and CLAUDE.md                                                                                                                                              |
| Project type + stack       | Determines folder structure and .gitignore additions                                                                                                                      |
| Folder scaffold            | Creates `src/`, `docs/`, `tests/` etc. based on type                                                                                                                      |
| `README.md`                | Minimal stub with name, description, structure                                                                                                                            |
| `.claude/CLAUDE.md`        | Project-level Claude config from template                                                                                                                                 |
| `.claude/settings.json`    | Baseline permission allowlist                                                                                                                                             |
| `.claude/trello-board`     | Board name for `/sync-trello` auto-resolution                                                                                                                             |
| Planning files             | `.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `.memory/SESSION-LOG.md`, `TODOS.md`, `CHANGELOG.md`, `RELEASE-NOTES.md`                                       |
| `.gitignore`               | Covers secrets, Claude artifacts, OS noise; gitignores planning files by default (`.work/*`, `.memory/SESSION-LOG.md`, `TODOS.md`)                                        |
| `git-crypt` (Step 15)      | Opt-in — offered separately after `.gitignore`. Accept it and those same planning files flip from gitignored to tracked+encrypted via a `.gitattributes` negation instead |
| Git init                   | Checks for repo, offers `git init -b main` if missing                                                                                                                     |
| GitHub repo                | Offers `gh repo create` with visibility choice                                                                                                                            |
| `/ce-setup` reminder       | Printed at end — run manually after                                                                                                                                       |

> `/dev-setup` is safe to re-run. It checks before overwriting any file.

---

### .work/PLAN.md Format

`/sync-trello` reads this hierarchy from `.work/PLAN.md`:

```markdown
## Goal: [Goal name] [trello:CARD_ID after first sync]

### Micro-Goal: [Micro-Goal name]

- [ ] Task one
- [x] Task two (done — still synced as checklist item)

### Micro-Goal: [Another name]

- [ ] Task three
```

| Level      | Markdown           | Trello                 |
| ---------- | ------------------ | ---------------------- |
| Goal       | `## Goal:`         | Card in "Back Log"     |
| Micro-Goal | `### Micro-Goal:`  | Checklist on that card |
| Task       | `- [ ]` or `- [x]` | Checklist item         |

Rules:

- Goals tagged `[trello:CARD_ID]` are skipped on next sync — idempotent
- Tasks outside any Micro-Goal are ignored
- Plain `##` headers are organization-only and not synced

The format above is **FLAT-FORMAT** — the original shape, still the default for
most repos. A second **NEW-FORMAT** (index+detail) exists for `TODOS.md`,
`.work/PLAN.md`, and `.work/FINDINGS.md`: each becomes a lean index of pointers,
with real content living in per-item detail files (`.work/plan/<goal-slug>.md`,
etc.). It graduated 2026-07-23 to a standing lazy per-repo rollout — migrate a
repo only when already working there with a clean tree, never as a big-bang
conversion. Migrated so far: `dotfiles`, `kodex-ide`. Every skill that touches
these files format-detects per repo (`test -d .work/plan`) and falls back to
flat-format automatically — see `claude/.claude/references/planning-format-detect.md`
for the shared detection logic every skill defers to.

---

## Part 5 — The Full Workflow (Example Project)

### Scenario

You're building a CLI tool called `kos-cli` — a command-line interface for querying KOS notes from the terminal.

---

### Step 1: Scope the project

Before touching any code, open Claude Code in the project root and run the design pipeline:

```
/brainstorm
```

Explores 2-3 approaches with tradeoffs and a recommendation. Writes `docs/brainstorm/<topic>-YYYY-MM-DD.md`. Skip this step for small, unambiguous work.

```
/grill-me
```

Resolves every design decision — data model, architecture, scope — one branch at a time before building starts. Outputs to `.work/FINDINGS.md`.

```
/requirements
```

Formalizes the resolved design into a numbered, testable FR/NFR spec at `docs/REQUIREMENTS.md`.

```
/architecture
```

Designs the system that satisfies those requirements — components, interfaces, data flow — as a living `docs/ARCHITECTURE.md` with FR/NFR traceability. Skip for work with no real system-design surface.

```
/write-plan
```

Converts the grilled design + `.work/FINDINGS.md` into `.work/PLAN.md` (Goal/Micro-Goal/Task, every Task carries a verify command). Offers a `/threat-model` review if the plan has a security surface, then offers `/sync-trello` at the end.

---

### Step 2: Start a work session

Open Claude Code. If continuing from a previous session, paste your re-entry prompt first:

```
"We're building kos-cli. Last session we scaffolded the CLI entrypoint in
src/cli.py and added argparse. Next: implement the `search` subcommand that
queries notes.db via fuzzy match. Read .work/PLAN.md for full context."
```

---

### Step 3: Work

Claude writes `.work/PLAN.md` automatically using the Goal/Micro-Goal/Task hierarchy.

Status bar shows live cost/burn/context + session elapsed time passively.

Open work tracks in `TODOS.md` (project root). Across all projects, `~/dev/.memory/TRIAGE-BLOCK.md` shows the priority-ordered view — auto-refreshed whenever `TODOS.md` is edited, or run `update-triage` manually.

---

### Step 4: Sync Goal to Trello

```
/sync-trello
```

Claude reads `.work/PLAN.md`, creates cards/checklists/items for all Goals without a `[trello:ID]` tag, then annotates each Goal with its card ID. Fully idempotent.

---

### Step 5: Code review before committing

```
/code-crit
```

Parallel Agent-spawn personas review logic, edge cases, naming, efficiency, test coverage — Spec-vs-Standards severity report, report-only. Findings that name a smell go to `/code-refactor` to fix; a finding this environment already tracks as `[CHORE]` does too. For anything touching auth, file I/O, or external input, run the security suite:

```
/code-sec         # broad hygiene sweep
/bounty-hunter    # reachability filter (what an attacker can actually reach)
/harness-audit    # if the project ships .claude/ config
```

See [docs/security/README.md](security/README.md) for the full suite and skill composition.

---

### Step 6: 45-minute mark

Status bar flips:

```
⚠️  45m — run /handoff soon
```

Reach a stopping point, then choose the right session tool:

**Lean fork — side-issue surfaced mid-session:**

```
/handoff
```

Emits a reason-first re-entry prompt. No narrative written. Saves to `/tmp/handoff-{timestamp}.md`. Open a fresh session and paste.

```
── Tangent fork ──────────────────────────────
Reason: fuzzy_match() edge cases surfaced a notes.db schema question
Scope:  audit notes.db schema; decide if FTS5 is worth adding
First action: read src/db.py and check current schema
Suggested skills: /diagnose, /tdd
──────────────────────────────────────────────
```

When done with the tangent, run `/handoff-return` to merge findings back into the main session.

**Lightweight close — done for now, no major decisions:**

```
/close
```

Emits a resume-focused re-entry prompt. No narrative. Run `/clear` after.

**Durable close — end of work session or real decisions made:**

```
/checkpoint
```

Writes a full narrative block to `.memory/SESSION-LOG.md`, syncs open work to `TODOS.md`, runs the triage pipeline, prints a re-entry prompt. Run `/clear` after. ~2K tokens.

Example `.memory/SESSION-LOG.md` block:

```markdown
---
## Session Checkpoint — 2026-05-26 02:32 PM

### Goal

Implement the `search` subcommand for kos-cli with fuzzy matching against notes.db.

### Completed

- [x] Scaffolded CLI entrypoint in src/cli.py
- [x] Implemented `search` subcommand with argparse
- [x] Fuzzy match logic against notes.db via rapidfuzz

### Decisions Made

- **Used rapidfuzz over fuzz** — 10x faster on large note sets, same API
- **SQLite FTS5 rejected** — overkill for current note volume, revisit at 10k+ notes

### Files Touched

- `src/cli.py` — added search subcommand and argparse wiring
- `src/search.py` — new file, fuzzy match core logic
- `requirements.txt` — added rapidfuzz

### Gotchas / Notes

- notes.db path is currently hardcoded to ~/.kos/notes.db — needs env var or config file
- rapidfuzz returns float scores — don't compare with == 100

### Re-Entry Prompt

> "kos-cli: implemented search subcommand with fuzzy match via rapidfuzz.
> Read .memory/SESSION-LOG.md and TODOS.md. For what's next, read .memory/TRIAGE-BLOCK.md.
> First action: add --tag filter flag."

---
```

Open work lives in `TODOS.md` only — there is no `### Incomplete / Next Steps` block in the log.

---

### Step 7: Next session

New session opens. Paste the re-entry prompt. Claude reads `.memory/SESSION-LOG.md`, `TODOS.md`, and `.work/PLAN.md`. Full context in seconds.

---

## Part 6 — Quick Reference

| When                               | What                                                                                           |
| ---------------------------------- | ---------------------------------------------------------------------------------------------- |
| Starting a new project             | `/dev-setup` → `/brainstorm` → `/grill-me` → `/requirements` → `/architecture` → `/write-plan` |
| Continuing a session               | Paste re-entry prompt                                                                          |
| Status (cost/burn/time)            | Glance at status bar (always visible)                                                          |
| Goal is ready to track             | `/sync-trello`                                                                                 |
| Before committing code             | `/code-crit`                                                                                   |
| Reduce complexity / apply a fix    | `/code-refactor` (fixes what `/code-crit` names)                                               |
| Find where to invest refactor time | `/code-decay` (churn × complexity hotspots)                                                    |
| Anything touching security         | `/code-sec` · `/bounty-hunter` · `/harness-audit` · `/threat-model`                            |
| Before claiming done/fixed/works   | `/trust-but-verify` (automatic reflex, not opt-in)                                             |
| Handling PR review or CI feedback  | `/review-response`                                                                             |
| 45-minute timer fires, side-issue  | `/handoff` (lean fork)                                                                         |
| 45-minute timer fires, wrapping up | `/close` (lightweight close)                                                                   |
| End of work session                | `/checkpoint` (durable — writes narrative + triage)                                            |
| After tangent session done         | `/handoff-return` (merges findings to TODOS.md)                                                |
| Returning after a break            | Open `.memory/SESSION-LOG.md` → copy re-entry prompt                                           |
| What's highest priority now        | Read `~/dev/.memory/TRIAGE-BLOCK.md`                                                           |
| Session produced changes           | `/changelog` (manual — do not auto-update inline)                                              |
| Cutting a release                  | `/changelog` → `/release-notes` → post to GitHub                                               |
| Bug or failure                     | `/diagnose`                                                                                    |
| Need test coverage                 | `/tdd`                                                                                         |
| Unsure about a design              | `/brainstorm`, `/grill-me`, or `/prototype`                                                    |
| Pre-release fragility audit        | `/ante-mortem`                                                                                 |
| Verify test suite is meaningful    | `/mutation-testing`                                                                            |
| Unfamiliar code section            | `/zoom-out`                                                                                    |
| Mid-session fact worth keeping     | `/remember` (write) / `/recall` (retrieve)                                                     |
| Judging a module's interface/seams | `codebase-design` (vocabulary — usually invoked implicitly)                                    |
| Draw a flowchart/UML/DFD           | `/diagram`                                                                                     |
| New repo needs encryption          | `/encrypt`                                                                                     |
| Task keeps failing/stalling        | `/fable-mode`                                                                                  |
| Starting real code work            | `/code-mode`                                                                                   |
| Need a new skill                   | `/find-skills [query]` or `/write-a-skill`                                                     |

---

## Part 7 — What Goes Where

```
~/.claude/                        (symlinked from dotfiles/claude/.claude/, entry by entry)
  CLAUDE.md                       ← global standing orders
  KNOWLEDGE.md                    ← global curated facts (git-crypt encrypted)
  settings.json                   ← hooks, statusLine, plugins
  hooks/
    session_timer.py              ← tracks session start time
    combined-statusline.sh        ← statusLine: ccusage + caveman badge + elapsed timer + rate-limit bars, one row
    command_guard.py / secret_guard.py   ← PreToolUse(Bash): block dangerous/secret-leaking commands
    standards_guard.py            ← PreToolUse(Edit/Write): forces reading CODE-STANDARD.md + language file first
    code_formatter.py / code_standard_lint.py / gate3_skip_detector.py  ← PostToolUse(Edit/Write)
    refresh_triage.py             ← PostToolUse: auto-refreshes .memory/TRIAGE-BLOCK.md on TODOS.md edit
    caveman-*.js / .sh            ← caveman plugin hooks
  references/
    code/
      CODE-REFERENCE.md           ← vocabulary reference (Ousterhout, Feathers, ADR format + gate)
      CODE-PRINCIPLES.md          ← committed principles + smell vocabulary
      CODE-STANDARD.md            ← mechanical rules + per-language delegation
      ANTI-PATTERNS.md            ← full anti-pattern catalogue (Fowler, Brown, Meszaros)
      TESTING-STANDARD.md         ← test-type decision layer; coverage stance
      LUA.md / PYTHON.md / ...    ← per-language rules
    MEMORY-STANDARD.md            ← KNOWLEDGE.md promotion bar, routing rules, entry format
    MEMORY-ARCHITECTURE.md        ← 5-store memory system reference
    PROMPT-DEFENSE.md             ← shared prompt-injection defense baseline (code-sec, bounty-hunter, harness-audit, threat-model)
    planning-format-detect.md     ← shared FLAT vs index+detail format-detection logic
    git-crypt-lock-check.md       ← unlock-before-read pipe for encrypted files
  skills/                         (authored under dotfiles/claude/.claude/skills/<name>/, symlinked here)
    session-handoff/              ← /handoff  (lean fork)
    session-handoff-return/       ← /handoff-return  (merge tangent)
    session-close/                ← /close  (lightweight close)
    session-checkpoint/           ← /checkpoint  (durable wrap-up)
    dev-brief/                    ← /dev-brief  (cross-project status)
    changelog/                    ← /changelog  (generate dated changelog entries)
    release-notes/                ← /release-notes  (polish for GitHub release)
    diagnose/                     ← /diagnose  (RCA → fix → post-mortem)
    tdd/                          ← /tdd  (red-green-refactor)
    prototype/                    ← /prototype  (throwaway spike)
    brainstorm/                   ← /brainstorm  (explore approaches pre-plan)
    grill-me/                     ← /grill-me  (stress-test a plan)
    requirements/                 ← /requirements  (FR/NFR spec)
    architecture/                 ← /architecture  (living system design doc)
    write-plan/                   ← /write-plan  (Goal/Micro-Goal/Task plan)
    code-crit/                    ← /code-crit  (structured code review, report-only)
    code-refactor/                ← /code-refactor  (fixes smells code-crit names)
    code-decay/                   ← /code-decay  (churn × complexity hotspot ranking)
    codebase-design/              ← deep-module vocabulary (module/interface/depth/seam)
    trust-but-verify/             ← /trust-but-verify  (fresh verify-command evidence gate)
    review-response/              ← /review-response  (incoming PR/CI feedback discipline)
    code-sec/                     ← /code-sec  (project security sweep)
    bounty-hunter/                ← /bounty-hunter  (remote reachability triage)
    harness-audit/                ← /harness-audit  (harness attack surface audit)
    threat-model/                 ← /threat-model  (design-time STRIDE)
    ante-mortem/                  ← /ante-mortem  (future bug audit)
    mutation-testing/             ← /mutation-testing  (test gap detection)
    dev-setup/                    ← /dev-setup  (per-project wizard)
    sync-trello/                  ← /sync-trello  (push .work/PLAN.md → Trello)
    trello-agent/                 ← /trello-agent  (ad-hoc board management)
    remember/                     ← /remember  (ad-hoc fact capture)
    recall/                       ← /recall  (progressive memory retrieval)
    consolidate/                  ← /consolidate  (episodic → semantic promotion)
    encrypt/                      ← /encrypt  (git-crypt setup)
    diagram/                      ← /diagram  (Mermaid/PlantUML/DFD generation)
    fable-mode/                   ← /fable-mode  (five-gate working-discipline loader)
    code-mode/                    ← /code-mode  (code-lifecycle five-gate loader)
    create-gdd/                   ← /create-gdd  (Game Design Document)
    write-a-skill/                ← /write-a-skill  (structured skill authoring)
    zoom-out/                     ← /zoom-out  (map unfamiliar codebase)
    kos*/                         ← KOS vault skills (installed separately via npx)
  plugins/
    caveman/                      ← terse response mode (active, heavy use)
    compound-engineering/         ← multi-agent code review (active use)
    planning-with-files/          ← mid-session persistent memory (active, low use)
    pm-*/                         ← PM skills, 5 plugins (installed, disabled — unused)

~/dev/
  .triage-cache                   ← pointer index: project → TODOS.md path + mtime
  .triage-dates                   ← first-seen dates per TODO item (stale detection)
  .memory/
    TRIAGE-BLOCK.md               ← auto-generated priority view across all projects

your-project/                    (default state below; changes if git-crypt is accepted — dev-setup Step 15 / /encrypt)
  .claude/
    CLAUDE.md                     ← project-specific context (committed)
    settings.json                 ← project-level permissions (committed)
    settings.local.json           ← local overrides (gitignored)
    trello-board                  ← board name for /sync-trello (gitignored)
  src/                            ← source (structure varies by project type)
  docs/
    REQUIREMENTS.md                ← via /requirements — always committed + git-crypt (unconditional, not tied to Step 15)
    ARCHITECTURE.md                ← via /architecture — always committed + git-crypt (unconditional, not tied to Step 15)
    brainstorm/<topic>-DATE.md     ← via /brainstorm, pre-plan design docs (committed, plaintext)
  README.md                       ← committed
  TODOS.md                        ← canonical open work — single source of truth (gitignored by default; tracked + git-crypt encrypted if git-crypt accepted)
  .memory/
    SESSION-LOG.md                ← checkpoint/handoff narrative (gitignored by default; tracked + git-crypt encrypted if git-crypt accepted)
  .work/
    PLAN.md                       ← live Goals/Micro-Goals/Tasks + Trello IDs (gitignored by default; tracked + git-crypt encrypted if git-crypt accepted — everything under .work/ is meant to be, no exceptions, once accepted)
    FINDINGS.md                   ← research and decisions (same as PLAN.md above)
    PROGRESS.md                   ← session progress log (same as PLAN.md above)
  CHANGELOG.md                    ← committed changelog (updated via /changelog)
  KNOWLEDGE.md                    ← committed curated facts about this codebase (plaintext by default; git-crypt encrypted if git-crypt accepted — never gitignored either way, see dev-setup Step 13)
  RELEASE-NOTES.md                ← scratch pad for /release-notes (gitignored)
  .gitignore                      ← covers all Claude artifacts, secrets, OS noise
```

---

## Part 8 — Trello Sync

**Status: Complete.** Skill installed at `~/.claude/skills/sync-trello/`.

### Setup

Checklist item CRUD was added to a local fork of `trello-cli` and installed globally:

```bash
npm install -g ~/dev/trello-cli/packages/trello-cli
```

New commands available:

- `trello card:add-checklist-item` — create item in checklist
- `trello card:update-checklist-item` — rename or reposition item
- `trello card:delete-checklist-item` — delete item
- `trello card:delete-checklist` — delete entire checklist

> **Note:** checklist CRUD PR (upstream [mheap/trello-cli#233](https://github.com/mheap/trello-cli/pull/233)) is still open. Until merged, the local fork install above is required.

### Usage

```
/sync-trello [optional board name]
```

Board resolution order:

1. Arg passed inline: `/sync-trello "My Board"`
2. `.claude/trello-board` file in project root (set by `/dev-setup`)
3. Prompt with `trello board:list` output + offer to save

Goal→card / Micro-Goal→checklist / Task→item mapping, the `[trello:ID]` skip
rule, and full sync algorithm live in `sync-trello/SKILL.md` (canonical, single
home — not restated here to avoid the two-copy drift this guide's last audit
pass fixed elsewhere).
