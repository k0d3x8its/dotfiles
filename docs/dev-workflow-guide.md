# K0d3x Dev Workflow Guide
> Claude Code · Session Management · Project Efficiency

---

## Part 1 — Install Everything

### 1. Session Timer Hook (yours)

```bash
mkdir -p ~/.claude/hooks
cp ~/Downloads/session_timer.py ~/.claude/hooks/session_timer.py
chmod +x ~/.claude/hooks/session_timer.py
```

Merge into `~/.claude/settings.json`:
```json
{
  "hooks": {
    "SessionStart": [
      { "type": "command", "command": "python3 \"$HOME/.claude/hooks/session_timer.py\" session_start 2>/dev/null || true" }
    ],
    "Stop": [
      { "type": "command", "command": "python3 \"$HOME/.claude/hooks/session_timer.py\" stop 2>/dev/null || true" }
    ]
  }
}
```

### 2. Session Handoff Skill (yours)

```bash
mkdir -p ~/.claude/skills
cp ~/Downloads/session-handoff.md ~/.claude/skills/session-handoff.md
```

### 3. Planning With Files

```bash
# Inside a Claude Code session:
/plugin marketplace add OthmanAdi/planning-with-files
/plugin install planning-with-files@planning-with-files
```

Verify it loaded — you should see:
```
[planning-with-files] Ready.
```

### 4. Compound Engineering

```bash
# Inside a Claude Code session:
/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering@compound-engineering-plugin
```

Then run setup once per project:
```
/ce-setup
```

### 5. PM Skills

```bash
# Inside a Claude Code session:
/plugin marketplace add phuryn/pm-skills

# Install all 8 plugins:
/plugin install pm-toolkit@pm-skills
/plugin install pm-product-strategy@pm-skills
/plugin install pm-product-discovery@pm-skills
/plugin install pm-market-research@pm-skills
/plugin install pm-data-analytics@pm-skills
/plugin install pm-marketing-growth@pm-skills
/plugin install pm-go-to-market@pm-skills
/plugin install pm-execution@pm-skills
```

### 6. ccusage Status Bar

Persistent bottom bar showing live session cost, burn rate, and context usage.

```bash
npm install -g ccusage
```

Add `statusLine` to `~/.claude/settings.json` alongside your existing `hooks` block:
```json
{
  "statusLine": {
    "type": "command",
    "command": "npx ccusage statusline",
    "padding": 0
  }
}
```

Restart Claude Code. The bar appears at the bottom of every session:
```
🤖 Sonnet 4.6 | 💰 $0.12 session / $0.84 today | 🔥 $0.08/hr | 🧠 18k (9%)
```

---

## Part 2 — Global CLAUDE.md

Create once at `~/.claude/CLAUDE.md`. Read at the start of every session, globally.

```markdown
# K0d3x Global Claude Config

## Who I Am
Solo developer. Builder. Ubuntu 24.04 (Noble). Tools: Neovim, Nala, Git.
KOS (Kodex OS) is my personal knowledge management system.

## Skills Available
- /handoff or /session-handoff — end-of-session context preservation, logs to session-log.md
- /planning-with-files — mid-session persistent memory (task_plan.md, findings.md, progress.md)
- /release-notes — synthesize RELEASE-NOTES.md entries into polished GitHub prose release notes
- /find-skills — discover and install agent skills via `npx skills find [query]`. Use when asking "is there a skill for X". Browse at https://skills.sh/
- /ce-code-review — 12-agent parallel code review before committing
- /ce-security-audit — security scan for anything touching auth, file I/O, or external input
- /discover — PM-style project scoping for new projects
- /write-prd — generate a structured product requirements document
- /sync-trello — push current Goals from task_plan.md to Trello (card → checklist → items)

## Session Rules
- Track session start time. Warn me at 45 minutes to run /handoff.
- Always read task_plan.md, findings.md, and progress.md if they exist in the project root.
- When I paste a re-entry prompt, treat it as ground truth for project state.

## My Conventions
- Commit messages: conventional commits format (feat:, fix:, docs:, chore:)
- Branch naming: feature/, fix/, docs/, chore/
- All Trello boards use a six-column Kanban: Back Log → To Do → Doing → Review → Testing → Done
- Code comments: always explain the why, not just the what

## Trello Sync Rules
When syncing task_plan.md to Trello, always map as follows:
- Goal       → Trello card (placed in "Back Log", directly under the top card in that list)
- Micro-Goal → Trello checklist on that card
- Task       → Trello checklist item

Always create in order: card first, checklist second, items third.
Before creating, check if a [trello:ID] tag exists on the Goal — if so, skip it.
After creating a card, annotate the Goal in task_plan.md with [trello:CARD_ID].
```

---

## Part 3 — Per-Project Setup

Do this once when you start any new project. Run inside Claude Code from the project root:

```
/dev-setup
```

