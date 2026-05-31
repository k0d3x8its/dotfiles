# Changelog

## [Unreleased]

### Changed
- 🔧 `session-handoff` re-entry dup-kill: the `### Re-Entry Prompt` block written to `session-log.md` now stores a *pointer* to the same block's `### Incomplete / Next Steps` instead of re-embedding the verbatim TODO list. The terminal-printed prompt (and `dev-brief` deep-dive) splice the list back in at render, so the paste stays self-contained while the log drops ~14K chars (~3.5K tok) of duplicate re-read per dev-brief/handoff load.

### Added
- ➕ `session-handoff` step 7c: auto-rotates `session-log.md` — keeps the newest 3 session blocks live, moves older blocks to a sibling `ARCHIVE-LOG.md` (date-sorted, newest-at-bottom). Cuts the machine log's dev-brief/handoff read cost ~74% (220 KB → 57 KB).

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
