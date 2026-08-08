# RESOURCE-ACCESS

**Invariant:** when a value selects _which_ file, URL, or destination the code acts on,
the set of valid destinations MUST be allowlisted and canonicalized before the check
runs — never inferred from the shape of the input after the fact.

## MUSTs / SHOULDs

- File paths built from any request-derived value MUST be canonicalized (resolve `.`,
  `..`, symlinks) before a prefix/allowlist check runs, not after. A check performed on
  the raw, uncanonicalized path can be satisfied by a value that still escapes the
  intended directory once resolved.
- Redirect targets MUST be validated against an exact allowlist of destinations, not a
  `startswith()`/prefix check against a trusted domain string.
- SSRF-relevant destination checks (a URL/host the server itself will fetch) MUST
  reject private, loopback, and link-local ranges after resolving any encoding — octal,
  decimal, or hex IP representations, and IPv6-mapped forms, all resolve to the same
  address as their dotted-decimal form and MUST be checked as such, not string-matched.
- SSRF checks MUST account for DNS rebinding — a hostname that resolves to a public IP
  at validation time and a private/internal IP at fetch time. Resolve once and reuse
  the resolved address for the actual fetch, don't re-resolve between check and use.
- Cloud metadata endpoints (`169.254.169.254` and equivalents) MUST be explicitly
  denied by resolved address, not relied on being caught incidentally by a general
  private-range block that a request can be crafted to miss.
- File upload validation MUST inspect actual file content (magic bytes), not the
  filename extension alone. An extension-only check accepts a payload with a
  real-image-header-then-executable-payload construction, or a double extension
  (`shell.php.jpg`).
- Deep links (mobile) MUST be treated as an untrusted, attacker-controlled entry point
  — any installed app or website can trigger one with arbitrary parameters. Route
  parameters extracted from a deep link get the same validation as a web request
  parameter, not less because the transport feels internal.

## Guards that don't work

| Defense as written                                                                            | Bypass                                                                                                                                     | Why it works                                                                               | Sound form                                                                                                              |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Redirect target checked with `url.startswith("https://myapp.com")`                            | `https://myapp.com.evil.com` passes the same check                                                                                         | `startswith` matches a prefix, not a domain — a subdomain-looking suffix satisfies it      | Parse the URL and compare the exact host against an allowlist, not a string prefix                                      |
| SSRF filter blocking the literal string `169.254.169.254`                                     | `0251.0376.0251.0376` (octal) or the decimal/hex equivalent resolves to the identical address and is not string-matched                    | The filter matches a specific textual representation, not the resolved address             | Resolve the address first, then check the resolved value against the denylist — never string-match the input as written |
| Path traversal check via `path.startswith(base_dir)` with no canonicalization                 | `base_dir/../../etc/passwd` still starts with `base_dir` as a string, but resolves outside it                                              | The check runs on the raw path; `..` segments are not evaluated until the OS resolves them | Canonicalize (resolve `.`/`..`/symlinks) first, then check the resolved absolute path against the allowlisted base      |
| File upload restricted to `.jpg`/`.png` by filename extension                                 | Real image magic bytes prepended to a PHP/executable payload, or a `shell.php.jpg` double extension, both pass an extension-only check     | The filename is attacker-controlled and unrelated to the actual file content               | Verify magic bytes / content-type by inspection, not by trusting the claimed extension                                  |
| SSRF check performed once at validation time, fetch performed later against the same hostname | DNS rebinding — the hostname resolves to a public IP at check time and a private IP at fetch time (attacker controls the DNS TTL/response) | Re-resolving between check and use gives the attacker a second, uncontrolled resolution    | Resolve once, validate the resolved address, and reuse that same resolved address for the actual outbound request       |

## Sink or pattern catalog

- Path traversal / arbitrary file read: `open(BASE + user_value)`,
  `send_file(user_value)`, or equivalent path-concatenation-into-file-I/O shapes —
  covered by existing `precise` tier path-traversal rules (`code-sec/rules/precise/`).
- SSRF: `requests.get(user_value)`, `fetch(user_value)`, or equivalent
  value-into-outbound-request shapes — covered by existing `precise`/`noisy` tier SSRF
  rules.
- Open redirect: `redirect(user_value)` without a preceding allowlist check — not
  currently a dedicated rule; candidate for `code-sec`'s OWASP-layer growth backlog
  (`TODOS.md`).
- Deep links as an entry-point class have no enumerator support today —
  `enumerate-entrypoints.sh` recognizes route/listener code shapes (Flask routes,
  Express handlers, etc.), not a mobile app's deep-link registration. A deep-link
  handler with no matching enumerator signature is invisible to a `code-sec` sweep the
  same way a PostgREST-exposed table is (`DATA-STORE.md`'s headline finding) — tracked
  in the same detection-surface gap TODO (`TODOS.md`, 2026-08-08).

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under
- `~/.claude/references/security/DATA-STORE.md` _(sibling, this pilot)_ — storage
  bucket path scoping there is about who may read/write a bucket, once this file's
  canonicalization has already resolved which object is being addressed. This file
  answers "which target," `DATA-STORE.md` answers "may this caller touch it"
- `~/.claude/references/security/INJECTION.md` _(not yet built)_ — the split this file
  observes: injection is attacker data reaching an interpreter (`f"SELECT … {id}"`);
  resource-access is attacker data selecting the target (`open("/data/" + name)`).
  Different failure mode, different fix — do not conflate "sanitize" across the two
  once `INJECTION.md` exists
- `code-sec` — path-traversal and SSRF rule tiers already exist and enforce a subset of
  this file's guidance at sweep time; open redirect and deep-link entry points do not
  yet have rule/enumerator coverage

## Sources

- OWASP Top 10 (2021) — A10 Server-Side Request Forgery, A01 Broken Access Control
- OWASP ASVS 4.0 — file and resources, and SSRF sections
- PortSwigger Web Security Academy — SSRF, path traversal, open redirect topics
- MITRE CWE-22 (path traversal), CWE-918 (SSRF), CWE-601 (open redirect)
