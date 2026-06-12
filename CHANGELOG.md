# Changelog

## [Unreleased]

### 2026-06-12
#### Added
- ➕ `brainstorm` skill — generative design dialogue (Superpowers-derived): explores context, clarifies one question at a time, proposes 2-3 approaches with tradeoffs + recommendation, writes `docs/brainstorm/<topic>-YYYY-MM-DD.md`, hands off to `/grill-me` [\[4bb5fe9\]](https://github.com/k0d3x8its/dotfiles/commit/4bb5fe93dd909f0cbacb45e32a6eef0236a4f974) [\[53bbc65\]](https://github.com/k0d3x8its/dotfiles/commit/53bbc65c43fa19d92716b46121dcf38f1f063160)
- ➕ `write-plan` skill — converts a grilled design doc + findings.md into Goal/Micro-Goal/Task task_plan.md; every Task carries a `verify:` sub-bullet invisible to `/sync-trello`; offers (never forces) Trello sync [\[23e3c1b\]](https://github.com/k0d3x8its/dotfiles/commit/23e3c1b0ea31512cddc9c006075d64c839ddb961)
- ➕ `trust-but-verify` skill — evidence gate: fresh verify-command run + exit code before any done/push/PR/handoff claim (not commits); unproven claims become `[VERIFY]` TODOs, unverifiable ones become `[UX]` checklists; `detect.md` resolves the verify command project-agnostically (declaration → build runner → CI workflows minus install steps → tool presence) [\[f03cabf\]](https://github.com/k0d3x8its/dotfiles/commit/f03cabfc3497886daf5271d0b75688230c2f7e48) [\[2e06b0d\]](https://github.com/k0d3x8its/dotfiles/commit/2e06b0dc3d3fd4530ddeb0e979fab7ed9a749025)
- ➕ `review-response` skill — rail for incoming review/CI feedback: read fully → restate → verify against code → judge fit → fix or reasoned pushback, one item at a time through the trust-but-verify gate [\[2f5549c\]](https://github.com/k0d3x8its/dotfiles/commit/2f5549cb122a1ba9b2b5969989730d7de2abd989)
- ➕ Revised adaptation spec for the four Superpowers-derived skills (gap analysis fixes folded in) [\[4ad5156\]](https://github.com/k0d3x8its/dotfiles/commit/4ad5156ed5c19b8861fb5fffe38d5cbf34e9ca5a)

#### Changed
- ♻️ `CLAUDE.md` — added `[VERIFY]` to priority (always Critical, like `[TEST]`) and annotation tag tables, trust-but-verify session rule, design-doc row in File Taxonomy, and the five pipeline skills to the Skills Available list [\[ec23814\]](https://github.com/k0d3x8its/dotfiles/commit/ec23814bb7727d2922d900f4e8bc85143514a2da)
- ♻️ Repo `KNOWLEDGE.md` — declared the explicit verify command so trust-but-verify detection resolves at priority 1 [\[f2767c8\]](https://github.com/k0d3x8its/dotfiles/commit/f2767c8ba6b7609b0c94c1fe71575dfc06d4d9b4)

### 2026-06-02
#### Added
- ➕ Append short commit hash to changelog entries [\[e4210ad\]](https://github.com/k0d3x8its/dotfiles/commit/e4210ad7460c279894afcdaa7e330951dffb8677)
- ➕ Add /tmp save, argument-hint, suggested skills [\[33f4f7f\]](https://github.com/k0d3x8its/dotfiles/commit/33f4f7fdb8c0e7378ab8f7b8725e0f0d9c52ad96)
- ➕ Auto-refresh TRIAGE-BLOCK on TODOS.md edit [\[843e3b3\]](https://github.com/k0d3x8its/dotfiles/commit/843e3b3bbc1f2501d770f75a1bd5d8f97e974a7b)
- ➕ Pop tool to merge tangent findings [\[7d2906e\]](https://github.com/k0d3x8its/dotfiles/commit/7d2906ef87c303af0db4079fb68295144b63deba)
- ➕ Durable end-of-work-session skill [\[9f0cd82\]](https://github.com/k0d3x8its/dotfiles/commit/9f0cd8266c527ce63ad578c74b2125e6d0f00bf3)
- ➕ `grill-me` skill — stress-tests a plan from idea to foundation, resolving decisions one branch at a time before building starts; appends resolved decisions to `findings.md` [\[c438355\]](https://github.com/k0d3x8its/dotfiles/commit/c43835571ffa7301f55115bd44a66d04a4f851c5)
- ➕ `zoom-out` and `write-a-skill` skills — `zoom-out` maps unfamiliar codebase modules and callers on demand; `write-a-skill` provides structured authoring process for new skills with progressive disclosure [\[5c6bb45\]](https://github.com/k0d3x8its/dotfiles/commit/5c6bb4515c614f61150e28b356796c98e09f14a0)

#### Changed
- ♻️ `/changelog` SKILL.md — switched hash links from double-bracket ref format to standard markdown links; entries now prose descriptions, not raw commit subjects [\[8fe6fb8\]](https://github.com/k0d3x8its/dotfiles/commit/8fe6fb838a122ef92911d82359355c74cbb4c5bf)
- ♻️ `CLAUDE.md` session tools — added `/close` to the four-tool session model, documented its role as lightweight close+resume distinct from `/checkpoint` [\[dc4747d\]](https://github.com/k0d3x8its/dotfiles/commit/dc4747d6aba4982a9dc28d563635d3045c023d51)
- ♻️ Add [UX] annotation tag to TODO tag table [\[06af40c\]](https://github.com/k0d3x8its/dotfiles/commit/06af40ce3ceafa1cc9b6c3f13972ce0e5b671a1d)
- ♻️ Remove model override — revert to default (sonnet) [\[20109ef\]](https://github.com/k0d3x8its/dotfiles/commit/20109effaa172d20102f123e7a2655ed6fda0223)
- ♻️ Delete dead format-triage.md [\[5176d0a\]](https://github.com/k0d3x8its/dotfiles/commit/5176d0a547fde0d390288f48b81c4597d87c017b)
- ♻️ Trim SKILL.md 60% — remove duplication and compress verbosity [\[60fed30\]](https://github.com/k0d3x8its/dotfiles/commit/60fed309ab7a101df2b3832fc7a2f80fccc50c25)
- ♻️ Register refresh_triage hook; reconcile to live [\[00eb39e\]](https://github.com/k0d3x8its/dotfiles/commit/00eb39e885cc6d30ca8eb2af97129b5b6bb17660)
- ♻️ Ignore Python __pycache__ and *.pyc [\[05d8b36\]](https://github.com/k0d3x8its/dotfiles/commit/05d8b363c4aa064182d226191e11f15e453d1f7f)
- ♻️ Document three-tool session model [\[f0335fc\]](https://github.com/k0d3x8its/dotfiles/commit/f0335fcb4ffd22b8f7ce7e9fdb399e424fddfb94)
- ♻️ Make lean mid-session fork tool [\[2259e45\]](https://github.com/k0d3x8its/dotfiles/commit/2259e4554479e23f36dcb68a9b6147437f2e76c5)
- ♻️ Remove unused truncate function [\[8ccb78d\]](https://github.com/k0d3x8its/dotfiles/commit/8ccb78d54bd1dbb7a16ea3ab041b919d3b8e5b01)
- ♻️ Replace dead inline changelog step with /changelog pointer [\[4e0dc9d\]](https://github.com/k0d3x8its/dotfiles/commit/4e0dc9d0f307670d7ea1fbdcae3e3d89facc0f54)
- ♻️ Add TestCheckpointBlocks regression class [\[2bda548\]](https://github.com/k0d3x8its/dotfiles/commit/2bda548ca51eafb29594c17158392ddaa09dd26b)

#### Fixed
- 🛠️ Match Session Checkpoint headings in BLOCK_RE [\[343eaf6\]](https://github.com/k0d3x8its/dotfiles/commit/343eaf695738668443092baf6bc4dd8b5d7be54b)
- 🛠️ Anchor planning-file patterns to repo root [\[95949c6\]](https://github.com/k0d3x8its/dotfiles/commit/95949c6aa49989da67d3c89032056b69bbed8b31)
- 🛠️ `session-handoff` and `session-handoff-return` — removed `close` from skill `name:` field; it was polluting `/close` autocomplete with irrelevant matches [\[463c3ef\]](https://github.com/k0d3x8its/dotfiles/commit/463c3ef134553e438b24b99f31db88ed7bb59282) [\[31099ea\]](https://github.com/k0d3x8its/dotfiles/commit/31099ead37f99e4413d4dbd9dce1c8822281a215)
- 🛠️ `session-checkpoint` frontmatter `name:` — changed from `session-checkpoint` to `checkpoint` so `/checkpoint` resolves as exact match in autocomplete, beating the built-in `rewind-checkpoint` [\[d8377a8\]](https://github.com/k0d3x8its/dotfiles/commit/d8377a88430bc50cf8a5be8ed934b2b49ecf1bd3)

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
- ➕ `tests/test_rotate_log.py` — `TestCheckpointBlocks` regression class (4 tests): checkpoint block parsed, handoff+checkpoint counted separately, checkpoint not swallowed into handoff, checkpoint date → epoch. Suite now 24 tests
- ➕ `claude/.claude/hooks/refresh_triage.py` — `PostToolUse` hook: when a `TODOS.md` under `~/dev` is edited, derives the project and runs `update-cache` + `update-triage` to refresh `TRIAGE-BLOCK.md` automatically. Path-guarded (silent no-op on any other edit), runs in harness → zero model tokens. Registered in `settings.json` with an `Edit|Write` matcher

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
- ♻️ `claude/.claude/CLAUDE.md` — `[INVESTIGATE]` row expanded: covers audits and open sweeps, no hypothesis required; output findings list, spawn new tasks
- ♻️ `git/.gitignore_global` — added `TODOS.md`; anchored all filename-only patterns to repo root with leading `/`
- ♻️ `git/.gitconfig` and `git/.gitignore_global` — stowed (were real files; now symlinks managed by install.sh)
- ♻️ `.gitignore` — removed redundant `TODOS.md` entry (now covered by global excludes)

- ♻️ `claude/.claude/settings.json` — reconciled to live machine state and re-symlinked (`install.sh` already links it; the link had been replaced by a real file). Added `"model": "opus"`; removed stale manual caveman hooks (`caveman-activate.js` SessionStart + `caveman-mode-tracker.js` UserPromptSubmit) — the caveman plugin provides these, so they were the duplicate-hook burn already removed from live but never synced here

#### Fixed
- 🛠️ `scripts/rotate-log` — `BLOCK_RE` now matches `## Session Checkpoint` as well as `## Session Handoff` (`^## Session (?:Handoff|Checkpoint)`). Old regex undercounted blocks and swallowed checkpoint blocks into the preceding handoff block on rotation

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