The wizard walks through every step:

| Step | What it does |
|---|---|
| Project name + description | Used in README and CLAUDE.md |
| Project type + stack | Determines folder structure and .gitignore additions |
| Folder scaffold | Creates `src/`, `docs/`, `tests/` etc. based on type |
| `README.md` | Minimal stub with name, description, structure |
| `.claude/CLAUDE.md` | Project-level Claude config from template |
| `.claude/settings.json` | Baseline permission allowlist (reduces approval prompts) |
| `.claude/trello-board` | Board name for `/sync-trello` auto-resolution |
| Planning files | `task_plan.md`, `findings.md`, `progress.md`, `session-log.md`, `RELEASE-NOTES.md` |
| `.gitignore` | Covers secrets, Claude artifacts, planning files, OS noise |
| Git init | Checks for repo, offers `git init -b main` if missing |
| GitHub repo | Offers `gh repo create` with visibility choice |
| `/ce-setup` reminder | Always printed — must be run manually after |

> `/dev-setup` is safe to re-run. It checks before overwriting any file.

---

### task_plan.md Format

`/sync-trello` reads this hierarchy from `task_plan.md`:

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
- Tasks outside any Micro-Goal are ignored (no checklist to belong to)
- Phases (major project stages) can be used as plain `##` headers for organization — they are not synced to Trello

---

## Part 4 — The Full Workflow (Example Project)

### Scenario
You're building a CLI tool called `kos-cli` — a command-line interface for querying your KOS notes from the terminal.

---

### Step 1: Scope the project (PM Skills)

Before touching any code, open Claude Code in the project root and run:

```
/discover
```

Claude chains four skills: brainstorm → assumptions → prioritize → experiments.
You'll end up with a clear picture of what you're actually building and why.

Then generate a lightweight spec:
```
/write-prd
```

This produces a structured document: goals, non-goals, user stories, success metrics.
Save it as `docs/prd.md` and commit it. This becomes the project's north star.

---

### Step 2: Start a work session

Open Claude Code. Planning-with-files auto-activates. You'll see:
```
[planning-with-files] Ready.
```

If continuing from a previous session, paste your re-entry prompt first:
```
"We're building kos-cli. Last session we scaffolded the CLI entrypoint in
src/cli.py and added argparse. Next: implement the `search` subcommand that
queries notes.db via fuzzy match. Read task_plan.md for full context."
```

Claude re-reads `task_plan.md` and is immediately in context.

---

### Step 3: Work

Claude writes `task_plan.md` automatically as you work using the Goal/Micro-Goal/Task hierarchy:

```markdown
## Goal: Implement search subcommand

### Micro-Goal: Core fuzzy match logic
- [x] Create search.py
- [ ] Write fuzzy_match() function
- [ ] Return ranked results list

### Micro-Goal: CLI wiring
- [ ] Add search subcommand to argparse
- [ ] Connect fuzzy_match() to CLI output
```

Two monitoring layers run passively the entire session:

**Bottom bar (persistent)** — ccusage statusLine:
```
🤖 Sonnet 4.6 | 💰 $0.12 session / $0.84 today | 🔥 $0.08/hr | 🧠 18k (9%)
```

**Inline after every response** — session timer hook:
```
⏱  Session time: 23m 14s
```

---

### Step 4: Sync Goal to Trello

When a Goal is ready to be tracked on your board, run:

```
/sync-trello
```

Claude reads `task_plan.md`, finds all Goals without a `[trello:ID]` tag, and cascades:

```bash
# Claude runs these automatically via trello-cli:
trello card:create -n "Implement search subcommand" --board "My Board" --list "Back Log" --format json
# → captures card ID: abc123

trello card:checklist --board "My Board" --list "Back Log" --card "Implement search subcommand" -n "Core fuzzy match logic"
trello card:checklist --board "My Board" --list "Back Log" --card "Implement search subcommand" -n "CLI wiring"

trello card:add-checklist-item --board "My Board" --list "Back Log" --card "Implement search subcommand" \
  --checklist "Core fuzzy match logic" --item "Write fuzzy_match() function"
trello card:add-checklist-item --board "My Board" --list "Back Log" --card "Implement search subcommand" \
  --checklist "Core fuzzy match logic" --item "Return ranked results list"
# ...and so on for every Micro-Goal and Task
```

After sync, `task_plan.md` is annotated:
```markdown
### Goal: Implement search subcommand [trello:abc123]
```

Running `/sync-trello` again skips any Goal already tagged — fully idempotent.

---

### Step 5: Code review before committing

You've implemented the `search` subcommand. Before committing:

```
/ce-code-review
```

12 parallel sub-agents review your code simultaneously — logic, edge cases,
naming, efficiency, test coverage gaps. Claude presents findings and applies fixes.

For anything touching auth, file I/O, or external input:
```
/ce-security-audit
```

---

### Step 6: 45-minute mark

