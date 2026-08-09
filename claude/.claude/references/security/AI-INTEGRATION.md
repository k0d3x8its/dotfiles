# AI-INTEGRATION

**Invariant:** a model's output is untrusted input the moment it leaves the model —
the same status as any other externally-influenced value — and a model's input channel
must keep system instructions separated from user-controlled content, not concatenated
into one string the model has no way to tell apart.

## MUSTs / SHOULDs

- LLM/model API keys MUST be held server-side and called through a backend the client
  proxies through — never reachable from client-side code (this is `SECRETS.md`'s
  general rule, applied to this specific credential class; see Related rather than
  restating).
- A spending cap MUST exist at the provider level, the application level, or both — an
  endpoint that calls a metered model with no cap lets a single caller (malicious or
  accidental — a retry loop, a scripted abuse pattern) exhaust a budget in minutes,
  not an edge case worth deferring.
- System instructions and user-controlled content MUST be passed through the
  provider's distinct message-role channels (system/developer role vs. user role), not
  concatenated into a single string. A collapsed string gives user input no structural
  separation from the instructions it's supposed to be constrained by.
- Model output MUST be treated as untrusted before it is rendered, executed, or acted
  on — rendered as HTML requires the same escaping as any other untrusted value fed to
  a template (`INJECTION.md`); passed to a tool call requires the same parameter
  validation as any other caller-influenced input reaching a sink
  (`RESOURCE-ACCESS.md`/`INJECTION.md`, depending on what the tool does); never
  `eval`'d or executed as code regardless of how well-formed it looks.
- Tool/function-call parameters proposed by a model MUST be validated against an
  allowlist of permitted values/shapes before execution — the model proposing a call
  is not authorization for that call to run unchecked, the same way a client
  submitting a value is not authorization to act on it (`CLIENT-TRUST.md`'s invariant,
  applied to a model as the submitting party instead of a human client).

## Guards that don't work

| Defense as written                                                                      | Bypass                                                                                                                                                            | Why it works                                                                                               | Sound form                                                                                                            |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Client-side code calls the model API directly, key "protected" by a CORS/referrer check | CORS/referrer headers are client-supplied and trivially spoofed by a direct HTTP request outside a browser context                                                | The check constrains browser-initiated requests only; the key itself is still present in shipped code      | Proxy the call through a backend that holds the key; the client never receives it in any form                         |
| System prompt and user input concatenated into one string passed as a single message    | User input containing instruction-like text ("ignore previous instructions...") has no structural boundary separating it from the real system instructions        | The model receives one undifferentiated string; there is no channel-level distinction to fall back on      | Use the provider's distinct system/user message roles; do not flatten them into one string at the call site           |
| Model output rendered directly as HTML because "it's our own model, not a random user"  | The model's training/context can be influenced by upstream untrusted input (a document it summarized, a tool result), and its output is rendered without escaping | Trusting the _source_ of a value (a model call you made) is not the same as the value being _safe content_ | Escape/sanitize model output at the render sink exactly as any other untrusted value, regardless of the call's origin |

## Sink or pattern catalog

- Client-side model API calls with a key literal present, and unbounded/uncapped model
  API usage (no rate limit or spend-cap check on the calling route) — not currently in
  `code-sec/rules/`, tracked in the detection-surface gap TODO (`TODOS.md`,
  2026-08-08).
- System/user role collapse (a single concatenated prompt string built from both a
  fixed instruction and a request-derived value) and unsanitized-model-output-to-render
  or -to-tool-call sinks have no current rule coverage — same tracked gap.

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under
- `~/.claude/references/security/SECRETS.md` — this sector's key-handling MUST is a
  pointer to that file's general client-exposure rule, not a restatement
- `~/.claude/references/security/CLIENT-TRUST.md` — this sector's tool-call validation
  MUST reuses that file's "a submission is a request, not a fact" invariant with a
  model as the submitting party instead of a human client
- `~/.claude/references/security/INJECTION.md` / `~/.claude/references/security/RESOURCE-ACCESS.md`
  — whichever of these owns the specific sink model output is flowing into (an
  interpreter vs. a target-selection value) governs the actual escaping/validation
  rule; this file only states that model output qualifies as untrusted input at all
- `~/.claude/references/PROMPT-DEFENSE.md` — **opposite direction, do not conflate.**
  That file protects _this agent_ (Claude Code) from a malicious target repository it
  is operating on. This sector audits _an application_ that itself calls a model —
  the application being reviewed is the caller, not the agent doing the reviewing
- `code-sec` — no current rule coverage for any item in this sector; tracked in the
  detection-surface gap TODO

## Sources

- OWASP Top 10 for LLM Applications — LLM01 Prompt Injection, LLM02 Insecure Output
  Handling, LLM04 Model Denial of Service, LLM06 Sensitive Information Disclosure
- OWASP ASVS 4.0 — secrets management section (applied to model API keys)
