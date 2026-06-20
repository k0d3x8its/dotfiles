# Build Guide: A Native, Skills-Based Memory Architecture

> **How to use this guide.** Hand this whole file to Claude Code in the `dotfiles`
> repo. It is self-contained — you do not need any prior conversation. Build in the
> order in §4. Respect the invariants in §3 at every step. Commit per file
> (conventional commits, no `Co-Authored-By`), then re-run `install.sh`.
>
> **Revision 2026-06-19** — incorporates 13 fixes from design review (see §8 for the
> changelog). Two are load-bearing: capture fires on `SessionEnd` (not `Stop`), and
> files-touched is computed against a SessionStart git baseline (not a bare
> working-tree diff). Build those correctly or the episodic backbone silently corrupts.

---

## 1. Context — why this exists

The `dotfiles` repo already contains a multi-store memory system; it just isn't
named or unified as one. `KNOWLEDGE.md` is only the **semantic** layer. The system
also has procedural memory (the skills), prospective memory (`TODOS.md` + triage),
and episodic memory (`SESSION-LOG.md`). Three things are missing:

1. **A shared model** naming the stores and how they relate.
2. **A retrieval layer** — recall is currently ad-hoc `grep`.
3. **A consolidation layer** — episodic→semantic promotion only happens as a
   side-effect of `/checkpoint`.

This is inspired by `claude-mem` (github.com/thedotmack/claude-mem) but **does not
install it**. We steal four ideas, stripped of its SQLite/Chroma/worker machinery:
progressive-disclosure retrieval, structured episodic records, consolidation as a
distinct phase, and forgetting/decay as a feature. Everything is built from the
repo's own primitives.

> **On the fourth idea (decay).** It is now an actual build task (Task 2g — index
> rotation), not just framing. If you choose to drop decay, also delete this sentence
> and the claim above so the doc and the tasks agree.

---

## 2. The model

### Memory taxonomy

| Memory type | What it is | Primitive | State |
|---|---|---|---|
| Working / short-term | Active context now | session context, `findings.md`, `task_plan.md`, scratchpad | ✅ have |
| Semantic | Decontextualized facts | `KNOWLEDGE.md` (local+global), `MEMORY-STANDARD.md` | ✅ strong |
| Procedural | "How to do things" | the skills + `CLAUDE.md` rules | ✅ strong |
| Prospective | Remember to act later | `TODOS.md` + tags + `update-triage` → `TRIAGE-BLOCK.md` | ✅ have |
| Episodic | Time-indexed events | `SESSION-LOG.md` + `ARCHIVE-LOG.md` | ⚠️ weakest |
| Retrieval | Cue-driven lookup | — | ❌ build it (`/recall`) |
| Consolidation | Episodic→semantic ("sleep") | partial: `/checkpoint` gate | ⚠️ build it (`/consolidate`) |

> **Note on the auto-memory scratchpad.** `~/.claude/projects/<hash>/memory/`
> (the `[[…]]`-linked fact files + `MEMORY.md` index) is a *fifth* store — auto-written
> working/semantic notes that are NOT committed and NOT subject to the `KNOWLEDGE.md`
> bar. It is deliberately **out of `/recall`'s default scope** (Task 3) because it is
> per-machine, unvetted, and noisy. `/recall --deep` MAY read it; flag any hit from it
> as `[scratch]` so the user knows it skipped the bar.

### Two-layer episodic memory (the key design)

- `EPISODIC-INDEX.md` = **complete but thin** — one auto-captured line per session
  (every session, metadata only). The searchable spine.
- `SESSION-LOG.md` = **sparse but rich** — full narrative, only for `/checkpoint`ed
  sessions. The curated "why."

Mirrors human memory: a continuous faint trace + a few vivid consolidated episodes.
The short-term→long-term gradient is this **pipeline** (faint recent index → curated
durable `KNOWLEDGE.md` via `/consolidate`), not two static buckets. There is
deliberately **no `LONG-TERM.md`/`SHORT-TERM.md`**: "horizon" is an axis over the
existing stores, not a store (same reason §3 forbids `MEMORY.md`/`COGNITION.md`).

