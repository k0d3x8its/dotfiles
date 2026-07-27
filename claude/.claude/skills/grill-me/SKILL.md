---
name: grill-me
description: Stress-test a plan before committing. Use when moving from idea → foundation — resolving decisions one branch at a time before building starts. Outputs findings to .work/FINDINGS.md.
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback before continuing. (Firing multiple at once is bewildering — it stalls resolution instead of advancing it.)

Distinguish facts (answerable by exploring the codebase — do it) from decisions (requires user input — ask).

**Format detection:** check `~/.claude/references/planning-format-detect.md`
(`test -d .work/plan`) before writing.

- **FLAT-FORMAT** (no `.work/plan/` — today's behavior, unchanged): append each
  resolved decision directly to `.work/FINDINGS.md`.
- **NEW-FORMAT** (`.work/plan/` exists): append each resolved decision to
  `.work/findings/<cluster-slug>.md` — one file per grill-me session/decision-cluster,
  slug is `<id>-<topic-slug>.md` — and add or update one index line in
  `.work/FINDINGS.md`: `<status> — <cluster title> — <pointer>`, status
  `open`/`in-progress`/`done`.

When all branches are resolved, confirm: "All open questions resolved. Ready to proceed to /requirements?"
