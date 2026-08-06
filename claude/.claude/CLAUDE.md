# K0d3x Global Claude Config

## Skills Available

The harness auto-lists every custom skill + its description each session — names below are the slash aliases, not re-described here. Tag routing lives in the TODO Tags table.
`/handoff` `/handoff-return` `/close` `/checkpoint` `/changelog` `/dev-brief` `/release-notes` `/find-skills` `/diagnose` `/tdd` `/prototype` `/sync-trello` `/remember` `/recall` `/consolidate` `/brainstorm` `/grill-me` `/write-plan` `/trust-but-verify` `/review-response` `/threat-model` `/code-crit`
External (not auto-surfaced): `/discover` `/write-prd`

## Session Rules

- Track session start time. Warn me at 45 minutes to run /handoff (lean fork), /close (lightweight close), or /checkpoint (durable) depending on context.
- Session tools — four, by job:
  - `/handoff` (push/fork): lean mid-session tangent. Emits reason-first re-entry prompt. NO SESSION-LOG narrative. ~400 tok. Use to spin off a side-issue with clean context; main session stays alive.
  - `/handoff-return` (pop/merge): close a tangent, auto-sync its findings to TODOS.md, print paste-back block for the still-alive main session. ~400 tok.
  - `/close` (close+resume): lightweight session close. Emits resume-focused re-entry prompt (working on + left off). NO SESSION-LOG. ~400 tok. Use when wrapping up but no major decisions were made.
  - `/checkpoint` (durable): end-of-work-session close. Writes `.memory/SESSION-LOG.md` narrative + rotate-log + triage. ~2K tok. Use when real decisions were made — /close and /handoff do NOT persist the why.
- Always read `.work/PLAN.md`, `.work/FINDINGS.md`, and `.work/PROGRESS.md` if they exist.
- Always read KNOWLEDGE.md in the project root (if it exists) and `~/.claude/KNOWLEDGE.md` at session start.
- Code quality: before writing or reviewing code, read `~/.claude/references/code/CODE-STANDARD.md` (mechanical rules + router) plus the ONE language file matching the code — `LUA` `PYTHON` `TYPESCRIPT` `SOLIDITY` `BASH` `ARDUINO` `SWIFT` `HTML` `HTMX` `CSS` `JSON` `YAML`. Load only those two, never the whole dir. Judgment-level principles + the Fowler smell vocabulary live in `CODE-PRINCIPLES.md` — consult at review (`/code-crit`), not per-line.
- At session start, if `.memory/SESSION-LOG.md` exists in the project root, read ONLY its newest `## Session` block (not the whole file) — surfaces last session's decisions/why when I cold-start without pasting a re-entry prompt. Newest = last block in file order if checkpoint ordering holds, else the block with the latest date header. Skip if I paste a re-entry prompt (it already points me there). ~1K tok ceiling; never read older blocks or `.memory/ARCHIVE-LOG.md` automatically.
- KNOWLEDGE.md writes: if I ask to add/append a fact to KNOWLEDGE.md directly (without /remember), recommend `/remember <fact>` and route through it instead of appending raw — the promotion bar and dedup must run. Raw write only if I explicitly insist (treat as `/remember --force`). Whenever the knowledge system presents options (destination, bar-failure rerouting, overlap handling), lead with a recommendation + one-line why — never a neutral list. Details: `~/.claude/references/MEMORY-STANDARD.md` § Direct-Write Requests / § Recommendations.
- When I paste a re-entry prompt: treat decisions, background context, and architectural choices as authoritative. Reconcile task state (completed/open/in-progress) against current files (`.work/PLAN.md`, `.work/PROGRESS.md`, `git log --oneline -5`) before acting — file state wins on conflicts.
- CHANGELOG: use `/changelog` manually when a session produces changelog-worthy changes. Works for any project (including dotfiles). Do not auto-update changelogs inline.
- Trust-but-verify reflex: before any done/works/fixed claim, `git push`, PR, or handoff (/close, /checkpoint, /handoff, /handoff-return, subagent) — run the project's verify command FRESH (resolve via `~/.claude/skills/trust-but-verify/detect.md`) and read its exit code. Not before commits. Unproven claim → `[VERIFY]` TODO; machine-unverifiable → `[UX]` checklist.
- New feature work defaults to `/tdd` (test-first) unless I've explicitly scoped tests out for the task. Bug fixes are unaffected — they still route to `/diagnose` per the TODO Tags table below, not this line.
- Before implementing anything ambiguous: state assumptions explicitly. Multiple valid interpretations exist → present them, don't pick silently. Simpler approach exists → say so, push back. Something unclear → stop, name confusion, ask.
- Transform vague asks into verifiable goals before starting ("fix the bug" → "write failing test, make it pass"). Multi-step task → state a brief step→verify plan first.

