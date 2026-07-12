# fable-mode — architecture, usage, and maintenance

fable-mode captures Fable 5's *working discipline* — not its intelligence — so any
model (especially Opus or Sonnet) can run it. Fable 5 is being retired; this skill
is the durable copy of how it worked. The discipline lives in three layers that
back each other up:

1. **Prose** — the five gates, the inner loop, and the standing habits (SKILL.md),
   plus the concrete reasoning moves mined from real traces (fable-patterns.md).
2. **Mechanics** — things the harness *enforces* whether or not the model
   remembers: on-disk state, the persistence hook, effort level, and an optional
   post-edit verify hook.
3. **Measurement** — a scorecard (fable-score.py) that proves or disproves,
   from your own session logs, that the skill is changing behavior.

Prose decays as context grows; mechanics don't; measurement tells you when the
prose needs tightening. That division is the design.

---

## The pieces

### SKILL.md — the method itself

- **Five gates (macro discipline).** Every hard task passes Scope → Evidence →
  Adversarial reasoning → Verification → Calibrated report, in order. Each gate
  routes to the harness tool that enforces it (`/grill-me`, `/write-plan`,
  `/code-review`, `/ante-mortem`, `/trust-but-verify`, `/verify`, `/diagnose`) —
  fable-mode is the dispatcher, not a replacement.
- **The inner loop (micro discipline).** `REASON → ACT → OBSERVE → RE-EVALUATE`
  on every non-trivial beat: state a one-line hypothesis before the first tool
  call, read every result and ask "confirms or changes?", fresh-read lines before
  editing them, batch independent operations. This targets the habits where
  measured Fable led baselines widest (reasoning before action 92% vs 40%;
  re-evaluation after results 87% vs 39%).
- **Standing habits.** Always-on rules across gates: first-failure diagnose loop,
  narrate transitions, absolute paths over `cd`, reversibility sorting,
  script-what-repeats, preserve-by-default, and more.
- **Smells.** A checklist of signals that a gate got skipped; any hit means stop
  and re-read `.work/GATES.md`.

### On-disk state — `.work/.fable-active` + `.work/GATES.md`

Method discipline decays in long sessions because it lives in attention. The
skill survives by keeping state on disk instead:

- `.work/GATES.md` — the task's done-definition, exact check command,
  load-bearing unknowns, current gate, and a one-line-per-gate log. The anchor
  file; re-read whenever lost.
- `.work/.fable-active` — activation marker. Its contents belong to the hook
  (line 1 = turn count, line 2 = last emitted gate); never edit them, only
  create on activation and delete on deactivation.

### The persistence hook — `hooks/fable-mode-inject.sh` (UserPromptSubmit)

Re-injects a one-line "FABLE METHOD ACTIVE — <current gate>" reminder, but only
when it matters: on a gate transition, every 5th turn as a heartbeat, or every
turn if GATES.md has gone missing. Deliberately sparse — injecting every prompt
turns the reminder into wallpaper (habituation), and drift sets in around turns
5–8 on smaller models, so the cadence matches the failure mode.

### Activation mechanical levers (SKILL.md § Activation, step 4)

Offered once per activation, never silently applied:

- **`/effort max`** — reasoning density on adaptive-thinking models is governed
  by effort level, not token budgets (`MAX_THINKING_TOKENS` does nothing there).
  The measured reasoning-share gap (~86% vs ~39%) does not close by prose alone;
  effort does most of it. Accept when running fable-mode on Opus/Sonnet for real
  work; skip for cheap tasks.
- **Post-edit verify hook** — a `PostToolUse` hook on `Edit|Write|MultiEdit`
  running the project's verify command (resolved via trust-but-verify's
  `detect.md`). Fires whether or not the model remembers. This exists because
  running the real test after edits was *Fable's own weakest measured habit*
  (~two-thirds of edit sessions) — the one place the skill is deliberately
  stricter than the thing it models.

### `references/fable-patterns.md` — the reasoning moves

Six concrete moves distilled from the public Fable 5 trace dataset (4,665 real
Claude Code events with chain of thought intact), each with its measured
frequency: state-summary-first openings, reasoning over cited observed facts,
justify-why-this-action-is-next, expectation-before-action, micro-planned edits
with anchor-selection reasoning, out-loud self-correction. All paraphrased —
zero verbatim dataset content (see License boundary below).

Progressive disclosure: NOT loaded on every activation. Load it when the inner
loop feels mechanical on a weaker model — thin one-line reasoning, plan momentum,
edits without fresh reads.

### `scripts/fable-score.py` — the scorecard

Scores local Claude Code session logs (`~/.claude/projects`) on seven discipline
habits: reasoning present per beat, reasoning before the first action,
re-evaluation after results, read-before-edit, any-check-after-edit,
real-test-after-edit, and tool error rate. Same habit definitions as the
published Fable analysis, so the shapes are comparable. Streams line by line —
never loads a session whole; a full history scan takes ~1 second.

Three modes:

```bash
# Profile one model
python3 fable-score.py claude-opus-4-8

# Compare two models (is the gap to Fable closing?)
python3 fable-score.py claude-opus-4-8 --baseline claude-fable-5

# Compare fable-mode ON vs OFF for one model (does the skill itself work?)
python3 fable-score.py claude-opus-4-8 --split-fable
```

