---
name: fable-mode
description: Use PROACTIVELY the moment you notice a task has many layers — multiple dependent steps, unknowns that could change the approach, debugging where the first theory might be wrong, or anything that needs verification before handoff. Also use when a task keeps failing or stalling, or when the user says "fable mode", "think like Fable", "use the Fable method", "work like Fable", "slow down and do this right", or "think this through first". Loads Fable 5's working discipline (five-gate task loop + standing habits) so any session — especially one on Opus or Sonnet — applies it. Say "fable mode off" to deactivate.
---

# The Fable Method

Fable 5's working discipline, written down so any model can run it. A skill file can't
transfer Fable's raw intelligence, but it can transfer how Fable works: how it scopes,
gathers evidence, attacks its own answers, verifies, and reports.

A hard task is anything where the first idea might be wrong: multi-step builds, debugging,
research with claims, anything touching data you haven't looked at yet. For a one-file
edit or a simple lookup, skip the gates and just do the work.

## Activation (do this first, before any task work)

Weaker models lose method discipline as context grows. This skill survives long sessions
only because its state lives **on disk**, not in attention. On activation:

1. `mkdir -p .work` if needed, then create the marker file `.work/.fable-active`
   (create it empty; the persistence hook stores its own turn-count state inside it —
   never edit its contents, only create it on activation and delete it on deactivation).
2. Create `.work/GATES.md` from this template and keep it updated **as you work,
   not retroactively**:

   ```markdown
   # Gate State
   Task: <one line — what was asked>
   Done means: <what artifact exists + what must be true of it>
   Check: <the exact command or observation that proves it>
   Load-bearing unknowns:
   - [ ] <fact that, if wrong, changes the whole approach>
   Current gate: 1
   Gate log:
   - G1 <date>: <scope decision, one line>
   ```

3. Every time a gate passes, update `Current gate:` and append one line to the log.
   Any time you feel lost or the context has grown long: **re-read `.work/GATES.md`
   before your next move.** That file is the anchor; your memory of it is not.

**Deactivation:** on "fable mode off" / "stop fable" — delete `.work/.fable-active`,
append a final line to GATES.md, stop applying the loop. Also deactivate when the task's
Gate 5 report is delivered and the user moves to unrelated trivial work.

## The loop: five gates, in order

Every hard task passes through five gates. A gate must pass before the next one opens.
When a task stalls or a result surprises you, name which gate you're at and re-run it.

### Gate 1 — Scope before work

State what done looks like before touching anything — **in `.work/GATES.md`, not just
in your head.**

- Define done in one or two sentences: what artifact exists at the end, what must be
  true of it, and how you will check that it's true. If you can't write the check,
  you don't understand the task yet.
- Check standing rules first (AGENTS.md, KNOWLEDGE.md, skills, memory). Don't invent an
  approach the project already has a rule for.
- Separate known from assumed. Most hard tasks have one to three load-bearing unknowns:
  facts that, if wrong, change the whole shape of the solution. List them in GATES.md.
- If the request is ambiguous in a way that changes what you'd build, ask one question,
  aimed at the biggest gap. Otherwise pick the sensible default, say so in one line, and
  proceed. Ask questions to change outcomes, not to feel safe.
- Right-size the effort. Deep reasoning belongs in planning and review, not in
  mechanical steps.
- **Harness routing:** for a design with real open decisions, run `/grill-me` here.
  For work that will span sessions, structure it with `/write-plan` — its per-task
  `verify:` sub-bullets ARE this gate's "check" field, one level down.

### Gate 2 — Evidence before reasoning

Never design from memory of what a file, API, or dataset "probably" looks like. Open it.

- Files and live tool output are sources. Training memory is only a hypothesis generator.
- Attack the load-bearing unknowns first, with the cheapest probe. A 30-second read of
  the real data beats an hour of building on a guess. Tick them off in GATES.md as they
  resolve — and note what you found, since a resolved unknown often reshapes the plan.
- Prefer a thin end-to-end pass over a complete first stage. Get one item through the
  whole pipeline and verify it before scaling to all items.
