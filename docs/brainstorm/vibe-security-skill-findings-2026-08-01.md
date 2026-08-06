# Mining `raroque/vibe-security-skill` — Findings

**Date:** 2026-08-01
**Subject repo:** `raroque/vibe-security-skill` (MIT, 905 stars, 4 commits, by Chris Raroque / Aloa)
**Compared against:** `k0d3x8its/dotfiles` branch `chore/code-quality-refs` (`d433600`)
**Companion doc:** `vibesec-mining-findings.md` (the `BehiSecc/VibeSec-Skill` review)
**Status:** Discussion notes. No implementation planned or performed.

---

## 1. What it is, and why it's a different case from VibeSec

```
vibe-security-skill/
├── vibe-security/
│   ├── SKILL.md              (~2,800 words)
│   ├── agents/openai.yaml
│   └── references/
│       ├── secrets-and-env.md      ├── payments.md
│       ├── database-security.md    ├── mobile.md
│       ├── authentication.md       ├── ai-integration.md
│       ├── rate-limiting.md        ├── deployment.md
│       └── data-access.md
├── CONTRIBUTING.md · LICENSE · README.md · .gitignore
```

**This one is architecturally aligned with your suite**, unlike VibeSec's 8,500-word
monolith. It independently arrived at several of your conventions:

- Progressive disclosure — thin `SKILL.md` + `references/` loaded on demand
- **Conditional loading gated on detected technology** ("skip Supabase RLS checks if the
  project doesn't use Supabase") — structurally the same idea as `bounty-hunter`'s
  `applies when` domain-pack load signal
- Severity tiers (Critical → High → Medium → Low)
- Findings prioritized by exploitability
- "Never trust the client" as the stated organizing principle

**But it has no deterministic layer at all.** No ast-grep rules, no scripts, no fixtures,
no entry-point enumerator. It is entirely prose plus one packaging YAML. Your `rules/`
pack, `fixtures/vuln-app/`, and `bin/enumerate-entrypoints.sh` are exactly what it lacks.

**So: it is a reasoning-layer donor only.** Anything mined has to have your deterministic
half built for it.

### Novelty profile vs VibeSec

| | VibeSec | vibe-security-skill |
|---|---|---|
| Content type | Generic web CWE taxonomy (OWASP restated) | Modern BaaS/SaaS stack specifics |
| Overlap with your existing rules | High — you already cover most of it | **Low** |
| Rot rate | Low (CWEs are stable) | **High** (vendor-coupled: Stripe, Expo, Supabase APIs) |
| Best single asset | Bypass tables | **The BaaS authz blind spot** (§3.1) |
| Deterministic layer | None | None |

They are complementary, not redundant. VibeSec fills gaps in *vulnerability class
coverage*; this one fills gaps in *architectural assumptions*.

---

## 2. The headline finding

**Your entire authorization model assumes authz is enforced in application code.**

Your IDOR/authz rules match application-code shapes — `res.json($OBJ[$KEY])`, Python owner
checks, route guards. When authorization instead lives in **SQL policies or a
Firestore rules file**, your rule pack sees nothing, because there is no application-code
sink to match.

A Supabase app with zero RLS policies — every table world-readable through the public REST
API — **looks clean to `code-sec` today.** Not a missed rule: a missing *surface*.
`enumerate-entrypoints.sh` parses py/js/ts/go/lua/solidity route and listener shapes; a
Supabase table exposed via PostgREST is an entry point with no code shape at all.

This is also the fastest-growing way applications are being built, which is why a
"vibe-coded app" skill hit it first.

---

## 3. What is genuinely mineable

### 3.1 BaaS / declarative authorization — the structural gap

Their `database-security.md` (~2,000 words) covers Supabase RLS, Firebase Security Rules,
and Convex. The specific checks worth taking:

| Check | Why it matters |
|---|---|
| Tables with RLS not enabled | Whole table readable via the public REST API |
| Policies using `USING (true)` | Policy exists, enforces nothing — a **bypassable guard** |
| Missing `WITH CHECK` on INSERT/UPDATE | Privilege escalation — user writes rows they couldn't read |
| Junction / audit / log tables without their own policies | Authz assumed to inherit; it doesn't |
| `SECURITY DEFINER` functions in a public schema | Runs as owner, bypasses RLS by design |
| Storage buckets without path-based per-user access | Object storage is a separate authz domain |
| Firestore subcollections | Do **not** inherit parent rules; need explicit rules |
| Custom claims vs. queryable user docs | Immutable claim beats a mutable lookup |

**Several of these are deterministically matchable** — but against `.sql` migrations,
`supabase/` policy files, and `firestore.rules`, not application code. That is a new rule
*surface* for the pack, not just new rules. `sgconfig.yml` currently globs three tier dirs
over app-language files only.

Note the `USING (true)` case is a textbook instance of the **Gap 2 bypassable-guard
pattern** from the VibeSec review: a control that is present, looks enforced, and does
nothing. It would be suppressed as "already protected" today.

### 3.2 Payments / commerce — better `domains/` pack material than VibeSec offered

Last review flagged a tension: `bounty-hunter/domains/TEMPLATE.md` requires packs be filled
**empirically, after a real sweep** — and VibeSec's content was README-derived. This
repo's payments content is closer to field-derived (an agency's accumulated client work)
and, more importantly, **already has the abuse-family shape your template asks for**:

