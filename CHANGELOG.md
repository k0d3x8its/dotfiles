# Changelog

## [Unreleased]

### 2026-06-01
#### Added
- ➕ `claude/.claude/skills/changelog/` — new `/changelog` skill: generates dated sub-blocks under `[Unreleased]`, groups commits by conventional-commit prefix, emoji per entry, deduplicates against existing content
- ➕ `tests/test_rotate_log.py` — 20 unit tests for `rotate-log` (parse_blocks, rotate return value, content correctness, archive creation/append/accumulation)
- ➕ `tests/test_update_triage.py` expanded — 55 new tests; now 82 total. Covers `fmt_line`, `colorize_tags`, `strip_priority_tags`, `remove_project_block`, full `is_urgent` keyword coverage, `get_tier` conflicting-tag resolution
- ➕ `tests/test_update_triage.py` — 27 unittests for `update-triage` and `update-cache` (parse_cache pointer format, get_tier all tiers, is_urgent backtick exclusion, build_triage sort, update-cache mtime correctness, dedup)
- ➕ `[TEST]` priority tag — always resolves to CRITICAL tier, overrides all other priority tags. Documented in CLAUDE.md
- ➕ `scripts/update-cache` — pointer-only triage cache updater. Stats TODOS.md, writes 3-line pointer block to `.triage-cache`. Replaces inline awk in `/handoff` step 7b. Zero Claude tokens
- ➕ `scripts/rotate-log` — Python log rotation. Keeps newest N session blocks live in SESSION-LOG.md, moves older blocks to ARCHIVE-LOG.md. Replaces inline bash in `/handoff` step 7c
- ➕ `TODOS.md` per-project canonical TODO source — separates open work from session narrative. SESSION-LOG.md is now narrative-only; TODOS.md is the single source of truth for open items

#### Changed
- ♻️ `claude/.claude/CLAUDE.md` — replaced inline dotfiles-only changelog rule with pointer to `/changelog` skill; added `/changelog` to skills list
- ♻️ `scripts/update-triage` — added `"error"` to `URGENT_KEYWORDS` (was aspirationally listed in TODO, missing from implementation)
- ♻️ `.github/workflows/ci.yml` — switched Python step to `python3 -m unittest discover -s tests -p "test_*.py"` so new test files are auto-picked up without CI edits
- ♻️ `tests/install.bats` `make_fixture` — added `scripts/update-triage` stub so `chmod +x` in `install.sh` doesn't fail with "No such file or directory"
- ♻️ `README.md` — structure table updated: scripts dir lists all 4 scripts; tests dir lists both Python test files
- ♻️ `scripts/update-triage` `get_tier` — `[TEST]` tag now always returns CRITICAL regardless of other tags present
- ♻️ `CLAUDE.md` — `[TEST]` added to priority tag table as CRITICAL; note that it overrides all other priority tags
- ♻️ `.github/workflows/ci.yml` — added `python3 tests/test_update_triage.py` step after bats suite
- ♻️ `session-handoff` skill rewritten — reads TODOS.md (not full SESSION-LOG.md), calls update-cache/rotate-log scripts, simplifies Top-5 selection to tier-order. ~3.5K tokens per run vs ~10K prior
- ♻️ `dev-brief` skill updated — supports TODOS.md projects (pointer cache format), SESSION-LOG.md rename, updated reconcile write routing
- ♻️ `scripts/update-triage` — handles pointer-format cache entries; find_orphans checks SESSION-LOG.md and TODOS.md alongside session-log.md
- ♻️ `CLAUDE.md` — TODO tag reference updated from session-log.md to TODOS.md; re-entry prompt rule softened to trust-but-verify (decisions/context authoritative; task state reconciles against file state)
- ♻️ `session-log.md` renamed to `SESSION-LOG.md`

### 2026-05-31
#### Added
- ➕ `scripts/update-triage` — Python script reads `~/dev/.triage-cache` and writes `TRIAGE-BLOCK.md` with HTML color spans (tier/annotation tag colors, RELEASE PENDING, orphan list). Zero Claude tokens. Called by `/handoff` step 7d and runnable manually via `update-triage` on PATH
- ➕ `session-handoff` step 7d — run `update-triage` after every `/handoff` so `TRIAGE-BLOCK.md` is always current
- ➕ `install.sh` symlinks `update-triage` to `~/.local/bin/update-triage`
- ➕ `dev-brief` Step 3b fix-commit reconcile (stale-after-fix protection P1): flags open `[BUG]`/`[FEAT]`/`[RELEASE]` TODOs whose work a commit may have already done, as `⚑ possibly resolved by <hash>(<repo>) — verify`. Advisory-only, never auto-closes. Conservative matching biases to precision
- ➕ `session-handoff` step 7c — auto-rotates `session-log.md`. Keeps newest 3 blocks live, moves older blocks to `ARCHIVE-LOG.md`. Cuts read cost ~74% (220 KB → 57 KB)

#### Changed
- ♻️ `/dev-brief triage` demoted to cache-repair tool — `TRIAGE-BLOCK.md` is now owned by the `update-triage` shell script
- ♻️ `dev-brief` deep-dive OPEN TODOs now tiered + tag-grouped — renders by priority tier (CRITICAL → HIGH → MEDIUM → LOW → BACKLOG, empty tiers omitted) with annotation-tag subgroups inside each tier
- ♻️ `session-handoff` re-entry Top-5 trim — terminal paste now splices only the Top-5 attention set (first-action + items advanced + highest-priority carry-forwards, excluding `[WAITING]`/`[BACKLOG]`) plus `+N more` pointer. Saves ~750 tok at handoff print + ~750 tok at next-session paste-in
- ♻️ `session-handoff` re-entry dup-kill — `### Re-Entry Prompt` in session-log.md now stores a pointer to `### Incomplete / Next Steps` instead of re-embedding the verbatim TODO list. Drops ~14K chars (~3.5K tok) of duplicate re-read per dev-brief/handoff load

#### Fixed
- 🛠️ 45-minute `/handoff` warning now actually visible — root cause: `session_timer.py` printed to Stop-hook stdout (debug log only, never UI). Fix: `combined-statusline.sh` shows persistent elapsed clock (`⏱ Nm`, flips to `⚠️`/`🚨` at 45m/55m); `session_timer.py` switched to JSON `systemMessage` field, one-shot per threshold
- 🛠️ hooks dir un-drifted — live `~/.claude/hooks` was a real dir, not the dotfiles symlink, so hook edits never reached the running machine. Re-symlinked and verified byte-identical
- 🛠️ `dev-setup` Step 12 `.gitignore` — replaced overwrite-or-skip with append-if-missing merge. Adds only absent patterns under `# --- added by /dev-setup ---` marker, never touches existing lines, idempotent across re-runs

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
