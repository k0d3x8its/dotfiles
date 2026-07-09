---
name: ante-mortem
description: Imagine future bug post-mortems for the codebase. Identifies fragile code, implicit assumptions, and likely failure modes by writing realistic incident reports for bugs that haven't happened yet. Hardening suggestions become tagged TODOs in TODOS.md. Security fragility triggers /ce-security-audit. Real bugs get [BUG] TODOs for /diagnose.
argument-hint: "[file, directory, or description of what to focus on]"
disable-model-invocation: true
---

# Ante-Mortem: Future Bug Post-Mortems

You are now in ante-mortem mode. Your job is to read production code, identify
areas of fragility and implicit assumptions, and then write realistic
post-mortem reports for bugs that **haven't happened yet** — but plausibly
could, given the kind of changes a future developer might reasonably make.

This is the proactive half of the post-mortem pair:

- **ANTE-MORTEM.md** (this skill) — written before things break. Identifies
  fragility and documents imagined incidents to harden the codebase.
- **POST-MORTEM.md** (written by `/diagnose` Phase 6) — written after a real
  bug is found, fixed, and closed. Documents root cause, timeline, and
  prevention.

Both artifacts live in the project root. They are complementary: ante-mortem
surfaces structural risk; post-mortem captures what actually went wrong.

This is not a bug hunt. The code may be perfectly correct today. You're looking
for places where the code is **fragile against future edits**: places where a
developer who doesn't have full context could make a seemingly reasonable change
that breaks something in a non-obvious way.

## Scope

$ARGUMENTS

- If the user names specific files or directories, scope your analysis to those.
- If no argument is given, look at the project's source layout and use
  `AskUserQuestion` to agree on a starting scope. Pick a module or package with
  meaningful logic — don't try to cover everything at once.
- Focus on production code. Config files, migrations, and boilerplate are out
  of scope unless they contain logic that other code depends on.

## Workflow

1. **Read deeply.** Read the files in scope carefully. Don't skim — you need to
   understand data flow, state management, implicit invariants, and the
   relationships between components. Read callers and callees, not just the file
   in isolation.

2. **Identify fragility.** Look for the patterns described in the catalogue
   below. For each one you find, ask: "What change would a reasonable developer
   make here that would break this?" If you can't imagine a plausible edit that
   causes a problem, move on — not everything is fragile.

3. **Flag real bugs immediately.** If you discover an actual, current bug while
   reading, do not bury it in a fictional post-mortem. Output it to the user
   immediately as plain text: "Real bug found: <description>." Then write a
   `[BUG]` TODO to `TODOS.md`:

   ```
   - [ ] [BUG] <file>:<function> — <one-line description> (found during ante-mortem — use /diagnose)
   ```

4. **Write post-mortems.** For each fragility you identify, write a fictional
   post-mortem in the format described below. Write them as if the bug has
   already happened, in past tense, from the perspective of the team
   investigating the incident after the fact. Make the scenarios concrete and
   specific — name the functions, the variables, the values.

5. **Write hardening TODOs.** After completing the report, extract the
   hardening suggestions and write them as tagged TODOs to `TODOS.md`. See
   "Writing Hardening TODOs" below.

6. **Produce the report.** Write all post-mortems to `ANTE-MORTEM.md` in the
   project root. If the file already exists, append a new dated section rather
   than overwriting. Use `AskUserQuestion` if you need to confirm scope or
   output path.

Use `TaskCreate` to track progress across files when there are more than a
handful.

## Fragility Catalogue

Read `~/.codex/skills/ante-mortem/CATALOGUE.md` for the full list of 11
fragility patterns with descriptions and example future edits. Pattern #11
(Security fragility) triggers the stricter handling described below.

## Post-Mortem Format

Write each post-mortem as a self-contained section. Use this structure:

```markdown
### <Short incident title>

**Severity:** Critical | High | Medium | Low
**Component:** <file(s) and function(s) involved>
**Fragility type:** <category from the catalogue>

#### What happened

<2-4 sentences describing the bug as if it already occurred. What did users or
the team observe? Be specific — name the symptom.>

#### The change that caused it

<Describe the edit a future developer made. Make it sound reasonable — this
should be a change that would pass code review. Include a plausible motivation
for the change (new feature, refactoring, performance improvement, dependency
upgrade, etc.)>

#### Why it broke

<Explain the hidden assumption or fragility that the change violated. Point to
the specific lines or patterns in the current code that create this fragility.
Reference actual function names, variable names, and file paths.>

#### How it was caught

<How would this bug surface? Would tests catch it? Would it fail silently?
Would it corrupt data? Would it only manifest under specific conditions or
at scale? Be honest — if no test would catch it, say so.>

#### Hardening suggestions

<1-3 concrete, actionable suggestions for making the code more resilient
against this kind of change. These might include: adding assertions or
validation, introducing types that enforce invariants, writing a specific test,
adding a comment that explains the non-obvious constraint, refactoring to make
the dependency explicit. Don't suggest vague improvements — be specific enough
that someone could implement your suggestion directly.>
```

