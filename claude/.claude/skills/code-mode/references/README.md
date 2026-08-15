# code-mode — architecture, usage, and maintenance

code-mode is the dispatcher layer over the code-quality + security substrate — the
five-gate discipline reoriented to the code lifecycle, routing into `/tdd`, `/diagnose`,
`/code-refactor`, `/code-decay`, `/requirements`, `/architecture`, `/brainstorm`,
`/grill-me`, `/write-plan`, `/threat-model`, `/prototype`, `/code-crit`,
`/mutation-testing`, `/ante-mortem`, `/review-response`, `/trust-but-verify`, `/run`,
and `/changelog` rather than restating what they own. The discipline lives in three
layers that back each other up:

1. **Prose** — the five gates, the red-green inner loop, and the code-specific
   gate-skip smells (SKILL.md).
2. **Mechanics** — things the harness _enforces_ whether or not the model remembers:
   on-disk state, the persistence hook, effort level, `standards_guard.py` forcing
   `CODE-STANDARD.md` before the first edit.
3. **Measurement** — a scorecard (`code-score.py`) that proves or disproves, from your
   own session logs, that the skill is changing behavior.

Prose decays as context grows; mechanics don't; measurement tells you when the prose
needs tightening. That division is the design.

---

## The pieces

### SKILL.md — the method itself

- **Five gates (macro discipline).** Every hard task passes Spec → Evidence →
  Adversarial reasoning → three-rung Verification → Diff-shaped report, in order.
  Gate 1 carries the route table (`[FEAT]`→`/tdd`, `[BUG]`→`/diagnose`,
  named-smell→`/code-refactor`, unnamed risk→`/code-decay`, new system→`/requirements`
  then `/architecture`, open design decisions→`/brainstorm`→`/grill-me`→`/write-plan`,
  security-touching→`/threat-model`, unanswered design question→`/prototype`) —
  code-mode is the dispatcher, not a replacement for any of them.
- **The inner loop (micro discipline).** Red-green replaces the generic loop:
  `REASON → ACT → OBSERVE → RE-EVALUATE` nests inside it, refactoring explicitly
  excluded and deferred to review. Fresh-read-before-every-edit is a hard rule, not a
  bullet — the highest-value habit `code-score.py` measures.
- **Standing habits.** Always-on rules across gates: first-failure diagnose loop,
  narrate transitions, absolute paths over `cd`, reversibility sorting,
  script-what-repeats, preserve-by-default.
- **Code-specific smells.** A checklist of signals a gate got skipped — named and
  checkable (abstraction on the second look-alike, TODO not mirrored to TODOS.md, the
  throwaway-became-the-implementation case for `/prototype`). Any hit means stop and
  re-read `.work/GATES.md`.

### On-disk state — `.work/.code-active` + `.work/GATES.md`

Method discipline decays in long sessions because it lives in attention. The skill
survives by keeping state on disk instead:

- `.work/GATES.md` — the task's `Done means:` (a failing test + the command that
  proves it), load-bearing unknowns, current gate, and a one-line-per-gate log. The
  anchor file; re-read whenever lost.
- `.work/.code-active` — activation marker. Contents belong to the hook (turn count,
  last emitted gate); never edit them, only create on activation, delete on
  deactivation.

### The persistence hook — `hooks/code-mode-inject.sh` (UserPromptSubmit)

Re-injects a one-line "CODE MODE ACTIVE — <current gate>" reminder, but only when it
matters: on a gate transition, every 5th turn as a heartbeat, or every turn if
GATES.md has gone missing. Deliberately sparse — injecting every prompt turns the
reminder into wallpaper.

### Activation mechanical levers (SKILL.md § Activation, step 4)

Offered once per activation, never silently applied:

- **`/effort high|max`** — not hardcoded to max; let the gate reasoner pick the level
  the task warrants. Reasoning density on adaptive-thinking models is governed by
  effort level, not token budgets.
- **No post-edit verify hook offer** — unlike fable-mode's, this lever is dropped
  deliberately. `code_standard_lint.py` and `code_formatter.py` already fire on
  `Edit|Write|MultiEdit` in this harness; offering a duplicate hook would just be
  noise. Check what's wired before offering anything new.

### `scripts/code-score.py` — the scorecard

Scores local Claude Code session logs (`~/.claude/projects`) on the discipline habits,
including two code-specific additions over fable-mode's seven: full-suite-vs-single-test
after an edit, and failing-test-before-implementation ordering on `[FEAT]` work.
Streams line by line — never loads a session whole.

```bash
# Profile one model
python3 code-score.py claude-opus-4-8

# Compare two models
python3 code-score.py claude-opus-4-8 --baseline claude-fable-5

# Compare code-mode ON vs OFF for one model
python3 code-score.py claude-opus-4-8 --split-code
```

`--split-code` classifies a session as code-mode-ON when its log mentions the skill's
on-disk state (`.code-active` / `.work/GATES.md`) — the only durable trace an
activation leaves. Read the **gap column**, not absolute percentages: rates shift with
the window scanned, so the comparison is the signal.

---

## Using it to full potential

### Day to day

1. Say "code mode" (or let it auto-activate on real code work — the frontmatter
   triggers on feature/bug/refactor/new-system shapes). Skill creates the marker +
   GATES.md.
2. Accept `/effort high|max` for real work. Gate 1 preloads `CODE-STANDARD.md` + the
   matching language file automatically.
3. Work the gates. The hook keeps the current gate in view; GATES.md is the anchor
   when context grows long.
4. "code mode off" when done (or after the Gate 5 report lands).

### Force multipliers

- **Stack with caveman mode.** Caveman governs how the model _speaks_, code-mode how
  it _works_ — they compose.
- **Advisor split.** With an advisor model configured, consult automatically at Gate
  3 (adversarial) and optionally at Gate 4/5 — the SKILL.md Gate 3 section has the
  exact framing.
- **Don't over-apply.** Five gates on a two-minute edit is its own failure mode.
- **Escalate model, not process.** A task that keeps failing under the discipline is
  the signal to switch to a stronger model — never to loosen the gates.

---

## Keeping it up to date

### Periodically — measure

```bash
python3 ~/.claude/skills/code-mode/scripts/code-score.py claude-opus-4-8 --split-code
```

Watch the gap column between code-mode ON and OFF sessions, not absolute rates — rates
shift with the scan window. A sudden drop to near zero in total beat counts means
Claude Code changed its log schema, not that the habits vanished — fix the record
parsing in `code-score.py`, don't trust the rates.

### When the daily-driver model changes

Same commands, new model id. Habit definitions are model-agnostic. Caveat: the
reasoning metrics only count _stored_ thinking blocks — a near-zero reasoning read on
a new model is a logging-configuration signal, not a thinking-failure signal.

---

## File map

```
code-mode/
├── SKILL.md                        # the method: gates + inner loop + habits
├── references/
│   └── README.md                   # this file
└── scripts/
    └── code-score.py               # habit scorecard over local session logs

related, outside this dir:
    hooks/code-mode-inject.sh       # UserPromptSubmit persistence hook
    .work/GATES.md                  # per-task gate state (created on activation)
    .work/.code-active              # activation marker (hook-owned contents)
```
