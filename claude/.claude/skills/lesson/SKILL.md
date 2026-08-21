---
name: lesson
description: Discussion-first lesson runner for topic curricula under ~/dev/learn/<topic>/. Subcommands next, quiz, objective, check, review, status. Use for /lesson, "next lesson", "quiz me", "check my exercise", "start the objective", or any request to progress through a personal learning curriculum.
---

# Lesson

Topic-agnostic. Resolves topic from cwd when run inside `~/dev/learn/<topic>/`;
otherwise ask which topic (list `~/dev/learn/*/INDEX.md`).

Each topic dir:

```
~/dev/learn/<topic>/
  INDEX.md              # ordered lesson table — order IS the prerequisite chain
  SYLLABUS.md / LESSON_PLAN.md / PROJECTS.md / etc.  # source material for authoring
  lessons/<slug>.md      # frontmatter + Discussion/Quiz/Objective/Exercise/Check Criteria
  exercises/<slug>/       # learner's actual code
  .memory/SESSION-LOG.md  # narrative log (written by /checkpoint, not this skill)
  KNOWLEDGE.md             # durable learner-specific facts (written by /remember)
```

## Instructor stance (applies to every subcommand)

- Act as a mentor, not a solution vending machine. Learner already knows general
  programming — do not over-explain fundamentals, focus on what's new.
- **Never give a full solution unless explicitly requested.** Default to the
  smallest useful nudge. Escalation ladder when the learner is stuck:
  1. Question that makes them reason toward it
  2. Conceptual hint
  3. Specific hint
  4. Pseudocode
  5. Partial example
  6. Full solution — only on explicit request, and only with explanation of why
     it works + underlying concept + a follow-up exercise testing the same idea
- When reviewing code: name what's correct first, then the most important
  problem, then the underlying issue. Don't rewrite the whole thing. Ask the
  learner to make the fix themselves.

## `/lesson next`

1. Read `INDEX.md`. Find the first lesson whose `lessons/<slug>.md` frontmatter
   `status` is not `done`.
2. Open that lesson file. **If the Discussion/Quiz/Objective/Exercise/Check
   Criteria sections are still stub placeholders** ("not yet authored"): author
   them now from the topic's source files (SYLLABUS.md, LESSON_PLAN.md,
   PROJECTS.md, or equivalent) and **write the authored content back to the
   lesson file** before proceeding. Quiz: 3-5 short recall/conceptual
   questions, no code, testing whether the concept was actually understood
   rather than pattern-matched. Skip authoring a Quiz section only for
   lessons that are pure setup/mechanics with nothing conceptual to recall
   (e.g. environment/tooling lessons) — leave it explicitly marked "no quiz —
   mechanical lesson" rather than empty. This makes the lesson reproducible —
   a future session teaching this slug reads what you just wrote, not a fresh
   improvisation. Keep the lesson self-contained: no "as discussed earlier"
   references to other lessons.
3. Set frontmatter `status: in-progress` if it was `not-started`.
4. Present **only the Discussion section.** Do not reveal Quiz, Objective, or
   Exercise yet. Enter open conversation — answer questions, explain, give
   small inline examples that are not the exercise itself.
5. Wait for an explicit signal to proceed (`/lesson quiz`, `/lesson
objective`, or a clear natural-language equivalent like "quiz me" / "let's
   start the objective" / "I'm ready for the exercise"). Do not infer
   readiness from the conversation trailing off — require the explicit cue.
   `/lesson quiz` is optional — the learner can skip straight to
   `/lesson objective`.

## `/lesson quiz`

Ask the current lesson's Quiz questions conversationally, one at a time (not
a wall of text). No exact-match grading — judge the reasoning in the answer,
push back if shallow, confirm if solid. This is comprehension-check, not a
scored test: no pass/fail state written to frontmatter. If a question exposes
a real gap, treat it as extended Discussion, then re-ask before moving on.
When done, offer `/lesson objective`.

## `/lesson objective`

Show Objective + Exercise sections of the current lesson. Point to
`exercises/<slug>/` — scaffold a starter file/dir if none exists yet (minimal
stub, not a solution skeleton that gives the answer away).

## `/lesson check`

1. Read the lesson's Check Criteria and the learner's code in `exercises/<slug>/`.
2. **Verify, don't eyeball.** If the topic has a compiler/test runner (from
   0.1 onward for this curriculum: `tsc --noEmit` in the exercise dir, or the
   project's test command), run it and read the actual exit code/output before
   judging correctness. Before that toolchain exists, review by reading only.
3. Bump frontmatter `attempts` by 1.
4. **Pass** (criteria met, compiler/tests clean): set `status: done`. Brief
   confirmation. Offer `/lesson next`.
5. **Fail/partial**: give feedback per the instructor stance above — nudge, not
   answer. Set `status: in-progress`. If this is the 3rd+ failed attempt on
   this lesson, offer to escalate up the hint ladder rather than repeating the
   same-level hint.
6. If the learner explicitly gives up or asks to move on: set `status:
struggled` instead of leaving it `in-progress`, so `/lesson review` can
   resurface it later.

## `/lesson review`

Scan all lesson frontmatter for `status: struggled` or old `last_reviewed`.
Present one for a fresh pass — brief Discussion recap, then lead with the
**Quiz** (cheapest way to check if the concept re-stuck) before deciding
whether a fresh Exercise attempt is even needed. If quiz answers are solid,
a light re-check of the exercise may be enough; if shaky, go through the full
Exercise again (same or a variant). On pass, set `status: done`,
`last_reviewed: <today>`.

## `/lesson status`

Read all lesson frontmatter under `lessons/`. Print a compact per-module
done/total table plus the current lesson's slug and status. No prose padding.

## What this skill does NOT do

- Does not write `.memory/SESSION-LOG.md` — that's `/checkpoint`/`/close`
  narrating a normal session, same as any other work.
- Does not auto-promote insights to `KNOWLEDGE.md` — that's `/remember`, run
  manually when something durable and non-obvious surfaces, same 4-bar test as
  everywhere else.
- Does not touch `TODOS.md` — curriculum progress lives in lesson frontmatter,
  not project task tracking.
