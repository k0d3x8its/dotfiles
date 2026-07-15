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

| Step | Command |
|------|---------|
| kos skills | `npx skills install kos` |
| Particle CLI | `npm install -g particle-cli && particle login` |
| Antigravity | Has its own CLI installer — see https://antigravity.dev |
| Ghostty sidebar | `sudo nala install xdotool` (required for window positioning) |

### 3. Plugins (inside a Claude Code session)

```bash
# Caveman (terse response mode)
/plugin marketplace add JuliusBrussee/caveman
/plugin install caveman@caveman

# Karpathy engineering principles
/plugin marketplace add forrestchang/andrej-karpathy-skills
/plugin install andrej-karpathy-skills@karpathy-skills

# Planning with files (persistent mid-session memory)
/plugin marketplace add OthmanAdi/planning-with-files
/plugin install planning-with-files@planning-with-files

# Compound engineering (code review agents)
/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering@compound-engineering-plugin

# PM skills (5 plugins, one marketplace)
/plugin marketplace add phuryn/pm-skills
/plugin install pm-toolkit@pm-skills
/plugin install pm-product-strategy@pm-skills
/plugin install pm-product-discovery@pm-skills
/plugin install pm-go-to-market@pm-skills
/plugin install pm-execution@pm-skills
```

### 4. Status Bar

`combined-statusline.sh` is already wired in `settings.json`. It outputs three lines on every response:

```
🤖 Sonnet 4.6 | 💰 $0.12 session / $0.84 today | 🔥 $0.08/hr | 🧠 18k (9%)
[CAVEMAN full]
⏱  23m
```

Line 1: live cost/burn/context from ccusage  
Line 2: current caveman mode (or blank if off)  
Line 3: session elapsed time — flips to `⚠️ 45m` at 45 min, `🚨 55m` at 55 min

---

## Part 2 — Global CLAUDE.md

Lives at `~/.claude/CLAUDE.md` (symlinked from dotfiles). Loaded every session globally. Edit the dotfiles source — changes sync automatically.

```markdown
# K0d3x Global Claude Config

## Who I Am
Solo developer. Maker. Ubuntu 24.04 (Noble). Tools: Neovim, Nala, Git.
KOS (Kodex OS) is my personal knowledge management system.

## Skills Available
The harness auto-lists every custom skill + its description each session — names below are the slash aliases, not re-described here. Tag routing lives in the TODO Tags table.
`/handoff` `/handoff-return` `/close` `/checkpoint` `/changelog` `/dev-brief` `/planning-with-files` `/release-notes` `/find-skills` `/diagnose` `/tdd` `/prototype` `/sync-trello`
External (not auto-surfaced): `/ce-code-review` `/discover` `/write-prd`

## Session Rules
- Track session start time. Warn me at 45 minutes to run /handoff (lean fork), /close
  (lightweight close), or /checkpoint (durable) depending on context.
- Session tools — four, by job:
  - `/handoff` (push/fork): lean mid-session tangent. Emits reason-first re-entry prompt.
    NO SESSION-LOG narrative. ~400 tok.
  - `/handoff-return` (pop/merge): close a tangent, auto-sync its findings to TODOS.md,
    print paste-back block for the still-alive main session. ~400 tok.
  - `/close` (close+resume): lightweight session close. Emits resume-focused re-entry
    prompt. NO SESSION-LOG. ~400 tok.
  - `/checkpoint` (durable): end-of-work-session close. Writes SESSION-LOG narrative +
    rotate-log + triage. ~2K tok. Use when real decisions were made.
- Always read `.work/PLAN.md`, `.work/FINDINGS.md`, and `.work/PROGRESS.md` if they exist.
- When I paste a re-entry prompt: treat decisions and architectural choices as authoritative.
  File state wins on task-state conflicts.
- CHANGELOG: use `/changelog` manually when a session produces changelog-worthy changes.
  Do not auto-update changelogs inline.

## TODO Tags
[... see CLAUDE.md for full tag table — Priority tags + Annotation tags ...]

## My Conventions
- Commit messages: conventional commits format (feat:, fix:, docs:, chore:)
- Commit granularity: one file per commit with a brief conventional-commit message.
- Branch naming: feature/, fix/, docs/, chore/
- NEVER add `Co-Authored-By` lines to any commit message.
- All Trello boards use a six-column Kanban: Back Log → To Do → Doing → Review → Testing → Done
- Code comments: always explain the why, not just the what
```

---

## Part 3 — Skills Reference

All custom skills live in `~/.claude/skills/` (symlinked from dotfiles). KOS-specific skills are installed separately via `npx skills install kos`.

### Session Tools

These four skills manage context across sessions. Pick the right one based on what just happened.

