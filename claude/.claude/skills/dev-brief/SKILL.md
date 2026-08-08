---
name: dev-brief
description: Morning/context-switch brief across all projects in ~/dev. Reads TODOS.md or .memory/SESSION-LOG.md per project, surfaces open TODOs, live git state, gotchas, decisions, branch, and release-pending signals. Auto-reconciles TODOs against live git state. Triggers on /dev-brief or /dev-brief <project>.
---

# Dev Brief Skill

**Trigger:** `/dev-brief` · `/dev-brief <project>` · `/dev-brief triage`

## Modes

- **Default** — full sweep of all `~/dev` projects. One block per project with session-log. Orphans listed at bottom. Triage Block at end.
- **Deep-dive** (`/dev-brief <project>`) — single project. Full re-entry prompt, all TODOs tiered (Critical→High→Medium→Low→Backlog) and tag-grouped within each tier. Skip cross-project Triage Block.
- **Triage-only** (`/dev-brief triage`) — cache repair. Full discovery + reconcile, output Triage Block only (no project blocks, no orphans), then run `update-triage` (instruction 9).

---

## Steps

### Step 1 — Discover projects

```bash
find ~/dev -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
```

Active = has `TODOS.md`, `.memory/SESSION-LOG.md`, or `session-log.md`. None = orphan.

**Format detection (per project, not once):** dev-brief sweeps every repo in
`~/dev`, and each repo can independently be flat or new-format. Check
`~/.claude/references/planning-format-detect.md`'s cross-repo form —
`test -d ~/dev/<project>/.work/plan` — for EACH project during discovery, never
once for the whole sweep. As of the pilot, dotfiles is the only new-format repo;
the dominant path across `~/dev` is FLAT.

### Step 2 — Per project: cache gate → data

**Cache gate (mtime read-skip):**

```bash
live=$(stat -c %Y "$log" 2>/dev/null)
cached=$(awk -v want="$proj" '/^## /{cur=substr($0,4);next} /^mtime:/&&cur==want{sub(/^mtime:[[:space:]]*/,"");print;exit}' ~/dev/.triage-cache 2>/dev/null)
```

- `live` empty → **GONE**: drop project's cache block, omit from brief
- `cached` empty → **READ** (cold)
- `live > cached` → **READ** (changed)
- `live <= cached` → **HIT**: load open-TODO lines from `.triage-cache` block; skip log read

**Cache format** (`~/dev/.triage-cache`):

```
## [dotfiles]       ← pointer format (TODOS.md project)
mtime: 1780324513
path: /home/k0d3x/dev/dotfiles/TODOS.md

## batctrl          ← legacy format (session-log project)
mtime: 1780189650
- [ ] [BUG] ...
```

**On READ:**

- **First, per file: apply `~/.claude/references/git-crypt-lock-check.md`.** A git-crypt-locked planning file is ciphertext — skip + flag it, never parse it as content. One locked repo skips only its own files; the rest of the sweep proceeds.
- `TODOS.md` exists, FLAT-FORMAT project: read `- [ ]` lines for TODOs; read session-log latest block for date, Gotchas, Decisions, Re-Entry Prompt.
- `TODOS.md` exists, NEW-FORMAT project: read `- [ ]` index lines for TODOs (title + tags only — do not open `.work/todos/<slug>.md` detail files during the sweep; that expansion is deep-dive-only, see Re-Entry Prompt splice below). Session-log read is unchanged either format.
- No `TODOS.md`: parse session-log latest block for all of the above.
- Latest block = highest date in `## Session Handoff/Checkpoint — {date}` headers — never assume position (kos is newest-at-bottom; others vary).
- Re-Entry Prompt: stored as prose + pointer to TODOS.md. **Splice on render** (deep-dive only): expand that pointer — inline every `- [ ]` item so the pasted prompt is self-contained.

**After READ — refresh cache (mandatory, including triage mode):**

- TODOS.md project: `update-cache <project> <todos_path>`
- Legacy project: rewrite `## {project}` block with verbatim open-TODO lines + fresh `mtime:` = `stat -c %Y` taken _after_ any Step 3 self-heal write.
- Re-`stat` to confirm written mtime == live. Unrefreshed block re-reads forever.

**Git (run in parallel):**

```bash
git -C ~/dev/<project> branch --show-current 2>/dev/null
git -C ~/dev/<project> status --short 2>/dev/null | wc -l
git -C ~/dev/<project> log @{u}.. --oneline 2>/dev/null | wc -l
```

Not a git repo → `not a git repo`. No upstream → `no upstream`.

**Release pending:** `[ -s ~/dev/<project>/RELEASE-NOTES.md ] && echo "RELEASE PENDING"`

**`.work/PLAN.md`:** if present, FLAT-FORMAT project: merge `- [ ]` items into
TODOs labeled `[plan]`. NEW-FORMAT project: `.work/PLAN.md` index lines use
`<status> — Goal <N>: <title>` (no `- [ ]` checkbox — see
`~/.claude/references/planning-format-detect.md`), so merge `open`/`in-progress`
status lines into TODOs labeled `[plan]` instead; skip `done` lines.

**KNOWLEDGE.md (deep-dive only):** if `KNOWLEDGE.md` exists in the project root, read it. Surface entries under a `### Knowledge` section in the deep-dive output, before the TODOs tiers.

### Step 3 — Reconcile TODOs against git

Git always live (never cached). Compare open TODOs (from cache on HIT, from log on READ).