`--split-fable` classifies a session as fable-ON when its log mentions the
skill's on-disk state (`.fable-active` / `.work/GATES.md`) — the only durable
trace an activation leaves. Read the **gap column**, not absolute percentages:
rates shift with the window scanned, so the comparison is the signal.

### `scripts/fetch-fable-traces.py` — the dataset downloader

Pulls `Glint-Research/Fable-5-traces` from Hugging Face for local analysis.
Default target is `~/.cache/fable-traces` — outside any repo, so the data can't
be committed by accident. `--sample N` streams only N rows for a quick look.
Requires the `datasets` library (PEP 668 blocks user pip on this system — use a
venv: `python3 -m venv /tmp/venv && /tmp/venv/bin/pip install datasets`).

---

## Using it to full potential

### Day to day

1. Say "fable mode" (or let it auto-activate on layered tasks — the frontmatter
   triggers on multi-step/unknowns/debugging shapes). Skill creates the marker +
   GATES.md and offers the two levers.
2. Accept `/effort max` for real work on Opus/Sonnet. Accept the verify hook if
   the project has a real test command.
3. Work the gates. The hook keeps the current gate in view; GATES.md is the
   anchor when context grows long.
4. If reasoning quality sags mid-task: "load fable-patterns" — the six moves
   give a weaker model the concrete phrasing, not just the rule.
5. "fable mode off" when done (or after the Gate 5 report lands).

### Force multipliers

- **Stack with caveman mode.** Caveman governs how the model *speaks*, fable-mode
  how it *works* — they compose. Caveman cuts output tokens; fable-mode spends
  reasoning tokens where they pay.
- **Advisor split.** With an advisor model configured, consult at gate
  boundaries (after Gate 1, before Gate 5) framed from GATES.md state — the
  SKILL.md § Consulting an advisor section has the exact framing. Target config
  worth field-testing: cheaper executor + stronger advisor.
- **Don't over-apply.** Five gates on a two-minute edit is its own failure mode.
  The skill's calibration rule is part of the method.
- **Escalate model, not process.** A task that keeps failing under the
  discipline is the signal to switch to a stronger model — never to loosen the
  gates.

---

## Keeping it up to date

### Monthly — measure (tracked as a `[LOW][CHORE]` TODO in dotfiles TODOS.md)

```bash
python3 ~/.claude/skills/fable-mode/scripts/fable-score.py claude-opus-4-8 --split-fable
```

Baseline (2026-07-12, BEFORE the inner loop shipped): fable-ON showed no lift on
per-beat habits (n=14 sessions) — expected, since the gates target task-level
quality these seven signals don't capture. What to watch now:

- **If the inner loop works**: `reasons before the first action` and
  `re-evaluates after a result` in the ON column climb toward Fable's measured
  93–96% (your local Fable numbers).
- **If flat after a month of real fable-mode use**: the prose isn't landing —
  tighten the inner-loop wording in SKILL.md, or lean harder on `/effort max`
  (density is partly intrinsic; effort is the bigger lever).
- **Sanity check**: total beat counts should grow month over month. A sudden
  drop to near zero means Claude Code changed its log schema — fix the record
  parsing in fable-score.py, don't trust the rates.

### While Fable is still available — grow the local corpus

Every session run ON Fable adds beats to `~/.claude/projects`. Those logs are
the asset that makes `--baseline claude-fable-5` comparisons meaningful after
retirement. Run the hardest tasks on Fable now; the traces are free.

### When the daily-driver model changes

Same commands, new model id. Habit definitions are model-agnostic. Caveat: the
reasoning metrics only count *stored* thinking blocks — if a new model's logs
read near-zero on reasoning, that's the logging configuration (extended
thinking settings), not the model failing to think.

### Rarely — re-mine the patterns

The dataset is frozen (retired weights produce no new traces), so
fable-patterns.md should rarely need changes. To go deeper on a specific
dimension (e.g., error-recovery phrasing):

```bash
python3 ~/.claude/skills/fable-mode/scripts/fetch-fable-traces.py --sample 1000
```

then analyze locally and fold *paraphrased* findings into fable-patterns.md.

---

## License boundary (read before committing anything dataset-derived)

The trace dataset is **AGPL-3.0**. The rule this skill follows:

- **Never commit or redistribute** raw traces or verbatim excerpts — they are
  derivatives of the dataset and carry AGPL obligations that would infect this
  repo. The fetch script's default target (`~/.cache/fable-traces`) is outside
  any repo for exactly this reason.
- **Safe to commit**: the fetch script (it only links), measured statistics
  (facts), and behavioral patterns described in your own words (ideas aren't
  copyrightable). Everything in fable-patterns.md follows this rule.
- The extract-mindset kit the analysis approach was inspired by has no stated
  license; fable-score.py is a fresh implementation for the same reason.

---

## File map

```
fable-mode/
├── SKILL.md                        # the method: gates + inner loop + habits
├── references/
│   ├── README.md                   # this file
│   └── fable-patterns.md           # six reasoning moves, measured, paraphrased
└── scripts/
    ├── fable-score.py              # habit scorecard over local session logs
    └── fetch-fable-traces.py       # AGPL-safe dataset downloader (to ~/.cache)

related, outside this dir:
    hooks/fable-mode-inject.sh      # UserPromptSubmit persistence hook
    .work/GATES.md                  # per-task gate state (created on activation)
    .work/.fable-active             # activation marker (hook-owned contents)
```