### Cognition map (one screen — memory is one faculty of a larger system)

This goes *inside* `MEMORY-ARCHITECTURE.md`. Do **not** create separate files for
these yet (see §3, grow-and-extract).

| Faculty | Implemented by | Spec status |
|---|---|---|
| Perception | session-start reads | n/a (rules in `CLAUDE.md`) |
| Attention | triage → `TRIAGE-BLOCK.md`; progressive disclosure | **TBD** (next likely extraction) |
| Memory | the 4-store system | **this doc** ✅ |
| Reasoning | `/brainstorm`, `/diagnose`, plan mode | TBD (may stay pointer-only) |
| Metacognition | `/trust-but-verify` | TBD |
| Executive function | `TODOS.md` + session tools | TBD (may merge with Attention) |

---

## 3. Invariants (do not violate these while building)

1. **Reuse over rebuild.** Lift existing patterns; don't invent parallel ones.
2. **Capture costs zero model tokens.** Hooks parse stdin, act, and suppress *all*
   output — emitting to stdout injects text into model context and defeats the point.
3. **Never auto-write to `KNOWLEDGE.md`.** Every entry passes the 4-test bar + dedup
   + explicit user approval. This is the store's trust guarantee.
4. **Distill-on-write.** No blind append to `KNOWLEDGE.md` — update existing entries
   on overlap.
5. **Keep existing filenames.** No renames (`SESSION-LOG.md`, `ARCHIVE-LOG.md`, etc.).
   Filenames describe mechanics; the architecture doc maps them to roles.
6. **No `MEMORY.md` and no `COGNITION.md` *store*.** Cognition is process, not
   content. The cognition map is a *section*, grown & extracted only under pressure.
7. **Token frugality in recall** via progressive disclosure (cheap index → context →
   full). `--deep` stays Layer-1 grep-only across projects — never auto-expands.
8. **`~/.claude` config is symlinked from `dotfiles`.** Edit sources under
   `dotfiles/claude/.claude/`, never `~/.claude/` directly. Re-run `install.sh` after
   adding skills/scripts.
9. **Right hook event.** Session-scoped capture uses `SessionEnd` (fires once per
   session). `Stop` fires once per *response* — using it would append a line per turn
   and bloat the index. `PostToolUse` is per-edit. Match the event to the cadence.

---

## 4. Build order & per-task specs

### Task 1 — `references/MEMORY-ARCHITECTURE.md` (+ cognition map)
**Create** `dotfiles/claude/.claude/references/MEMORY-ARCHITECTURE.md`, peer to
`MEMORY-STANDARD.md` (`MEMORY-STANDARD.md` covers only semantic; this covers the
whole system). Include: the taxonomy table (§2, **including the scratchpad note**),
the two gaps, the two-layer episodic model, the short→long pipeline framing, and the
inline cognition map (§2). `references/` is a whole-dir symlink, so the file is live
immediately.
**Done when:** every `claude-mem` capability maps to a named store or a deliberate
omission; the cognition map lists each faculty with a `Spec:` status; the scratchpad
is named as the fifth store with its recall-scope rule.

### Task 2 — Episodic capture backbone
Build before `/recall` so there's a complete trace to recall *from*.

