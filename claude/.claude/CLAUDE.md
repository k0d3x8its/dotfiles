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
- NEVER add `Co-Authored-By` lines to any commit message.
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
