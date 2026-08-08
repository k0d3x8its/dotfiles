# DATA-STORE

**Invariant:** every store — a table, a document collection, an object bucket — MUST
enforce who may read and write it at the store's own policy layer, not just at the
application layer above it. A policy that exists but permits everything is
indistinguishable from no policy, and the application code that assumes it works has
no way to know.

## MUSTs / SHOULDs

- Row-level security (or the equivalent declarative policy layer — Firestore rules,
  Convex, etc.) MUST be enabled on every table/collection reachable through a public
  API, not opted into selectively.
- A policy MUST NOT be written as `USING (true)` (or an equivalent always-true
  predicate). A policy that permits everything is present but enforces nothing — see
  Guards that don't work.
- Write policies (INSERT/UPDATE) MUST carry their own `WITH CHECK` clause. A `USING`
  clause alone governs what is visible on read; without `WITH CHECK`, a user who can
  see a row can write rows they should not be able to create.
- Junction, audit, and log tables MUST have their own explicit policy. Authorization
  does not inherit from the table they reference — a permissive junction table can
  expose the relationship even when the tables it joins are individually locked down.
- Functions marked `SECURITY DEFINER` in a public schema MUST be reviewed individually
  — they run as their owner, not the caller, which means they bypass RLS by design.
  Every one is a deliberate exception to the invariant above, not an oversight.
- Object/file storage buckets MUST scope access by path per-user (or per-tenant), not
  rely on obscurity of the path or bucket-level-only permissions. Storage is a separate
  authorization domain from the row-level policies on structured data — enforcing one
  does not enforce the other.
- Firestore (and equivalent document-store) subcollections do NOT inherit the parent
  document's rules. Each subcollection MUST carry its own explicit rule.
- Application code MUST still parameterize every query — this sector's declarative-authz
  content is additive to standard SQL injection defense, not a replacement for it
  (`INJECTION.md`, not yet built, owns the injection mechanics).

## Guards that don't work

| Defense as written                                                                                  | Bypass                                                                                                                                      | Why it works                                                                                    | Sound form                                                                                                                                                                               |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RLS policy: `USING (true)`                                                                          | Every row is readable — the policy exists and enforces nothing                                                                              | `true` is a passing predicate for any row, unconditionally                                      | Write the predicate against the actual ownership/tenant column, e.g. `USING (user_id = auth.uid())`                                                                                      |
| RLS enabled with a read (`USING`) policy but no `WITH CHECK` on INSERT/UPDATE                       | A user who can read rows in a table can also write rows they shouldn't be able to create — the write path has no predicate at all           | `WITH CHECK` and `USING` are separate clauses; omitting one leaves that operation unconstrained | Pair every write-capable policy with an explicit `WITH CHECK` matching the same ownership predicate                                                                                      |
| Junction/audit/log table left without its own policy, "because the tables it joins are locked down" | The junction table itself is queryable and exposes the relationship (who is linked to what) even when both sides are individually protected | Policies do not cascade through foreign keys or joins — each table is independently gated       | Write an explicit policy on every table, including junction/audit tables, keyed to the same ownership logic as the tables it relates                                                     |
| Firestore subcollection assumed to inherit the parent document's rule                               | Subcollection is fully open — Firestore rules are not inherited across the parent/subcollection boundary                                    | Firestore's rule model scopes rules per path segment, not per document tree                     | Write an explicit rule for every subcollection path                                                                                                                                      |
| `SECURITY DEFINER` function in the public schema, assumed covered by the table's RLS                | Function runs as its owner and bypasses RLS entirely by Postgres design, regardless of the caller's permissions                             | `SECURITY DEFINER` intentionally elevates privilege for the duration of the call                | Audit every `SECURITY DEFINER` function individually; keep the privileged surface it exposes as narrow as possible, and prefer `SECURITY INVOKER` unless elevation is the explicit point |

## Sink or pattern catalog

No application-code sink exists for the RLS/Firestore-rules/storage-policy findings
above — this is the sector's headline structural finding, not an oversight in this
file. These are misconfigurations in `.sql` migrations, `supabase/` policy files, and
`firestore.rules`, which the current `code-sec` rule pack does not scan (`sgconfig.yml`
globs application-language files only). A `USING (true)` policy or a missing
`WITH CHECK` clause is real, matchable content — pattern-matchable against those file
types specifically — but no rule surface exists yet to run it. Tracked as a
`[SECURITY][FEAT]` TODO (`TODOS.md`, 2026-08-08): a new rule surface over
policy/migration files, plus `enumerate-entrypoints.sh` taught to recognize a
PostgREST-exposed table as an entry point with no code shape. Until that lands, this
sector's guidance is read-and-apply at write time only, with no sweep-time backstop.

Application-code parameterization (the one item in this sector's MUSTs that _is_
application-code) already has a sink catalog — see
`~/.claude/references/security/INJECTION.md` _(not yet built)_ and the existing SQLi
rules in `code-sec/rules/`.

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under
- `~/.claude/references/security/CLIENT-TRUST.md` — a rate-limit counter stored in a
  client-writable table is this sector's `USING (true)` failure viewed from the
  trust-boundary side rather than the policy side; same underlying bug, two sectors
- `~/.claude/references/security/RESOURCE-ACCESS.md` _(sibling, this pilot)_ — storage
  bucket path scoping here is about who may read/write a bucket; path traversal in
  `RESOURCE-ACCESS.md` is about which file a value selects. Related but distinct
  failure modes — this file's storage-bucket MUST assumes `RESOURCE-ACCESS.md`'s path
  canonicalization already happened
- `~/.claude/references/security/INJECTION.md` _(not yet built)_ — owns SQL injection
  mechanics; this file's parameterization MUST is a pointer, not a restatement
- `code-sec` — its rule pack does not currently scan policy/migration files; this
  sector documents guidance with no sweep-time detection until the tracked TODO lands

## Sources

- PostgreSQL row security policy documentation; Supabase RLS documentation
- Firebase/Firestore Security Rules documentation
- OWASP Top 10 (2021) — A01 Broken Access Control; OWASP ASVS 4.0 — access control and
  data protection sections
