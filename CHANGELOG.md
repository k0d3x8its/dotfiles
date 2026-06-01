# Changelog

## [Unreleased]

### Changed
- 🔧 `dev-brief` deep-dive OPEN TODOs now tiered + tag-grouped: a single-project `/dev-brief <project>` renders its TODOs by priority tier (severity descending `CRITICAL → HIGH → MEDIUM → LOW → BACKLOG`, empty tiers omitted) with annotation-tag subgroups inside each tier, reusing the Step-6 tier assignment. Replaces the old flat verbatim list. `⚠`/`⚑` prefixes kept; `✓` auto-resolved listed untiered at the bottom. Distinct from the cross-project Triage Block (still default-mode only).
- 🔧 `session-handoff` re-entry Top-5 trim: the terminal re-entry paste now splices only the **Top-5 attention set** (first-action + items advanced this session + highest-priority carry-forwards, excluding `[WAITING]`/`[BACKLOG]`) plus a `+N more` pointer, instead of every carried-forward `- [ ]`. New step 9b defines the mechanical selection rule. Log integrity untouched — `### Incomplete / Next Steps` still carries ALL open items; only the paste is curated. Saves ~750 tok at handoff print + ~750 tok at next-session paste-in.
- 🔧 `session-handoff` re-entry dup-kill: the `### Re-Entry Prompt` block written to `session-log.md` now stores a *pointer* to the same block's `### Incomplete / Next Steps` instead of re-embedding the verbatim TODO list. The terminal-printed prompt (and `dev-brief` deep-dive) splice the list back in at render, so the paste stays self-contained while the log drops ~14K chars (~3.5K tok) of duplicate re-read per dev-brief/handoff load.

### Added
- ➕ `dev-brief` Step 3b fix-commit reconcile (stale-after-fix protection P1, RCA 2026-05-30): flags open `[BUG]`/`[FEAT]`/`[RELEASE]` TODOs whose work a normal commit may have already done, as `⚑ possibly resolved by <hash>(<repo>) — verify`. Advisory-only — never writes the log, never auto-closes, recomputed live each run like git state. For `[machine]` TODOs it scans `~/dev/dotfiles` + named repos (the fix-repo ≠ TODO-repo gap). Conservative matching (path/filename or ≥2 distinctive content words) biases to precision. P2 (stable `[#id]` exact reconcile) deferred to backlog, gated on P1 noise.
- ➕ `session-handoff` step 7c: auto-rotates `session-log.md` — keeps the newest 3 session blocks live, moves older blocks to a sibling `ARCHIVE-LOG.md` (date-sorted, newest-at-bottom). Cuts the machine log's dev-brief/handoff read cost ~74% (220 KB → 57 KB).

### Fixed
- 🐛 `dev-setup` Step 12 `.gitignore` no longer overwrite-or-skip: on an existing repo, "skip" left the Step-11 planning/session files (`task_plan.md`, `findings.md`, `progress.md`, `session-log.md`, `RELEASE-NOTES.md`, `.claude/trello-board`) un-ignored, leaking them into git; "overwrite" clobbered the user's existing ignores. Now an **append-if-missing merge** — adds only absent patterns under a `# --- added by /dev-setup ---` marker, never touches existing lines, idempotent across re-runs.

---

<!--
## [X.Y.Z] - YYYY-MM-DD

### Added
- ➕ 

### Changed
- ♻️ 

### Fixed
- 🛠️ 

### Removed
- ❌ 
-->

## Glossary

| ➕ | ❌ | 🛠️ | 🐞 | 🚀 | ♻️ | 🛡️ | ⚠️ | ⬆️ |
|-------|---------|-------|-----|----------|---------|----------|------------|---------|
| ADDED | REMOVED | FIXED | BUG | IMPROVED | CHANGED | SECURITY | DEPRECATED | UPDATED |