Timer fires:
```
⚠️  45 minutes elapsed — consider running /handoff soon to preserve cache.
```

Reach a logical stopping point, then:

```
/handoff
```

Claude writes to `session-log.md`:

```markdown
---
## Session Handoff — 2026-05-26 14:32

### Goal
Implement the `search` subcommand for kos-cli with fuzzy matching against notes.db.

### Completed
- [x] Scaffolded CLI entrypoint in src/cli.py
- [x] Implemented `search` subcommand with argparse
- [x] Fuzzy match logic against notes.db via rapidfuzz
- [x] Synced Goal to Trello [trello:abc123]

### Incomplete / Next Steps
- [ ] Add --tag filter flag to search subcommand
- [ ] Write unit tests for fuzzy_match()
- [ ] Hook up results formatter (currently just raw print)

### Decisions Made
- **Used rapidfuzz over fuzz** — 10x faster on large note sets, same API
- **SQLite FTS5 rejected** — overkill for current note volume, revisit at 10k+ notes

### Files Touched
- `src/cli.py` — added search subcommand and argparse wiring
- `src/search.py` — new file, fuzzy match core logic
- `requirements.txt` — added rapidfuzz
- `task_plan.md` — updated with Trello card ID [trello:abc123]

### Gotchas / Notes
- notes.db path is currently hardcoded to ~/.kos/notes.db — needs env var or config file
- rapidfuzz returns float scores, not int — don't compare with == 100

### Re-Entry Prompt
"kos-cli project. Implemented search subcommand with fuzzy match via rapidfuzz
in src/search.py. Synced to Trello [trello:abc123]. Next: add --tag filter flag,
write unit tests for fuzzy_match(), fix hardcoded notes.db path. Read task_plan.md first."
---
```

Copy the re-entry prompt. Then:
```
/clear
```

---

### Step 7: Next session

New session opens. Paste the re-entry prompt. Claude reads `task_plan.md`.
You're back at full context in 10 seconds instead of 10 minutes.

---

## Part 5 — Quick Reference

| When | What |
|---|---|
| Starting a new project | `/dev-setup` → `/discover` → `/write-prd` |
| Continuing a session | Paste re-entry prompt |
| During work (passive) | planning-with-files + ccusage bar + timer hook run automatically |
| Want current cost/burn | Glance at bottom status bar |
| Want elapsed time | Glance at inline timer after last response |
| Goal is ready to track | `/sync-trello` |
| Before committing code | `/ce-code-review` |
| Anything touching security | `/ce-security-audit` |
| 45-minute timer fires | `/handoff` → `/clear` |
| Returning after a long break | Open `session-log.md` → copy re-entry prompt |

---

## Part 6 — What Goes Where

```
~/.claude/
  CLAUDE.md                ← global standing orders (edit once)
  settings.json            ← hooks config (session timer + ccusage statusLine)
  hooks/
    session_timer.py       ← inline timer + 45/55 min warnings
  skills/
    session-handoff/       ← /handoff skill
    sync-trello/           ← /sync-trello skill
    dev-setup/             ← /dev-setup per-project wizard
    trello-agent/          ← trello-agent skill (full CLI reference)
    kos*/                  ← KOS vault skills
  plugins/
    planning-with-files/   ← mid-session persistent memory
    compound-engineering/  ← code review agents
    pm-*/                  ← PM skills

your-project/
  .claude/
    CLAUDE.md              ← project-specific context (committed)
    settings.json          ← project-level permissions (committed)
    settings.local.json    ← local overrides (gitignored)
    trello-board           ← board name for /sync-trello (gitignored)
  src/                     ← source (structure varies by project type)
  docs/
    prd.md                 ← committed, your project north star
  README.md                ← committed
  session-log.md           ← handoff history (gitignored)
  task_plan.md             ← live Goals/Micro-Goals/Tasks + Trello IDs (gitignored)
  findings.md              ← research and decisions (gitignored)
  progress.md              ← session progress log (gitignored)
  RELEASE-NOTES.md         ← scratch pad for /release-notes (gitignored)
  .gitignore               ← covers all Claude artifacts, secrets, OS noise
```

---

## Part 7 — Trello Sync

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

### Usage

```
/sync-trello [optional board name]
```

Board resolution order:
1. Arg passed inline: `/sync-trello "My Board"`
2. `.claude/trello-board` file in project root (set by `/dev-setup`)
3. Prompt with `trello board:list` output + offer to save

### How it works

Reads `task_plan.md` and for each Goal without a `[trello:ID]` tag:
1. Creates a Trello card in "Back Log"
2. Annotates the Goal line immediately with `[trello:CARD_ID]`
3. Creates a checklist for each Micro-Goal
4. Creates a checklist item for each Task

Fully idempotent — re-running skips already-tagged Goals.

See `~/.claude/skills/sync-trello/SKILL.md` for full implementation details.
