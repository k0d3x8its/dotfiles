---
name: dev-setup
description: Per-project setup wizard for any new project. Creates .claude/CLAUDE.md, scaffolds folder structure, initializes planning files, configures .gitignore, sets up GitHub repo, and walks through every step so nothing is forgotten. Triggers on /dev-setup.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# KOS Project Setup Wizard

**Trigger:** `/dev-setup`
**Purpose:** Complete per-project setup in one guided run. Never requires remembering steps.

---

## What This Skill Does

1. Confirms project root and name
2. Collects project type, stack, and description
3. Scaffolds folder structure based on project type
4. Creates `README.md`
5. Creates `.claude/CLAUDE.md` from template
6. Scaffolds `.claude/settings.json` with baseline permissions
7. Configures `.claude/trello-board` for `/sync-trello`
8. Initializes planning files: `task_plan.md`, `findings.md`, `progress.md`, `session-log.md`, `RELEASE-NOTES.md`
9. Creates `.gitignore`
10. Checks git / offers `git init`
11. Offers GitHub repo creation via `gh`
12. Reminds about `/ce-setup`
13. Prints completion summary

---

## Wizard Steps

Ask **one question at a time**. Each step shows a default — user accepts or overrides. Check before overwriting any existing file.

---

### Step 1: Confirm project root

Show current directory:
> "Setting up project in: `[cwd]`
> Correct root? (yes / provide different path)"

If different path given, use it for all subsequent operations.

### Step 2: Project name

> "Project name? Used in CLAUDE.md, README, and task_plan.md."
> Default: directory basename

### Step 3: One-line description

> "One sentence: what does this project do?"
> Default: "TBD"

Used in README and CLAUDE.md.

### Step 4: Project type

> "Project type?"
> 1. Web app (frontend / fullstack)
> 2. CLI / backend service
> 3. Library / SDK
> 4. Script / automation
> 5. Other (describe briefly)

Record — used for folder scaffold and .gitignore.

### Step 5: Tech stack

> "Primary language and key frameworks? (e.g. TypeScript + Next.js, Python + FastAPI)"
> Default: "TBD"

---

### Step 6: Scaffold folder structure

Based on project type, create these directories (skip any that already exist):

| Type | Directories |
|---|---|
| Web app | `src/`, `public/`, `docs/` |
| CLI / backend | `src/`, `tests/`, `docs/` |
| Library / SDK | `src/`, `tests/`, `docs/`, `examples/` |
| Script / automation | `scripts/`, `docs/` |
| Other | Ask: "Which directories should I create?" |

Place a `.gitkeep` in each empty directory so they appear in git.

Print what was created.

---

### Step 7: Create README.md

Check if `README.md` exists — if so, ask before overwriting.

Write:
```markdown
# [Project Name]

[One-line description]

## Stack
[Tech stack]

## Getting Started
_TODO_

## Project Structure
[List the directories created in Step 6 with one-line descriptions]
```

---

### Step 8: Create .claude/CLAUDE.md

Check if `.claude/CLAUDE.md` exists — if so, ask before overwriting.

Create `.claude/` if it doesn't exist. Write:

```markdown
# [Project Name] — Claude Config

## Project Overview
**Type:** [project type]
**Stack:** [tech stack]
**Goal:** [one-line description]

## Conventions
- Commit format: conventional commits (feat:, fix:, docs:, chore:)
- Branch naming: feature/, fix/, docs/, chore/
- NEVER add `Co-Authored-By` lines to commit messages
- Code comments: explain the why, not the what

## Trello
- Board: [board name, or "not configured — run /sync-trello to set up"]

## Skills
- `/sync-trello` — push task_plan.md Goals to Trello
- `/handoff`     — end-of-session context preservation
- `/plan`        — create/update task_plan.md

## Session Rules
- Always read task_plan.md, findings.md, and progress.md if they exist
- When I paste a re-entry prompt, treat it as ground truth for project state

## Current State
See task_plan.md for active goals and progress.
See session-log.md for recent session history.
```

---

### Step 9: Scaffold .claude/settings.json

Check if `.claude/settings.json` exists — if so, ask before overwriting.

