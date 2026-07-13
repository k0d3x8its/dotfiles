# Security Suite

Four skills, one engine, one shared context file. The suite audits three distinct
things — a project's code, that code's *remotely reachable* subset, and the Claude
Code harness itself — plus a design-time threat model that feeds the other three.
All of them are **read-only**: findings become tagged `[SECURITY]` TODOs in
`TODOS.md` (user-confirmed before writing); remediation is always its own task.

## How the suite composes

```
┌─────────────────────────────────────────────────────────┐
│                  .work/SEC-CONTEXT.md                   │
│   shared, git-crypted — topology · actors/auth tiers    │
│                   · trust boundaries                    │
└─────────▲───────────────────▲───────────────────▲───────┘
          │ read/write        │ read/write        │ read/write
┌─────────┴─────┐    ┌────────┴─────┐    ┌────────┴───────┐
│ /threat-model │    │  /code-sec   │    │ /bounty-hunter │
│  design-time  │    │    broad     │    │  reachability  │
│    STRIDE     │    │   hygiene    │    │     filter     │
│  (in build)   │    │    sweep     │    │                │
└───────────────┘    └───────┬──────┘    └───────┬────────┘
                        owns │            reuses │
                             ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                shared deterministic core                │
│  bin/enumerate-entrypoints.sh · rules/ (tiered pack) ·  │
│              fixtures/vuln-app (red-green)              │
└─────────────────────────────────────────────────────────┘

data handoffs:
  /code-sec phase-2 CVE scan ──► /bounty-hunter (consume + rank)
  /code-sec phase 6 ─────────► /harness-audit (repo ships .claude/)

┌─────────────────────────────────────────────────────────┐
│  /harness-audit — separate track: audits the harness    │
│  itself (hooks · plugins · MCP · settings · memory),    │
│  not the project code                                   │
└─────────────────────────────────────────────────────────┘
```

Two axes tell the skills apart:

| | Breadth (everything dangerous) | Depth (one lens) |
|---|---|---|
| **Project code** | `/code-sec` | `/bounty-hunter` (reachability), `/threat-model` (design) |
| **Harness config** | `/harness-audit` | — |

Shared conventions across all four: read-only sweeps, never print a discovered
secret or working exploit payload (file:line + description only), code-sec's
Finding discipline (taint-trace entry→sink, `CONFIRMED`/`TRACED`/`CANDIDATE`
confidence tiers, suppress-list) applied verbatim, severity tags
(`[BROKEN]`/`[BLOCKER]`/default/`[LOW]`), CVE data queried live never recited
from memory, and loud disclosure whenever a tool was missing or a scan didn't
run — a quiet degrade reads as a clean sweep and is worse than none.

## Per-skill usage

### /code-sec — project security sweep (breadth)

**What:** full-project hygiene audit in 7 phases: (0) attack-surface inventory
via the shared enumerator, (1) gitleaks full-history + working-tree secret scan,
(2) dependency audit (auto-detects npm/pip/cargo/go), (3) git-crypt coverage vs
the File Taxonomy including the `\0GITCRYPT` blob check, (4) input-handling scan
— tiered ast-grep rule pack first, then inline ast-grep/rg patterns, (5)
app-layer pass when the repo serves HTTP (input validation, SQLi, XSS, auth/authz,
sessions, SSRF/traversal), (6) harness-surface check for repos shipping
`.claude/` (points to `/harness-audit` for the full treatment).

**When:** new or newly-audited project, before a repo goes public, periodically
on active projects, or whenever a `[SECURITY]` TODO routes here. This is the
default "audit this project" entry point.

**Output:** phase-grouped findings report + a mini threat model (top-3 exploits
an attacker would try) + tagged `[SECURITY]` TODOs.

### /bounty-hunter — remote-reachability triage (depth)

**What:** answers the narrower, higher-value question: *what can an external
attacker actually reach?* Reuses code-sec's enumerator and rule pack, then gates
every finding on a full path from an external entry point to the sink. Phase 0
confirms exposure + auth tier per surface with the user **once** (or
`--assume-public` for the no-human CI path — deliberate fail-open, every network
surface treated as external-unauthenticated with the enumerator's original guess
retained as a sort annotation). Three auth tiers (unauth-external /
authenticated-any-user / privileged) so IDOR and privilege-escalation survive the
gate. CVEs are consumed and reachability-ranked, never re-scanned. Domain packs
(game abuse, web business-logic) load on demand at Phase 0 — see authoring below.

**When:** "what's actually exploitable from outside", bug-bounty-style pass,
pre-launch check on anything network-facing, or a `[SECURITY]` TODO specifically
about remote exploitability. Run *after* or *instead of* code-sec depending on
whether you want breadth or the exploitable subset.

**Output:** report grouped by entry point (attack surface), headed by a mandatory
per-language rule-coverage declaration (`NO SINK RULES RAN — treat as UNSCANNED,
not clean` for uncovered languages), a trailing `Dropped — local-only` section
routing unreachable findings to code-sec, and a fixed next-steps guide. Only
reachable findings become TODOs.

### /harness-audit — the harness's own attack surface

**What:** audits the Claude Code setup that runs Claude itself, not a project:
hooks (highest privilege — network egress, transcript-read + egress pairing,
obfuscated exec), skills/plugins as a prompt-injection supply chain
(hidden-unicode payloads, approval-widening instructions), MCP servers,
settings overrides (`ANTHROPIC_BASE_URL`, `apiKeyHelper`,
`enableAllProjectMcpServers`, over-broad allow-lists), memory/CLAUDE.md
instruction-injection points, and the Claude Code CVE version floor.