**Auto-resolve:**

| Git condition                  | TODO text matches                                                                 | Action       |
| ------------------------------ | --------------------------------------------------------------------------------- | ------------ |
| `git log @{u}..` = 0 commits   | `push`, `unpushed`, `commits ahead`, `push to remote`, `ahead of origin`          | Auto-resolve |
| `git status --short` = 0 files | `uncommitted`, `not yet committed`, `stage`, `dirty`, `git add`, `commit changes` | Auto-resolve |

Auto-resolve = remove from `TODOS.md` (or mark `[x]` in session-log + append ` *(auto-resolved by dev-brief {YYYY-MM-DD})*`). NEW-FORMAT project: remove BOTH the index line and its `.work/todos/<slug>.md` detail file if one exists. Show `✓` in output. Skip ambiguous intent. Only touch latest session block. Refresh cache with post-write mtime immediately after.

**Step 3b — Fix-commit flags (advisory only, never written):**

For open `[BUG]`/`[FEAT]`/`[RELEASE]` TODOs in latest block:

```bash
git -C ~/dev/<repo> log --since="<block-date>" --no-merges --pretty='%h %s' --name-only 2>/dev/null
```

`[dotfiles]` TODOs: also scan any repo named in the TODO text — dotfiles items frequently describe work that lands in another repo.

Flag on high-signal match only: filename from TODO in commit's changed paths, OR ≥2 distinctive content words shared between TODO and commit subject. Prefix with `⚑`, append ` — possibly resolved by <hash>(<repo>) — verify`. Report flag count separately from auto-resolved count. Skip `[DECISION]`/`[INVESTIGATE]`/`[CHORE]`/`[DOCS]` — don't close via code commit.

### Step 4 — Flag urgent TODOs

Flag `⚠` if TODO contains (case-insensitive):
`failing` · `broken` · `not yet` · `do not` · `DO NOT` · `warning` · `stale` · `never` · `never committed` · `bug` · `error` · `unresolved` · `critical` · `missing` · `haven't` · `has not` · `hasn't`

### Step 5 — Staleness

Parse date from `## Session Handoff/Checkpoint — {date}`. Days since today. Mark `[STALE]` if >7 days.

### Step 6 — Priority triage

Tiers recomputed fresh every run (never cached). Tag-first, keyword fallback for untagged.

**Tag → tier** (full tag table in `~/.claude/CLAUDE.md`):
`[BROKEN]` → Critical · `[TEST]` → Critical · `[BLOCKER]` → High · `[LOW]` → Low · `[BACKLOG]` → Backlog · untagged → Medium · `[BROKEN]`+`[BLOCKER]` together → Critical

**Keyword fallback (untagged TODOs only):**

| Tier     | Condition                                                                                                                 |
| -------- | ------------------------------------------------------------------------------------------------------------------------- |
| Critical | ⚠-flagged AND text has: `broken`, `failing`, `can't work`, `not working`, `crashed`, `down`                               |
| High     | ⚠-flagged (not Critical) · OR text has: `blocker`, `blocks`, `blocked`, `critical` · OR `[STALE]` project with open TODOs |
| Low      | text has: `consider`, `evaluate`, `low priority`, `nice to have`, `when ready`, `no rush`                                 |
| Backlog  | text has: `someday`, `eventually`, `future`, `parked`, `long-term`, `backlog`                                             |
| Medium   | everything else                                                                                                           |

**Line format:** `  [project]  {annotation tags} {todo text — 70 chars max, truncate with …}`
Strip priority tags from displayed text (tier already shows it). Sort within tier: ⚠/`[BROKEN]` first, then alpha by project. Omit empty tiers. Omit `✓` auto-resolved items.

**Deep-dive:** same tier headers, tag-grouped within each tier (`[BUG]`, `[FEAT]`, `[CHORE]`, etc. — untagged under `[misc]`). ⚠/⚑ items first within each group. `✓` items listed once at bottom untiered.

**Zero open TODOs:** show `· (no open TODOs)` — never skip silently. No `### Incomplete` section → show `· (no TODO section found)`.

### Step 7 — Print output

- **Default:** see `templates/format-default.md`
- **Deep-dive:** see `templates/format-deep-dive.md`
- **Triage:** header `TRIAGE — {YYYY-MM-DD}` · `{Y} open TODOs across {N} projects` · Triage Block (same structure as end of default). Then run `update-triage` (instruction 9).

---

## Claude Instructions

1. Execute immediately — no clarifying questions.
2. Cache gate before every log read. Refresh after every READ is mandatory — unrefreshed block re-reads forever. Deep-dive always READs its single target (skip gate).
3. Latest session = highest date in block headers; never assume by position.
4. Orphans = directories only. Root files are never listed — `~/dev` itself is not a project.
5. Output: plain markdown, no code-block wrapper.
6. Fix-commit flags (Step 3b): advisory only — never written, never auto-closed, recomputed each run.
7. Triage Block: default mode only, after orphans list. Deep-dive skips it.
8. Dev dir = `~/dev/`. Never prompt for path.
9. Triage mode: after terminal output, run `update-triage` via Bash — script writes HTML to `~/dev/.memory/TRIAGE-BLOCK.md`. Do not generate HTML directly.
10. `[BUG]` Triage item → append `→ /diagnose`. `[TEST]` → append `→ /tdd`.
11. Deep-dive: if `KNOWLEDGE.md` exists in project root, read and show it. Section header: `### Knowledge`. Place before TODOs tiers.
