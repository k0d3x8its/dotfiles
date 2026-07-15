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
8. Initializes planning files: `.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `.memory/SESSION-LOG.md`, `CHANGELOG.md`
9. Creates `KNOWLEDGE.md` — curated facts, committed with the repo
10. Creates `.gitignore`, or append-if-missing merges into an existing one
11. Checks git / offers `git init`
12. Offers git-crypt init + `.gitattributes` for encrypted planning files
13. Offers GitHub repo creation via `gh`
14. Reminds about `/ce-setup`
15. Prints completion summary

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

Static templates (`settings.json`, `SESSION-LOG.md` (written to `.memory/`), `CHANGELOG.md`, `gitignore.core`)
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

> "Project name? Used in CLAUDE.md, README, and .work/PLAN.md."
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
> `~/.claude/references/code/CODE-REFERENCE.md`."

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

Check which of these exist: `.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `.memory/SESSION-LOG.md`, `CHANGELOG.md`

For each missing file, write the matching `templates/<name>` (no prompt — always wanted):

Create `.work/` with `mkdir -p .work` before writing files there.

| Template | Destination | Tokens to substitute |
|---|---|---|
| `task_plan.md` | `.work/PLAN.md` | `{{PROJECT_NAME}}` |
| `findings.md` | `.work/FINDINGS.md` | `{{PROJECT_NAME}}`, `{{DATE}}` |
| `progress.md` | `.work/PROGRESS.md` | `{{PROJECT_NAME}}`, `{{DATE}}` |
| `SESSION-LOG.md` | `.memory/SESSION-LOG.md` | none (static) |
| `CHANGELOG.md` | `CHANGELOG.md` | none (static) |

Create `.memory/` if it does not exist (`mkdir -p .memory`) before writing `SESSION-LOG.md` there.

Print which files were created (skip already-existing ones silently).

---

### Step 12: Create KNOWLEDGE.md

Check if `KNOWLEDGE.md` exists in the project root — if not, write `templates/KNOWLEDGE.md` (substitute `{{PROJECT_NAME}}`) to `KNOWLEDGE.md`.

`KNOWLEDGE.md` is **committed with the repo** — not a session artifact. Do **not** add it to `.gitignore`.

Print `✓ KNOWLEDGE.md created` if written, skip silently if it already exists.

---

### Step 13: Create / merge .gitignore

The required entry set = `templates/gitignore.core` (static) **plus** the type-specific block below:

| Type | Additional entries |
|---|---|
| Web app | `node_modules/`, `dist/`, `.next/`, `build/`, `coverage/` |
| CLI / backend | `node_modules/`, `dist/`, `build/`, `__pycache__/`, `*.pyc`, `venv/`, `.venv/` |
| Library / SDK | `node_modules/`, `dist/`, `coverage/`, `*.egg-info/` |
| Script / automation | `__pycache__/`, `*.pyc`, `venv/`, `.venv/`, `*.log` |

**Apply by whether `.gitignore` already exists — never overwrite, never skip wholesale:**