- **2a — `dotfiles/scripts/update-episodic`** (Python; sibling of `update-triage` /
  `update-cache`). Appends one line per session to a per-project `EPISODIC-INDEX.md`
  **and** to a global roll-up at `~/dev/EPISODIC-INDEX.md`. Fields: ISO timestamp,
  project, branch, files touched, `git --shortstat`.
  - **PATH SPEC (do not guess):** per-project index = `<project-root>/EPISODIC-INDEX.md`;
    global roll-up = `~/dev/EPISODIC-INDEX.md`. The `machine` project (`~/dev` root) is
    **not a git repo** — its per-project index *is* the global roll-up; skip git fields
    there (guard every git call, write the line with empty file/shortstat fields).
  - **TEMPLATE CAVEAT:** `update-triage` writes a single fixed global pair
    (`~/dev/.triage-cache`, `~/dev/TRIAGE-BLOCK.md`). It is the template for the
    *install wiring and zero-token style only* — `update-episodic` must add its own
    per-project path logic (derive project root from the cwd passed by the hook).
  - **CONCURRENCY:** two sessions can end together and race-append the global roll-up.
    Wrap the global append in an `flock` on `~/dev/.episodic.lock` (per-project files
    rarely collide, but lock them too if cheap).
- **2b — `dotfiles/claude/.claude/hooks/episodic_index.py`** — a **`SessionEnd`** hook
  mirroring `refresh_triage.py` structure (parse stdin JSON → scope guard →
  `subprocess.run` to `update-episodic` → suppress all output).
  - **WHY `SessionEnd`, NOT `Stop`:** `Stop` fires every time the model finishes a
    response (many times per session) → one index line per turn → backbone bloat.
    `SessionEnd` fires once when the session terminates. Verify the real `SessionEnd`
    payload shape first (it carries `reason` and `cwd`; it does **not** carry
    `tool_input.file_path`).
  - **FILES-TOUCHED — use a baseline, not a bare diff.** A working-tree
    `git diff --name-only` at session end **misses everything already committed**
    (per-file commits are a stated convention → diff is usually clean). Instead:
    1. Capture a baseline at session start (Task 2g-pre below): write
       `git rev-parse HEAD` to `<project>/.episodic-baseline` in a `SessionStart` hook.
    2. At `SessionEnd`, compute touched = `git diff --name-only <baseline>..HEAD`
       **plus** the current working-tree diff (`git diff --name-only` +
       `git diff --name-only --staged`), unioned and de-duped. Shortstat the same range.
    3. If no baseline exists (first run / detached), fall back to working-tree diff and
       tag the line `[no-baseline]`.
- **2c — `dotfiles/claude/.claude/settings.json`** — add the hook under a **new
  `SessionEnd` array** (it does not exist yet; the existing `Stop` array stays
  untouched and keeps running `session_timer.py stop`). Additive, same
  `2>/dev/null || true` guard. Also add the baseline-capture command to the existing
  `SessionStart` array (second entry alongside `session_timer.py session_start`).
- **2d — `dotfiles/install.sh`** — symlink `update-episodic` into `~/.local/bin`
  (follow the `update-triage` / `update-cache` wiring: `safeguard` → `ln -sf` →
  `chmod +x` on the source).
- **2e — structured `SESSION-LOG` line in `/checkpoint`** — in
  `skills/session-checkpoint/SKILL.md`, add to the Output Format block (after
  `### Files Touched`) and a new instruction step: a machine-greppable `Files:` +
  `Tags:` line using the existing annotation tags from `CLAUDE.md` (`[BUG]`/`[FEAT]`/…)
  so `/recall` Layer 1 can filter.
- **2f — gitignore decision:** `EPISODIC-INDEX.md` is a high-churn runtime artifact
  (like `TRIAGE-BLOCK.md` / `.triage-cache`). It must be gitignored **per project**,
  not via one global rule (`~/dev` root is not a repo, so a rule there is moot):
  - Add `EPISODIC-INDEX.md`, `.episodic-baseline`, `.episodic.lock` to each project's
    `.gitignore`.
  - Add the same lines to the **`dev-setup` gitignore template** so new projects
    inherit them.
  (Unlike `KNOWLEDGE.md`/`SESSION-LOG.md`, which are committed.)
