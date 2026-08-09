# AUTHENTICATION

**Invariant:** a session or token proves _who is asking_, nothing more. Verifying a
signature is not optional, decoding is not verifying, and a valid identity in one
request does not carry forward past the point a login state legitimately changed.

## MUSTs / SHOULDs

- A JWT (or equivalent signed token) MUST be verified with the library's verify call,
  not decoded and trusted. Decoding reads the payload without checking the signature —
  a forged token decodes to whatever claims the forger wrote.
- Token verification MUST reject `alg: none` and MUST pin the expected algorithm
  server-side rather than trusting an `alg` header the token itself supplies — an
  attacker who controls the algorithm choice can downgrade to unsigned or to a
  symmetric algorithm verified with a public key as the secret.
- Token verification MUST check `exp` (expiry) and, where the issuer is not
  self-evident from context, `aud`/`iss` — a token that never expires or that was
  issued for a different audience is not proof of the claim being relied on.
- Session identifiers MUST be rotated on login (and on any privilege change). A session
  ID issued before authentication and reused after it is fixation-vulnerable — an
  attacker who plants a pre-auth session ID in a victim's browser inherits it once the
  victim logs in.
- CSRF-protected state-changing routes MUST validate the token on every method that
  changes state, not only `POST` — a route reachable by `GET` with the same
  side-effect is unprotected regardless of what the `POST` handler checks.
- **CSRF ownership note:** filed here, not `CLIENT-TRUST.md`, because it is a
  session-riding attack — the exploit rides an authenticated session's cookies, the
  same trust unit this sector already owns. `CLIENT-TRUST.md` covers what a client
  _submits_ being untrustworthy; CSRF is about a request the victim didn't submit at
  all. Recorded once, here, so this does not get relitigated per source doc §9.4.
- On mobile, tokens/credentials MUST be stored in the platform's secure storage
  (`expo-secure-store`, `react-native-keychain` — backed by iOS Secure Enclave /
  Android Strongbox), never in `AsyncStorage`, which is plaintext on disk.
- Biometric authentication MUST gate a cryptographic operation (unlocking a stored key,
  signing a challenge), not merely branch on a boolean "did biometric check pass" —
  a boolean check can be bypassed by any code path that skips the call.

## Guards that don't work

| Defense as written                                                         | Bypass                                                                                                         | Why it works                                                                                     | Sound form                                                                                                 |
| -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| `const user = jwt.decode(token); if (user.role === "admin")`               | Attacker crafts any token payload — `decode()` never checks the signature                                      | `decode` and `verify` are different calls; `decode` reads the payload structure only             | Use the library's `verify()`/`verifyAsync()` call with the expected algorithm and secret/public key pinned |
| CSRF token checked on the `POST` handler for a state-changing action       | The same action is also reachable via a `GET` route (e.g. a legacy or convenience endpoint) with no check      | The guard exists on one method, not on the action itself                                         | Validate CSRF on every method that changes state, or remove the state-changing `GET` route entirely        |
| Session ID issued at first page load, reused unchanged after login         | Attacker plants a known session ID (via URL, cookie, or subdomain) before the victim authenticates             | The session identifier is the same value before and after the trust level changed                | Issue a new session ID at the moment of successful authentication; invalidate the pre-auth one             |
| Token accepted with no `alg` pinned server-side, verified per token header | Attacker sets `alg: none` or `alg: HS256` (symmetric) while the server holds an RSA public key as "the secret" | The verify call trusts the token to declare its own algorithm instead of the server declaring it | Pin the expected algorithm and key server-side; never read `alg` from the token to decide how to verify it |

## Sink or pattern catalog

- JWT decode-without-verify: a `jwt.decode(...)` (or equivalent) call whose result
  flows into an authorization decision with no adjacent `jwt.verify(...)` call on the
  same token — two-line ast-grep matchable, not currently in `code-sec/rules/`.
- CSRF method-coverage gap requires cross-referencing which HTTP methods a route
  registers against which of those methods run the CSRF check — not a single-call
  pattern match; no sink exists yet.
- Session fixation (no rotation call adjacent to a login success path) and mobile
  `AsyncStorage.setItem` used for a token/credential value are both plain
  shape-matchable but not yet in the rule pack — tracked in the detection-surface gap
  TODO (`TODOS.md`, 2026-08-08) alongside this sector's siblings.

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under
- `~/.claude/references/security/AUTHORIZATION.md` — sibling split: this file answers
  "is this a real, current session," `AUTHORIZATION.md` answers "may this session
  touch this specific record." A route that only checks one is incomplete regardless
  of which
- `~/.claude/references/security/CLIENT-TRUST.md` — CSRF is filed here instead, per
  the ownership note above; rate limiting on auth endpoints (credential stuffing,
  enumeration) is `CLIENT-TRUST.md`'s exploitability-first framing, not restated here
- `~/.claude/references/security/SECRETS.md` — mobile secure-storage guidance here
  covers _where a token is stored on-device_; `SECRETS.md` covers a credential
  extractable from the _app bundle itself_ — different surfaces, same platform
- `code-sec` — no current rule coverage for JWT decode-vs-verify, session fixation, or
  mobile insecure storage; tracked in the detection-surface gap TODO

## Sources

- OWASP Top 10 (2021) — A07 Identification and Authentication Failures
- OWASP ASVS 4.0 — session management and authentication sections
- OWASP Mobile Top 10 — insecure data storage
- MITRE CWE-287 (improper authentication), CWE-384 (session fixation), CWE-352 (CSRF)
- Expo SecureStore / react-native-keychain documentation
