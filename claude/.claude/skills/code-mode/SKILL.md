---
name: code-mode
description: Use PROACTIVELY the moment you start real code work — writing a new function or feature, fixing a bug, refactoring, building a new system, reviewing or cleaning up a diff, adding tests, or debugging a failure. Also use when the user says "code mode", "use code-mode", "work like code-mode", or "think this through first" on a coding task. Loads the code-lifecycle discipline (five-gate task loop, red-green inner loop, code-specific gate-skip smells) and routes into the code-quality and security substrate that already exists (`CODE-STANDARD.md`, `SECURITY-STANDARD.md`, `/tdd`, `/diagnose`, `/code-refactor`, `/code-decay`, `/requirements`, `/architecture`, `/brainstorm`, `/grill-me`, `/write-plan`, `/threat-model`, `/prototype`, `/code-crit`, `/mutation-testing`, `/ante-mortem`, `/review-response`, `/trust-but-verify`, `/run`, `/changelog`). Say "code mode off" to deactivate.
---

# The Code Method

The **dispatcher layer** over the coding skills — decides _when_ to reach for them,
never restates what they own. Don't re-teach `CODE-PRINCIPLES.md`/`CODE-STANDARD.md`;
`standards_guard.py` already forces those before the first edit.

A hard task is one where the first idea might be wrong: multi-step builds, debugging,
anything touching data you haven't looked at yet. One-file edit or a lookup: skip the
gates, just do it.

## Status check (before answering/acting on activation state)

