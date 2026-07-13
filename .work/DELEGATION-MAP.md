# Delegation Map — sec-auditor epic (bounty-hunter + threat-model)

> Routing of remaining PLAN.md work across the fable-mode v2 tri-model split.
> Reconciled against live file state 2026-07-12 (PLAN.md checkboxes were stale).
> Source split (SESSION-LOG 2026-07-07): playbook-execution / config mechanics /
> test-writing → **Sonnet-executor + Opus-advisor**; deciding-what's-dangerous /
> methodology-design / resolving-open-branches → **Fable**. Builds delegated down,
> reviewed on return.
>
> ⚠️ git-crypt: this file is NOT in `.gitattributes` (only FINDINGS/PROGRESS/PLAN are)
> → plaintext. Contains no secrets, only task routing. Move to a covered name if that
> changes.

## Ground truth (what's actually done)

- **DONE — drop from all planning:** G1-3 (statusline; one [UX] live-check outstanding),
  G4, G5, G6, G7, G8, G9 — the whole memory-architecture epic shipped and is wired live.
- **All decisions locked:** FINDINGS BH-D1..D9 (grilled 07-11), TM-D1..D10 (grilled 07-12).
  No open branches remain → most work is execution against a fixed spec.
- **Advisor caveat:** live cross-session advisor tool errors "unavailable" every session
  ([[project_goal15_delegation]]). The working pattern is **build-then-review**, not live
  advisory. "Opus-advisor" below = review-on-return, not a live channel.

## Sequencing constraint

G10 shared core (enumerator + rule pack) **blocks** both G11 (bounty-hunter consumes it)
and G18 (threat-model DFD nodes, TM-D9). **Finish G10 first.** Within G10 the fixture is
the red-green bed — it exists; remaining pieces are the rule pack + code-sec consumer wiring.

---

## Fable-only — danger judgment / security methodology / prose-where-wording-is-the-safety

| Ref | Task | Why Fable |
|---|---|---|
| G11 · MG1 | bounty-hunter reachability-gate + 3 auth tiers (BH-D1/D2) | Gate defines "remote-reachable" — mis-word ⇒ false-safe verdict. High blast radius. |
| G18 · MG2 | threat-model STRIDE chart + additive-only overrides (TM-D2) | Methodology semantics; loose override rule ⇒ silent-skip gaps. |
| G18 · MG3 | risk-grid forced-TODO vs accepted-with-sign-off (TM-D3) | Security acceptance policy — human-sign-off gating is judgment. |
| G18 · MG4 | mitigation-map VERIFIED/TODO/ACCEPTED discipline (TM-D4) | Evidence-tier judgment. |
| G18 · MG5 | design-review rubric `speculative → drop` (TM-D6/D7) | Judgment boundary; loose ⇒ slop findings. |
| G19 · last MG | kos-portal validation run + fold gotchas back | Live field-test; interprets degrade path, folds learnings. |
| — | **Review-on-return of every delegated task below** | The review half of build-then-review. |

## Opus (fable-mode, solo) — locked spec, real logic/correctness

| Ref | Task | Why |
|---|---|---|
| G10 · MG3 | tiered ast-grep rule pack `rules/{precise,normal,noisy}/` + CWE/reachable tags | **Not built.** Rule correctness + noise-tier judgment; spec locked (deepsec docs cited). |
| G10 · MG4 | wire code-sec SKILL.md phase-0 to consume enumerator + `rules/` | **Not built.** Closes v2 items 2+6 — the consumer is what makes the core "done". |
| G16 | /diagram DFD mode (notation + engine + smoke-render) | Deterministic render spec fully in TM design doc. |
| G12 | bounty-hunter domain-pack seam + `_TEMPLATE.md` | Architecture seam; small judgment on the load signal. |

## Sonnet + Opus-review — mechanical / config / structured-prose / tests

| Ref | Task | Why |
|---|---|---|
| G11 · MG2 | bounty-hunter CVE consume-rank / report shape / handoff-guide (BH-D3/D6/D7) | Structured prose off locked decisions. |
| G13 | `tests/test_bounty_enumerator.py` + `test_bounty_rules.py` (MANIFEST-sourced red-green) | Test-writing = explicit delegate-down category. |
| G14 | `docs/security/README.md` (suite composition + workflow) | Docs prose. |
| G17 · MG1 | `code-sec/templates/SEC-CONTEXT.md` superset schema | Template authoring off a fixed section list. |
| G17 · MG2 | code-sec phase-0 reads `.work/SEC-CONTEXT.md` | Config wiring, verify-gated. |
| G17 · MG3 | git-crypt patterns (`.gitattributes` + /encrypt + dev-setup) + File-Taxonomy rows | Pattern/config mechanics. |
| G15 / G19·MG1 | register `/bounty-hunter` + `/threat-model` aliases; `bash install.sh` exit 0 | Registration + install. |

---

## Recommended run order

1. **Opus:** G10 MG3 (rules) → G10 MG4 (consumer wiring) — unblocks everything.
2. **Fable:** G11 MG1 (gate) — the security-critical spine of bounty-hunter.
3. **Sonnet:** G11 MG2, G12, G13, G14 — flesh out bounty-hunter + tests + docs. Fable reviews.
4. **Sonnet:** G17 (SEC-CONTEXT + git-crypt) — shared dependency for threat-model.
5. **Opus:** G16 (DFD render mode) — threat-model's rendering dependency.
6. **Fable:** G18 (threat-model core, all judgment MGs).
7. **Sonnet:** G15 + G19 register/install; **Fable:** G19 kos-portal validation run.

The memory-arch epic (G4-9) and statusline (G1-3) are complete — only the statusline
`[UX]` live-check remains, and that is a manual you-run-it step, not a delegation.
