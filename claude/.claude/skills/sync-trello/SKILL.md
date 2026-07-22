---
name: sync-trello
description: Sync .work/PLAN.md to Trello — Goals→cards, Micro-Goals→checklists, Tasks→items. Idempotent (skips Goals tagged [trello:ID]); annotates .work/PLAN.md after each card. Board resolved per-project. Triggers on /sync-trello.
allowed-tools:
  - Bash
  - Read
  - Edit
---

# Sync Trello Skill

**Trigger:** `/sync-trello [board name]`
**Purpose:** Push Goals from `.work/PLAN.md` into Trello as cards with checklists and checklist items. Idempotent — already-synced Goals are skipped.

---

## .work/PLAN.md Format

This skill expects the following hierarchy in `.work/PLAN.md`:

```markdown
## Goal: [Goal name] [trello:CARD_ID] ← [trello:ID] appended after first sync

### Micro-Goal: [Micro-Goal name]

- [ ] Task one
- [ ] Task two
- [x] Task three (completed — still synced as a checklist item)

### Micro-Goal: [Another name]

- [ ] Task four
```

**Mapping:** see **Trello Sync Rules** in `~/.claude/CLAUDE.md` (canonical) for the Goal→card / Micro-Goal→checklist / Task→item rule and the `[trello:ID]` skip rule. Skill-specific detail: both `- [ ]` and `- [x]` lines become checklist items (completed tasks still sync).

---

## Sync Algorithm

### Step 1: Read .work/PLAN.md

Read `.work/PLAN.md` from the current working directory. If missing, stop:

> "No .work/PLAN.md found. Create one first, or run /plan to generate one."

**Format detection (D12):** check `~/.claude/references/planning-format-detect.md`
(`test -d .work/plan`).

- **FLAT-FORMAT** (no `.work/plan/`): `.work/PLAN.md` holds the full Goal body
  directly — continue with Steps 2-5 below unchanged, scanning `.work/PLAN.md` itself
  for `## Goal:` lines and `[trello:ID]` tags.
- **NEW-FORMAT** (`.work/plan/` exists, D9a): `.work/PLAN.md` is a lean index only —
  it has no `[trello:ID]` tags and no Goal bodies. Instead: read the index for each
  Goal's pointer to its detail file (`.work/plan/<goal-slug>.md` or
  `.work/plan/<epoch-slug>/<goal-slug>.md`), open that detail file, and check for
  `[trello:CARD_ID]` there — the tag lives in the detail file, not the index line.
  All of Steps 3-5's per-Goal logic (skip-if-tagged, create card, annotate,
  checklists/items) runs identically, just reading from and writing to the detail
  file instead of `.work/PLAN.md` directly. Epoch grouping (D6) stays untracked in
  Trello — the Goal remains the card unit regardless of Epoch membership; a
  per-Epoch label is a documented escape hatch, not built.

### Step 2: Resolve the board

**If the user passed a board name as an argument** (e.g., `/sync-trello "My Project Board"`): use it directly.

**If `.claude/trello-board` exists** in the project root: read the board name from that file and use it.

**Otherwise**: run `trello board:list --format json`, display the board names, and ask:

> "Which Trello board should I sync to? I can save your choice to `.claude/trello-board` so you don't have to pick again."

If the user agrees to save: write the board name (just the name, no quotes) to `.claude/trello-board`.

Record the resolved board name — use it for every subsequent command in this run.

### Step 3: Parse Goals

Scan `.work/PLAN.md` for lines matching `## Goal:`. For each Goal:

- Extract the Goal name (text after `## Goal:`, strip any trailing `[trello:...]` tag)
- Check if a `[trello:CARD_ID]` tag already exists on that line
- Collect all Micro-Goals and Tasks nested under this Goal (until the next `## Goal:` or end of file)

### Step 4: Sync each Goal

For each Goal, in document order:

#### 4a. Skip if already synced

If `[trello:CARD_ID]` tag exists → skip this entire Goal. Print:

```
⏭  Skipping "[Goal name]" — already synced [trello:ID]
```

#### 4b. Create the card

```bash
trello card:create -n "[Goal name]" --board "[board]" --list "Back Log" --position bottom --format json
```

Capture the returned card ID from JSON output.

#### 4c. Annotate .work/PLAN.md immediately

Edit the Goal line to append the card ID **before** creating checklists. This ensures the ID is saved even if later steps fail.

Before: `## Goal: Implement login flow`
After: `## Goal: Implement login flow [trello:abc123def456]`

#### 4d. Create checklists and items

For each Micro-Goal under this Goal, in document order:

1. Create the checklist:

```bash
trello card:checklist \
  --board "[board]" \
  --list "Back Log" \
  --card "[Goal name]" \
  -n "[Micro-Goal name]"
```

2. For each Task under this Micro-Goal:

```bash
trello card:add-checklist-item \
  --board "[board]" \
  --list "Back Log" \
  --card "[Goal name]" \
  --checklist "[Micro-Goal name]" \
  --item "[Task text]"
```

Task text is the raw text after `- [ ] ` or `- [x] `. Do not include the checkbox prefix.

Tasks outside any Micro-Goal are ignored — they have no checklist to belong to.

### Step 5: Report

```
✓ Synced [N] card(s) to "[board]"
⏭  Skipped [N] already-synced Goal(s)
→ .work/PLAN.md annotated with card IDs
```

---

## Error Handling

- `card:create` fails → print exact error, skip checklists for that Goal, continue to next Goal
- `card:checklist` fails → print error, skip items for that Micro-Goal, continue to next Micro-Goal
- `card:add-checklist-item` fails → print error, skip that item, continue
- Never retry a failed command
- Never write to .work/PLAN.md unless `card:create` succeeded (step 4c only runs on success)

---

## Notes

- Board name is resolved once per run
- List names must exist on the target board — standard KOS Kanban columns are defined in `~/.claude/CLAUDE.md`. Any board layout works as long as a `Back Log` list exists (or the user is asked which list to use)
- If a Goal name contains special characters or quotes, prefer using the card ID (from `[trello:ID]` tag) as the `--card` value on retry
- `.claude/trello-board` is project-local — different projects can point to different boards