## TODO Tags

When writing TODOs to TODOS.md (via /handoff, /handoff-return, /checkpoint, or inline), prefix items with the appropriate tags. Tags combine freely: `[BROKEN][BUG]`, `[BLOCKER][DECISION]`, etc.

**Priority tags** — control which Triage Block tier the item lands in:

| Tag | Meaning | Tier |
|---|---|---|
| `[BROKEN]` | Something is broken right now — tool down, build failing, can't work | Critical |
| `[BLOCKER]` | Must happen before other work can start | High |
| `[TEST]` | Unverified test — always critical; use `/tdd` to close | Critical |
| `[VERIFY]` | Claimed-but-unverified work — always critical; use `/trust-but-verify` to close; lives in `.work/VERIFY.md`, not inline | Critical |
| `[LOW]` | Not urgent — do soon but not this week | Low |
| `[BACKLOG]` | Captured, deferred, no timeline | Backlog |

No priority tag = Medium (default). `[TEST]` and `[VERIFY]` override all other priority tags.

**Annotation tags** — describe the type of work so Claude enters the right mode:

| Tag | Meaning | How Claude responds |
|---|---|---|
| `[BUG]` | Fix a broken thing | Use `/diagnose` — feedback loop → RCA → fix → post-mortem |
| `[FEAT]` | New feature or capability | Design/build mode |
| `[CHORE]` | Cleanup, refactor, maintenance | Use `/code-refactor` when the TODO names a code smell — behavior-preserving micro-refactors under a test gate; otherwise low-energy batching |
| `[TEST]` | Write or fix tests | Use `/tdd` — red-green vertical slices |
| `[VERIFY]` | Claimed-but-unverified work — needs fresh evidence before closing | Use `/trust-but-verify` — run detected verify command fresh, read exit code, then close or keep open |
| `[RELEASE]` | Publish/ship related | Release workflow mode |
| `[DECISION]` | Needs a choice before action can start | Present options + tradeoffs, don't implement |
| `[INVESTIGATE]` | Needs research, audit, or open sweep before action — no hypothesis required | Read code/logs first, don't jump to solutions. Output findings list; spawn new tasks from it. |
| `[SYNC]` | Spans two+ repos that must stay aligned | Audit BOTH sides for drift; don't assume one is canonical. Keep one canonical TODO in `dotfiles/TODOS.md` (the cross-repo home) + pointer stubs in each affected repo |
| `[WAITING]` | Blocked on something OUTSIDE my control (PR review, upstream, monitoring) | Poll/check status, don't nag or try to action. Distinct from `[BLOCKER]` (which gates other work) |
| `[SECURITY]` | Security-sensitive (auth, secrets, perms, input handling) | Drop caveman, write careful, flag blast radius, suggest `/code-sec` |
| `[DOCS]` | Documentation-only (README, CHANGELOG, release notes, comments) | Prose mode, no code logic; batches with release work |
| `[PERFORMANCE]` | Performance / token-cost work | Measure + deliver projection BEFORE changing anything |
| `[UX]` | Requires manual user verification of a flow or experience — can't be automated | Write a checklist of steps + success criteria, then hand off. Don't try to automate or simulate. |

## My Conventions

