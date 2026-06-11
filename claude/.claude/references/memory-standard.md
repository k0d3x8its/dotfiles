# Memory Standard

Reference for the KNOWLEDGE.md system. Read by /remember and /checkpoint before any gate or write.

---

## Files

| Scope | Path |
|---|---|
| Global | `~/.claude/KNOWLEDGE.md` |
| Per-project | `<project-root>/KNOWLEDGE.md` |

Both committed to git (global via dotfiles, local with the repo). Never gitignored.

---

## Entry Format

Flat prose bullet. No slugs, no frontmatter, no tags.

```
- Powerline removed 2026-05-29 — caused "read() failed: Connection reset by peer". Trueline replaces it.
- Skills + CLAUDE.md symlinked from dotfiles — edit source at dotfiles/claude/.claude/, not ~/.claude/ directly.
```

One fact per bullet. Keep it tight — no multi-sentence explanations.

---

## Promotion Bar (4 tests — ALL must pass)

1. **SETTLED** — not open work. If the sentence contains a verb like "implement", "fix", "add", "build", "update" → TODOS.md instead.
2. **NON-OBVIOUS** — can't be derived by reading the code or files alone. If a new session could figure it out in 30 seconds by looking at the repo → don't promote.
3. **NOT A RULE** — empirical observation, not a normative instruction. Rules go to CLAUDE.md.
4. **DURABLE** — unlikely to go stale within ~3 months.

---

## NOT A RULE — Examples

These are **rules** → `CLAUDE.md`:
- "Always use kebab-case filenames"
- "Commit granularity: one file per commit"
- "Never add Co-Authored-By to commits"
- "Always explain the why in code comments, not the what"

These are **facts** → `KNOWLEDGE.md`:
- "Powerline removed 2026-05-29 — Trueline replaces it"
- "trello-cli uses pnpm — npm install breaks the lockfile"
- "Skills symlinked from dotfiles — edit source, not ~/.claude directly"
- "references/ is a whole-dir symlink — files added to dotfiles/claude/.claude/references/ are immediately available at ~/.claude/references/"

Quick test: "Am I telling Claude **how to behave**, or telling Claude **what is true**?"
- Behavior → CLAUDE.md
- Truth → KNOWLEDGE.md

---

## Routing Rule

Default: **LOCAL** (`<project-root>/KNOWLEDGE.md`).

Escalate to **GLOBAL** (`~/.claude/KNOWLEDGE.md`) if:
- Fact is true in ≥2 projects, OR
- Fact is about environment, toolchain, or workflow (shell, git config, Ubuntu setup, Claude Code behavior itself)

---

## Deduplication

Before writing, scan existing entries semantically.
- Exact duplicate → report "already captured", stop
- Overlap → distill: propose a merged entry that replaces both; confirm before writing
- No overlap → proceed

---

## Distill-on-write

No append-only log. Every entry must earn its place. Before writing, ask: "Does this replace, extend, or stand alone from existing entries?" Never blind-append when an update to an existing line is more precise.
