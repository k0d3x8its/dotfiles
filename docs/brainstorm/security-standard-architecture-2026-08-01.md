# SECURITY-STANDARD.md — Architecture Proposal

**Date:** 2026-08-01
**Status:** Design discussion. Not implemented, not planned in detail.
**Origin:** User proposal — a security router paralleling `CODE-STANDARD.md`, routing to
vulnerability *sector* files the way the code router routes to *language* files.

**Supersedes** two recommendations in `vibesec-mining-findings.md`:
- the flat `references/code/SECURITY.md` (§3 Gap 1) → replaced by router + sectors
- the standalone `BYPASS-CATALOG.md` (§3 Gap 2) → replaced by a per-sector section

**Companion docs:** `vibesec-mining-findings.md`, `vibe-security-skill-mining-findings.md`

---

## 1. The proposal

```
claude/.claude/references/
├── code/                       (existing — routes by LANGUAGE)
│   ├── CODE-STANDARD.md        router + universal MUSTs + delegation table
│   ├── PYTHON.md · TYPESCRIPT.md · …
└── security/                   (new — routes by DOMAIN)
    ├── SECURITY-STANDARD.md    router + universal MUSTs + trigger table
    ├── AUTHENTICATION.md · AUTHORIZATION.md · DATA-STORE.md
    ├── INJECTION.md · RESOURCE-ACCESS.md · SECRETS.md
    └── CLIENT-TRUST.md · AI-INTEGRATION.md
```

Why this beats a single flat security reference:

- **Reuses a proven pattern.** Anyone who understands `CODE-STANDARD.md` understands this
  on sight. Zero new architecture to learn.
- **Scales.** A flat file grows unbounded as coverage expands; sectors don't.
- **Gives the mined content a home.** Every item from both repo reviews lands in exactly
  one sector (see §7). That mapping is the main evidence the decomposition is sound.
- **Closes the write-time gap** — the one gap both reviews independently identified, and
  the only one no existing skill addresses.

---

## 2. The design problem to solve first

`CODE-STANDARD.md` routes on an unambiguous observable fact: what language is this file?
One answer, determined by extension. That is why its protocol can safely say *"load only
this file + the one language file."*

**Security domains do not partition that way.** A login endpoint that queries a database
and sets a cookie is Authentication *and* Data-store *and* Authorization. Three files, and
the two-file budget the protocol exists to protect is gone.

Three fixes, all three needed:

### 2.1 Universals live in the router

`CODE-STANDARD.md` already carries a "Universal MUSTs" section — same precedent applies.
Most of the value sits in roughly ten invariants that hold everywhere:

- Never build a string for an interpreter — use the structured API
- Validate at entry, escape at the sink, never in between
- Authorize at the resource, not the route
- Deny by default
- Secrets come from the environment, never from source
- Anything shipped to a client is public, including "compiled" bundles
- Server-side state is authoritative; client-submitted state is a request, not a fact
- Fail closed on error paths

With these in the router, **the common case loads zero sector files.**

### 2.2 Budget of two sectors, not one

Security genuinely cross-cuts in a way language does not. One is too tight and will be
silently violated; two is honest.

### 2.3 Make overflow a signal, not just a limit

If more than two sectors trigger for a single function, that is evidence the function is
doing too much — an SRP finding, for which `CODE-PRINCIPLES.md` already has vocabulary.
The constraint becomes diagnostic rather than merely restrictive.

---

## 3. Proposed sectors

| Sector | Owns | Load when the code… |
|---|---|---|
| `AUTHENTICATION.md` | Identity, sessions, tokens, password storage, JWT, CSRF | verifies identity, or issues/validates a session or token |
| `AUTHORIZATION.md` | Object-level access, IDOR/BOLA, privilege escalation, role fields | decides whether a caller may access a **specific record** |
| `DATA-STORE.md` | Parameterization **and declarative authz** (RLS, Firestore rules), object storage | reads/writes a store, or defines a schema, policy, or migration |
| `INJECTION.md` | SQL, shell, HTML/XSS, template, XXE, deserialization | builds a query, command, markup, or document from a value |
| `RESOURCE-ACCESS.md` | Path traversal, SSRF, open redirect, file upload, deep links | uses a value to select **which** file, URL, or destination |
| `SECRETS.md` | Credential lifecycle, client-bundle exposure, log/URL leakage | loads a credential, or ships code to a client |
| `CLIENT-TRUST.md` | Prices, quantities, entitlements, subscription state, rate limiting | accepts a value affecting money, access, or identity |
| `AI-INTEGRATION.md` | Model keys, spend caps, role separation, output as untrusted input | calls a model, or consumes model output |

