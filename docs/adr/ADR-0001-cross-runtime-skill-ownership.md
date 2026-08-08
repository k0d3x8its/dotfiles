# ADR-0001: Cross-runtime skill ownership

- Status: accepted
- Date: 2026-07-14

## Context

Claude Code and Codex use separate live catalogs (`~/.claude/skills` and
`~/.codex/skills`). Most custom skills are authored in the Claude catalog first.
Copying them into the Codex catalog made a skill available, but created two sources
that could drift. A single blanket symlink is also unsafe because many skills name
runtime-specific files, hooks, instructions, or product behavior.

## Decision

Use a hybrid ownership model:

1. Runtime-neutral skills have one canonical directory under
   `claude/.claude/skills/<name>`.
2. Their Codex catalog entries are relative repository symlinks to that canonical
   directory. The installer continues to link each catalog entry into the matching
   live runtime catalog.
3. Skills with real runtime-specific behavior keep two real directories, one per
   runtime.
4. Runtime-only skills remain in their owning catalog until they are ported or made
   portable.
5. `tests/test_skill_architecture.py` is the ownership manifest and enforcement
   gate. Every skill must be classified, shared links must resolve to the canonical
   Claude source, and byte-identical runtime-specific copies are rejected.

The initial shared set is `bounty-hunter`, `create-gdd`, `grill-me`,
`mutation-testing`, `write-a-skill`, and `zoom-out`. `threat-model` remains
Claude-only. All other paired skills are runtime-specific at the time of this ADR.

## Consequences

- Editing a shared skill from either runtime edits the same source.
- New skills authored in Claude can be exposed to Codex with one relative catalog
  link when they are runtime-neutral.
- Product-specific wording and behavior are not flattened merely to reduce file
  count.
- Adding or changing a skill requires updating the ownership manifest deliberately.
- A fresh runtime session may be required before newly installed skill metadata is
  discovered.
