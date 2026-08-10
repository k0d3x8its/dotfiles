# CODE-STANDARD

Checkable rules — every rule here is settled _at review_, either by a tool or by an
agent reading the diff. Two senses of checkable, both count:

- **Tool-checkable** — a regex/linter/grep exits on it (single-letter ban, trailing
  whitespace, final newline, TODO mirrored in `TODOS.md`). Where a tool can settle a
  rule, the tool is authoritative (see _Tools are authoritative_ below).
- **Review-checkable** — no tool decides it, but an agent can by reading the change
  (does this name describe what it holds? does this comment restate the next line?
  is this repeated literal magic?). Still a MUST — the evidence is the diff itself.

Universal MUSTs below apply to every language; everything language-specific is delegated
to the per-language files. Judgment-level _principles_ (when rules collide) live in
`CODE-PRINCIPLES.md` — not here.

**Rule strength vocabulary (RFC 2119, used in every file in this directory):**

- **MUST / MUST NOT** — mandatory; a violation is a review finding.
- **SHOULD / SHOULD NOT** — recommended; deviate only with a stated reason.
- **AVOID** — allowed but a smell; expect it questioned at review.

**Tools are authoritative.** Where a formatter/linter config exists in a repo, that
config _is_ the standard — these files record only what tools can't check. If a rule
here contradicts a repo's linter config, the linter config wins; flag the drift.

## Universal MUSTs

### Naming

- Names MUST describe what they hold or do. Single-letter identifiers are banned —
  including loop counters and lambda parameters (`index`, `line`, `retry_count`;
  never `i`, `x`, `fn`).
- Names MUST NOT use abbreviations that aren't domain-standard (`config` fine,
  `cfg`/`mgr`/`tmp2` not).
- A name's _casing_ signals its kind (constant vs function vs variable vs type) —
  casing tables are per-language; see the delegation table below.
- **Neighbors win on casing convention.** An existing directory's established naming
  convention overrides the per-language casing table — match your neighbors (the table
  is the default for greenfield code, not a mandate to rename an established dir). This
  hatch covers _casing/file-naming style only_; it does NOT relax the hard bans
  (single-letter identifiers, TS `I`-prefix, Solidity `I`-prefix) — those hold everywhere.
- Booleans SHOULD read as predicates (`is_active`, `has_pending_diff`).
- Functions SHOULD be verb-phrases (`resolve_diff_card`), values noun-phrases.

### Comments

- Comments MUST explain _why_, never restate _what_ the next line does.
- Commented-out code MUST NOT be committed — delete it; git remembers.
- TODO comments in code MUST be mirrored as tagged items in `TODOS.md` or they
  don't exist. This mirroring applies to any marker below with a matching
  `TODOS.md` annotation tag — `TODO:`, `BUG:` (`[BUG]`), `HOTFIX:` (`[CHORE]`
  or `[VERIFY]`), `SECURITY:` (`[SECURITY]`), `TEST:` (`[TEST]`),
  `PERFORMANCE:` (`[PERFORMANCE]`). `HACK:`, `NOTE:`, and `WARN:` have no
  tag counterpart and are inline-only — they document current code state,
  not a pending action item.
- Code markers MUST use a trailing colon (`BUG:` not `BUG,`/`BUG `) — editor
  highlighting (todo-comments.nvim) requires it, no colon means no highlight.
  Recognized keywords: `TODO:`, `BUG:` (alt `FIXME:`), `HOTFIX:`, `HACK:`,
  `NOTE:`, `WARN:`, `PERFORMANCE:` (absorbs `PERF:`/`OPTIMIZE:`), `SECURITY:`,
  `TEST:` (alt `TESTING:`/`PASSED:`/`FAILED:`). This vocabulary is separate
  from TODOS.md's `[TAG]` vocabulary — code markers point at a line, TODOS.md
  tags track task lifecycle. No skill parses code markers programmatically.

### Hygiene

- No dead code: unused functions, params, imports MUST be removed in the diff
  that orphans them.
- Files MUST end with a newline; no trailing whitespace.
- Magic numbers/strings used more than once MUST become named constants.

### Error handling

- Errors MUST NOT be silently swallowed — handle, propagate, or log with context.
  An empty `catch`/`except`/`pcall`-and-ignore is a review finding, not a style
  choice.
- A logged error MUST include enough context to act on without re-reading the
  stack trace from scratch: what operation was attempted, what input/state it
  was attempted with. `log("failed")` is not sufficient; `log("bufadd failed for "
.. path)` is.
- Validate at system boundaries (user input, external APIs, file/network I/O);
  trust internally. Re-validating a value your own code already produced is
  noise, not safety (see ANTI-PATTERNS.md's _Input Kludge_ — the failure mode
  this rule prevents is having no consistent boundary at all, not over-validating
  everywhere).
- A caller MUST NOT be able to mistake a silent no-op for success. If a function
  can fail to do what its name promises, its return value MUST make that
  observable (boolean/Result/exception) — the caller decides what to do with a
  failure, but only if it can see one happened.
- Per-language mechanics (which error style: exceptions vs `Result`/`Option`
  types vs Lua-style `ok, err` returns) are delegated to the per-language files
  in this directory — this rule is the universal MUST that survives whichever
  mechanism a language uses.

### Commits & branches (already normative in `~/.claude/CLAUDE.md` — pointer only)

- Conventional commits, no scope parens; one file per commit on "commit changes";
  git-crypt files commit as `updated <filename>` only; branches `feature/ fix/ docs/ chore/`.

## Delegation table

| Language        | File            | Authoritative tooling (when present in repo) |
| --------------- | --------------- | -------------------------------------------- |
| Lua (Neovim)    | `LUA.md`        | stylua; luacheck                             |
| Python          | `PYTHON.md`     | ruff (format + lint); pyright                |
| TypeScript / JS | `TYPESCRIPT.md` | prettier; eslint; tsc strict                 |
| Solidity        | `SOLIDITY.md`   | solhint; forge fmt                           |
| Bash            | `BASH.md`       | shellcheck; shfmt                            |
| Arduino / C++   | `ARDUINO.md`    | clang-format; arduino-lint                   |
| Swift           | `SWIFT.md`      | swift-format; SwiftLint                      |
| HTML            | `HTML.md`       | prettier; html-validate                      |
| HTMX            | `HTMX.md`       | prettier (markup); no htmx-specific linter   |
| CSS             | `CSS.md`        | prettier; stylelint                          |
| JSON            | `JSON.md`       | jq                                           |
| YAML            | `YAML.md`       | yamllint                                     |

Reading protocol for agents: load _only_ this file + the one language file matching the
code being written. Do not load the whole directory. When the task involves writing or
reviewing tests, also load `TESTING-STANDARD.md` — it routes test-type decisions
(unit/integration/system/playtesting/compatibility/etc.) that this file doesn't cover.

## Related

- `CODE-PRINCIPLES.md` — judgment-level principles + review-stage smell vocabulary
- `CODE-REFERENCE.md` — shared vocabulary/glossary terms (e.g. "seam") linked
  from `CODE-PRINCIPLES.md`
- `TESTING-STANDARD.md` — test-type decision layer; unit vs integration; coverage
  and compatibility/accessibility stances
- `~/.claude/references/security/SECURITY-STANDARD.md` — sibling router, routes by
  security domain instead of language; same RFC 2119 vocabulary and
  Universal-MUSTs-in-the-router pattern (pilot: 3 of 8 sectors built)
- `~/.claude/CLAUDE.md` — commit/branch/TODO-tag conventions (canonical)
- `/trust-but-verify` — how "checkable" gets checked before claiming done
