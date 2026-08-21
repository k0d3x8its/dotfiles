---
name: syllabus-setup
description: Setup wizard for a new self-taught curriculum under ~/dev/learn/<topic>/ — scaffolds INDEX.md, per-lesson stub files, exercises/, and topic-scoped memory (.memory/SESSION-LOG.md, KNOWLEDGE.md), ready for the /lesson skill to run. Use for /syllabus-setup, "set up a new curriculum", "start learning X", or when migrating existing course notes into the lesson-runner format.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Syllabus Setup Wizard

**Trigger:** `/syllabus-setup`
**Purpose:** Scaffold everything `/lesson` needs for a new topic, in one guided run —
mirrors `/dev-setup`'s per-project wizard pattern but for a learning curriculum
instead of a code project. Produces the structure documented in
`~/.claude/skills/lesson/SKILL.md`:

```
~/dev/learn/<topic>/
  INDEX.md                # ordered lesson table — order IS the prerequisite chain
  <source material>.md     # SYLLABUS.md/etc — kept for lesson authoring reference
  lessons/<slug>.md         # stub: frontmatter + Discussion/Quiz/Objective/Exercise/Check Criteria
  exercises/                # empty — /lesson objective scaffolds per-lesson
  .memory/SESSION-LOG.md     # narrative log, written by /checkpoint
  KNOWLEDGE.md                # durable learner facts, written by /remember
```

This wizard scaffolds structure only — it does **not** author lesson content.
`/lesson next` authors each lesson's Discussion/Quiz/Objective/Exercise the first
time it's reached, from whatever source material exists in the topic dir. Do not
bulk-author lessons up front here — see Step 5 note.

---

## Templates

Read the template, substitute tokens, write to destination:

| Token             | Value              |
| ----------------- | ------------------ |
| `{{SLUG}}`        | per-lesson, Step 5 |
| `{{TITLE}}`       | per-lesson, Step 5 |
| `{{MODULE}}`      | per-lesson, Step 5 |
| `{{TOPIC_TITLE}}` | Step 2             |

Static templates (`SESSION-LOG.md`, `KNOWLEDGE.md`) take only `{{TOPIC_TITLE}}`.

---

## Wizard Steps

Ask **one question at a time**. Check before overwriting any existing file.

### Step 1: Topic slug

> "Topic slug? Used as the directory name: `~/dev/learn/<slug>/`. Lowercase,
> hyphenated (e.g. `typescript-svelte`, `rust-systems`)."

Verify `~/dev/learn/<slug>/` doesn't already exist — if it does, stop and ask
whether this is meant to resume/extend an existing curriculum (route to
`/lesson status` instead) rather than overwrite it.

### Step 2: Topic title

> "Full title for this curriculum? (e.g. 'TypeScript + Svelte 5', used in
> headers of generated files)"
> Default: title-cased slug

### Step 3: Source material

> "Do you have existing curriculum notes/syllabus/plan to seed this from
> (paste, or give a file path), or should we build the module/lesson outline
> from scratch together right now?"

If existing material given: copy/write it into the topic dir root (e.g.
`SYLLABUS.md`, `LESSON_PLAN.md`, or whatever files/sections it naturally
splits into) — this becomes the source `/lesson next` reads when authoring
each lesson.

If building from scratch: have a short back-and-forth to establish the module
breakdown (broad phases/weeks) and a rough lesson list per module — doesn't
need full prose per lesson, just titles and one-line scope per lesson is
enough for Step 5's stub generation and for `/lesson next` to author from
later. Write this outline to `SYLLABUS.md` in the topic dir root so it
persists as source material too.

### Step 4: Scaffold directories

```bash
mkdir -p ~/dev/learn/<slug>/lessons ~/dev/learn/<slug>/exercises ~/dev/learn/<slug>/.memory
```

Print what was created.

### Step 5: Build INDEX.md and lesson stubs

From the source material (Step 3), derive the ordered lesson list: number,
slug (kebab-case, prefixed with module/week number for sort stability —
e.g. `1-3-interfaces-optional-properties`), title, module/phase name.

Write `INDEX.md` as a table (number | slug | title | module) — order is the
prerequisite chain, no separate dependency field.

**Do not author lesson content here.** For every row, write
`templates/lesson-stub.md` (substituting `{{SLUG}}`, `{{TITLE}}`,
`{{MODULE}}`) to `lessons/<slug>.md` — frontmatter + placeholder sections
only. If the lesson count is large (dozens+), generate stubs with a script
rather than one Write call per file — same approach as this skill's own
migration used.

Print the count of lessons scaffolded.

### Step 6: Memory scaffolding

Write `templates/SESSION-LOG.md` (substitute `{{TOPIC_TITLE}}`) to
`.memory/SESSION-LOG.md`.

Write `templates/KNOWLEDGE.md` (substitute `{{TOPIC_TITLE}}`) to
`KNOWLEDGE.md` in the topic dir root.

### Step 7: Offer to author the first lesson now

> "Want me to fully author lesson 1 (Discussion/Quiz/Objective/Exercise/Check
> Criteria) right now, so the format is validated end-to-end before you run
> `/lesson next` for real? Recommended — catches format issues on one lesson
> instead of discovering them later."

If yes: author it following the exact contract `/lesson next` uses (see
`~/.claude/skills/lesson/SKILL.md`), write it into `lessons/<first-slug>.md`
replacing the stub.

If no: leave it as a stub — `/lesson next` will author it on first run.

### Step 8: Completion summary

```
✓ <Topic Title> curriculum is ready at ~/dev/learn/<slug>/

Created:
  INDEX.md (<N> lessons)
  lessons/ (<N> stub files, <M> fully authored)
  exercises/ (empty — populated per-lesson by /lesson objective)
  .memory/SESSION-LOG.md
  KNOWLEDGE.md
  <source material files>

What's next:
  → /lesson next        start (or continue) the first lesson
  → /lesson status       check progress anytime
```

---

## Notes

- Safe to re-run only for a _new_ topic slug — Step 1 refuses to touch an
  existing curriculum dir. Resuming/extending an existing one is `/lesson`'s
  job, not this wizard's.
- Mirrors `/dev-setup`'s question-then-scaffold pattern deliberately, but
  scoped down: no git, no GitHub repo, no git-crypt, no eslint — this is a
  personal learning directory, not a shipped project.
- If the learner later wants a second topic (e.g. `~/dev/learn/rust-systems/`),
  run this wizard again — it's fully topic-agnostic.
