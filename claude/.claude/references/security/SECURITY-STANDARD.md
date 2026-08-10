# SECURITY-STANDARD

Write-time security reference — routes by **domain**, the way `CODE-STANDARD.md` routes
by language. Prevention layer: catches a vulnerability while code is being written,
before `code-sec`/`bounty-hunter`/`threat-model`/`code-crit`'s SECURITY persona ever run
against it.

**All 8 sectors live.** `CLIENT-TRUST.md`, `DATA-STORE.md`, `RESOURCE-ACCESS.md` shipped
as the initial 3-sector pilot; `AUTHENTICATION.md`, `AUTHORIZATION.md`, `INJECTION.md`,
`SECRETS.md`, `AI-INTEGRATION.md` followed once the pilot validated
(`.work/findings/security-standard-sectors-pilot.md`). See
`docs/brainstorm/security-standard-architecture-2026-08-01.md` §3 for the full design.

**Rule strength vocabulary:** same RFC 2119 terms as `CODE-STANDARD.md` — MUST/MUST NOT
mandatory, SHOULD/SHOULD NOT recommended (deviate only with a stated reason), AVOID
allowed-but-a-smell.

## Universal MUSTs

These hold everywhere, regardless of sector. Loading the router alone (zero sector
files) covers the common case.

- Never build a string for an interpreter — use the structured/parameterized API.
- Validate at entry, escape at the sink, never in between.
- Authorize at the resource, not the route — a valid session proves identity, not
  permission on a specific record.
- Deny by default — an explicit allow, never an implicit one.
- Secrets come from the environment, never from source.
- Anything shipped to a client is public, including "compiled" bundles and minified JS —
  a secret embedded client-side is disclosed, not hidden.
- Server-side state is authoritative; client-submitted state is a request, not a fact.
- Fail closed on error paths — an exception in an authz/validation check MUST NOT
  default to allow.

## Trigger table

| Sector               | Owns                                                                                                                                                                             | Load when the code…                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `AUTHENTICATION.md`  | Identity, sessions, tokens, password storage, JWT, CSRF                                                                                                                          | verifies identity, or issues/validates a session or token       |
| `AUTHORIZATION.md`   | Object-level access, IDOR/BOLA, privilege escalation, role fields                                                                                                                | decides whether a caller may access a **specific record**       |
| `CLIENT-TRUST.md`    | Prices, quantities, entitlements, subscription state, rate limiting                                                                                                              | accepts a value affecting money, access, or identity            |
| `DATA-STORE.md`      | Declarative authz (RLS, Firestore rules) and object storage scoping — SQL parameterization mechanics belong to `INJECTION.md`; this sector points to it rather than restating it | reads/writes a store, or defines a schema, policy, or migration |
| `INJECTION.md`       | SQL, shell, HTML/XSS, template, XXE, deserialization                                                                                                                             | builds a query, command, markup, or document from a value       |
| `RESOURCE-ACCESS.md` | Path traversal, SSRF, open redirect, file upload, deep links                                                                                                                     | uses a value to select **which** file, URL, or destination      |
| `SECRETS.md`         | Credential lifecycle, client-bundle exposure, log/URL leakage                                                                                                                    | loads a credential, or ships code to a client                   |
| `AI-INTEGRATION.md`  | Model keys, spend caps, role separation, output as untrusted input                                                                                                               | calls a model, or consumes model output                         |

## Budget: two sectors, not one

Security genuinely cross-cuts in a way language does not — one sector is too tight and
will be silently violated. Load at most two per function/route.

**Overflow-flag protocol (MUST):** if three or more sectors trigger for a single
function, that is an SRP finding, not just a budget violation — see `CODE-PRINCIPLES.md`.
Load all triggered sectors anyway; do not block the edit. But the agent MUST state this
explicitly in its response: _"this touches N security sectors, consider splitting."_
Same pattern as an SRP finding surfaced by `/code-crit`. Silently loading 3+ files with no
statement defeats the purpose of the budget — the overflow itself is the signal, and it
only functions as a signal if it's said out loud. This rule is pure prose enforcement
today; no hook checks it yet (a `PreToolUse` pattern-match hook is designed but deferred
to a later pass — see `.work/findings/security-standard-sectors-pilot.md`).

## Reading protocol

Load _only_ this file + the sector file(s) triggered by the trigger table above (at most
two under the budget). Do not load the whole `security/` directory. Same rule as
`CODE-STANDARD.md:117-120`, applied to domain routing instead of language routing.

## Related

- `~/.claude/references/code/CODE-STANDARD.md` — sibling router, routes by language
  instead of security domain; same RFC 2119 vocabulary and Universal-MUSTs-in-the-router
  pattern
- `~/.claude/references/code/CODE-PRINCIPLES.md` — SRP vocabulary the overflow-flag
  protocol cites
- `code-sec` — bottom-up repo sweep; sectors are write-time prevention, `code-sec` is
  after-the-fact detection. Overlap now spans all 8 sectors' worth of phase-5 close-out
  content, not reconciled yet — the phase-5 rewrite (sectors own normative content,
  `code-sec` cites rather than restates, per source doc §8) is filed as its own
  `[SECURITY][CHORE]` TODO (`TODOS.md`), deliberately not done in this build
- `bounty-hunter` — remote-reachability triage; shares the same trust-boundary framing
  ("client-submitted state is a request, not a fact")
- `docs/brainstorm/security-standard-architecture-2026-08-01.md` — full 8-sector
  design, all 8 built
