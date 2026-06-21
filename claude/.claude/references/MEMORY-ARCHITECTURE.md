# Memory Architecture

Reference for the full multi-store memory system. `MEMORY-STANDARD.md` covers only the semantic store; this covers the whole system, how the stores relate, and what each recall/consolidation tool touches.

---

## Memory Taxonomy

| Memory type | What it is | Primitive | State |
|---|---|---|---|
| Working / short-term | Active context now | session context, `.work/FINDINGS.md`, `.work/PLAN.md`, scratchpad | ✅ have |
| Semantic | Decontextualized facts | `KNOWLEDGE.md` (local+global), `MEMORY-STANDARD.md` | ✅ strong |
| Procedural | "How to do things" | the skills + `CLAUDE.md` rules | ✅ strong |
| Prospective | Remember to act later | `TODOS.md` + tags + `update-triage` → `.memory/TRIAGE-BLOCK.md` | ✅ have |
| Episodic | Time-indexed events | `.memory/SESSION-LOG.md` + `.memory/ARCHIVE-LOG.md` + `.memory/EPISODIC-INDEX.md` | ⚠️ building |
| Retrieval | Cue-driven lookup | `/recall` skill | ⚠️ building |
| Consolidation | Episodic→semantic ("sleep") | `/consolidate` skill | ⚠️ building |

> **The fifth store — auto-memory scratchpad.** `~/.claude/projects/<hash>/memory/` (the `[[…]]`-linked fact files + `MEMORY.md` index) is auto-written working/semantic notes that are NOT committed and NOT subject to the `KNOWLEDGE.md` bar. It is deliberately **out of `/recall`'s default scope** because it is per-machine, unvetted, and noisy. `/recall --deep` MAY read it; any hit from there is labeled `[scratch]` so the reader knows it skipped the bar.

---

## What Is Being Built

Two capabilities are absent today and are the target of this architecture:

1. **Retrieval** — recall is ad-hoc grep with no progressive disclosure. `/recall` (in progress).
2. **Consolidation** — episodic→semantic promotion only happens as a side-effect of `/checkpoint`; `/close` and `/handoff` sessions leave no episodic trace. `/consolidate` (in progress).

Both will be first-class skills built on existing primitives. Until they ship, the status column above reads ⚠️ building.

---

## Two-Layer Episodic Memory

- `.memory/EPISODIC-INDEX.md` = **complete but thin** — one auto-captured line per session (every session, metadata only). The searchable spine.
- `.memory/SESSION-LOG.md` = **sparse but rich** — full narrative, only for `/checkpoint`-ed sessions. The curated "why."

Mirrors human memory: a continuous faint trace + a few vivid consolidated episodes.

The short-term→long-term gradient is a **pipeline** (faint recent index → curated durable `KNOWLEDGE.md` via `/consolidate`), not two static buckets. There is deliberately **no `LONG-TERM.md`/`SHORT-TERM.md`**: "horizon" is an axis over the existing stores, not a store.

### Episodic file map

| File | Role | Gitignored? |
|---|---|---|
| `.memory/SESSION-LOG.md` | Curated session narratives (checkpoint only) | No — git-crypt encrypted + committed |
| `.memory/ARCHIVE-LOG.md` | Rotated-out old SESSION-LOG blocks | No — committed |
| `.memory/EPISODIC-INDEX.md` | One-line-per-session auto-captured spine | Yes — runtime artifact |
| `.memory/EPISODIC-ARCHIVE.md` | Rotated-out old index lines | Yes — runtime artifact |
| `.episodic-baseline` | SessionStart git HEAD snapshot for files-touched | Yes — runtime artifact |

---

## The Consolidation Pipeline

```
session ends
    ↓
SessionEnd hook → update-episodic → .memory/EPISODIC-INDEX.md   (zero tokens, every session)
    ↓
/checkpoint → .memory/SESSION-LOG.md block with Files:/Tags: line  (human-curated, rich)
    ↓
/consolidate → sweeps index + log → bar test → /remember → KNOWLEDGE.md  (gated promotion)
```

Facts only reach `KNOWLEDGE.md` through explicit approval. The index is a faithful but cheap trace; the log is a rich but sparse one; consolidation is the sleep step that distills both into durable semantic memory.

---

## Cognition Map

Memory is one faculty of a larger cognitive system. The map lives here (not in a separate `COGNITION.md` — cognition is process, not content; extract only under pressure).

| Faculty | Implemented by | Spec status |
|---|---|---|
| Perception | session-start reads (`CLAUDE.md` rules) | n/a |
| Attention | triage → `.memory/TRIAGE-BLOCK.md`; progressive disclosure | TBD (next likely extraction) |
| Memory | the 5-store system (this doc) | ✅ this doc |
| Reasoning | `/brainstorm`, `/diagnose`, plan mode | TBD (may stay pointer-only) |
| Metacognition | `/trust-but-verify` | TBD |
| Executive function | `TODOS.md` + session tools | TBD (may merge with Attention) |

---

## Key Invariants

1. **Capture costs zero model tokens.** Hooks suppress all stdout — emitting to stdout injects text into model context.
2. **Never auto-write to `KNOWLEDGE.md`.** Every entry passes the 4-test bar + dedup + explicit user approval.
3. **`--deep` is Layer-1 grep-only across projects** — emit index hits, expand only on user request.
4. **`SessionEnd` not `Stop` for episodic capture.** `Stop` fires per-response → index bloat.
5. **Files-touched uses a SessionStart git baseline**, not a bare end-of-session diff (bare diff misses mid-session commits).
6. **Distill-on-write.** No blind append to `KNOWLEDGE.md` — update existing entries on overlap.

See `MEMORY-STANDARD.md` for the full KNOWLEDGE.md bar, entry format, routing, and dedup rules.

---

*Architecture influenced by [claude-mem](https://github.com/thedotmack/claude-mem). Design decisions diverge intentionally — no SQLite/vector store, no daemon, gated promotion over auto-capture.*
