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
8. Initializes planning files: `task_plan.md`, `findings.md`, `progress.md`, `session-log.md`, `CHANGELOG.md`
9. Creates `.gitignore`
10. Checks git / offers `git init`
11. Offers GitHub repo creation via `gh`
12. Reminds about `/ce-setup`
13. Prints completion summary

---

## Templates

File bodies live in `templates/` next to this skill. Steps below say which template to
write where. Read the template, substitute these tokens, write to the destination:

| Token | Value |
|---|---|
| `{{PROJECT_NAME}}` | Step 2 |
| `{{DESCRIPTION}}` | Step 3 |
| `{{TYPE}}` | Step 4 |
| `{{STACK}}` | Step 5 |
| `{{DIRS_WITH_DESCRIPTIONS}}` | Step 6 dirs, one-line each |
| `{{BOARD}}` | Step 10 board name, or `not configured — run /sync-trello to set up` |
| `{{DATE}}` | today |

Static templates (`settings.json`, `session-log.md`, `CHANGELOG.md`, `gitignore.core`)
have no tokens — copy verbatim.

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
| CLI / backend | `src/`, `tests/`, `docs/`, `docs/adr/` |
| Library / SDK | `src/`, `tests/`, `docs/`, `docs/adr/`, `examples/` |
| Script / automation | `scripts/`, `docs/` |
| Other | Ask: "Which directories should I create?" |

Place a `.gitkeep` in each empty directory so they appear in git.

For CLI/backend and Library/SDK projects, note after scaffolding:
> "`docs/adr/` is active. Record any decision that meets the three-condition ADR gate
> (cost of change is meaningful + future reader would wonder why + alternatives were
> considered). Format: `docs/adr/ADR-0001-short-title.md`. Full schema in
> `~/.claude/references/kos-code-reference.md`."

Print what was created.

---

### Step 7: Create README.md

Check if `README.md` exists — if so, ask before overwriting.
Write `templates/README.md` (substitute `{{PROJECT_NAME}}`, `{{DESCRIPTION}}`, `{{STACK}}`,
`{{DIRS_WITH_DESCRIPTIONS}}`) to `README.md`.

---

### Step 8: Create .claude/CLAUDE.md

Check if `.claude/CLAUDE.md` exists — if so, ask before overwriting. Create `.claude/` if missing.
Write `templates/CLAUDE.md` (substitute `{{PROJECT_NAME}}`, `{{TYPE}}`, `{{STACK}}`,
`{{DESCRIPTION}}`, `{{BOARD}}`) to `.claude/CLAUDE.md`.

---

### Step 9: Scaffold .claude/settings.json

Check if `.claude/settings.json` exists — if so, ask before overwriting.
Copy `templates/settings.json` (static — pre-approves common read-only/low-risk Bash calls so
they don't prompt every session) to `.claude/settings.json`.

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

Check which of these exist: `task_plan.md`, `findings.md`, `progress.md`, `session-log.md`, `CHANGELOG.md`

For each missing file, write the matching `templates/<name>` (no prompt — always wanted):

| Template | Tokens to substitute |
|---|---|
| `task_plan.md` | `{{PROJECT_NAME}}` |
| `findings.md` | `{{PROJECT_NAME}}`, `{{DATE}}` |
| `progress.md` | `{{PROJECT_NAME}}`, `{{DATE}}` |
| `session-log.md` | none (static) |
| `CHANGELOG.md` | none (static) |

Print which files were created (skip already-existing ones silently).

---

### Step 12: Create .gitignore

Check if `.gitignore` exists — if so, ask before overwriting.

Write `templates/gitignore.core` (static) to `.gitignore`, then append the type-specific block:

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
  task_plan.md, findings.md, progress.md, session-log.md, CHANGELOG.md
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
- `CHANGELOG.md` accumulates changes under `## [Unreleased]` via `/handoff`. Commit it — it's tracked source.
- `RELEASE-NOTES.md` is generated output from `/release-notes`. Never commit it (already in `.gitignore`).
- `.claude/trello-board` contains a board name — excluded from git via `.gitignore`.
- Project-level `.claude/CLAUDE.md` is separate from global `~/.claude/CLAUDE.md`. Both are active.
