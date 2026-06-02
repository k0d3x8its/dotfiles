---
name: changelog
description: Generate and insert a dated sub-block under ## [Unreleased] in the project's CHANGELOG.md based on git commits since the last versioned release. Uses the project's emoji template format. Triggers on /changelog.
---

# Changelog Skill

**Trigger:** `/changelog`
**Purpose:** Read recent git commits, group by type, and insert a dated sub-block under `## [Unreleased]` in the project's `CHANGELOG.md`.

---

## When to Use This

- End of a session that produced real project changes
- Before running `/release-notes` (ensures [Unreleased] is populated)

---

## What Claude Will Do

1. **Detect `CHANGELOG.md`** in the current project root (`pwd`). If missing, ask: "No CHANGELOG.md found — create one? (yes / no)". If yes, copy the template from `~/.claude/skills/dev-setup/templates/CHANGELOG.md`. If no, stop.
2. **Find the last versioned entry** — scan for the first `## [vX.Y.Z]` or `## [X.Y.Z]` header (not `[Unreleased]`). Extract the version string.
3. **Get commits since last version:**
   - If a matching git tag exists: `git log {tag}..HEAD --oneline --no-merges`
   - If no matching tag: `git log --oneline --no-merges -20` (last 20, capped)
   - Filter out any commit whose subject already appears verbatim anywhere in the current `[Unreleased]` block (dedup).
4. **If no new commits** after dedup → print "Nothing new since last entry — CHANGELOG.md unchanged." and stop.
5. **Group commits by conventional-commit prefix** → sections with emoji prefix per entry:

   | Prefix | Section | Emoji |
   |--------|---------|-------|
   | `feat:` | `#### Added` | ➕ |
   | `fix:` | `#### Fixed` | 🛠️ |
   | `refactor:` | `#### Changed` | ♻️ |
   | `perf:` | `#### Changed` | 🚀 |
   | `docs:` | `#### Changed` | ♻️ |
   | `chore:` | `#### Changed` | ♻️ |
   | `ci:` | `#### Changed` | ♻️ |
   | `security:` | `#### Security` | 🛡️ |
   | `remove:` / `revert:` | `#### Removed` | ❌ |
   | `deprecate:` | `#### Deprecated` | ⚠️ |
   | no prefix / other | `#### Changed` | ♻️ |

   Strip the prefix from each entry body. Capitalise first letter. No trailing period. Append the short commit hash in brackets at end of line: `[abc1234]`. The hash comes from the leading 7-char token of each `git log --oneline` line — capture it before stripping the conventional-commit prefix.

6. **Write a dated sub-block into `CHANGELOG.md`:**
   - Use today's date (`YYYY-MM-DD`) as the sub-block header: `### YYYY-MM-DD`
   - If a `### YYYY-MM-DD` block for today already exists inside `[Unreleased]`: append new section groups into it (merge, don't duplicate section headers).
   - If no block for today: prepend a new dated block at the top of the `[Unreleased]` content (after the `## [Unreleased]` line, before any existing dated blocks).
   - If `## [Unreleased]` is missing entirely: prepend it before the first versioned `##` block, then add the dated sub-block inside it.

7. **Print the diff** — show exactly what was inserted so the user can verify.

---

## CHANGELOG.md Format

```markdown
# Changelog

## [Unreleased]

### 2026-06-01
#### Added
- ➕ Changelog skill [a1b2c3d]

#### Changed
- ♻️ CLAUDE.md rule replaced with /changelog pointer [e4f5a6b]

### 2026-05-28
#### Fixed
- 🛠️ CI badge stuck on stale run [c7d8e9f]

---

## [v1.0.0] - 2026-05-30

### Added
- ➕ Initial release
```

---

## Emoji Glossary (from project template)

| ➕ | ❌ | 🛠️ | 🐞 | 🚀 | ♻️ | 🛡️ | ⚠️ | ⬆️ |
|-------|---------|-------|-----|----------|---------|----------|------------|---------|
| ADDED | REMOVED | FIXED | BUG | IMPROVED | CHANGED | SECURITY | DEPRECATED | UPDATED |

---

## Claude Instructions

**1.** Execute immediately. No clarifying questions unless `CHANGELOG.md` is missing.

**2.** Use `git log` to get commits — never invent entries.

**3.** Strip ticket numbers, PR refs, and `Co-Authored-By` lines from commit bodies. Keep the subject line only.

**4.** Don't add entries for: merge commits, version-bump commits (`chore: bump version`), CHANGELOG/RELEASE-NOTES edit commits (`docs: update CHANGELOG`, `docs: update RELEASE-NOTES`).

**5.** Do NOT commit the file — leave that to the user.
