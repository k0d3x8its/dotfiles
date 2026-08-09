# CLIENT-TRUST

**Invariant:** anything the client submits — a price, a quantity, an entitlement claim,
a subscription status — is a request, not a fact. The server MUST re-derive or verify it
against its own state before acting.

## MUSTs / SHOULDs

- Prices and Stripe/payment-provider amounts MUST be looked up server-side by a stable
  identifier (a Stripe Price ID, a catalog SKU) — never trust `req.body.price` or any
  client-submitted amount.
- Quantities MUST be validated for sign and bounds server-side. A well-formed positive
  integer is not sufficient — `-1` is well-formed and can credit an account if the only
  check is "is this an integer."
- Webhook payloads (Stripe, and equivalents) MUST have their signature verified before
  the body is trusted or acted on.
- The raw request body MUST survive to the signature-verification call unparsed. A
  correct-looking signature-verify call still fails silently-wrong if JSON parsing ran
  first. Concretely: `express.raw()` MUST run before `express.json()` on the webhook
  route (Express); `request.text()`, not `request.json()`, in Next.js App Router
  handlers.
- Subscription/entitlement status MUST be read from the database, synced by the
  webhook — never from a JWT claim or cached session value. A claim issued at login time
  does not reflect a cancellation that happened five minutes later.
- Checkout session metadata (plan, quantity, user ID) that influences what a payment
  grants MUST be set and re-read server-side, never trusted from client-supplied
  session-creation parameters — client-controlled metadata is an escalation vector.
- Rate limiting MUST be justified by exploitability, not applied generically. Endpoints
  that spend money, verify credentials, or trigger a third-party call (LLM, email, SMS)
  MUST be rate-limited; a bare "consider rate limiting" with no such endpoint named is
  architecture feedback, not a finding (this narrows `code-sec`'s existing suppress
  clause — see Related).
- Rate-limit counters MUST live somewhere the request's own caller cannot write to
  directly. A counter in a table reachable through the same REST API the request uses
  is not a limit — it is a value the attacker can reset.
- Rate limiting keyed on IP address alone MUST be treated as bypassable, not sufficient
  — rotating IPs (trivially available via VPN/botnet) defeats it. Prefer a
  server-controlled identity, not the caller-supplied network origin, as the primary
  limiting key.

## Guards that don't work

| Defense as written                                                                                                                                      | Bypass                                                                                                                                            | Why it works                                                                                                 | Sound form                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Rate-limit counter stored in a user-writable table (e.g. a public Supabase table with permissive RLS, or any row the caller's own API access can reach) | Caller resets or overwrites their own counter through the same API                                                                                | The "limit" and the data it depends on are both inside the trust boundary the limit is supposed to constrain | Store counters server-side only (in-memory store, or a table with no client-reachable write path)                                |
| Rate limiting keyed only on IP address                                                                                                                  | Attacker rotates IP via VPN or botnet                                                                                                             | IP is caller-supplied network origin, not identity                                                           | Key on an authenticated identity or a harder-to-rotate signal; treat IP-only as a secondary signal, not the limit itself         |
| Subscription check reads `status` from a JWT claim                                                                                                      | Claim is stale the moment the subscription is cancelled — token isn't revoked until it expires                                                    | Client holds a token asserting a fact that may no longer be true                                             | Read subscription status from the database on each check; webhook keeps the DB row current                                       |
| Checkout session metadata (plan/qty) trusted from the client-initiated session-creation call                                                            | Attacker crafts the session-creation request with escalated metadata                                                                              | Metadata set at session creation is client-influenced input, not server fact                                 | Server sets metadata itself, from server-known state, at session creation                                                        |
| Webhook `constructEvent()`/signature-verify call looks correct                                                                                          | Route already ran `express.json()` (or `request.json()` in Next.js) before the signature check, mutating the body the signature was computed over | Signature verification needs the exact raw bytes; a re-serialized body no longer matches                     | Route the raw body to the verify call untouched — `express.raw()` before `express.json()`; `request.text()` not `request.json()` |

## Sink or pattern catalog

- Webhook signature verification: `constructEvent(...)` call (Stripe SDK) — presence
  and correct body-raw-ness are ast-grep matchable (checks presence/absence of the
  call, not the body-parsing order, which needs route-shape awareness).
- Client-submitted price/quantity: any handler reading `req.body.price`,
  `req.body.amount`, or an unvalidated `req.body.quantity` that flows into a
  payment-provider call or a DB write affecting stock/credit — matchable as a
  taint-from-request-body-to-money-sink pattern.
- No sink exists yet for "subscription status read from JWT claim instead of DB" or
  "rate-limit counter reachable through a client-writable path" — these require
  cross-referencing a read site against a schema/policy definition, not a single-file
  pattern match. Tracked in the detection-surface gap TODO (`TODOS.md`, 2026-08-08).

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under
- `~/.claude/references/security/DATA-STORE.md` — where a rate-limit counter's storage
  location (a table with permissive RLS) is actually enforced or not; this file's
  "counter reachable through client API" bypass row and `DATA-STORE.md`'s `USING (true)`
  finding are the same failure class from two angles
- `~/.claude/references/security/AUTHENTICATION.md` — CSRF and session concerns live
  there, not here, even though both sectors touch trust boundaries (see that file's
  ownership note under §9.4)
- `code-sec` — its Finding discipline currently suppresses generic rate-limiting advice;
  this file's exploitability framing is the intended narrowing of that suppress clause,
  not yet wired into `code-sec` itself (phase-5 rewrite tracked as its own TODO, see
  `SECURITY-STANDARD.md`'s Related)

## Sources

- Stripe webhook signature verification documentation
- OWASP Top 10 (2021), OWASP ASVS 4.0 — business logic / trust boundary sections
