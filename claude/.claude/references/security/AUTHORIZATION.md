# AUTHORIZATION

**Invariant:** proving who is asking (`AUTHENTICATION.md`) is a separate question from
whether that specific caller may act on this specific record. A valid session MUST NOT
be treated as sufficient — every access to an object-level resource MUST re-check
ownership or role against that record, not against the fact that a session exists.

## MUSTs / SHOULDs

- Every handler that reads or writes a specific record by ID MUST check that the
  authenticated caller owns or is permitted to access that exact record — a valid
  session proves identity, not permission on the record being requested (IDOR/BOLA).
- Object-level checks MUST run on every method that touches the record (read, update,
  delete), not only the one a developer thought to protect. A route that checks
  ownership on `GET` but not `DELETE` for the same resource is unprotected on `DELETE`.
- Fields that carry privilege — `role`, `isAdmin`, `permissions`, a plan tier — MUST be
  excluded from mass-assignment paths (`Object.assign(model, req.body)` or equivalent).
  Client-submitted request bodies MUST be allowlisted to the fields a caller is
  permitted to set, never passed through wholesale.
- GraphQL field-level authorization MUST be checked per-field/per-resolver, not only at
  the query root. A query-level check that gates _whether the request runs at all_
  does not gate _which fields the resolver is allowed to return or accept_ once it
  does.
- Role/permission checks MUST be re-evaluated server-side on every request, not cached
  from a prior check — a role that changed since the last check (demotion, revocation)
  must take effect immediately, not on next login.

## Guards that don't work

| Defense as written                                                                        | Bypass                                                                                                                         | Why it works                                                                           | Sound form                                                                                             |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `GET /orders/:id` checks `order.userId === session.userId`, `DELETE /orders/:id` does not | Attacker who owns no orders sends `DELETE /orders/<victim's id>` and it succeeds — the check was never written for that method | Ownership was verified once for one method and assumed to cover the resource generally | Re-run the same ownership check on every method that touches the resource, not just the one audited    |
| `Object.assign(user, req.body); await user.save()`                                        | Attacker includes `"role": "admin"` in the request body; it is assigned along with legitimate fields                           | Mass assignment copies every key present in the client payload, privileged or not      | Allowlist the specific fields a caller may set; never pass a client body directly into a model save    |
| GraphQL query-level auth check passes, resolver returns full object                       | A field like `internalNotes` or `costPrice` has no field-level check and is returned to any authenticated caller               | The query-level gate answers "may this request run," not "which fields may it see"     | Add per-field or per-resolver authorization for any field that is not uniformly visible to all callers |
| Role checked once at request start, cached for the request's remaining handlers           | A role revoked mid-session (demotion, ban) still passes checks that read the cached value instead of current state             | The cached value reflects the role at the moment it was read, not the moment it's used | Re-read current role/permission state at each authorization decision point, not once per request       |

## Sink or pattern catalog

- IDOR/BOLA: `res.json($OBJ[$KEY])`, a Python owner-check omitted before a
  record-by-ID lookup, or equivalent record-access-without-ownership-check shapes —
  already covered by existing rules in `code-sec/rules/` (Python and JavaScript
  execute; other languages are model-only per `bounty-hunter`'s stated scope).
- Mass assignment: `Object.assign($MODEL, req.body)` or equivalent
  spread-request-body-into-model shapes — two-line ast-grep matchable, not currently
  in `code-sec/rules/`.
- GraphQL field-level authz gaps require cross-referencing a schema's resolver map
  against which fields carry a check — not a single-call pattern match; no sink exists
  yet. Tracked in the detection-surface gap TODO (`TODOS.md`, 2026-08-08).

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under
- `~/.claude/references/security/AUTHENTICATION.md` — sibling split: that file answers
  "is this a real, current session," this file answers "may this session touch this
  specific record." Conflating the two is the most common root cause of IDOR in
  production — the two files are separate for exactly this reason (source doc §3.1)
- `~/.claude/references/security/DATA-STORE.md` — declarative authz (RLS, Firestore
  rules) enforces an equivalent object-level check at the store's own policy layer;
  this file covers the same invariant enforced in application code instead
- `code-sec` — IDOR/BOLA already has rule coverage (Python/JS); mass assignment and
  GraphQL field-level gaps do not yet

## Sources

- OWASP Top 10 (2021) — A01 Broken Access Control
- OWASP API Security Top 10 — BOLA (API1), broken function-level authorization (API5)
- MITRE CWE-639 (authorization bypass through user-controlled key), CWE-915 (improperly
  controlled modification of dynamically-determined object attributes)