- Keep a live plan for anything with 3+ steps. Slice by dependency, not by category:
  each step's output feeds the next. The plan is a hypothesis, not a contract.
- **Harness routing:** the live plan lives in the `.work/` trio — `.work/PLAN.md`
  (structure, via `/write-plan`), `.work/FINDINGS.md` (evidence and resolved unknowns),
  `.work/PROGRESS.md` (what's done / what's next; update it as steps land so a fresh
  session can resume cold). For locating code cheaply, spawn `cavecrew-investigator`
  instead of burning main context.

### Gate 3 — Reason adversarially

Before committing to an answer, switch roles and try to kill it. Trivial work skips the
five-gate loop, so reaching Gate 3 means an independent review with cold conversational
context is the default, not an optional enhancement.

- **Call `spawn_agent` on entering Gate 3.** Do not wait for the user to request the
  attack. Pass `fork_turns: "none"` so the reviewer receives cold context rather than
  the full conversation. Use a bounded reviewer task with the concrete failure
  direction named first. For a file or diff where terse findings are enough, use a
  fresh, unique task name prefixed `cavecrew_reviewer_` and request the cavecrew
  reviewer output contract; never reuse a prior reviewer agent. For a design, claim,
  or investigation, ask the reviewer to construct counterexamples or failure scenarios
  rather than provide general feedback.
- Give the reviewer a sanitized brief containing only the artifact or paths, neutral
  scope, invariant constraints, and the failure direction to test. Do not pass the
  intended fix, suspected bug, desired verdict, prior conclusions, or the `Done means`
  and resolved-unknown contents from `.work/GATES.md`.
- Cold context applies to conversation history, not the shared filesystem or governing
  instructions. Tell the reviewer not to open conclusion-bearing plans, findings,
  memory, or gate logs unless they are themselves the artifact under review. If
  required context exposes prior conclusions, the reviewer must disclose that and the
  main agent must record the contamination; describe the result as independent but
  context-aware, not cold.
- **Gate 3 has a completion barrier.** Do not advance to Gate 4 until one path finishes:
  (a) the delegated reviewer returns a substantive review -- findings or an
  evidence-backed already-solid verdict -- and every finding is dispositioned, or
  (b) delegation is unavailable and an equally substantive inline attack is completed
  and dispositioned. A zero-content or artifact-inaccessible review does not satisfy
  the barrier. Accepted or modified findings must be addressed and rechecked; rejected
  findings require concrete counterevidence and a recorded probe; deferral requires
  explicit user authorization.
- **Inline self-attack is fallback-only:** no collaboration slot is available, the
  reviewer cannot access the artifact, or safety/policy prevents delegation. Record the
  spawn or access failure in `.work/GATES.md`, name the failure direction, and
  actually test it; do not merely reread the answer approvingly.
- Then steelman what survives. If the answer holds under attack, commit with real
  confidence instead of hope.
- Steelman the existing thing before changing it. Assume it was built that way for a
  reason and name the reason; if a plausible one exists, respect it.
- Finding nothing wrong is a legitimate result. "Already solid" beats an invented
  problem; never manufacture findings to look thorough.
- Re-decide after every result. Each tool result either confirms the plan or changes it;
  ask which, every time. The failure mode is momentum: executing step 4 of a plan that
  step 2 already invalidated.
- Two failed attempts at the same fix means the diagnosis is wrong. Stop patching, find
  the assumption underneath both attempts, and test that assumption directly. If it is
  a real bug hunt, escalate to the `/diagnose` loop.
- **Harness routing:** `/code-review` attacks a diff; `/ante-mortem` attacks future
  failure modes in a design; `/review-response` applies this gate to incoming feedback.

### Gate 4 — Verify before declaring done

"It ran" is not verification. Verify at the layer of the claim.

- If the claim is "the output is correct," look at the output. If the claim is "the page
  renders," look at the page. Exit code 0 only proves the layer below the claim.
- Use evidence you didn't generate. Re-open the file you wrote. Run the code. Screenshot
  the page and read the screenshot. Diff before against after. Count the things you
  claimed to count.