| Skill | Trigger | Weight | Use when |
|---|---|---|---|
| `/handoff` | `/handoff` | ~400 tok | Spinning off a side-issue mid-session; main session stays alive |
| `/handoff-return` | `/handoff-return` | ~400 tok | Finishing a tangent; merging findings back into main session |
| `/close` | `/close` | ~400 tok | Done for now; no major decisions made |
| `/checkpoint` | `/checkpoint` | ~2K tok | End of work session; real decisions were made |

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

| Flag | Effect |
|---|---|
| `/remember <fact>` | Auto-route + bar check |
| `/remember --global <fact>` | Force global `~/.claude/KNOWLEDGE.md` |
| `/remember --force <fact>` | Bypass bar, write regardless |

When to use: mid-session fact worth preserving that doesn't need a full `/checkpoint`.

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

| Skill | What it does |
|---|---|
| `/find-skills` | Discover and install agent skills via `npx skills find [query]` |
| `/kos-ingest` | Ingest new notes/transcripts into the KOS vault |
| `/kos-query` | Query the KOS vault |
| `/kos-capture` | Capture a new KOS note |
| `/kos-lint` | Lint KOS vault entries |
| `/kos-archive` | Archive KOS vault entries |

---

## Part 4 — Per-Project Setup

Run once when starting any new project:

```
/dev-setup
```

| Step | What it does |
|---|---|
| Project name + description | Used in README and CLAUDE.md |
| Project type + stack | Determines folder structure and .gitignore additions |
| Folder scaffold | Creates `src/`, `docs/`, `tests/` etc. based on type |
| `README.md` | Minimal stub with name, description, structure |
| `.claude/CLAUDE.md` | Project-level Claude config from template |
| `.claude/settings.json` | Baseline permission allowlist |
| `.claude/trello-board` | Board name for `/sync-trello` auto-resolution |
| Planning files | `.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `.memory/SESSION-LOG.md`, `TODOS.md`, `CHANGELOG.md`, `RELEASE-NOTES.md` |
| `.gitignore` | Covers secrets, Claude artifacts, planning files, OS noise |
| Git init | Checks for repo, offers `git init -b main` if missing |
| GitHub repo | Offers `gh repo create` with visibility choice |
| `/ce-setup` reminder | Printed at end — run manually after |

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

| Level | Markdown | Trello |
|---|---|---|
| Goal | `## Goal:` | Card in "Back Log" |
| Micro-Goal | `### Micro-Goal:` | Checklist on that card |
| Task | `- [ ]` or `- [x]` | Checklist item |

Rules:
- Goals tagged `[trello:CARD_ID]` are skipped on next sync — idempotent
- Tasks outside any Micro-Goal are ignored
- Plain `##` headers are organization-only and not synced

---

## Part 5 — The Full Workflow (Example Project)

### Scenario
You're building a CLI tool called `kos-cli` — a command-line interface for querying KOS notes from the terminal.

---

### Step 1: Scope the project

Before touching any code, open Claude Code in the project root and run:

```
/grill-me
```

Resolves every design decision — data model, architecture, scope — before building starts. Outputs to `.work/FINDINGS.md`.

Then generate a lightweight spec:
```
/write-prd
```

