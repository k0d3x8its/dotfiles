---
name: review-response
description: Discipline for INCOMING review and CI feedback — the counterpart to code-review, which gives it. Read all feedback without reacting, restate it, verify each claim against the actual code, judge fit for this codebase, then fix or push back with reasons — no performative agreement. Use when handling PR review comments, CI failures, or reviewer suggestions.
---

# Review Response

**Trigger:** `/review-response` — or reflexively when review comments / CI feedback arrive.
**Purpose:** Respond to feedback with verification, not deference. A reviewer's comment is
a hypothesis about the code, not an instruction.

---

## Phase 1 — Read fully

Read **all** feedback before responding to any of it. No fixing mid-read — later comments
change what earlier ones mean, and reviewers often contradict themselves across a pass.

## Phase 2 — Restate

Each item in your own words, one line. This catches misreadings before they become wrong
fixes. If a restatement feels uncertain, the comment is ambiguous — ask, don't guess.

## Phase 3 — Verify against the code

For each item, check the claim against the actual code:

- Does the bug it describes actually exist at that line?
- Does the suggested change compile / pass / fit the surrounding code?
- Is the comment based on a stale view of the diff?

Reviewers are sometimes wrong. CI is sometimes flaky. Evidence first.

## Phase 4 — Judge fit

Valid suggestion ≠ right for this codebase. Weigh against: project conventions
(CLAUDE.md), scope of the PR, YAGNI. Sort each item: **accept** / **accept modified** /
**push back**.

## Phase 5 — Respond

- **Accept:** fix it. No "great point!" preamble — the fix is the acknowledgment.
- **Push back:** specific reason + evidence (file:line, a failing counter-example, the
  convention it violates). Respectful, never performative.

## Phase 6 — Implement one at a time

One item per change. After each: run the verify command via the `/trust-but-verify` gate
before calling the item addressed. Batch-fixing review items is how regressions slip in
between comments.

## Routing

- Comment exposes a **real bug** → `[BUG]` TODO, close with `/diagnose`
- Comment exposes a **test gap** → `[TEST]` TODO, close with `/tdd`
- Item fixed but **evidence not yet fresh** → `[VERIFY]` TODO, close with `/trust-but-verify`