- **Client-submitted price trusted.** `req.body.price` flows into Stripe. Server must look
  up by Stripe Price ID. (The `quantity: -1` example from the last discussion is the same
  family.)
- **Webhook signature not verified.** Plus a genuinely non-obvious implementation gotcha:
  the raw body must survive JSON parsing — `express.raw()` *before* `express.json()`;
  `request.text()` not `request.json()` in Next.js App Router. A correct-looking
  `constructEvent()` call still fails if the body was already parsed.
- **Subscription status read from a JWT claim or cached session** instead of the database
  → access persists after cancellation. DB synced by webhook is the only source of truth.
- **Checkout session metadata client-controlled** → impersonation and plan escalation.

Webhook signature verification is ast-grep matchable (presence/absence of
`constructEvent`), giving the pack a real deterministic half rather than a provisional
prose-only one.

### 3.3 AI/LLM integration as an audit target

You have `references/PROMPT-DEFENSE.md`, but that protects **your agent** from a malicious
target repo. This is the inverse: auditing an application that **calls** an LLM. Distinct
concerns:

- LLM API key reachable from the client → unbounded spend
- No spending cap at either provider or application level
- **System vs. user message roles collapsed into one concatenated string** → user input
  overrides system instructions
- **LLM output treated as trusted** — rendered as HTML without sanitizing, executed as
  code, or fed to tool calls without validating parameters against an allowlist

Thin in their repo (~275 words) — the *idea* is worth more than the text. Given you build
agent tooling, this is close to home, and the last bullet is the same trust-boundary
reasoning your own suite applies to itself.

### 3.4 Mobile / React Native — and a missing entry-point class

You have `SWIFT.md` but nothing on mobile security. Worth taking:

- **Everything in the JS bundle is extractable**, including `EXPO_PUBLIC_*` and
  `react-native-config` values. Hermes bytecode compilation does not change this. Any
  third-party API called directly from the app leaks its key; calls must proxy through a
  backend.
- **Token storage:** AsyncStorage is plaintext. `expo-secure-store` /
  `react-native-keychain` use iOS Secure Enclave / Android Strongbox.
- **Deep link parameters are attacker-controlled** — any app or website can trigger them.
- Biometric auth as a boolean check vs. cryptographic verification.

**The enumerator angle is the real find here.** Deep links are an *entry point class your
enumerator does not know about*. Same category as §2's PostgREST tables: an untrusted input
surface with no route/listener code shape.

### 3.5 Rate limiting — this one narrows a rule in your own suite

`code-sec`'s Finding discipline currently suppresses:

> "generic hardening advice ('consider rate limiting') with no exploitable finding
> attached — that's architecture feedback, not a sweep finding."

**That rule is correct about generic advice, and too broad as written.** This repo frames
rate limiting exploitability-first:

- Auth endpoints → credential stuffing, account enumeration
- LLM endpoints → "a single user can drain your entire monthly budget in minutes"
- Email/SMS endpoints → your app becomes a spam relay
- File processing → denial of service