Produces: goals, non-goals, user stories, success metrics. Save as `docs/prd.md` and commit.

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
/ce-code-review
```

Parallel sub-agents review logic, edge cases, naming, efficiency, test coverage. For anything touching auth, file I/O, or external input, run the security suite:

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

| When | What |
|---|---|
| Starting a new project | `/dev-setup` → `/grill-me` → `/write-prd` |
| Continuing a session | Paste re-entry prompt |
| Status (cost/burn/time) | Glance at status bar (always visible) |
| Goal is ready to track | `/sync-trello` |
| Before committing code | `/ce-code-review` |
| Anything touching security | `/code-sec` · `/bounty-hunter` · `/harness-audit` · `/threat-model` |
| 45-minute timer fires, side-issue | `/handoff` (lean fork) |
| 45-minute timer fires, wrapping up | `/close` (lightweight close) |
| End of work session | `/checkpoint` (durable — writes narrative + triage) |
| After tangent session done | `/handoff-return` (merges findings to TODOS.md) |
| Returning after a break | Open `.memory/SESSION-LOG.md` → copy re-entry prompt |
| What's highest priority now | Read `~/dev/.memory/TRIAGE-BLOCK.md` |
| Session produced changes | `/changelog` (manual — do not auto-update inline) |
| Cutting a release | `/changelog` → `/release-notes` → post to GitHub |
| Bug or failure | `/diagnose` |
| Need test coverage | `/tdd` |
| Unsure about a design | `/grill-me` or `/prototype` |
| Pre-release fragility audit | `/ante-mortem` |
| Verify test suite is meaningful | `/mutation-testing` |
| Unfamiliar code section | `/zoom-out` |
| Need a new skill | `/find-skills [query]` or `/write-a-skill` |

---

## Part 7 — What Goes Where

```
~/.claude/                        (symlinked from dotfiles)
  CLAUDE.md                       ← global standing orders
  KNOWLEDGE.md                    ← global curated facts (committed via dotfiles)
  settings.json                   ← hooks, statusLine, plugins
  hooks/
    session_timer.py              ← tracks session start time
    combined-statusline.sh        ← statusLine: ccusage + caveman mode + elapsed timer
    refresh_triage.py             ← PostToolUse: auto-refreshes .memory/TRIAGE-BLOCK.md on TODOS.md edit
    caveman-*.js / .sh            ← caveman plugin hooks
  references/
    code/
      CODE-REFERENCE.md           ← vocabulary reference (Ousterhout, Feathers, ADR format + gate)
      CODE-PRINCIPLES.md          ← committed principles + smell vocabulary
      CODE-STANDARD.md            ← mechanical rules + per-language delegation
      ANTI-PATTERNS.md            ← full anti-pattern catalogue (Fowler, Brown, Meszaros)
      LUA.md / PYTHON.md / ...    ← per-language rules
    MEMORY-STANDARD.md            ← KNOWLEDGE.md promotion bar, routing rules, entry format
    MEMORY-ARCHITECTURE.md        ← 5-store memory system reference
  skills/
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
    grill-me/                     ← /grill-me  (stress-test a plan)
    code-sec/                     ← /code-sec  (project security sweep)
    bounty-hunter/                ← /bounty-hunter  (remote reachability triage)
    harness-audit/                ← /harness-audit  (harness attack surface audit)
    threat-model/                 ← /threat-model  (design-time STRIDE)
    ante-mortem/                  ← /ante-mortem  (future bug audit)
    mutation-testing/             ← /mutation-testing  (test gap detection)
    dev-setup/                    ← /dev-setup  (per-project wizard)
    sync-trello/                  ← /sync-trello  (push .work/PLAN.md → Trello)
    trello-agent/                 ← /trello-agent  (ad-hoc board management)
    write-a-skill/                ← /write-a-skill  (structured skill authoring)
    zoom-out/                     ← /zoom-out  (map unfamiliar codebase)
    kos*/                         ← KOS vault skills (installed separately via npx)
  plugins/
    planning-with-files/          ← mid-session persistent memory
    compound-engineering/         ← multi-agent code review
    caveman/                      ← terse response mode
    andrej-karpathy-skills/       ← engineering principles
    pm-*/                         ← PM skills

~/dev/
  .triage-cache                   ← pointer index: project → TODOS.md path + mtime
  .triage-dates                   ← first-seen dates per TODO item (stale detection)
  .memory/
    TRIAGE-BLOCK.md               ← auto-generated priority view across all projects

your-project/
  .claude/
    CLAUDE.md                     ← project-specific context (committed)
    settings.json                 ← project-level permissions (committed)
    settings.local.json           ← local overrides (gitignored)
    trello-board                  ← board name for /sync-trello (gitignored)
  src/                            ← source (structure varies by project type)
  docs/
    prd.md                        ← committed, project north star
  README.md                       ← committed
  TODOS.md                        ← canonical open work — single source of truth (gitignored)
  .memory/
    SESSION-LOG.md                ← checkpoint/handoff narrative (git-crypt encrypted)
  .work/
    PLAN.md                       ← live Goals/Micro-Goals/Tasks + Trello IDs (gitignored)
    FINDINGS.md                   ← research and decisions (gitignored)
    PROGRESS.md                   ← session progress log (gitignored)
  CHANGELOG.md                    ← committed changelog (updated via /changelog)
  KNOWLEDGE.md                    ← committed curated facts about this codebase
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

> **Note:** checklist CRUD PR (`feat/checklist-item-crud`) is open against upstream trello-cli. Until merged, the local fork install above is required.

### Usage

```
/sync-trello [optional board name]
```

Board resolution order:
1. Arg passed inline: `/sync-trello "My Board"`
2. `.claude/trello-board` file in project root (set by `/dev-setup`)
3. Prompt with `trello board:list` output + offer to save

### How it works

Reads `.work/PLAN.md` and for each Goal without a `[trello:ID]` tag:
1. Creates a Trello card at the bottom of "Back Log"
2. Annotates the Goal line immediately with `[trello:CARD_ID]`
3. Creates a checklist for each Micro-Goal
4. Creates a checklist item for each Task

Fully idempotent — re-running skips already-tagged Goals.

See `~/.claude/skills/sync-trello/SKILL.md` for full implementation details.