Activation is a **filesystem fact, not a conversational one** — `.work/.code-active`
can outlive the session that created it. Check the file on disk before answering
"is code-mode on?" or acting on "turn it off"; never answer from memory. If asked to
deactivate and the file exists (even if you don't recall activating it), delete it and
log a deactivation line in `.work/GATES.md`. If it doesn't exist, say so — that's the
one case "not active" is correct.

## Activation (before any task work)

State lives **on disk**, not in attention — that's what survives long sessions.

1. `mkdir -p .work`, create empty marker `.work/.code-active` (the persistence hook owns
   its contents — never edit, only create/delete).
2. Create `.work/GATES.md`:
   ```markdown
   # Gate State

   Task: <one line>
   Done means: <a failing test + the exact command that runs it>
   Check: <command/observation that proves it>
   Load-bearing unknowns:

   - [ ] <fact that, if wrong, changes the whole approach>
         Current gate: 1
         Gate log:
   - G1 <date>: <scope decision, one line>
   ```
3. Update `Current gate:` + append a log line every gate pass. Lost or context grown
   long: re-read `.work/GATES.md` before your next move — it's the anchor, memory isn't.
4. **Mechanical levers**, once per activation: recommend `/effort high|max` if not
   already high (let the reasoner pick the level). Check what's already wired before
   offering a hook — `code_standard_lint.py`/`code_formatter.py` already fire on
   `Edit|Write|MultiEdit`; don't duplicate them.

**Deactivation:** "code mode off" — delete the marker, log a final GATES.md line, stop
the loop. Also deactivate when Gate 5's report lands and the user moves to trivial work.

## The five gates

A gate must pass before the next opens. Stalled or surprised: name the gate, re-run it.

### Gate 1 — Spec before work

`Done means:` = **a failing test + the exact command that runs it.** Can't write the
test → you don't understand the task.

**Route table:**

- `[FEAT]` → `/tdd` (branch CLAUDE.md already defaults to test-first).
- `[BUG]` → `/diagnose`.
- `[CHORE]`/refactor with a **named** smell → `/code-refactor` (behavior-preserving fix
  under a test gate).
- "Where do I start" / unnamed refactor risk → `/code-decay` (churn × complexity finds
  the smell first).
- New system → `/requirements` → `/architecture`.
- Open design decisions → `/brainstorm` → `/grill-me` → `/write-plan`.
- Security-touching → `/threat-model`.
- Design question itself unanswered (data model/state-machine shape unclear, or which
  UI/API variant is right) → `/prototype` first, then re-enter Gate 1 with a real spec.
  Prototype code is explicitly throwaway, not the deliverable — discard or rewrite once
  Gate 1 can be stated. **Skips Gates 4–5 entirely**: no `Done means:` to check against,
  success = "the question is answered." Gates 4–5 run only on the real implementation.

Preload `CODE-STANDARD.md` + the ONE matching language file — turns `standards_guard.py`
from a blocker into a check already passed. No matching preload for
`SECURITY-STANDARD.md`: that router loads independently via `CLAUDE.md`
(unconditional, no hook enforces it — `standards_guard.py`'s `REFS_DIR` is
`references/code` only). `security-touching→/threat-model` above is the only touchpoint
this gate owns.

Pick test type from `TESTING-STANDARD.md`'s decision table, record it. Record diff base.
Check standing rules (CLAUDE.md/KNOWLEDGE.md/skills/memory) before inventing an approach
the project already has. List load-bearing unknowns in GATES.md. Ambiguous in a way that
changes what you'd build → ask one question at the biggest gap; otherwise pick the
default, say so in one line, proceed.

### Gate 2 — Evidence before reasoning

Never design from memory of what a file/API/dataset "probably" looks like — open it.

- **Baseline green first.** Run the suite before touching anything — an unknown-state
  suite makes every later result unreadable. `TESTING-STANDARD.md` calls this the smoke
  pre-flight; `/mutation-testing` requires it too.
- `[BUG]`: reproduce before theorizing — pin the failing case before hypothesizing.
- Find the seam before editing (`CODE-REFERENCE.md` § Seams/Deep Modules).
- `/code-decay` when "where is the risk" is itself the unknown.
- Thin end-to-end pass: one vertical slice through the real pipeline, verified, before
  scaling.
- 3+ steps: keep a live plan in the `.work/` trio (PLAN/FINDINGS/PROGRESS), format-detect
  per `planning-format-detect.md` first.

### Gate 3 — Reason adversarially

Switch roles, try to kill the answer. Strongest form is an **independent attacker with
cold context** — the mind that wrote the answer shares its blind spots. Delegate
automatically on any non-trivial task; don't wait to be asked. Technique itself
(assumption violation, cascade construction, confidence rubric) lives in
`~/.claude/skills/code-crit/references/ADVERSARIAL-TECHNIQUES.md` — per its
caller-policy, no `verified`/`unverified` field, drop ≤25/speculative findings.

**Route in preference order**, checking restrictions first and recording skips in
GATES.md:

1. **Advisor**, if available — strongest, sees the transcript (context-aware, not
   cold; require evidence-backed challenges, not fresh conclusions). Frame by gate
   state: "At Gate <N>. Done means: X. Check: Y. Unknowns: Z. Attack <thing> — what
   input/state/reading makes it wrong?" Fails/times out/no substance → subagent.
2. **Subagent**, the common case. `Agent` tool, `run_in_background: false`, wait for
   result. Use `cavecrew-reviewer` (or namespaced ID) if registered; else a
   general-purpose type with an adversarial persona instructed to CONSTRUCT failure
   scenarios. Never invent a type. **`/code-crit` is the primary route for a diff**
   (fast/thorough). Sanitized brief only: neutral scope, invariants, the failure
   direction — never the intended fix, suspected bug, desired verdict, or full
   GATES.md/resolved unknowns. Fails → retry once with a revised prompt, then inline.
3. **Inline self-attack**, fallback only when delegation is unavailable/exhausted/
   prohibited. Actually test the failure direction — don't just reread approvingly.

**Completion barrier:** don't advance until (a) a delegated review is substantive and
every finding dispositioned, or (b) delegation was genuinely unavailable and an equally
substantive inline attack is dispositioned. Zero-content review doesn't count.

**Loop until stable:** a finding that revises the fix is a new claim — re-attack it
(same order) before advancing. Stop when a round changes nothing, or the fix is too
trivial to hide another error. Log rounds (`G3`, `G3-continued`, `G3-FINAL`).

Name the concrete failure direction first (false-negative for security, malformed input
for a parser, counterexample for a claim) — test it, don't imagine it. Then steelman
what survives; steelman the existing thing before changing it. "Already solid" is a
legitimate verdict — never manufacture findings, never discard a clean verdict because
you wanted findings. Two failed fix attempts → diagnosis is wrong, escalate to
`/diagnose`.

`/mutation-testing` attacks the tests, not the code. `/code-sec` + `/threat-model` are
required conditional routes when the diff touches auth/input/secrets. `/ante-mortem`
attacks a design's future failure modes; `/review-response` is this gate applied to
incoming feedback. `gate3_skip_detector.py` enforces delegation mechanically (keys on
the `GATES.md` filename).

### Gate 4 — the three-rung ladder

"It ran" isn't verification. Verify at the layer of the claim.

1. **`/trust-but-verify`** — suite green, fresh run, exit code actually read. Proves
   nothing broke.
2. **Spec check** (prose, no skill) — does it do what Gate 1's `Done means:` claimed?
   A green suite testing the wrong thing passes rung 1, fails here.
3. **`/run`** — app launches and works with the change in. Catches what tests mocked
   away: wiring, config, startup order.

Full suite, not just the new test (regression is a separate claim). Re-read your own
`git diff` as a reviewer. Name which rung you stopped at. `[UX]` checklist for anything
machine-unverifiable. Sample the tails (first/last/weirdest), not just the middle — an
all-clean sweep means the verification is broken until you can explain why it's real.

### Gate 5 — diff-shaped report

Files touched; tests added with real output pasted; rung reached (named); standards
deviations flagged (`CODE-STANDARD.md`'s "flag the drift"). Separate verified from
assumed, out loud. Cite specifics — paths, line numbers, commands, numbers seen. Report
what you observed, not what you intended. `[VERIFY]` items to `.work/VERIFY.md`, never
a hedged sentence. Commit granularity per CLAUDE.md: one file per commit. `/changelog`
if changelog-worthy.

## Inner loop — red-green

`CODE-PRINCIPLES.md` commits to it: red-green, one vertical slice, refactoring excluded
and deferred to review — naming "you're in green, not refactor" is the point.

```
REASON       what do I expect this test to fail on
ACT          write the test, or the implementation
OBSERVE      read what came back — red/green as expected?
RE-EVALUATE  confirms the plan or changes it? decide, loop
```

**Fresh read before every edit** — hard rule, highest-value habit, `code-score.py`
measures it. After every result: confirms or changes? (momentum is the failure mode).
Batch only truly independent operations.

## Standing habits

Relative → absolute (dates, versions). Surface constraints before they bite. Cheapest
probe of the biggest unknown beats the largest visible chunk. Reversible+in-scope: just
do it; irreversible/outward-facing/scope-change: confirm first. Unblock yourself before
escalating; bundle real questions. 3+ repeats → script, not per-instance reasoning.
Preserve by default — deleting substantive content needs approval. First failure:
diagnose then fix, never re-issue the same failing command (two failures of the same
fix → Gate 3's stop rule). Narrate gate transitions, don't go dark. Absolute paths over
`cd`.

## Code-specific gate-skip smells

- Abstraction extracted on the _second_ look-alike, not the third (rule-of-three).
- Edited a file outside the diff — shotgun surgery; file a `[CHORE]` instead.
- Implementation before a failing test on `[FEAT]`.
- New test passed on first run when red was expected — it isn't testing.
- Ran the new test but not the suite.
- `TODO:` in code without a mirrored `TODOS.md` entry (`CODE-STANDARD.md` MUST).
- Mocked your own file/buffer layer inside an integration test.
- Attempt three of the same fix → `/diagnose`.
- The throwaway became the implementation — kept `/prototype` code as deliverable
  without re-entering Gate 1.

Any one: stop, re-read `.work/GATES.md`, go back to that gate.

## Non-code fallback

Five gates still apply to docs/config/prose: skip the route table, red-green loop, and
code smells. Define done in a sentence, open the real file instead of assuming, attack
once (same advisor→subagent→inline order), verify at the claim's layer, report
calibrated.

## Notes

Method skill, not a workflow — its only artifacts are the marker and GATES.md. Measure,
don't assume: `scripts/code-score.py <model>` (`--baseline`, `--split-code`) scores real
sessions on the discipline habits. Dispatcher over `/tdd` `/diagnose` `/code-refactor`
`/code-decay` `/requirements` `/architecture` `/brainstorm` `/grill-me` `/write-plan`
`/threat-model` `/prototype` `/code-crit` `/mutation-testing` `/ante-mortem`
`/review-response` `/trust-but-verify` `/run` `/changelog` — invoke them, never
duplicate what they do. Stacks with caveman mode (caveman = how you speak, code-mode =
how you work). Skip it for trivial work. A task that keeps failing under this
discipline needs a stronger model, not a looser process.
