# Design: bounty-hunter skill — exploitability triage for remote-reachable vulns

> Brainstorm output, 2026-07-07. Pipeline: /brainstorm → /grill-me → /write-plan.
> Status: draft — not yet grilled.

## Problem

The security-skill suite has `code-sec` (broad OWASP hygiene, no reachability filter)
and `harness-audit` (own Claude Code config surface). Neither answers the adversary's
actual question: **"which of these findings can an outside attacker reach and exploit?"**
On a networked codebase, code-sec's broad net returns hardening gaps mixed with live
remote-exploitable holes at equal weight — the signal that matters (an unauthenticated
SQLi on a player-data endpoint) drowns in defense-in-depth noise.

`bounty-hunter` closes that gap: exploitability triage for **any networked application** —
web apps, REST/GraphQL APIs, microservices, backends, multiplayer game servers. It takes a
networked codebase, enumerates the *remotely-reachable* attack surface, and ranks findings
by whether a full attack path is constructible from outside the trust boundary. Everything
local-only it discards by design and hands to code-sec. Games are the *first driver*, not
the scope: friend's game (backend + multiplayer) review is near-term and two planned games
are backend + multiplayer, but the same reachability triage applies unchanged to a Flask
API, a Node service, or any request-handling server. Recurring surface across every app
project, not a game tool.

## Context & constraints

- **Lives in** `dotfiles/claude/.claude/skills/bounty-hunter/`, symlinked live (per KNOWLEDGE.md: never a loose `~/.claude/skills/` dir).
- **Adapts** ECC repo (`github.com/affaan-m/ECC`) `security-bounty-hunter` skill + its "Prompt Defense Baseline" header. ECC source not local — pull structure at build time.
- **Taxonomy split** (established suite convention): CWE baked in offline (structures findings + severity + the reachability filter itself), CVE queried live (`npm audit`/`osv-scanner`/`gh advisory`) never hardcoded — the model hallucinates CVE IDs.
- **Read-only sweep**, same as code-sec: findings → tagged `[SECURITY]` TODOs, never silent fixes. Drop caveman for the report.
- **Composes around, does not duplicate:** `ce-security-reviewer` (diff-level persona) and `code-sec` (broad net) are different layers. bounty-hunter is the reachability filter on top; overlapping-but-not-reachable findings route down to code-sec.
- **Reachability filter is the whole value.** A wide net is code-sec's job. bounty-hunter must aggressively discard local-only, physical-access, and dev-only noise or it becomes a second code-sec.
- **General-purpose, not game-specific.** Target is networked application development at large; the game codebases are the first driver. The core threat model (remote-reachability) is domain-agnostic.
- **v1 scope locked:** remote-reachable only, general web/API/service families. **v2 deferred:** domain-specific abuse dimensions, added per-domain as needed — e.g. game abuse (cheat/state-tampering, packet spoofing, trust-client, economy/rate-limit), or web-app business-logic abuse. Additive CWE families, filed as Open question.

## Approaches

### A — Reachability-filter layer over code-sec's engine

Reuse code-sec's phase-0 attack-surface inventory and injection taint-trace machinery,
but add a hard **reachability gate** as the first-class filter: every candidate finding
must have a constructible path from an *external, unauthenticated (or low-priv) network
entry point* to the sink. CWE-scoped to the remote-exploitable families: SSRF (CWE-918),
SQLi (CWE-89), auth-bypass (CWE-287/306), RCE (CWE-94/78), IDOR (CWE-639), deserialization
(CWE-502), path traversal reachable via request (CWE-22). Findings ranked by attack-path
completeness (mirrors code-sec's CONFIRMED/TRACED/CANDIDATE tiers, but the gate is
reachability not just taint). Local-only hits are dropped with a one-line "→ code-sec" note.

**Tradeoffs:** Lowest build cost — reuses proven taint-trace + inventory code, only the
gate + CWE scoping is new. Consistent with the suite's structure (a reader who knows
code-sec reads this instantly). Risk: too much shared machinery could blur the line and
it drifts back into "code-sec with extra steps" — mitigated by making the reachability
gate a mandatory, visible section every finding passes through.

### B — Standalone exploit-chain analyzer

Build fresh around attack-chain construction: model the codebase as trust boundaries and
data flows, then attempt to *construct* end-to-end exploit chains (entry → pivot → sink),
reporting each as a narrative kill-chain rather than a per-file finding. Closer to how a
human bug-bounty hunter thinks.

**Tradeoffs:** Highest-signal output (a real chain is undeniable), best fit for the
"bounty" framing. But much higher build cost, no reuse of existing machinery, and chain
construction is the part LLMs most easily hallucinate — high false-positive risk without
heavy grounding. Overkill for v1; most app codebases (games included) have flat, single-hop
surfaces where a reachability filter already catches the real holes.

### C — Wrapper that dispatches ce-security-reviewer per remote surface

Thin skill: enumerate remote entry points, then fan out `ce-security-reviewer` (or
`ce-security-reviewer`-style personas) scoped to each, aggregate + reachability-rank the
results.

**Tradeoffs:** Least new security logic; leans on a mature CE persona. But ce-security-reviewer
is diff/PR-oriented, not whole-repo-attack-surface-oriented — wrong altitude. Aggregation +
reranking is most of the work anyway, and you inherit the CE agent's cost/latency per surface.
Reachability ranking still has to be built, so little is actually saved.

## Recommendation

**Approach A** — reachability-filter layer over code-sec's engine. It's the cheapest to
build, structurally consistent with the shipped suite (same inventory + taint-trace + tier
vocabulary, so it reads as a sibling of code-sec not a stranger), and the reachability gate
gives it a crisp, defensible boundary against code-sec. It grows cleanly: B's exploit-chain
narrative and the v2 game-abuse CWE families are both additive on top of A's gate without a
rewrite. Start strict and narrow — the value is the low false-positive rate, and A defends
that best.

## Open questions → for /grill-me

- **v2 domain-abuse timing:** keep v1 to the general web/API/service remote families, or fold in a domain-specific dimension (game abuse: state-tampering/packet-spoofing/trust-client/economy; or web business-logic abuse) now? (Recommend defer all domain packs — real vectors beat guessed ones; add per-domain when a real codebase of that domain is in front of you.)
- **Reachability gate mechanism:** how is "reachable from external unauthenticated entry" decided — pure static taint from inventoried entry points, or does the skill ask the user to confirm which entry points are actually internet-exposed vs internal-network? Trust-boundary map is only as good as its inputs.
- **Auth-tier modeling:** does v1 distinguish unauthenticated vs authenticated-but-any-player (IDOR territory) vs privileged? Multiplayer IDOR (act on another player's state) is a top game vuln and needs the "authenticated low-priv" tier, not just "external unauth."
- **Delegated deterministic core:** which parts become tested scripts (entry-point enumeration, CWE-family ast-grep patterns) vs model judgment (the reachability gate, chain plausibility)? Sets the `/tdd` surface.
- **Overlap handoff format:** when a finding is dropped as local-only, does it auto-write a code-sec `[SECURITY]` TODO, or just annotate? Avoid double-reporting when both skills run.
- **CVE version floor:** does bounty-hunter carry its own dependency-CVE pass (osv-scanner on the networked deps) or defer entirely to code-sec's dependency audit? Remote-reachable dep CVEs are squarely in-scope.
- **Report shape:** ranked flat findings list (code-sec style) or grouped by attack surface / trust boundary? Grouping may read better for a networked target but diverges from suite convention.