### 3.1 Two splits worth defending

**Authentication and Authorization must be separate files.** Conflating them is precisely
why IDOR is the most common serious bug in production — "the user is logged in" gets
mistaken for "the user may have this record." `bounty-hunter` already treats
`authenticated-any-user` as its own auth tier for exactly this reason. The file structure
should encode that separation rather than fight it.

**Injection and Resource-access are different failure modes.**

| | Injection | Resource-access |
|---|---|---|
| Failure | Attacker data reaches an **interpreter** | Attacker data selects the **target** |
| Fix | Structured API; never string-build | Allowlist + canonicalize *before* checking |
| Example | `f"SELECT … {id}"` | `open("/data/" + name)` |

Merging them yields a file that contradicts itself about what "sanitize" means.

### 3.2 Deliberately excluded

- **Mobile** — a platform, not a domain. Its content decomposes cleanly: bundle
  extraction → `SECRETS.md`; keychain vs. AsyncStorage → `AUTHENTICATION.md`; deep links
  → `RESOURCE-ACCESS.md`. Platform-specific idiom already belongs in `SWIFT.md` and peers.
- **Deployment / headers / TLS / CORS** — config-time, not write-time. Belongs to the
  audit skills (`code-sec` already checks deployment surface). Revisit only if it proves
  to be written in code often enough to matter.

---

## 4. Standard shape for a sector file

Language files are consistent (Naming → Rules → File layout → Tooling), which is what
makes them fast to read. Sectors need the same discipline:

1. **Invariant** — the one-sentence rule the whole sector serves
2. **MUSTs / SHOULDs** — RFC 2119 voice, matching `CODE-STANDARD.md`
3. **Guards that don't work** — bypass rows (see §5)
4. **Sink or pattern catalog** — where the sector has one
5. **Related** — sibling sectors + which audit skill owns the runtime check
6. **Sources** — primaries, per the convention in `CODE-REFERENCE.md`

---

## 5. Correction: the bypass catalog is per-sector

`vibesec-mining-findings.md` proposed a standalone `BYPASS-CATALOG.md`. **Under this
architecture that is wrong.** Each sector carries its own **"Guards that don't work"**
section:

| Sector | Example rows |
|---|---|
| `RESOURCE-ACCESS.md` | `startswith()` allowlist; octal/decimal IP encodings; extension-only upload check; `basename` without canonicalization |
| `DATA-STORE.md` | `USING (true)` policy; RLS enabled but no `WITH CHECK`; subcollection assumed to inherit |
| `CLIENT-TRUST.md` | Rate-limit counter in a user-writable table; IP-only limiting; subscription state read from a JWT claim |
| `AUTHENTICATION.md` | `jwt.decode()` mistaken for verify; CSRF token checked on POST while GET is accepted |

Rows sit beside the guidance they qualify, write-time and audit-time read one source, and
there is no second file to drift. Four columns as previously specified:
`Defense as written | Bypass | Why it works | Sound form`.

---

## 6. Enforcement — the part that decides whether this works at all

Gap 1 was rated *speculative* because it depends on the model self-assessing "does this
code touch untrusted input?" A `CLAUDE.md` line alone will not achieve that reliably.

**Hook infrastructure already exists** — `claude/.claude/hooks/` and
`codex/.codex/hooks.json`. A `PreToolUse` hook on Write/Edit can pattern-match pending
content and inject the sector reminder deterministically.

**Treat the hook as part of the design, not a later enhancement.** Without it this is a
reference nobody loads, and the gap stays open while looking closed — which is worse than
not building it.

Wiring also required:
- `references/security/SECURITY-STANDARD.md` — new router
- `claude/.claude/CLAUDE.md` — reading-protocol line (`:19`) and routing table (`:97`)
- `codex/.codex/AGENTS.md` — file list, **plus a new symlink**: `:27` symlinks
  `~/.codex/references/code/` specifically, so a peer `references/security/` directory is
  invisible to codex until explicitly linked.

---

