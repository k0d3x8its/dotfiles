# INJECTION

**Invariant:** when attacker-influenced data reaches an interpreter — SQL, a shell,
HTML/a template engine, an XML parser, a deserializer — it MUST reach it through a
structured, parameterized API, never through string concatenation or interpolation
into a command the interpreter then parses as code.

## MUSTs / SHOULDs

- SQL queries MUST use parameterized queries or an ORM's parameter binding — never
  string-build a query with a request-derived value interpolated directly, regardless
  of any quoting or escaping applied by hand. This is `DATA-STORE.md`'s MUST list by
  pointer; the mechanics live here (see Related).
- Shell commands MUST be invoked via an argument-array API (`execve`-style, passing
  argv as a list) rather than a shell string built by concatenation — a string handed
  to a shell is re-parsed for metacharacters (`;`, `|`, `` ` ``, `$()`) regardless of
  escaping intent.
- Values rendered into HTML MUST go through the templating engine's default
  auto-escaping, not a manually-escaped string or a raw/unsafe-render call — the
  escaping rules differ by output context (HTML body, attribute, URL, JS string) and
  a single hand-rolled escape function typically covers only one.
- XML parsers MUST have external entity resolution (DTD processing) disabled by
  default, not selectively — a parser configured to accept some external entities
  while blocking others is still vulnerable to the ones it accepts (XXE).
- Deserializers for untrusted input MUST use a safe/restricted mode (e.g. `yaml.safe_load`
  instead of `yaml.load`, no `pickle` on attacker-reachable input) — a generic
  deserializer that reconstructs arbitrary objects can be made to execute code as a
  side effect of reconstruction, independent of what the resulting object is used for.

## Guards that don't work

| Defense as written                                                                   | Bypass                                                                                                                                          | Why it works                                                                                                       | Sound form                                                                                               |
| ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| SQL value manually escaped/quoted before string interpolation (`"'" + esc(v) + "'"`) | An escape function missing an encoding edge case (e.g. multi-byte, backslash handling) lets a quote through anyway                              | Hand-rolled escaping has to anticipate every encoding path the database's own parser accepts                       | Use parameterized queries / bound parameters — the driver handles encoding, no escape function needed    |
| Shell command built as a single string with arguments individually quoted            | Nested/unexpected metacharacters, or a quoting bug specific to the shell in use, still inject                                                   | The shell re-parses the whole string for its own syntax after quoting is applied                                   | Pass arguments as an array to an `execve`-style call; never construct a shell string at all              |
| XML parser blocks "known-bad" DTD patterns via a denylist                            | A DTD variant or nested-entity form not on the denylist still resolves external entities                                                        | Denylists enumerate known attack shapes, not the underlying capability being exploited                             | Disable external entity resolution entirely at the parser configuration level, not selectively           |
| `yaml.load(data)` used because "the input is from our own config, not a user"        | The trust boundary shifts (config becomes user-editable, or the file is included from an uploaded source) without the load call being revisited | `yaml.load` can construct arbitrary Python objects; safety depended on an assumption about the caller, not the API | Default to `yaml.safe_load` universally; require an explicit, documented reason to use the unsafe loader |

## Sink or pattern catalog

- SQL injection, OS command injection, XSS, and deserialization (pickle/YAML) already
  have rule coverage in `code-sec/rules/` — Python and JavaScript execute; other
  languages are model-only per `bounty-hunter`'s stated scope.
- XXE parser configuration (external entity resolution left enabled, or disabled via a
  denylist rather than outright) has no current rule coverage — tracked in the
  detection-surface gap TODO (`TODOS.md`, 2026-08-08).

## Related

- `~/.claude/references/security/SECURITY-STANDARD.md` — router; universal MUSTs and
  the overflow-flag protocol this file operates under
- `~/.claude/references/security/DATA-STORE.md` — this sector's parameterization MUST
  is what `DATA-STORE.md`'s own MUSTs point to rather than restate; that file owns
  declarative authz (RLS/Firestore rules) and object storage scoping, this file owns
  the injection mechanics for any query built against that store
- `~/.claude/references/security/RESOURCE-ACCESS.md` — the split this file observes:
  injection is attacker data reaching an **interpreter** (`f"SELECT … {id}"`);
  resource-access is attacker data selecting the **target**
  (`open("/data/" + name)`). Different failure mode, different fix — "sanitize" means
  different things in the two files, do not conflate them
- `code-sec` — SQLi/command-injection/XSS/deserialization rule tiers already exist and
  enforce a subset of this file's guidance at sweep time; XXE does not yet

## Sources

- OWASP Top 10 (2021) — A03 Injection
- OWASP ASVS 4.0 — input validation and output encoding sections
- PortSwigger Web Security Academy — SQL injection, OS command injection, XXE topics
- MITRE CWE-89 (SQL injection), CWE-78 (OS command injection), CWE-79 (XSS), CWE-611
  (XXE), CWE-502 (deserialization of untrusted data)