Write a baseline that pre-approves common read-only and low-risk tool calls so they don't trigger approval prompts every session:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git log*)",
      "Bash(git diff*)",
      "Bash(git branch*)",
      "Bash(ls*)",
      "Bash(find*)",
      "Bash(grep*)",
      "Bash(cat*)",
      "Bash(echo*)",
      "Bash(pwd)",
      "Bash(which*)",
      "Bash(trello*)"
    ],
    "deny": []
  }
}
```

Tell the user:
> "Add more permissions anytime with `/update-config` or by editing `.claude/settings.json` directly."

---

### Step 10: Configure Trello board

> "Which Trello board should this project sync to? (I'll save it so /sync-trello works automatically.)"
> Run `trello board:list --format json` and show board names.
> Option to skip.

If selected: write board name to `.claude/trello-board`.
If skipped: note in summary that `/sync-trello` will ask at runtime.

---

### Step 11: Initialize planning files

Check which of these exist: `task_plan.md`, `findings.md`, `progress.md`, `session-log.md`, `RELEASE-NOTES.md`

For each missing file, create it (no prompt needed — these are always wanted):

**task_plan.md:**
```markdown
# Task Plan: [Project Name]

## Goal: [First goal — fill this in]

### Micro-Goal: [First milestone]
- [ ] First task
```

**findings.md:**
```markdown
# Findings: [Project Name]

## [Date]
_Add research findings, decisions, and discovered constraints here._
```

**progress.md:**
```markdown
# Progress: [Project Name]

## Session: [Date]
- **Status:** in_progress
- Actions taken:
```

**session-log.md:**
```markdown
# Session Log
> Auto-generated by session-handoff skill. Do not edit manually mid-session.
---
```

**RELEASE-NOTES.md:**
```markdown
# Release Notes (Scratch)
> Accumulated by session-handoff. Consumed by /release-notes. Never committed.
---
```

Print which files were created (skip already-existing ones silently).

---

### Step 12: Create .gitignore

Check if `.gitignore` exists — if so, ask before overwriting.

Write a baseline appropriate to the project type. Always include this core block:

```gitignore
# Environment & secrets
.env
.env.*
!.env.example

# Claude Code — local/ephemeral files (not project code)
.claude/trello-board
.claude/settings.local.json
.claude/plugins/
.claude/skills/

# Planning & session files (local context, not source)
task_plan.md
findings.md
progress.md
session-log.md
RELEASE-NOTES.md

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp
*.swo
```

Append type-specific additions:

| Type | Additional entries |
|---|---|
| Web app | `node_modules/`, `dist/`, `.next/`, `build/`, `coverage/` |
| CLI / backend | `node_modules/`, `dist/`, `build/`, `__pycache__/`, `*.pyc`, `venv/`, `.venv/` |
| Library / SDK | `node_modules/`, `dist/`, `coverage/`, `*.egg-info/` |
| Script / automation | `__pycache__/`, `*.pyc`, `venv/`, `.venv/`, `*.log` |

---

### Step 13: Git check

Run `git status`.

- **Repo exists:** print "✓ Git initialized" and show current branch.
- **No repo:** ask:
  > "No git repo detected. Run `git init`? (yes / skip)"
  
  If yes: run `git init`, set `main` as default branch (`git init -b main`).

---

### Step 14: GitHub repo setup

Ask:
> "Create a GitHub repo for this project? Requires `gh` CLI."

If yes, ask:
> "Visibility?"
> 1. Private
> 2. Public

Run:
```bash
gh repo create [project-name] --[private|public] --source=. --remote=origin --push
```

If `gh` is not installed or not authenticated, print:
> "`gh` not found or not authenticated. Run `gh auth login` first, then create the repo manually with:
> `gh repo create [project-name] --private --source=. --remote=origin --push`"

If skipped: note in summary.

---

### Step 15: Remind about /ce-setup

Always print — regardless of other choices:
```
─────────────────────────────────────────────
 Next: run /ce-setup in this project
─────────────────────────────────────────────
 /ce-setup wires up compound-engineering
 (branch strategy, PR workflow, commit hooks).
 Run it once per project. Manual step.
─────────────────────────────────────────────
```

---

### Step 16: Completion summary

```
✓ [Project Name] is ready.

Created:
  [Project Type] folder structure: [dirs]
  README.md
  .claude/CLAUDE.md
  .claude/settings.json
  .claude/trello-board → "[board]"  (or: not configured)
  task_plan.md, findings.md, progress.md, session-log.md, RELEASE-NOTES.md
  .gitignore
  Git: [initialized / already existed]
  GitHub: [repo URL / skipped]

What's next:
  → /ce-setup          run once to wire up compound-engineering
  → /plan              build out task_plan.md with your Goals
  → /sync-trello       push Goals to Trello
  → /handoff           run at ~50 min to preserve session context
```

---

## Notes

- Safe to re-run. Checks before overwriting every file.
- `.claude/` created automatically if missing.
- `RELEASE-NOTES.md` is consumed by `/release-notes` and written to by `/handoff`. Never commit it.
- `.claude/trello-board` contains a board name — excluded from git via `.gitignore`.
- Project-level `.claude/CLAUDE.md` is separate from global `~/.claude/CLAUDE.md`. Both are active.
