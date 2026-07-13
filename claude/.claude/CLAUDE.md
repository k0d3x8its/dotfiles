# K0d3x Global Claude Config

## Skills Available
The harness auto-lists every custom skill + its description each session — names below are the slash aliases, not re-described here. Tag routing lives in the TODO Tags table.
`/handoff` `/handoff-return` `/close` `/checkpoint` `/changelog` `/dev-brief` `/release-notes` `/find-skills` `/diagnose` `/tdd` `/prototype` `/sync-trello` `/remember` `/recall` `/consolidate` `/brainstorm` `/grill-me` `/write-plan` `/trust-but-verify` `/review-response` `/threat-model`
External (not auto-surfaced): `/ce-code-review` `/discover` `/write-prd`

## Session Rules
- Track session start time. Warn me at 45 minutes to run /handoff (lean fork), /close (lightweight close), or /checkpoint (durable) depending on context.
- Session tools — four, by job:
  - `/handoff` (push/fork): lean mid-session tangent. Emits reason-first re-entry prompt. NO SESSION-LOG narrative. ~400 tok. Use to spin off a side-issue with clean context; main session stays alive.
  - `/handoff-return` (pop/merge): close a tangent, auto-sync its findings to TODOS.md, print paste-back block for the still-alive main session. ~400 tok.
  - `/close` (close+resume): lightweight session close. Emits resume-focused re-entry prompt (working on + left off). NO SESSION-LOG. ~400 tok. Use when wrapping up but no major decisions were made.
  - `/checkpoint` (durable): end-of-work-session close. Writes `.memory/SESSION-LOG.md` narrative + rotate-log + triage. ~2K tok. Use when real decisions were made — /close and /handoff do NOT persist the why.
- Always read `.work/PLAN.md`, `.work/FINDINGS.md`, and `.work/PROGRESS.md` if they exist.
- Always read KNOWLEDGE.md in the project root (if it exists) and `~/.claude/KNOWLEDGE.md` at session start.
- Code quality: before writing or reviewing code, read `~/.claude/references/code/CODE-STANDARD.md` (mechanical rules + router) plus the ONE language file matching the code — `LUA` `PYTHON` `TYPESCRIPT` `SOLIDITY` `BASH` `ARDUINO`. Load only those two, never the whole dir. Judgment-level principles + the Fowler smell vocabulary live in `CODE-PRINCIPLES.md` — consult at review (`/code-review`), not per-line.
- At session start, if `.memory/SESSION-LOG.md` exists in the project root, read ONLY its newest `## Session` block (not the whole file) — surfaces last session's decisions/why when I cold-start without pasting a re-entry prompt. Newest = last block in file order if checkpoint ordering holds, else the block with the latest date header. Skip if I paste a re-entry prompt (it already points me there). ~1K tok ceiling; never read older blocks or `.memory/ARCHIVE-LOG.md` automatically.
- KNOWLEDGE.md writes: if I ask to add/append a fact to KNOWLEDGE.md directly (without /remember), recommend `/remember <fact>` and route through it instead of appending raw — the promotion bar and dedup must run. Raw write only if I explicitly insist (treat as `/remember --force`). Whenever the knowledge system presents options (destination, bar-failure rerouting, overlap handling), lead with a recommendation + one-line why — never a neutral list. Details: `~/.claude/references/MEMORY-STANDARD.md` § Direct-Write Requests / § Recommendations.
- When I paste a re-entry prompt: treat decisions, background context, and architectural choices as authoritative. Reconcile task state (completed/open/in-progress) against current files (`.work/PLAN.md`, `.work/PROGRESS.md`, `git log --oneline -5`) before acting — file state wins on conflicts.
- CHANGELOG: use `/changelog` manually when a session produces changelog-worthy changes. Works for any project (including dotfiles). Do not auto-update changelogs inline.
- Trust-but-verify reflex: before any done/works/fixed claim, `git push`, PR, or handoff (/close, /checkpoint, /handoff, /handoff-return, subagent) — run the project's verify command FRESH (resolve via `~/.claude/skills/trust-but-verify/detect.md`) and read its exit code. Not before commits. Unproven claim → `[VERIFY]` TODO; machine-unverifiable → `[UX]` checklist.

## TODO Tags

When writing TODOs to TODOS.md (via /handoff, /handoff-return, /checkpoint, or inline), prefix items with the appropriate tags. Tags combine freely: `[BROKEN][BUG]`, `[BLOCKER][DECISION]`, etc.

**Priority tags** — control which Triage Block tier the item lands in:

| Tag | Meaning | Tier |
|---|---|---|
| `[BROKEN]` | Something is broken right now — tool down, build failing, can't work | Critical |
| `[BLOCKER]` | Must happen before other work can start | High |
| `[TEST]` | Unverified test — always critical; use `/tdd` to close | Critical |
| `[VERIFY]` | Claimed-but-unverified work — always critical; use `/trust-but-verify` to close | Critical |
| `[LOW]` | Not urgent — do soon but not this week | Low |
| `[BACKLOG]` | Captured, deferred, no timeline | Backlog |

No priority tag = Medium (default). `[TEST]` and `[VERIFY]` override all other priority tags.

**Annotation tags** — describe the type of work so Claude enters the right mode:

