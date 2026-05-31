# K0d3x Global Claude Config

## Who I Am
Solo developer. Builder. Ubuntu 24.04 (Noble). Tools: Neovim, Nala, Git.
KOS (Kodex OS) is my personal knowledge management system.

## Skills Available
The harness auto-lists every custom skill + its description each session — names below are the slash aliases, not re-described here. Tag routing lives in the TODO Tags table.
`/handoff` `/dev-brief` `/planning-with-files` `/release-notes` `/find-skills` `/diagnose` `/tdd` `/prototype` `/sync-trello`
External (not auto-surfaced): `/ce-code-review` `/ce-security-audit` `/discover` `/write-prd`

## Session Rules
- Track session start time. Warn me at 45 minutes to run /handoff.
- Always read task_plan.md, findings.md, and progress.md if they exist in the project root.
- When I paste a re-entry prompt, treat it as ground truth for project state.
- CHANGELOG on [machine] sessions, route by what changed: if the session modified files under `~/dev/dotfiles/`, prepend a changelog entry to `~/dev/dotfiles/CHANGELOG.md` under `## [Unreleased]`; if the changes were machine-only (no dotfiles impact), skip — don't ask.

## TODO Tags

When writing TODOs to session-log.md (via /handoff or inline), prefix items with the appropriate tags. Tags combine freely: `[BROKEN][BUG]`, `[BLOCKER][DECISION]`, etc.

**Priority tags** — control which Triage Block tier the item lands in:

| Tag | Meaning | Tier |
|---|---|---|
| `[BROKEN]` | Something is broken right now — tool down, build failing, can't work | Critical |
| `[BLOCKER]` | Must happen before other work can start | High |
| `[LOW]` | Not urgent — do soon but not this week | Low |
| `[BACKLOG]` | Captured, deferred, no timeline | Backlog |

No priority tag = Medium (default).

**Annotation tags** — describe the type of work so Claude enters the right mode:

| Tag | Meaning | How Claude responds |
|---|---|---|
| `[BUG]` | Fix a broken thing | Use `/diagnose` — feedback loop → RCA → fix → post-mortem |
| `[FEAT]` | New feature or capability | Design/build mode |
| `[CHORE]` | Cleanup, refactor, maintenance | Low-energy batching candidate |
| `[TEST]` | Write or fix tests | Use `/tdd` — red-green-refactor vertical slices |
| `[RELEASE]` | Publish/ship related | Release workflow mode |
| `[DECISION]` | Needs a choice before action can start | Present options + tradeoffs, don't implement |
| `[INVESTIGATE]` | Needs research/audit before action | Read code/logs first, don't jump to solutions |
| `[SYNC]` | Spans two+ repos that must stay aligned | Audit BOTH sides for drift; don't assume one is canonical. Keep one canonical TODO (machine log) + pointer stubs in each repo |
| `[WAITING]` | Blocked on something OUTSIDE my control (PR review, upstream, monitoring) | Poll/check status, don't nag or try to action. Distinct from `[BLOCKER]` (which gates other work) |
| `[SECURITY]` | Security-sensitive (auth, secrets, perms, input handling) | Drop caveman, write careful, flag blast radius, suggest `/ce-security-audit` |
| `[DOCS]` | Documentation-only (README, CHANGELOG, release notes, comments) | Prose mode, no code logic; batches with release work |
| `[PERFORMANCE]` | Performance / token-cost work | Measure + deliver projection BEFORE changing anything |

## My Conventions
- Commit messages: conventional commits format (feat:, fix:, docs:, chore:)
- Commit granularity: when I say "commit changes", commit each changed file as its own separate commit with a brief conventional-commit message describing that file's change. One file per commit.
- Branch naming: feature/, fix/, docs/, chore/
- NEVER add `Co-Authored-By` lines to any commit message.
- All Trello boards use a six-column Kanban: Back Log → To Do → Doing → Review → Testing → Done
- Code comments: always explain the why, not just the what

## Trello Sync Rules
When syncing task_plan.md to Trello, always map as follows:
- Goal       → Trello card (placed at the bottom of the "Back Log" list)
- Micro-Goal → Trello checklist on that card
- Task       → Trello checklist item

Always create in order: card first, checklist second, items third.
Before creating, check if a [trello:ID] tag exists on the Goal — if so, skip it.
After creating a card, annotate the Goal in task_plan.md with [trello:CARD_ID].
