---
name: grill-me
description: Stress-test a plan before committing. Use when moving from idea → foundation — resolving decisions one branch at a time before building starts. Outputs findings to .work/FINDINGS.md.
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback before continuing. (Firing multiple at once is bewildering — it stalls resolution instead of advancing it.)

Distinguish facts (answerable by exploring the codebase — do it) from decisions (requires user input — ask).

After each resolved decision, append it to `.work/FINDINGS.md`.

When all branches are resolved, confirm: "All open questions resolved. Ready to proceed to /write-plan?"