| Tag | Meaning | How Claude responds |
|---|---|---|
| `[BUG]` | Fix a broken thing | Use `/diagnose` — feedback loop → RCA → fix → post-mortem |
| `[FEAT]` | New feature or capability | Design/build mode |
| `[CHORE]` | Cleanup, refactor, maintenance | Low-energy batching candidate |
| `[TEST]` | Write or fix tests | Use `/tdd` — red-green vertical slices |
| `[VERIFY]` | Claimed-but-unverified work — needs fresh evidence before closing | Use `/trust-but-verify` — run detected verify command fresh, read exit code, then close or keep open |
| `[RELEASE]` | Publish/ship related | Release workflow mode |
| `[DECISION]` | Needs a choice before action can start | Present options + tradeoffs, don't implement |
| `[INVESTIGATE]` | Needs research, audit, or open sweep before action — no hypothesis required | Read code/logs first, don't jump to solutions. Output findings list; spawn new tasks from it. |
| `[SYNC]` | Spans two+ repos that must stay aligned | Audit BOTH sides for drift; don't assume one is canonical. Keep one canonical TODO (machine log) + pointer stubs in each repo |
| `[WAITING]` | Blocked on something OUTSIDE my control (PR review, upstream, monitoring) | Poll/check status, don't nag or try to action. Distinct from `[BLOCKER]` (which gates other work) |
| `[SECURITY]` | Security-sensitive (auth, secrets, perms, input handling) | Drop caveman, write careful, flag blast radius, suggest `/code-sec` |
| `[DOCS]` | Documentation-only (README, CHANGELOG, release notes, comments) | Prose mode, no code logic; batches with release work |
| `[PERFORMANCE]` | Performance / token-cost work | Measure + deliver projection BEFORE changing anything |
| `[UX]` | Requires manual user verification of a flow or experience — can't be automated | Write a checklist of steps + success criteria, then hand off. Don't try to automate or simulate. |

## My Conventions
- Commit messages: conventional commits format (feat:, fix:, docs:, chore:)
- Commit granularity: when I say "commit changes", commit each changed file as its own separate commit with a brief conventional-commit message describing that file's change. One file per commit.
- **git-crypt files**: commit message must ONLY be `"updated <filename>"` — where `<filename>` is the BASENAME only, never the directory path (`updated KNOWLEDGE.md`, not `updated claude/.claude/KNOWLEDGE.md`) — and never describe contents. Encrypted files (per `.gitattributes`): `KNOWLEDGE.md`, `TODOS.md`, `.memory/SESSION-LOG.md`, `.work/FINDINGS.md`, `.work/PROGRESS.md`, `.work/PLAN.md`, `claude/.claude/KNOWLEDGE.md`, `docs/GDD-*.md`, `docs/PRD-*.md`, `docs/ARD-*.md`, `docs/post-mortems/*` (when the repo encrypts that dir). Describing contents leaks plaintext metadata into public git history even when the blob is encrypted.
- Branch naming: feature/, fix/, docs/, chore/
- NEVER add `Co-Authored-By` lines to any commit message.
- All Trello boards use a six-column Kanban: Back Log → To Do → Doing → Review → Testing → Done
- Code comments: always explain the why, not just the what

## Trello Sync Rules
When syncing `.work/PLAN.md` to Trello, always map as follows:
- Goal       → Trello card (placed at the bottom of the "Back Log" list)
- Micro-Goal → Trello checklist on that card
- Task       → Trello checklist item

Always create in order: card first, checklist second, items third.
Before creating, check if a [trello:ID] tag exists on the Goal — if so, skip it.
After creating a card, annotate the Goal in `.work/PLAN.md` with [trello:CARD_ID].

## File Taxonomy (What Goes Where)

| Fact type | Destination |
|---|---|
| Open work, next steps | `TODOS.md` |
| Structured implementation plan (Goals/Micro-Goals/Tasks + Trello IDs) | `.work/PLAN.md` |
| Design docs (approaches + tradeoffs + recommendation, pre-plan) | `docs/brainstorm/<topic>-YYYY-MM-DD.md` (via `/brainstorm`) |
| Normative rules, standing instructions | `CLAUDE.md` |
| Code style / naming / structure rules (per-language mechanics + judgment principles) | `~/.claude/references/code/` — `CODE-STANDARD.md` (router) + one language file; principles in `CODE-PRINCIPLES.md` |
| Empirical facts, env truths, codebase gotchas | `KNOWLEDGE.md` (local or global) |
| Architectural decisions (cost meaningful + future reader wonders why + alternatives considered) | `docs/adr/ADR-NNNN-*.md` (CLI/SDK projects) |
| Bug post-mortems (root cause + fix + what-would-prevent, via `/diagnose`) | `docs/post-mortems/<slug>.md` — one file per bug (no date prefix; date is in the `**Date:**` field inside); git-crypt the dir on public repos |
| Threat model (STRIDE, risk ranks, mitigation map, via `/threat-model`) | `docs/threat-model.md` (git-crypt; DFD source `docs/threat-model.dfd.mmd` git-crypt, `.dfd.svg` render gitignored) |
| Shared security context (topology, actors/auth tiers, trust boundaries, repo's own sanitizers) | `.work/SEC-CONTEXT.md` (git-crypt; read/written by threat-model, bounty-hunter, code-sec) |
| Session narrative, decisions + why | `.memory/SESSION-LOG.md` |
| Changelog-worthy changes (features, fixes) | `CHANGELOG.md` (via `/changelog`) |
| Per-task scratch, investigation notes | `.work/FINDINGS.md` |
| Claude's working scratchpad (preferences, corrections — auto-written, not committed) | `~/.claude/projects/<hash>/memory/` |