## 7. Where mined content lands

This mapping is the main validation of the decomposition — every item from both reviews
has exactly one home, and every sector receives content. A sector with nothing to hold
would be a sign it was invented rather than derived.

| Mined item | Source | Sector |
|---|---|---|
| JWT `alg:none`, decode≠verify, missing `exp`/`aud` | VibeSec | `AUTHENTICATION.md` |
| CSRF (token placement, SameSite, GET-accepted routes) | VibeSec | `AUTHENTICATION.md` |
| Session fixation, rotation on login | VibeSec | `AUTHENTICATION.md` |
| AsyncStorage vs. keychain / SecureStore | vibe-security | `AUTHENTICATION.md` |
| Mass assignment of `role` | both | `AUTHORIZATION.md` |
| GraphQL field-level authz | VibeSec | `AUTHORIZATION.md` |
| Supabase RLS, `USING (true)`, `WITH CHECK` | vibe-security | `DATA-STORE.md` |
| Firestore rules, subcollection non-inheritance | vibe-security | `DATA-STORE.md` |
| `SECURITY DEFINER` in public schema | vibe-security | `DATA-STORE.md` |
| Storage bucket path scoping | vibe-security | `DATA-STORE.md` |
| XXE parser configuration | VibeSec | `INJECTION.md` |
| SQLi / command injection / XSS / deserialization | existing + VibeSec | `INJECTION.md` |
| Open redirect + `startswith` bypass | VibeSec | `RESOURCE-ACCESS.md` |
| SSRF IP encodings, DNS rebinding, cloud metadata | VibeSec | `RESOURCE-ACCESS.md` |
| File upload — magic bytes vs. extension | VibeSec | `RESOURCE-ACCESS.md` |
| Deep links as an entry point | vibe-security | `RESOURCE-ACCESS.md` |
| JS bundle extraction, `EXPO_PUBLIC_`/`NEXT_PUBLIC_` | vibe-security | `SECRETS.md` |
| Secrets in logs, error output, URLs | existing | `SECRETS.md` |
| Client-submitted price; Stripe Price ID lookup | vibe-security | `CLIENT-TRUST.md` |
| Webhook signature + raw-body gotcha | vibe-security | `CLIENT-TRUST.md` |
| Subscription status from stale claim | vibe-security | `CLIENT-TRUST.md` |
| Rate limiting anchored to exploitability | vibe-security | `CLIENT-TRUST.md` |
| Negative quantity / price tampering | VibeSec | `CLIENT-TRUST.md` |
| LLM keys, spend caps, role separation, output trust | vibe-security | `AI-INTEGRATION.md` |

All eight sectors populated; no item unhoused.

---

## 8. Risk: drift against the audit skills

`code-sec` phase 5 already carries a close-out checklist covering inputs, SQLi, XSS,
authz, sessions, CSRF, SSRF, and headers. That overlaps four sectors. **If both exist
independently they will drift**, and then the write-time reference and the audit skill
disagree about the rule.

**Resolution:** sectors own the normative content; audit skills *cite* rather than
restate. This means editing `code-sec` phase 5 to point at sectors instead of listing
items — a real change to an existing skill, and part of the honest cost of doing this
properly, not an afterthought.

Upside once done: sectors become **shared vocabulary** across write-time and audit-time. A
`code-sec` finding can cite `INJECTION.md §SQL`; the `code-crit` SECURITY persona can
check a diff against the same rows; `bounty-hunter` can reference the same bypass tables it
uses to reject a guard.

---

## 9. Open questions

1. **Does the hook fire accurately enough?** If pattern-matching pending content produces
   constant false triggers, the reminder becomes noise and gets ignored. Worth prototyping
   on one sector before writing all eight.
2. **Eight sectors or fewer to start?** `CLIENT-TRUST.md`, `DATA-STORE.md`, and
   `RESOURCE-ACCESS.md` hold the highest-value and least-covered material. A three-sector
   pilot would test the architecture at a third of the cost.
3. **Does the two-sector budget hold in practice?** Worth checking against real recent
   diffs before committing to it as protocol.
4. **Sector ownership of CSRF** — placed in `AUTHENTICATION.md` here because it is a
   session-riding attack, but it is arguably `CLIENT-TRUST.md`. Low stakes; note the
   decision wherever it lands so it does not get relitigated.
