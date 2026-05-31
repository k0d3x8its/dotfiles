---
name: release-notes
description: Read CHANGELOG.md [Unreleased] section and generate polished GitHub prose release notes. Optionally promotes [Unreleased] to a version entry and writes output to RELEASE-NOTES.md.
---

# Release Notes Skill

**Trigger:** `/release-notes`
**Purpose:** Read the `## [Unreleased]` section of `CHANGELOG.md` and produce human-readable, prose-style GitHub release notes ready to paste into a GitHub draft release.

---

## When to Use This

- You're about to tag a new version and create a GitHub Release
- One or more sessions have added entries to `CHANGELOG.md [Unreleased]`
- You want to turn changelog bullets into polished release prose

---

## What Claude Will Do

1. **Read `CHANGELOG.md`** — extract the `## [Unreleased]` section (everything between `## [Unreleased]` and the next `##` header)
2. If `[Unreleased]` is empty, missing, or `CHANGELOG.md` doesn't exist: tell the user and stop
3. **Ask for the version tag** if not provided (e.g. `v1.0.1`)
4. **Generate prose release notes** — narrative style, not bullets. Explain what changed and why it matters to the user. Group related changes. Lead with the most impactful change.
5. **Print the output** — rendered markdown, ready to copy-paste into a GitHub draft release
6. **Write output to `RELEASE-NOTES.md`** — ephemeral output file, never committed; create the file if absent
7. **Ask: "Promote `[Unreleased]` to `vX.Y.Z` and reset for next cycle? (yes / no)"**
   - If **yes**: rename `## [Unreleased]` → `## vX.Y.Z (YYYY-MM-DD)` in `CHANGELOG.md` and prepend a fresh empty `## [Unreleased]` section above it
   - If **no**: leave `CHANGELOG.md` unchanged

---

## Output Format

Rendered markdown — no code block wrapper. Print directly so the user can copy-paste straight into GitHub.

---

## What's New in v{X.X.X}

{3–5 sentence summary of the release theme. What motivated this release, what the most important changes are, and what the user gains from upgrading. Write for a human, not a changelog parser.}

### {Grouped change area}

{Prose paragraph explaining what changed and why it matters. Not a bullet list — write as if explaining to a user who will read the GitHub release page.}

### {Another grouped area if needed}

{Prose...}

---

**Full changelog:** See [CHANGELOG.md](./CHANGELOG.md)

---

## Prose Style Rules

- Write for the **user**, not the developer
- Lead with **impact**, not implementation
- No raw commit messages, no internal variable names
- Avoid: "fixed a bug where...", "refactored the...", "updated the..."
- Prefer: "You can now...", "X no longer...", "Setting Y now correctly..."
- Keep it tight — a release note is not a blog post

---

## Claude Instructions (Read Before Executing)

1. **Do not ask clarifying questions upfront** — read `CHANGELOG.md` first, then ask for version tag if missing
2. If `[Unreleased]` is empty, missing, or `CHANGELOG.md` absent: tell the user and stop — do not fabricate notes
3. Group changelog bullets thematically, not by order of entry
4. Ignore internal tooling entries (Claude Code artifacts, session overhead) — focus on product changes
5. After printing notes, write output to `RELEASE-NOTES.md`, then ask about promoting `[Unreleased]` to a version
6. When promoting: replace `## [Unreleased]` with `## vX.Y.Z (YYYY-MM-DD)` in-place; prepend fresh `## [Unreleased]\n\n` above it

---

## Integration With session-handoff

`session-handoff` prepends changelog bullets to `CHANGELOG.md [Unreleased]` at the end of each session. This skill reads that section when it's time to release and optionally promotes it to a versioned entry.

`RELEASE-NOTES.md` is in `.gitignore` — ephemeral output, never committed.
