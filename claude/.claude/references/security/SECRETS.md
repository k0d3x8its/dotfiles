# SECRETS

**Invariant:** anything shipped to a client — a compiled bundle, a mobile binary, a
minified script — is public, not hidden. A credential embedded there is disclosed, not
protected, regardless of build-step obfuscation. Secrets belong on the server, loaded
from the environment, and MUST NOT reach logs, error output, or URLs.

## MUSTs / SHOULDs

- Secrets MUST be read from the environment (or a secrets manager) at runtime, never
  committed to source, and never hardcoded as a fallback default.
- Any environment variable prefixed for client-bundle inclusion (`EXPO_PUBLIC_*`,
  `NEXT_PUBLIC_*`, `VITE_*`, or equivalent build-tool convention) MUST be treated as
  public the moment it exists — the prefix is a bundler instruction to _include_ the
  value in client output, not a safety boundary. A credential given one of these
  prefixes is shipped, not "exposed if someone looks."
- Any third-party API requiring a secret key MUST be called from a backend the client
  proxies through — never called directly from client-side code with the key present
  in that code, compiled or not. Bytecode compilation (e.g. Hermes) does not change
  extractability; it changes the tooling needed, not whether extraction is possible.
- Secrets MUST NOT appear in log output, error messages/stack traces, or URLs
  (including query strings, which are commonly logged by proxies/load balancers even
  when the request body is not).
- A secret accidentally logged or committed MUST be rotated, not just removed from the
  current version — history retains it (`git show` on an old revision, log retention
  windows) until rotation invalidates the value itself.

## Guards that don't work

| Defense as written                                                                                                                 | Bypass                                                                                                            | Why it works                                                                                     | Sound form                                                                                                               |
| ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| API key embedded in client code, compiled to Hermes bytecode / minified JS                                                         | Bytecode/minified output is extractable with standard decompilation/deobfuscation tooling — not a secret boundary | Compilation changes representation, not reachability — the client device holds the full artifact | Never ship the key client-side; proxy the third-party call through a backend that holds the key server-side              |
| Secret assigned to an `EXPO_PUBLIC_*`/`NEXT_PUBLIC_*`-prefixed environment variable "temporarily," intending to lock it down later | The prefix already told the build tool to inline the value into every client bundle built in the meantime         | The exposure happens at build time, not at some later "someone looks" moment                     | Never assign a secret to a client-exposed-prefix variable, even temporarily — use an unprefixed server-only variable     |
| Secret removed from the current file after being noticed in a log or commit                                                        | The value is still present in git history / log retention and remains valid                                       | Removing the current reference doesn't invalidate the value itself                               | Rotate the credential; treat the exposed value as compromised regardless of whether the current code still references it |

## Sink or pattern catalog

- Client-bundle secret exposure: an `EXPO_PUBLIC_*`/`NEXT_PUBLIC_*`/`VITE_*`-prefixed
  assignment whose value looks like a credential (API key shape, length/entropy
  heuristics), or a third-party SDK call made directly from client-side code with a
  key literal present — not currently in `code-sec/rules/`, tracked in the
  detection-surface gap TODO (`TODOS.md`, 2026-08-08).
- Secrets-in-source and secrets-in-git-history already have coverage — `code-sec`'s
  gitleaks full-history scan is exactly this sink, already wired.
- Secrets-in-logs/error-output/URLs has no current rule coverage; would need
  cross-referencing a logged value against known-secret shape, not a single-file
  pattern match.

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under. The Universal MUST "anything
  shipped to a client is public" is this sector's headline invariant restated at
  router level — loading the router alone already carries the core rule
- `~/.claude/references/security/AUTHENTICATION.md` — mobile secure-storage guidance
  (`AsyncStorage` vs. keychain) lives there and covers _where a token is stored
  on-device_; this file covers a credential extractable from the _app bundle itself_
  — different surfaces, same platform
- `~/.claude/references/security/AI-INTEGRATION.md` — an LLM API key reachable from
  the client is the same failure class as any other client-exposed key; that sector's
  MUSTs point here rather than restating the general secrets-handling rule
- `code-sec` — gitleaks full-history secret scan already covers secrets-in-source and
  secrets-in-history; client-bundle exposure and secrets-in-logs do not yet have rule
  coverage

## Sources

- OWASP Top 10 (2021) — A02 Cryptographic Failures (credential handling), A05 Security
  Misconfiguration
- OWASP ASVS 4.0 — secrets management section
- Expo environment variables documentation; Next.js environment variables documentation
