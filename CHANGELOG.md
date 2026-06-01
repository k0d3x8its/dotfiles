# Changelog

## [Unreleased]

### Changed
- 🔧 `CLAUDE.md` re-entry prompt rule: softened "ground truth" to trust-but-verify (Option C). Decisions/context/architectural choices remain authoritative; task state reconciles against task_plan.md, progress.md, and `git log --oneline -5` — file state wins on conflicts.

### Added
- ➕ `scripts/update-triage`: Python script reads `~/dev/.triage-cache` and writes `TRIAGE-BLOCK.md` with HTML color spans (tier/annotation tag colors, RELEASE PENDING, orphan list). Zero Claude tokens. Called by `/handoff` step 7d and runnable manually via `update-triage` on PATH.
- ➕ `session-handoff` step 7d: run `update-triage` after every `/handoff` so `TRIAGE-BLOCK.md` is always current — glanceable in live-preview.nvim with no session token cost.
- ➕ `install.sh` symlinks `update-triage` to `~/.local/bin/update-triage`.

### Changed
- 🔧 `/dev-brief triage` demoted to cache-repair tool — `TRIAGE-BLOCK.md` is now owned by the `update-triage` shell script. Run `/dev-brief triage` only when `.triage-cache` is stale or corrupted.

### Changed
- 🔧 `dev-brief` deep-dive OPEN TODOs now tiered + tag-grouped: a single-project `/dev-brief <project>` renders its TODOs by priority tier (severity descending `CRITICAL → HIGH → MEDIUM → LOW → BACKLOG`, empty tiers omitted) with annotation-tag subgroups inside each tier, reusing the Step-6 tier assignment. Replaces the old flat verbatim list. `⚠`/`⚑` prefixes kept; `✓` auto-resolved listed untiered at the bottom. Distinct from the cross-project Triage Block (still default-mode only).
- 🔧 `session-handoff` re-entry Top-5 trim: the terminal re-entry paste now splices only the **Top-5 attention set** (first-action + items advanced this session + highest-priority carry-forwards, excluding `[WAITING]`/`[BACKLOG]`) plus a `+N more` pointer, instead of every carried-forward `- [ ]`. New step 9b defines the mechanical selection rule. Log integrity untouched — `### Incomplete / Next Steps` still carries ALL open items; only the paste is curated. Saves ~750 tok at handoff print + ~750 tok at next-session paste-in.
- 🔧 `session-handoff` re-entry dup-kill: the `### Re-Entry Prompt` block written to `session-log.md` now stores a *pointer* to the same block's `### Incomplete / Next Steps` instead of re-embedding the verbatim TODO list. The terminal-printed prompt (and `dev-brief` deep-dive) splice the list back in at render, so the paste stays self-contained while the log drops ~14K chars (~3.5K tok) of duplicate re-read per dev-brief/handoff load.

### Added
- ➕ `dev-brief` Step 3b fix-commit reconcile (stale-after-fix protection P1, RCA 2026-05-30): flags open `[BUG]`/`[FEAT]`/`[RELEASE]` TODOs whose work a normal commit may have already done, as `⚑ possibly resolved by <hash>(<repo>) — verify`. Advisory-only — never writes the log, never auto-closes, recomputed live each run like git state. For `[machine]` TODOs it scans `~/dev/dotfiles` + named repos (the fix-repo ≠ TODO-repo gap). Conservative matching (path/filename or ≥2 distinctive content words) biases to precision. P2 (stable `[#id]` exact reconcile) deferred to backlog, gated on P1 noise.
- ➕ `session-handoff` step 7c: auto-rotates `session-log.md` — keeps the newest 3 session blocks live, moves older blocks to a sibling `ARCHIVE-LOG.md` (date-sorted, newest-at-bottom). Cuts the machine log's dev-brief/handoff read cost ~74% (220 KB → 57 KB).

### Fixed
- 🐛 45-minute `/handoff` warning now actually visible: root cause was the wrong output channel — `session_timer.py` `print()`ed the warning on the **Stop** hook, but Stop-hook stdout only reaches Claude Code's debug log, never the UI (confirmed against the hooks docs; only UserPromptSubmit/SessionStart stdout surfaces). Fix is two-channel: (1) `combined-statusline.sh` now shows a persistent elapsed clock (`⏱ Nm`, flips to `⚠️`/`🚨` at 45m/55m) — always visible, solves the "gone before user returns" case; (2) `session_timer.py` switched from `print()` to the JSON `systemMessage` field, fired **one-shot per threshold** (marker files cleared on SessionStart) so the user gets a single 45m and 55m popup instead of a per-turn nag.
- 🔗 hooks dir un-drifted: live `~/.claude/hooks` was a real dir, not the dotfiles symlink (`install.sh` lines 59-61 create it, but it had been overwritten), so hook edits in dotfiles never reached the running machine. Re-symlinked live → dotfiles (verified byte-identical first; backup at `~/.claude/hooks.bak-*`). Edits now propagate.
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
