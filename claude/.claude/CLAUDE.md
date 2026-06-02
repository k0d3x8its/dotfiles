# K0d3x Global Claude Config

## Who I Am
Solo developer. Builder. Ubuntu 24.04 (Noble). Tools: Neovim, Nala, Git.
KOS (Kodex OS) is my personal knowledge management system.

## Skills Available
The harness auto-lists every custom skill + its description each session — names below are the slash aliases, not re-described here. Tag routing lives in the TODO Tags table.
`/handoff` `/handoff-return` `/close` `/checkpoint` `/changelog` `/dev-brief` `/planning-with-files` `/release-notes` `/find-skills` `/diagnose` `/tdd` `/prototype` `/sync-trello`
External (not auto-surfaced): `/ce-code-review` `/ce-security-audit` `/discover` `/write-prd`

## Session Rules
- Track session start time. Warn me at 45 minutes to run /handoff (lean fork), /close (lightweight close), or /checkpoint (durable) depending on context.
- Session tools — four, by job:
  - `/handoff` (push/fork): lean mid-session tangent. Emits reason-first re-entry prompt. NO SESSION-LOG narrative. ~400 tok. Use to spin off a side-issue with clean context; main session stays alive.
  - `/handoff-return` (pop/merge): close a tangent, auto-sync its findings to TODOS.md, print paste-back block for the still-alive main session. ~400 tok.
  - `/close` (close+resume): lightweight session close. Emits resume-focused re-entry prompt (working on + left off). NO SESSION-LOG. ~400 tok. Use when wrapping up but no major decisions were made.
  - `/checkpoint` (durable): end-of-work-session close. Writes SESSION-LOG narrative + rotate-log + triage. ~2K tok. Use when real decisions were made — /close and /handoff do NOT persist the why.
- Always read task_plan.md, findings.md, and progress.md if they exist in the project root.
- When I paste a re-entry prompt: treat decisions, background context, and architectural choices as authoritative. Reconcile task state (completed/open/in-progress) against current files (task_plan.md, progress.md, `git log --oneline -5`) before acting — file state wins on conflicts.
- CHANGELOG: use `/changelog` manually when a session produces changelog-worthy changes. Works for any project (including dotfiles). Do not auto-update changelogs inline.

## TODO Tags

When writing TODOs to TODOS.md (via /handoff, /handoff-return, /checkpoint, or inline), prefix items with the appropriate tags. Tags combine freely: `[BROKEN][BUG]`, `[BLOCKER][DECISION]`, etc.

**Priority tags** — control which Triage Block tier the item lands in:

| Tag | Meaning | Tier |
|---|---|---|
| `[BROKEN]` | Something is broken right now — tool down, build failing, can't work | Critical |
| `[BLOCKER]` | Must happen before other work can start | High |
| `[TEST]` | Unverified test — always critical; use `/tdd` to close | Critical |
| `[LOW]` | Not urgent — do soon but not this week | Low |
| `[BACKLOG]` | Captured, deferred, no timeline | Backlog |

No priority tag = Medium (default). `[TEST]` overrides all other priority tags.

**Annotation tags** — describe the type of work so Claude enters the right mode:

| Tag | Meaning | How Claude responds |
|---|---|---|
| `[BUG]` | Fix a broken thing | Use `/diagnose` — feedback loop → RCA → fix → post-mortem |
| `[FEAT]` | New feature or capability | Design/build mode |
| `[CHORE]` | Cleanup, refactor, maintenance | Low-energy batching candidate |
| `[TEST]` | Write or fix tests | Use `/tdd` — red-green-refactor vertical slices |
| `[RELEASE]` | Publish/ship related | Release workflow mode |
| `[DECISION]` | Needs a choice before action can start | Present options + tradeoffs, don't implement |
| `[INVESTIGATE]` | Needs research, audit, or open sweep before action — no hypothesis required | Read code/logs first, don't jump to solutions. Output findings list; spawn new tasks from it. |
| `[SYNC]` | Spans two+ repos that must stay aligned | Audit BOTH sides for drift; don't assume one is canonical. Keep one canonical TODO (machine log) + pointer stubs in each repo |
| `[WAITING]` | Blocked on something OUTSIDE my control (PR review, upstream, monitoring) | Poll/check status, don't nag or try to action. Distinct from `[BLOCKER]` (which gates other work) |
| `[SECURITY]` | Security-sensitive (auth, secrets, perms, input handling) | Drop caveman, write careful, flag blast radius, suggest `/ce-security-audit` |
| `[DOCS]` | Documentation-only (README, CHANGELOG, release notes, comments) | Prose mode, no code logic; batches with release work |
| `[PERFORMANCE]` | Performance / token-cost work | Measure + deliver projection BEFORE changing anything |
| `[UX]` | Requires manual user verification of a flow or experience — can't be automated | Write a checklist of steps + success criteria, then hand off. Don't try to automate or simulate. |

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
