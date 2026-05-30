# K0d3x Global Claude Config

## Who I Am
Solo developer. Builder. Ubuntu 24.04 (Noble). Tools: Neovim, Nala, Git.
KOS (Kodex OS) is my personal knowledge management system.

## Skills Available
- /handoff or /session-handoff — end-of-session context preservation, logs to session-log.md
- /dev-brief — morning/context-switch brief across all ~/dev projects: open TODOs, git state, gotchas, branch, staleness. /dev-brief <project> for deep-dive + re-entry prompt.
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
- RELEASE-NOTES on [machine] sessions, route by what changed: if the session modified files under `~/dev/dotfiles/`, append the release-notes entry to `~/dev/dotfiles/RELEASE-NOTES.md`; if the changes were machine-only (no dotfiles impact), skip RELEASE-NOTES entirely — don't ask.

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
| `[BUG]` | Fix a broken thing | Root cause analysis first, then fix |
| `[FEAT]` | New feature or capability | Design/build mode |
| `[CHORE]` | Cleanup, refactor, maintenance | Low-energy batching candidate |
| `[TEST]` | Write or fix tests | Testing session mode |
| `[RELEASE]` | Publish/ship related | Release workflow mode |
| `[DECISION]` | Needs a choice before action can start | Present options + tradeoffs, don't implement |
| `[INVESTIGATE]` | Needs research/audit before action | Read code/logs first, don't jump to solutions |

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
