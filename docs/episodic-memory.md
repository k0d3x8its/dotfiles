# Episodic Memory

Automatic per-session capture that feeds `/recall` and `/consolidate`. Zero model tokens — runs entirely in the harness at session boundaries.

---

## Architecture

```
SessionStart hook → write .episodic-baseline (git HEAD snapshot)
    ↓
SessionEnd hook → episodic_index.py → update-episodic
    ↓
per-project  <project>/.memory/EPISODIC-INDEX.md   (one line per session, thin)
global       ~/dev/.memory/EPISODIC-INDEX.md  (roll-up across all projects)
    ↓
/recall      progressive-disclosure grep (Layer 1 → 2 → 3)
    ↓
/consolidate episodic→semantic promotion → KNOWLEDGE.md (gated)
```

---

## Why SessionStart baseline, not bare end-of-session diff

Per-file commits are the house convention, so by session end the working tree is usually clean and a bare `git diff` reports nothing. The hook writes a git HEAD snapshot (`.episodic-baseline`) at SessionStart, then diffs `<baseline>..HEAD` at SessionEnd — capturing all commits made during the session — unioned with any live staged/unstaged changes.

---

## Files

| File | Role | Gitignored? |
|------|------|------------|
| `.episodic-baseline` | SessionStart git HEAD snapshot | Yes — runtime artifact |
| `.memory/EPISODIC-INDEX.md` | One-line-per-session spine (per project) | Yes — runtime artifact |
| `~/dev/.memory/EPISODIC-INDEX.md` | Global roll-up across all projects | Yes — runtime artifact |
| `.memory/EPISODIC-ARCHIVE.md` | Rotated-out old index lines | Yes — runtime artifact |

---

## `episodic_index.py` — SessionEnd hook

**Event:** SessionEnd (NOT Stop).

Stop fires after every model response — using it would append an index line per turn and bloat the index. SessionEnd fires once when the session terminates.

The hook reads `cwd` from the SessionEnd payload, then calls `update-episodic <cwd>`.

---

## `update-episodic` script

Derives the project from `cwd`, computes files-touched via `git diff <baseline>..HEAD` + live working tree, and appends one structured line to both the per-project and global `.memory/EPISODIC-INDEX.md`.

**Concurrency:** two sessions can end simultaneously and race-append to the global roll-up. The append is wrapped in `flock` to prevent corruption.

**Decay / rotation:** once `.memory/EPISODIC-INDEX.md` exceeds `MAX_LINES`, the oldest half moves to `.memory/EPISODIC-ARCHIVE.md`. The global index stays thin; the archive preserves history.

The `~/dev` root itself is the `machine` project and is not a git repo. Every git call is guarded — it gets an index line with empty git fields rather than an error.

---

## `/recall` — Retrieval

Progressive disclosure across memory stores:

| Layer | Source | Cost |
|-------|--------|------|
| L1 | `.memory/EPISODIC-INDEX.md` + `KNOWLEDGE.md` grep (current project) | Cheap |
| L2 | Expand matching `.memory/SESSION-LOG.md` blocks | Medium |
| L3 (`--deep`) | Fan out across all `~/dev` projects + `.memory/EPISODIC-ARCHIVE.md` | More |

`--deep` results label hits from `~/.claude/projects/` scratch memory as `[scratch]` — those entries skipped the KNOWLEDGE.md bar and are unvetted.

---

## `/consolidate` — Episodic→semantic promotion

Sweeps `.memory/EPISODIC-INDEX.md` and `.memory/SESSION-LOG.md` entries since the last consolidation marker, runs each candidate through the 4-test bar (SETTLED · NON-OBVIOUS · NOT A RULE · DURABLE), and routes approved facts through `/remember`'s dedup logic into `KNOWLEDGE.md`.

Never auto-writes — every promotion requires explicit user approval.