**When:** after installing any new plugin, marketplace, MCP server, or hook;
periodically; or when anything in the harness feels off. `/code-sec` phase 6
hands off here when a *project repo* ships `.claude/` config.

**Output:** minimum-bar checklist (every item verified or finding-linked) +
`[SECURITY]` TODOs filed in `dotfiles/TODOS.md` (the harness is
dotfiles-managed).

### /threat-model — design-time STRIDE (in build)

**What:** full STRIDE threat model as a deliberate standalone workflow —
interview → DFD (rendered via `/diagram`'s DFD mode) → STRIDE per element →
risk-rank (3×3 grid, High forces a TODO) → mitigation map. Modes: create /
update / design-review (`--design`). Its interview persists to
`.work/SEC-CONTEXT.md`, and it consumes the shared enumerator for DFD nodes when
code exists (degrades to arch docs + interview pre-code).

**When:** pre-launch or at design time, when the risk question is structural
("what should we be defending against?") rather than code-level. Deliberately
NOT part of the sweep skills — it is a separate sit-down.

**Status:** shipped — `claude/.claude/skills/threat-model/SKILL.md`, symlinked by
`install.sh`. Design record: `docs/brainstorm/threat-model-skill-2026-07-11.md`
(decisions TM-D1..TM-D10 encoded in that doc + `.work/PLAN.md` Goals 16–19).

## End-to-end workflow

Typical order on a real project:

1. **`/threat-model`** (design-time, optional for small repos) —
   seeds `.work/SEC-CONTEXT.md` with topology, actors, and trust boundaries
   before any code-level pass.
2. **`/code-sec`** — the broad sweep. Its phase-0 inventory and phase-2
   dependency scan become inputs downstream.
3. **`/bounty-hunter`** — the reachability filter. Consumes the same-session
   code-sec CVE output when present (one source of truth, no drifting second
   scan), reads SEC-CONTEXT instead of re-asking exposure, and drops anything
   local-only back toward code-sec territory with an annotation.
4. **`/harness-audit`** — separate track, on its own cadence; also the phase-6
   handoff target whenever an audited repo ships `.claude/`.

Data flows that make the order matter:

- **code-sec → bounty-hunter:** entry-point inventory (shared enumerator), rule
  pack hits, and the phase-2 CVE scan. bounty-hunter ranks; it never owns the
  authoritative scan.
- **everything ↔ `.work/SEC-CONTEXT.md`:** confirmed exposure, auth tiers, and
  trust boundaries persist there (git-crypted — it is attacker context), so each
  skill reads instead of re-asking. Until the G17 template ships, the file may
  simply not exist yet; every skill degrades gracefully to enumerate-and-ask.
- **Overlap rule:** a finding unreachable from outside is code-sec's, a reachable
  one is bounty-hunter's, a design gap is threat-model's, and anything in
  hooks/skills/settings is harness-audit's. Dropped items are annotated with the
  owning skill, never double-filed.

Both sweep skills close with follow-up routing: `/encrypt` for git-crypt
coverage gaps, `/diagnose` for any CONFIRMED vuln, rotation checklist for leaked
secrets.

## Shared deterministic core

Lives in `claude/.claude/skills/code-sec/` and is consumed by both sweep skills:

- **`bin/enumerate-entrypoints.sh`** — structured entry-point inventory:
  `file:line | kind | bind-hint | exposure-guess`. Parses Python, JavaScript,
  TypeScript, Go, Lua, Solidity, and Arduino/C-family route + listener shapes.
  The exposure column is a default guess (0.0.0.0→public, 127.0.0.1→local,
  socket→internal, unknown→public fail-open), never a verdict.
- **`rules/`** — tiered ast-grep rule pack (`precise/` near-conclusive,
  `normal/` shape heuristics, `noisy/` candidates), CWE-tagged, run via
  `ast-grep scan -c rules/sgconfig.yml`. Coverage is keyed on ast-grep's
  **extension dispatch, not the rule's `language:` field** — `.ts/.tsx` and
  `.c/.h` dispatch to different grammars than their sibling rules target, which
  is why the pack ships a separate `language: c` rule and why TypeScript is
  declared uncovered. The pack is a fast-path candidate *seed*, not the ceiling:
  the model pass backstops uncovered languages and novel sink shapes.
- **`fixtures/vuln-app/`** — red-green corpus (`MANIFEST.md` is the source of
  truth): every rule must fire on its planted vuln and stay silent on the safe
  pair. Guarded by `tests/test_bounty_rules.py` + `test_bounty_enumerator.py`
  on `unittest discover`, so a broken rule cannot slip in between manual runs.

## Domain-pack authoring

bounty-hunter's core covers the general remote-reachable CWE families;
domain-specific abuse (game economy/state-tampering, web business-logic) lives
in on-demand packs so the always-on core stays lean. A pack is one `<domain>`
key with two halves: `domains/<domain>.md` (the reasoning lens) and
`rules/<domain>/` (the deterministic ast-grep layer). Detection runs once in
Phase 0 and always proposes, never auto-loads.

**Authoring guide: `claude/.claude/skills/bounty-hunter/domains/TEMPLATE.md`.**
Packs are filled *empirically* after a real sweep of that domain — never
speculatively; v1 ships the seam with zero packs, which is the intended default.
