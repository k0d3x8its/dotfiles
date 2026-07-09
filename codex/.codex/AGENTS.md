# K0d3x Global Codex Config

## Session Rules
- Track session start time. Warn me at 45 minutes to run the appropriate handoff, close, or checkpoint flow depending on context.
- Session tools, by job:
  - Use a lean handoff flow for side issues that should not keep the main session blocked.
  - Use a return flow to fold side-issue findings back into the active work.
  - Use a lightweight close flow when wrapping up without major decisions.
  - Use a durable checkpoint flow when the session made real decisions and the why needs to be preserved.
- Always read `.work/PLAN.md`, `.work/FINDINGS.md`, and `.work/PROGRESS.md` if they exist.
- Always read `KNOWLEDGE.md` in the project root, if it exists, and `~/.codex/KNOWLEDGE.md` at session start.
- At session start, if `.memory/SESSION-LOG.md` exists in the project root, read only its newest `## Session` block. Skip this if the user already pasted a re-entry prompt.
- When asked to add a fact to `KNOWLEDGE.md` directly, route it through the memory workflow instead of appending raw unless the user explicitly insists.
- When the user pastes a re-entry prompt, treat its decisions and background context as authoritative. Reconcile task state against current files and `git log --oneline -5` before acting.
- Use changelog updates manually when a session produces changelog-worthy changes. Do not auto-update changelogs inline.
- Before any done/works/fixed claim, `git push`, PR, or handoff, run the project's verify command fresh and read its exit code. Unproven claim -> `[VERIFY]` TODO; machine-unverifiable -> `[UX]` checklist.

## Codex Surface Notes
- Codex skills may trigger through natural language even when the TUI slash menu does not autocomplete the skill name. If a user invokes a known skill by name, use the skill.
- Do not assume Claude-style statusline UI exists in Codex. Codex hooks are backend lifecycle checks only unless current runtime evidence proves a visible UI channel.
- Caveman and other Marketplace skills may live in `~/.agents/skills`; dotfiles-owned Codex workflow skills live in `~/.codex/skills` or the `k0d3x-harness` plugin cache.

## TODO Tags

When writing TODOs to `TODOS.md` via any session workflow or inline, prefix items with the appropriate tags. Tags combine freely.

**Priority tags** - control which Triage Block tier the item lands in:

| Tag | Meaning | Tier |
|---|---|---|
| `[BROKEN]` | Something is broken right now - tool down, build failing, can't work | Critical |
| `[BLOCKER]` | Must happen before other work can start | High |
| `[TEST]` | Unverified test - always critical; use test-driven workflow to close | Critical |
| `[VERIFY]` | Claimed-but-unverified work - always critical; use trust-but-verify to close | Critical |
| `[LOW]` | Not urgent - do soon but not this week | Low |
| `[BACKLOG]` | Captured, deferred, no timeline | Backlog |

No priority tag = Medium (default). `[TEST]` and `[VERIFY]` override all other priority tags.

**Annotation tags** - describe the type of work so the agent enters the right mode:

| Tag | Meaning | How the agent responds |
|---|---|---|
| `[BUG]` | Fix a broken thing | Use diagnose mode - feedback loop -> RCA -> fix -> post-mortem |
| `[FEAT]` | New feature or capability | Design/build mode |
| `[CHORE]` | Cleanup, refactor, maintenance | Low-energy batching candidate |
| `[TEST]` | Write or fix tests | Use test-driven mode - red-green vertical slices |
| `[VERIFY]` | Claimed-but-unverified work - needs fresh evidence before closing | Use trust-but-verify - run detected verify command fresh, read exit code, then close or keep open |
| `[RELEASE]` | Publish/ship related | Release workflow mode |
| `[DECISION]` | Needs a choice before action can start | Present options and tradeoffs, do not implement |
| `[INVESTIGATE]` | Needs research, audit, or open sweep before action | Read code and logs first, do not jump to solutions |
| `[SYNC]` | Spans two or more repos that must stay aligned | Audit both sides for drift; keep one canonical TODO and pointer stubs in each repo |
| `[WAITING]` | Blocked on something outside my control | Poll or check status, do not nag or try to action |
| `[SECURITY]` | Security-sensitive | Be careful about blast radius and suggest a security review if needed |
| `[DOCS]` | Documentation-only | Prose mode, no code logic; batch with release work |
| `[PERFORMANCE]` | Performance or token-cost work | Measure and project before changing anything |
| `[UX]` | Requires manual user verification of a flow or experience | Write a checklist of steps and success criteria, then hand off |

## My Conventions
- Commit messages: conventional commits format (`feat:`, `fix:`, `docs:`, `chore:`)
- Commit granularity: when asked to commit changes, commit each changed file as its own separate commit with a brief conventional-commit message describing that file's change. One file per commit.
- Git-crypt files: commit message must only be `updated <filename>` - never describe contents.
- Branch naming: `feature/`, `fix/`, `docs/`, `chore/`
- Never add `Co-Authored-By` lines to any commit message.
- All Trello boards use a six-column Kanban: Back Log -> To Do -> Doing -> Review -> Testing -> Done
- Code comments: always explain the why, not just the what

## Trello Sync Rules
When syncing `.work/PLAN.md` to Trello, always map as follows:
- Goal -> Trello card (placed at the bottom of the Back Log list)
- Micro-Goal -> Trello checklist on that card
- Task -> Trello checklist item

Always create in order: card first, checklist second, items third.
Before creating, check if a `[trello:ID]` tag exists on the Goal - if so, skip it.
After creating a card, annotate the Goal in `.work/PLAN.md` with `[trello:CARD_ID]`.

## File Taxonomy

| Fact type | Destination |
|---|---|
| Open work, next steps | `TODOS.md` |
| Structured implementation plan (Goals/Micro-Goals/Tasks + Trello IDs) | `.work/PLAN.md` |
| Design docs (approaches + tradeoffs + recommendation, pre-plan) | `docs/brainstorm/<topic>-YYYY-MM-DD.md` |
| Normative rules, standing instructions | `CLAUDE.md` or `AGENTS.md` |
| Empirical facts, env truths, codebase gotchas | `KNOWLEDGE.md` (local or global) |
| Architectural decisions (cost meaningful + future reader wonders why + alternatives considered) | `docs/adr/ADR-NNNN-*.md` |
| Bug post-mortems (root cause + fix + what-would-prevent, via diagnose workflow) | `docs/post-mortems/<slug>.md` |
| Session narrative, decisions and why | `.memory/SESSION-LOG.md` |
| Changelog-worthy changes (features, fixes) | `CHANGELOG.md` |
| Per-task scratch, investigation notes | `.work/FINDINGS.md` |
| Working scratchpad, preferences, corrections | agent memory |