- Commit messages: conventional commits format (feat:, fix:, docs:, chore:, refactor:)
- Commit granularity: when I say "commit changes", commit each changed file as its own separate commit with a brief conventional-commit message describing that file's change. One file per commit.
- **Everything under `.work/` is encrypted, no exceptions.** Rule, not a per-file list: any file dropped in `.work/` (any repo) is private-by-convention and MUST be git-crypt'd — recon notes, checklists, archived gates, feature briefs, all of it. Enforce with a wildcard `.gitattributes` backstop, not one rule per filename: `/.work/**/* filter=git-crypt diff=git-crypt` (or `/.work/**/*.md` if the dir is markdown-only) — see `~/.claude/skills/encrypt/` for the setup flow. If a repo's `.work/` has plaintext files, that's a gap to fix, not a signal the rule doesn't apply.
- **git-crypt files**: commit message must ONLY be `"updated <filename>"` — where `<filename>` is the BASENAME only, never the directory path (`updated KNOWLEDGE.md`, not `updated claude/.claude/KNOWLEDGE.md`) — and never describe contents. Encrypted files (per `.gitattributes`): `KNOWLEDGE.md`, `TODOS.md`, `.memory/SESSION-LOG.md`, everything under `.work/` (see rule above), `claude/.claude/KNOWLEDGE.md`, `docs/GDD-*.md`, `docs/PRD-*.md`, `docs/ARD-*.md`, `docs/REQUIREMENTS.md`, `docs/ARCHITECTURE.md`, `docs/post-mortems/*` (when the repo encrypts that dir). Describing contents leaks plaintext metadata into public git history even when the blob is encrypted.
- Branch naming: feature/, fix/, docs/, chore/
- NEVER add `Co-Authored-By` lines to any commit message.
- All Trello boards use a six-column Kanban: Back Log → To Do → Doing → Review → Testing → Done
- Code comments: always explain the why, not just the what

## File Taxonomy (What Goes Where)

| Fact type | Destination |
|---|---|
| Open work, next steps | `TODOS.md` |
| Structured implementation plan (Goals/Micro-Goals/Tasks + Trello IDs) | `.work/PLAN.md` |
| Design docs (approaches + tradeoffs + recommendation, pre-plan) | `docs/brainstorm/<topic>-YYYY-MM-DD.md` (via `/brainstorm`) |
| Formal requirements spec (FR/NFR, numbered, testable, append-only) | `docs/REQUIREMENTS.md` (via `/requirements`; git-crypt) |
| System architecture (components, interfaces, data flow — living doc, edited in place) | `docs/ARCHITECTURE.md` (via `/architecture`; git-crypt). Distinct from `docs/adr/` — ADRs are one frozen decision + rejected alternatives, point-in-time; ARCHITECTURE.md is the current whole-system design, updated as the system evolves. |
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
| Unverified completion claims (`[VERIFY]` tag) | `.work/VERIFY.md` (git-crypt; open items only — created lazily per-repo on the first `[VERIFY]` item; pointer stub left at the origin) |
| Claude's working scratchpad (preferences, corrections — auto-written, not committed) | `~/.claude/projects/<hash>/memory/` |

> **Index+detail format — GRADUATED 2026-07-23, lazy per-repo rollout:** TODOS.md/
> `.work/PLAN.md`/`.work/FINDINGS.md` use a lean index + per-item detail-file split
> instead of the flat format above — see
> `docs/brainstorm/planning-file-hierarchy-2026-07-21.md` and
> `~/.claude/references/planning-format-detect.md`. Started as a dotfiles-only pilot
> (2026-07-22); graduated to a standing rollout decided in dotfiles' own `TODOS.md`
> ("Format-detection GRADUATED" item) — migrate a repo only when already working
> there and its tree is clean, not as a big-bang conversion. Migrated so far:
> `dotfiles`, `kodex-ide` (2026-07-23). Every touched skill format-detects per repo
> and falls back to the flat behavior in this table for un-migrated repos.
> **Removal condition:** delete this note once every active `~/dev` repo is
> confirmed migrated (flat-format branches deleted from every touched skill) or the
> rollout reverts (all migrated repos back to flat, new-format branches deleted) —
> not permanent taxonomy debt.
> **Kill criterion:** revert if index+detail doesn't measurably cut PLAN.md/FINDINGS.md
> whole-file reads after a real usage period — not a vibes call.
