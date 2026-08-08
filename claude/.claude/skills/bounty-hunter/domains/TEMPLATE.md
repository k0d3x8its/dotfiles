# Domain pack: <domain-name>

<!--
  TEMPLATE — copy to domains/<domain>.md and fill. TEMPLATE.md itself is NEVER
  loaded at runtime: its `applies when` matches nothing by construction. One pack
  per abuse domain (game-abuse, web-business-logic, …). A pack is the REASONING
  half; the matching rules/<domain>/ is the DETERMINISTIC ast-grep half — build
  both under the same <domain> key. Packs load ON DEMAND (see SKILL.md "Domain
  packs — on-demand abuse lenses"), so keep the always-on core lean and put every
  domain-specific abuse idea HERE, never in SKILL.md.

  Fill packs EMPIRICALLY — after a real sweep of a codebase in this domain, not up
  front. The first real game-abuse.md comes out of an actual game sweep.
-->

## applies when

The load signal. bounty-hunter reads THIS header to decide whether to pull the pack,
so state concrete, checkable signals against what Phase 0 already produced — never
vibes. Any ONE match proposes the pack; the user confirms in the Phase-0 checkpoint,
so a false match costs one keystroke, not a silent wrong lens.

- **Dependencies** (from the lockfile / import graph): e.g. `socket.io` + an
  authoritative game-state module; `stripe`/`braintree` + `cart`/`order` models.
- **Entry-point kinds** (from the enumerator output): e.g. WS handlers that mutate
  shared server state; checkout / refund / coupon / balance routes.
- **File or directory signals**: e.g. `game/`, `economy/`, `matchmaking/`, `billing/`.

If none match, the pack stays unloaded — that is the intended default, not a miss.

## Abuse families

The domain-specific abuse classes the general CWE pack does NOT capture. Each is a
reachability-first lens — what an external actor makes the system do wrong — not a
generic sink. Keep every entry tied back to a Phase-0 auth tier so the reachability
gate still governs.

### <abuse-family-1 — e.g. state tampering>

- **What:** the invariant an attacker breaks (e.g. client asserts its own position/
  score/inventory and the server trusts it).
- **Reachable when:** the external path that reaches it — which auth tier, which
  entry-point kind (e.g. any authenticated player over the WS surface).
- **Look for:** the code shape; point at `rules/<domain>/` for the deterministic
  matcher that flags it structurally.

### <abuse-family-2 — e.g. economy / resource duplication>

- **What:** …
- **Reachable when:** …
- **Look for:** …

## Reachability notes

How this domain bends the core gate. New trust tiers (a peer client in P2P is
untrusted, not same-tier), new "external" surfaces, or state that persists across
requests and so widens what a single reachable call can affect. Anything that changes
what "an external attacker can reach" for this domain relative to the core three tiers.

## Deterministic half

Rules live in `rules/<domain>/` under the same `<domain>` key, tiered
`precise`/`normal`/`noisy` like the core pack, each tagged with its CWE (or a domain
abuse-ID where no CWE fits) + a `reachable` flag. This markdown reasons about the
domain; those rules match it. The pack and its rules ship together or not at all.