- **No `.gitignore`:** write `gitignore.core` then append the type-specific block. Done.
- **`.gitignore` exists:** **append-if-missing merge** — do NOT overwrite (loses the user's project ignores) and do NOT skip (planning/session files from Step 11 then leak into git, the original bug):
  1. Read the existing `.gitignore`. Build the set of pattern lines already present — compare on the **trimmed, non-comment, non-blank** line so `node_modules/` matches regardless of section or surrounding comments.
  2. From the required set (core + type block), select only patterns **not** already present.
  3. If none are missing → leave the file untouched (idempotent; re-running `/dev-setup` is a no-op here).
  4. If ≥1 missing → append a single marked block at the end:
     ```
     # --- added by /dev-setup ---
     {missing patterns, in core-then-type order}
     ```
     Only the marker line plus the missing patterns. Never reorder, rewrite, or delete existing lines.
  5. If the `# --- added by /dev-setup ---` marker already exists from a prior run, append the newly-missing patterns under that same marker rather than adding a second one.

**Why a marked append-merge:** an existing repo's `.gitignore` is user-authored and must survive; but the Step-11 planning files (`.work/PLAN.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `RELEASE-NOTES.md`) and `.claude/trello-board` MUST be ignored or they leak. `SESSION-LOG.md` lives in `.memory/` and is handled by the git-crypt negation block. Merging the missing lines under a clear marker satisfies both and stays idempotent across re-runs.

**`KNOWLEDGE.md` must NOT be in `.gitignore`** — it is committed source, not a session artifact. If it appears in any existing `.gitignore`, warn the user and do not add it.

---

### Step 14: Git check

Run `git status`.

- **Repo exists:** print "✓ Git initialized" and show current branch.
- **No repo:** ask:
  > "No git repo detected. Run `git init`? (yes / skip)"
  
  If yes: run `git init`, set `main` as default branch (`git init -b main`).

---

### Step 15: git-crypt

Check if `git-crypt` is installed (`which git-crypt`). If not:
> "git-crypt not found. Install it (`brew install git-crypt` / `apt install git-crypt`) then re-run this step, or skip."
> Option to skip.

If installed, check if `.gitattributes` already exists with `filter=git-crypt` entries — if so, print "✓ git-crypt already configured" and skip.

Otherwise ask:
> "Initialize git-crypt to encrypt planning/session files? (yes / skip)"
> "These files will be encrypted at rest: KNOWLEDGE.md, TODOS.md, .memory/SESSION-LOG.md, .work/FINDINGS.md, .work/PROGRESS.md, .work/PLAN.md"

If yes:
1. Run `git-crypt init`
2. Write `templates/gitattributes` to `.gitattributes` (append-if-missing if file exists — never overwrite other rules)
3. Append the following negation block to `.gitignore` (global gitignore ignores these files by default; local negation re-includes them so git-crypt can encrypt them):
   ```
   # git-crypt repo — override global ignore for encrypted planning files
   !KNOWLEDGE.md
   !.memory/SESSION-LOG.md
   !.work/PLAN.md
   !.work/FINDINGS.md
   !.work/PROGRESS.md
   !TODOS.md
   ```
4. Export the key and store in Proton Pass Personal vault:
   - Title: `<repo-name>-gitcrypt`
   - Type: Custom item
   - Note:
     ```
     git-crypt symmetric key for the <repo-name> repo.
     Encrypts planning/session files at rest so they commit safely to a (potentially public) remote.

     The value stored in this item is BASE64-ENCODED — the raw key is binary and cannot be stored as plain text.

     To unlock on a fresh machine (run from inside the repo):
       k="$(mktemp)"; chmod 600 "$k"
       echo '{{ pass://Personal/<repo-name>-gitcrypt/key }}' | pass-cli inject | base64 -d > "$k"
       git-crypt unlock "$k"
       shred -u "$k"

     Run `pass-cli login` first if the CLI is not authenticated.
     ```
   - Section name: `git-crypt`
   - Field name: `key`, type: `hidden`, value: `$(git-crypt export-key - | base64 -w 0)`
   - Command: `pass-cli item create custom --vault-name "Personal" --from-template <json>`
4. Delete temp key file immediately after storing
5. Print: "✓ git-crypt initialized. Key stored in Proton Pass Personal vault as `<repo-name>-gitcrypt`."

**Important:** `.gitattributes` is committed source — do NOT add it to `.gitignore`.

---

### Step 16: GitHub repo setup

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

### Step 17: Remind about /ce-setup

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

### Step 18: Completion summary

```
✓ [Project Name] is ready.

Created:
  [Project Type] folder structure: [dirs]
  README.md
  .claude/CLAUDE.md
  .claude/settings.json
  .claude/trello-board → "[board]"  (or: not configured)
  .work/PLAN.md, .work/FINDINGS.md, .work/PROGRESS.md, .memory/SESSION-LOG.md, CHANGELOG.md
  KNOWLEDGE.md
  .gitignore
  .gitattributes (git-crypt)
  Git: [initialized / already existed]
  git-crypt: [initialized / already existed / skipped]
  GitHub: [repo URL / skipped]

What's next:
  → /ce-setup          run once to wire up compound-engineering
  → /write-plan        build out .work/PLAN.md with your Goals
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