And it names a genuinely non-obvious broken control: **rate-limit counters stored in a
Supabase public table can be reset by the user through the REST API.** That is not hardening
advice — it is a bypassable guard, the same Gap 2 pattern again. Likewise "IP-only limits
are defeated by rotating IPs (trivial with VPNs or botnets)."

**So the mining here is not "add rate-limiting advice."** It is a narrowing of your own
suppress clause: an absent limit on a money-spending or credential endpoint is an
exploitable finding, and a resettable counter is a broken control. Generic "consider rate
limiting" stays suppressed.

---

## 4. What to discard

- **Its `SKILL.md` as a skill.** Same collision problem as VibeSec — a fifth security skill
  overlapping four bounded territories. Its 9-step linear process is also weaker than your
  existing phase model.
- **Vendor-specific prose.** Stripe API shapes, Expo package names, and Supabase policy
  syntax all rot. Keep the *invariant* ("price is server-authoritative", "webhook bodies
  must stay raw") and cite the vendor doc rather than transcribing its current API.
- **`agents/openai.yaml`** — their Codex packaging. You have your own symlink convention
  (and its inconsistency is already noted in the companion doc, §6.1).
- **Severity tiers and "never trust the client"** — you already have both, expressed more
  precisely (`[BROKEN]`/`[BLOCKER]`/default/`[LOW]`, plus the three auth tiers).

---

## 5. Licensing note

MIT — more permissive than VibeSec's Apache-2.0, and would permit direct copying with
attribution. Not relevant given the stated approach of re-deriving rather than copying, but
worth recording: if any prose *were* taken verbatim, MIT requires the copyright notice to
travel with it. Re-derived invariants cited to vendor documentation carry no such
obligation.

---

## 6. Ranking

| Item | Value | Cost | Notes |
|---|---|---|---|
| **BaaS authz surface** (§3.1) | **Highest** | High — needs a new rule surface over `.sql`/`.rules` files | Structural blind spot, not a missing rule. Also supplies more `USING (true)`-style bypassable-guard rows |
| **Payments abuse family** (§3.2) | High | Medium | Best available fill for the empty `domains/` pack; has a real deterministic half |
| **Rate-limit suppress narrowing** (§3.5) | High | **Very low** — one clause edit | Cheapest item across both reviews |
| **LLM-integration audit** (§3.3) | Medium–high | Low | Close to your own domain; their text is thin, the framing is the value |
| **Mobile + deep-link entry points** (§3.4) | Medium | Medium | Only matters if you audit mobile codebases; the enumerator gap is the durable part |

---

## 7. How the two reviews combine

Reading both docs together, three items recur independently in both repos — which is the
strongest signal available that they are real gaps rather than one author's hobby-horse:

1. **Bypassable guards that read as protection.** VibeSec: `startswith` allowlists, octal
   IP encodings, extension-only upload checks. This repo: `USING (true)` policies,
   resettable rate-limit counters, IP-only limiting. **Same failure mode, different stacks.**
   The bypass-catalog idea from the last review now has a second, independent source of
   rows — and it is the one item both repos independently expose.
2. **Business-logic abuse the CWE pack cannot match.** VibeSec: negative quantity. This
   repo: client-submitted price, subscription status from a stale claim. Both point at the
   same empty `domains/` seam.
3. **Client-trust violations.** Both organize around "never trust the client," and both
   name concrete instances your rules do not currently match.

**Neither repo has a deterministic layer. Yours does.** In both cases the mining is prose
into your reasoning layer, with the matching `rules/` half still to be built — and that
half is where the actual work is.

**Suggested reading order if only one thing gets done:** §3.5 here (one clause, very low
cost), then the bypass catalog from the companion doc (now double-sourced), then §3.1.

---

## 8. Sources for any retained material

- Supabase RLS documentation; PostgreSQL row security policy documentation
- Firebase Security Rules documentation
- Stripe webhook signature verification documentation
- OWASP Top 10 (2021), OWASP ASVS 4.0, OWASP Mobile Top 10
- OWASP Top 10 for LLM Applications
- Expo SecureStore / react-native-keychain documentation