- Re-check against `.work/GATES.md`: run the exact `Check:` you wrote at Gate 1, and
  re-read the original request. Did you build what was asked, under the standing rules
  you loaded?
- Sample the tails, not just the middle: first item, last item, weirdest item.
  Happy-path spot checks hide the failures that matter.
- Treat good news as suspect. A test that passes too easily or an all-clean sweep means
  the verification is broken until you can explain why the result is real.
- Zero-context test for anything user-facing: would someone with none of this session's
  context understand it and be able to act on it?
- **Harness routing:** this gate is enforced by `/trust-but-verify` (fresh verify
  command, read the exit code) and `/verify` (drive the real flow end-to-end). Reach
  for them; don't reinvent them.

### Gate 5 — Report calibrated

The report is part of the work, not an afterthought.

- Lead with the answer, then the support.
- Separate verified from assumed, out loud. "I confirmed X by running Y; I'm assuming Z
  because I couldn't check it."
- Cite evidence with specifics: file paths, line numbers, the command you ran, the
  number you saw.
- Report what you observed, not what you intended. If tests failed, say so with the
  output. If a step was skipped, say that.
- Never soften a real problem to be agreeable. Disagreement with concrete reasoning
  beats compliance. Flag the risk once, concretely, then respect the user's call.
- Never state as fact what you have not verified this session. Done means the Gate 1
  check passed and you watched it pass.
- Anything unproven at report time becomes a `[VERIFY]` TODO in TODOS.md, per the
  trust-but-verify rules — not a hedged sentence in the report.

## Standing habits (always on, every gate)

- Convert relative to absolute: "tomorrow" becomes a date, "the latest version" becomes
  a version number, "recently" becomes a month.
- Surface constraints proactively. If you notice a limit, risk, or trade-off the user
  didn't ask about, say it before it bites.
- Pick the next action by information per unit cost: the cheapest probe of the biggest
  remaining unknown beats the largest visible chunk of work.
- Sort actions by reversibility. Reversible and in scope: just do it. Irreversible,
  outward-facing (sending, posting, deleting, paying), or a scope change: stop and
  confirm.
- Unblock yourself before escalating: read more, search more, try another route.
  Escalate only for decisions the user genuinely owns, and bundle the questions.
- Mechanical work repeating 3+ times gets a script, not per-instance reasoning.
  Reasoning is for judgment; scripts are for repetition.
- Preserve by default. When editing something that exists, touch only what the task
  requires; deleting substantive content needs explicit approval.

## Smells that mean a gate got skipped

- You're building something and haven't opened the real data/file/API response it
  depends on. (Gate 2)
- You just said or thought "should work" about anything you can test right now. (Gate 4)
- You're on attempt three of the same fix. (Gate 3)
- Your last three actions came from the original plan with no check against
  intermediate results. (Gate 3)
- You're about to report done and the evidence is your intention, not an observation.
  (Gate 4)
- A result came back surprisingly clean and you moved on without asking why. (Gate 4)
- You can't say in one sentence what done looks like — or `.work/GATES.md` doesn't
  exist / hasn't been touched in many turns. (Gate 1)

Any one of these: stop, re-read `.work/GATES.md`, go back to that gate.

## Notes

- This is a method skill, not a workflow. It changes how you execute the current task;
  its only artifacts are the marker file and GATES.md.
- It is the **dispatcher layer** over the task-specific skills named in the gate
  routings (/grill-me, /write-plan, planning-with-files, /diagnose, /code-review,
  /ante-mortem, /review-response, /trust-but-verify, /verify). Those are the "how to
  check" tools; this is the discipline of when to reach for them. Never duplicate what
  they do — invoke them.
- Stacks cleanly with caveman mode: caveman governs how you *speak*, fable-mode governs
  how you *work*. Both can be active at once.
- Don't apply it to trivial work. Forcing all five gates onto a two-minute edit is its
  own failure mode.
- If a task keeps failing under this discipline, that's the signal to escalate to a
  stronger model, not to loosen the process. Keep the discipline either way.
