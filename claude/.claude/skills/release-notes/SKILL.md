---
name: release-notes
description: Synthesize accumulated RELEASE-NOTES.md session entries into polished GitHub prose release notes. Triggers on /release-notes.
---

# Release Notes Skill

**Trigger:** `/release-notes`
**Purpose:** Read the accumulated `RELEASE-NOTES.md` scratch file from session-handoff entries and produce human-readable, prose-style GitHub release notes ready to paste into a GitHub draft release.

---

## When to Use This

- You're about to tag a new version and create a GitHub Release
- You've had one or more sessions that updated `RELEASE-NOTES.md`
- You want to turn raw session notes into polished release prose

---

## What Claude Will Do

When you run `/release-notes`:

1. **Read `RELEASE-NOTES.md`** — parse all session entries since the last release
2. **Read `CHANGELOG.md` if it exists** — use the latest version block for scope; skip if absent (RELEASE-NOTES→CHANGELOG migration is a pending decision)
3. **Ask for the version tag** if not obvious from context (e.g. `v1.0.1`)
4. **Generate prose release notes** — narrative style, not bullet changelog. Explain what changed and why it matters to the user. Group related changes. Lead with the most impactful change.
5. **Print the output** — rendered markdown, ready to copy-paste into a GitHub draft release
6. **Ask if you want to clear `RELEASE-NOTES.md`** — once notes are published, the file should be wiped for the next version cycle

---

## Output Format

The output is rendered markdown — no code block wrapper. Print it directly so the user can copy-paste straight into GitHub.

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

1. **Do not ask clarifying questions upfront** — read `RELEASE-NOTES.md` (and `CHANGELOG.md` if present) first, then ask for version tag if missing
2. If `RELEASE-NOTES.md` is empty or missing, tell the user and stop — do not fabricate notes
3. Group session entries thematically, not chronologically
4. Ignore internal tooling notes (Claude Code artifacts, session overhead) — focus on product changes
5. After printing notes, ask: `Clear RELEASE-NOTES.md for the next version cycle? (yes/no)`
6. If yes: wipe the file contents but keep the file (leave it empty, not deleted)

---

## Integration With session-handoff

`session-handoff` automatically appends a raw entry to `RELEASE-NOTES.md` at the end of each session. This skill consumes those entries when it's time to release.

`RELEASE-NOTES.md` is in `.gitignore` — it is a local scratch file, never committed.