## Security fragility path

When you identify a fragility of type "Security fragility" (catalogue #11),
apply stricter handling:

1. **In the post-mortem**, mark severity as Critical or High (never lower for
   security). In the "Hardening suggestions" section, explicitly note blast
   radius: what data or access could be affected if this fragility is exploited.

2. **In the TODOS.md entry** (see below), use `[SECURITY]` tag instead of
   `[INVESTIGATE]` or `[CHORE]`. Add a note to suggest `/ce-security-audit` for
   deeper analysis:

   ```
   - [ ] [SECURITY] <file>:<function> — <one-line description> (ante-mortem security fragility — consider /ce-security-audit)
   ```

3. **Drop caveman mode** when describing the security finding to the user.
   Security warnings need plain, unambiguous language.

## Writing hardening TODOs

After writing the report, extract the hardening suggestions and write them as
tagged TODOs to `TODOS.md` in the project root.

Tag each TODO by the type of work required:

| Hardening type | Tag |
|---|---|
| Refactor, cleanup, make explicit | `[CHORE]` |
| Needs research or audit first | `[INVESTIGATE]` |
| Security-sensitive (auth, input, secrets, perms) | `[SECURITY]` |

Format:

```
- [ ] [CHORE] <file>:<function> — <one-line hardening action> (ante-mortem: <incident title>)
- [ ] [INVESTIGATE] <file>:<function> — <one-line hardening action> (ante-mortem: <incident title>)
- [ ] [SECURITY] <file>:<function> — <one-line hardening action> (ante-mortem: <incident title> — consider /ce-security-audit)
```

If `TODOS.md` does not exist in the project root, create it with a minimal
header before writing. Append to the file; do not overwrite existing entries.

After writing TODOs, tell the user how many were written and which tags were
used.

## Output File Structure

Write to `ANTE-MORTEM.md` in the project root. If the file exists, append a
new dated section.

```markdown
# Ante-Mortem Report

**Scope:** <files/modules analysed>
**Date:** <today's date>

## Summary

<A short paragraph summarizing the overall fragility posture. How many
post-mortems? What are the dominant themes? Are there systemic patterns, or are
the fragilities mostly independent?>

## Post-Mortems

### 1. <title>
...

### 2. <title>
...

## Themes and Recommendations

<After all post-mortems, step back and identify cross-cutting themes. If
several post-mortems point to the same underlying architectural issue, call it
out here. Suggest structural changes that would address multiple fragilities at
once, not just point fixes.>
```

## Calibration

Quality over quantity. Aim for 3-7 post-mortems per module, depending on its
complexity. Each one should describe a genuinely plausible scenario — a bug that
a competent developer could introduce during a reasonable edit.

**Avoid:**

- **Current bugs.** You're not looking for things that are broken today. If you
  find an actual bug, flag it immediately and write a `[BUG]` TODO — don't
  write a fictional post-mortem about it.
- **Adversarial scenarios.** Don't imagine a developer deliberately sabotaging
  the code. The imagined changes should be things a well-intentioned developer
  would do.
- **Extremely unlikely changes.** "If someone rewrote the function in a
  completely different way, it might break" is not useful. The imagined change
  should be a small, local edit — a refactoring, a feature addition, a
  performance tweak.
- **Generic advice.** "This function has no tests" is an observation, not a
  post-mortem. Every post-mortem must describe a **specific** future change and
  a **specific** resulting failure.
- **Excessive severity.** Not everything is Critical. Use severity levels
  honestly. A bug that silently corrupts data is Critical. A bug that causes a
  clear error in an uncommon code path is Low.

**Aim for:**

- Scenarios where the **cause and effect are non-obvious** — the change is in
  one place and the breakage manifests somewhere else, or the breakage only
  appears under specific conditions.
- Fragilities that are **endemic to the design**, not surface-level issues. A
  missing null check is less interesting than an architectural assumption that
  permeates multiple files.
- Post-mortems that would make a reader say "oh, I wouldn't have thought of
  that" — not "well, obviously."

## Critical Rules

- **Read before writing.** Never write post-mortems for code you haven't read
  thoroughly. You must understand how the code actually works, not just what it
  looks like.
- **Be specific.** Every post-mortem must reference actual functions, variables,
  and file paths in the current codebase. No hand-waving.
- **Be plausible.** The imagined changes must be things a reasonable developer
  might do. If you can't articulate a plausible motivation for the change, the
  scenario isn't realistic enough.
- **Don't fix the code.** Your job is to write the report and the TODOs, not to
  refactor the codebase. The hardening suggestions describe what to do; you
  shouldn't implement them unless the user asks.
- **Separate actual bugs.** If you discover a real, current bug while reading,
  flag it to the user immediately via text output and write a `[BUG]` TODO.
  Do not bury it in a fictional post-mortem.
- **Ask when uncertain.** If you're unsure whether a pattern is truly fragile
  or just unfamiliar to you, use `AskUserQuestion` to discuss it with the user
  before including it in the report.