- **2g — decay / rotation (delivers the fourth stolen idea).** `EPISODIC-INDEX.md`
  grows unbounded otherwise. Mirror `rotate-log`: when an index exceeds N lines
  (start N=500), move the oldest half to `EPISODIC-ARCHIVE.md` (also gitignored).
  `/recall` reads the live index by default; `--deep` may also grep the archive.
  Wire it as a tail step inside `update-episodic` (cheapest — already touching the file)
  or as a sibling script called after the append.
**Done when:** ending any session (including `/close`) via **`SessionEnd`** appends
exactly **one** line to `EPISODIC-INDEX.md` at zero model tokens; files-touched
includes work committed mid-session; a `/checkpoint` produces the `Files:`/`Tags:`
line; an index past N lines rotates into `EPISODIC-ARCHIVE.md`.

### Task 3 — `/recall` skill
**Create** `dotfiles/claude/.claude/skills/recall/SKILL.md`.
Interface: `/recall <query>` and `/recall --deep <query>`. Progressive disclosure:
- **Layer 1 (index, ~50–100 tok):** grep `EPISODIC-INDEX.md` + `KNOWLEDGE.md` tiers →
  compact hit list (source + one-line + date).
- **Layer 2 (context):** expand the surrounding `SESSION-LOG` block / KNOWLEDGE
  neighbors for a chosen hit.
- **Layer 3 (full):** read the full block/file only when asked.

