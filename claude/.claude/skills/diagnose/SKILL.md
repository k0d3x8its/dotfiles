---
name: diagnose
description: Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce → minimise → hypothesise → instrument → fix → regression-test. Use when user says "diagnose this" / "debug this", reports a bug, says something is broken/throwing/failing, or describes a performance regression. Maps to the [BUG] TODO tag.
---

# Diagnose

A discipline for hard bugs. Skip phases only when explicitly justified.

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a fast, deterministic,
agent-runnable pass/fail signal, you will find the cause. If you don't, no amount of
staring at code will save you.

Spend disproportionate effort here. Be aggressive. Be creative. Refuse to give up.

### Ways to construct one — try in roughly this order

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot.
3. **Curl / HTTP script** against a running dev server.
4. **Headless browser script** (Playwright/Puppeteer) — drives UI, asserts on DOM/console/network.
5. **Replay a captured trace.** Save a real request/payload/event log to disk; replay in isolation.
6. **Throwaway harness.** Minimal subset of the system that exercises the bug path with one call.
7. **Property / fuzz loop.** If the bug is "sometimes wrong output", run 1000 random inputs.
8. **Bisection harness.** Automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Same input through old-version vs new-version; diff outputs.
10. **HITL bash script.** Last resort — if a human must click, structure the loop with
    `~/.claude/skills/diagnose/templates/hitl-loop.template.sh` so captured output feeds back.

### Iterate on the loop itself

- Can I make it faster? (Cache setup, skip unrelated init, narrow scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it deterministic? (Pin time, seed RNG, isolate filesystem, freeze network.)

A 30-second flaky loop is barely better than no loop. A 2-second deterministic loop is
a debugging superpower.

### Non-deterministic bugs

Goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×,
parallelise, add stress, narrow timing windows, inject sleeps. A 50%-flake is
debuggable; 1% is not — keep raising the rate.

### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask for: (a) access to the environment
that reproduces it, (b) a captured artifact (HAR file, log dump, core dump), or
(c) permission to add temporary production instrumentation. Do not proceed to hypothesise
without a loop.

---

## Phase 2 — Reproduce

Run the loop. Watch the bug appear. Confirm:

- [ ] Loop produces the failure the **user** described — not a different nearby failure
- [ ] Failure is reproducible across multiple runs (or at a high enough rate to debug)
- [ ] Exact symptom captured (error message, wrong output, slow timing)

Do not proceed until you reproduce the bug.

---

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any. Single-hypothesis generation
anchors on the first plausible idea.

Each hypothesis must be **falsifiable**:

> "If X is the cause, then changing Y will make the bug disappear / changing Z will make it worse."

If you cannot state the prediction, the hypothesis is a vibe — discard or sharpen it.

Show the ranked list before testing. Users often have domain knowledge that re-ranks
instantly. Proceed with your ranking if they're AFK.

---

## Phase 4 — Instrument

Each probe maps to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:
1. **Debugger / REPL inspection** if the env supports it. One breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end
is a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions: establish a baseline measurement first
(timing harness, profiler, query plan), then bisect. Measure first, fix second.

---

## Phase 5 — Fix + regression test

Write the regression test **before the fix** — but only if there is a **correct seam**.

A correct seam exercises the **real bug pattern** at the actual call site. If no correct
seam exists, a shallow test gives false confidence.

If no correct seam exists, note it. The architecture is preventing the bug from being
locked down. Flag for post-mortem.

If a correct seam exists:
1. Turn the minimised repro into a failing test at that seam.
2. Watch it fail.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase 1 feedback loop against the original scenario.

---

## Phase 6 — Cleanup + post-mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or absence of seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix)
- [ ] Throwaway prototypes deleted

**Then ask: what would have prevented this bug?**

If the answer involves architectural change (no good test seam, tangled callers, hidden
coupling), log it as `[DECISION][INVESTIGATE]` in `session-log.md` with the specific
question. For architectural vocabulary when writing the post-mortem, read
`~/.claude/references/kos-code-reference.md`.

Make the recommendation **after** the fix is in — you have more information now.

State the hypothesis that turned out correct in the commit message so the next
debugger learns.