Scope: default = cwd project (`SESSION-LOG.md` + `EPISODIC-INDEX.md`) + local + global
`KNOWLEDGE.md`. `--deep` = fan out across all `~/dev` projects (reuse `/dev-brief`'s
cross-project walk) **and** may read the scratchpad store + `EPISODIC-ARCHIVE.md`.
Constraints:
- **`--deep` is Layer-1 grep-only across projects** (invariant #7) — emit index hits,
  expand only the one the user picks. Never auto-read full logs in fan-out.
- **git-crypt guard:** `KNOWLEDGE.md` is git-crypt ciphertext until unlocked
  (`install.sh` unlocks the local one; *other* `~/dev` projects under `--deep` may be
  locked). Before grepping a `KNOWLEDGE.md`, detect lock state (first bytes / `file`);
  if locked, skip it and note `[locked: <project>]` rather than grepping ciphertext.
- Tag scratchpad hits `[scratch]` (skipped the bar) and archive hits `[archived]`.
No new storage.
**Done when:** a known query returns a cheap Layer-1 hit and expands on request; a
`--deep` run reaches another `~/dev` project, skips any locked KNOWLEDGE.md with a
note, and labels scratch/archive hits. (Pick a test query that actually exists in a
scanned source — see §6.)

### Task 4 — `/consolidate` skill
**Create** `dotfiles/claude/.claude/skills/consolidate/SKILL.md`.
**Lift `/checkpoint` Step 7 verbatim** (`skills/session-checkpoint/SKILL.md`, the
promotion gate): read `MEMORY-STANDARD.md`, run the 4 bar tests
(SETTLED · NON-OBVIOUS · NOT A RULE · DURABLE), present numbered candidates pre-routed
`[LOCAL]`/`[GLOBAL]`, accept grammar `a`/`d`/`1 2`/`r1 global`/`e1 new text`. Differs
only in **scope**: sweep `SESSION-LOG`/`EPISODIC-INDEX` entries since the last
consolidation, not just the current session. Approved facts route through
`/remember`'s logic (routing, dedup, distill-on-write).

- **MARKER (concrete spec):** track the last-consolidated point in
  `~/dev/.consolidation-marker` (JSON: `{ "<project>": "<ISO timestamp>" }`, mirror
  `.triage-cache`'s shape). `/consolidate` reads it, sweeps only entries newer than the
  marker for the in-scope project(s), and advances the marker on completion. Missing
  marker = sweep everything (first run).

Two modes:
- **Manual `/consolidate`:** review proposals inline (you are present).
- **Scheduled:** the producer runs unattended via **`/schedule` (cloud cron) or a
  system cron** — **not `/loop`** (`/loop` runs only inside a live session and cannot
  produce an inbox "for next session"). The scheduled run **never auto-writes**: it
  writes the candidate block to a transient `CONSOLIDATION-INBOX.md` and notifies. Next
  session you approve/reject; approved facts route through `/remember`; the inbox
  clears. (Empty inbox = healthy.) `CONSOLIDATION-INBOX.md` is gitignored (add to 2f).
**Done when:** seeding a `SESSION-LOG` block with one durable fact + one open-work item
promotes the fact to `KNOWLEDGE.md` and rejects the open-work item (fails SETTLED),
routing it to `TODOS.md`; the marker advances so a second run finds nothing new.

### Task 5 — registration
- Add `/recall` and `/consolidate` to the `## Skills Available` alias line in
  `dotfiles/claude/.claude/CLAUDE.md`.
- Re-run `bash dotfiles/install.sh`. (The install skill loop already symlinks every
  `skills/*/` dir, so the two new skills are picked up automatically — no per-skill
  symlink line needed. You only hand-wire the new *script*, `update-episodic`, in 2d.)

---

## 5. Critical files (reuse map)

| File | Role |
|---|---|
| `claude/.claude/references/MEMORY-STANDARD.md` | Pattern to mirror for the new doc; `/consolidate` reuses its bar |
| `claude/.claude/skills/remember/SKILL.md` | Routing/dedup logic reused by `/consolidate` |
| `claude/.claude/skills/session-checkpoint/SKILL.md` | Source of the promotion gate to lift (Step 7); gets the structured `SESSION-LOG` line |
| `claude/.claude/hooks/refresh_triage.py` | Structural template for the `SessionEnd` episodic hook (style only — different event + git-baseline logic) |
| `scripts/update-triage`, `scripts/update-cache` | Template for `update-episodic` install wiring + zero-token style (NOT for path logic — those are global-only) |
| `scripts/rotate-log` | Template for the index rotation in 2g |
| `claude/.claude/CLAUDE.md` | Annotation tags reused for episodic structure; add new skills to alias line |
| `claude/.claude/skills/dev-setup/…` | gitignore template gets the episodic ignore lines (2f) |
| `claude/.claude/skills/write-a-skill/SKILL.md` | The procedure for authoring the new skills |
| `claude/.claude/settings.json` | Add `SessionEnd` array + baseline cmd in `SessionStart` (symlinked — edit source) |
| `install.sh` | Symlink `update-episodic`; re-run after adding (skill dirs auto-symlinked) |

---

## 6. Verification (end-to-end)

- **Model:** read `MEMORY-ARCHITECTURE.md` back — every `claude-mem` capability maps to
  a named store or a deliberate omission; cognition map shows each faculty + `Spec:`;
  scratchpad named as fifth store.
- **Episodic capture:** end a session with `/close` (no `/checkpoint`) → confirm
  **exactly one** new line landed in `EPISODIC-INDEX.md` and nothing was emitted to
  model context. Then end another session and confirm it appends one more (not one per
  turn) — proves `SessionEnd`, not `Stop`.
- **Committed-work capture:** make a change, commit it mid-session, end session →
  confirm the committed file appears in the episodic line's files-touched (proves the
  git-baseline diff, not a bare working-tree diff).
- **Structured `SESSION-LOG`:** after `/checkpoint`, confirm the `Files:`/`Tags:` line
  is present and greppable.
- **`/recall`:** query a fact **known to exist in a scanned source** (a real
  `KNOWLEDGE.md` entry, or seed one first — do NOT assume the powerline note, which
  lives in the scratchpad store outside default scope) → Layer 1 returns it cheaply;
  Layer 3 expands on request. `--deep` reaches another `~/dev` project, skips any locked
  `KNOWLEDGE.md` with a `[locked]` note, and labels scratch/archive hits.
- **Rotation:** append past N lines (or temporarily lower N) → confirm oldest half
  moves to `EPISODIC-ARCHIVE.md` and the live index shrinks.
- **`/consolidate`:** seed a `SESSION-LOG` block with a durable fact + an open-work
  item → fact promotes to `KNOWLEDGE.md`; open-work item rejected (SETTLED) → `TODOS.md`;
  marker advances; a second immediate run finds nothing new.
- **Install:** `bash install.sh` → `/recall` and `/consolidate` resolve in a fresh
  session; `update-episodic` is on `PATH`.

---

## 7. Decisions log (already resolved — do not re-litigate)

1. **Episodic capture:** build **both** layers — zero-token auto-index hook (complete
   coverage) + structured `/checkpoint` line (curated detail). Auto-index is the
   backbone *because* `/close`/`/handoff` sessions otherwise leave no episodic trace.
2. **Capture event:** **`SessionEnd`**, once per session — not `Stop` (per-response).
3. **Files-touched:** diff against a SessionStart git **baseline** unioned with the
   working tree — not a bare end-of-session working-tree diff (misses commits).
4. **Recall scope:** `/recall` = current project + global `KNOWLEDGE`; `/recall --deep`
   = all `~/dev` projects + scratchpad + archive, Layer-1 grep-only, locked-KNOWLEDGE
   skipped.
5. **Consolidation:** manual `/consolidate` + scheduled cadence via `/schedule`/cron
   (not `/loop`); the scheduled run **never auto-writes** — it proposes to
   `CONSOLIDATION-INBOX.md` and notifies. Marker in `~/dev/.consolidation-marker`.
6. **Consolidation target:** promotes into existing `KNOWLEDGE.md` via the bar + dedup.
   **No `MEMORY.md`.** Only new files are transient `CONSOLIDATION-INBOX.md` +
   `EPISODIC-ARCHIVE.md`.
7. **Decay:** delivered as index rotation (2g), mirroring `rotate-log`.
8. **File naming:** keep existing filenames; **no `LONG-TERM.md`/`SHORT-TERM.md`** —
   horizon is an axis over stores, modeled as the consolidation pipeline, not a store.
9. **Cognition docs:** grow & extract — inline cognition-map section now; extract
   `*-ARCHITECTURE.md` leaves only when earned. Likely first extraction: **attention**.

---

## 8. Changelog (Rev 2026-06-19 — fixes from design review)

| # | Severity | Fix | Where |
|---|---|---|---|
| 1 | Critical | Capture moved `Stop` → `SessionEnd` (Stop fires per-response, not per-session) | 2b, 2c, §3.9, §6, §7.2 |
| 2 | Critical | Files-touched via SessionStart git baseline ∪ working tree (bare diff misses commits) | 2b, 2c, §6, §7.3 |
| 3 | High | Decay/rotation actually built (was promised in §1, absent from tasks) | 2g, §7.7 |
| 4 | High | Consolidation marker given a concrete file + format | Task 4 marker spec |
| 5 | High | Scheduled consolidation uses `/schedule`/cron, not `/loop` (loop is in-session) | Task 4, §7.5 |
| 6 | High | Verification query fixed; scratchpad named as fifth store + out of default scope | §2 note, Task 3, §6 |
| 7 | Med | `--deep` skips git-crypt-locked `KNOWLEDGE.md` with a note | Task 3 |
| 8 | Med | Explicit paths for per-project index + global roll-up + `machine` project | 2a PATH SPEC |
| 9 | Med | Noted `update-triage` template is global-only; `update-episodic` adds own path logic | 2a, §5 |
| 10 | Med | gitignore restated per-project + dev-setup template (root rule was moot) | 2f |
| 11 | Low | Concurrency: `flock` on global roll-up append | 2a |
| 12 | Low | Trimmed redundant per-skill symlink instruction (install loop already does it) | Task 5 |
| 13 | Low | `--deep` constrained to Layer-1 grep-only (token-frugality invariant) | §3.7, Task 3 |
