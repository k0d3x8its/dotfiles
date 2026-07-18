# CODE-STANDARD

Checkable rules — every rule here is settled *at review*, either by a tool or by an
agent reading the diff. Two senses of checkable, both count:
- **Tool-checkable** — a regex/linter/grep exits on it (single-letter ban, trailing
  whitespace, final newline, TODO mirrored in `TODOS.md`). Where a tool can settle a
  rule, the tool is authoritative (see *Tools are authoritative* below).
- **Review-checkable** — no tool decides it, but an agent can by reading the change
  (does this name describe what it holds? does this comment restate the next line?
  is this repeated literal magic?). Still a MUST — the evidence is the diff itself.

Universal MUSTs below apply to every language; everything language-specific is delegated
to the per-language files. Judgment-level *principles* (when rules collide) live in
`CODE-PRINCIPLES.md` — not here.

**Rule strength vocabulary (RFC 2119, used in every file in this directory):**
- **MUST / MUST NOT** — mandatory; a violation is a review finding.
- **SHOULD / SHOULD NOT** — recommended; deviate only with a stated reason.
- **AVOID** — allowed but a smell; expect it questioned at review.

**Tools are authoritative.** Where a formatter/linter config exists in a repo, that
config *is* the standard — these files record only what tools can't check. If a rule
here contradicts a repo's linter config, the linter config wins; flag the drift.

## Universal MUSTs

### Naming
- Names MUST describe what they hold or do. Single-letter identifiers are banned —
  including loop counters and lambda parameters (`index`, `line`, `retry_count`;
  never `i`, `x`, `fn`).
- Names MUST NOT use abbreviations that aren't domain-standard (`config` fine,
  `cfg`/`mgr`/`tmp2` not).
- A name's *casing* signals its kind (constant vs function vs variable vs type) —
  casing tables are per-language; see the delegation table below.
- **Neighbors win on casing convention.** An existing directory's established naming
  convention overrides the per-language casing table — match your neighbors (the table
  is the default for greenfield code, not a mandate to rename an established dir). This
  hatch covers *casing/file-naming style only*; it does NOT relax the hard bans
  (single-letter identifiers, TS `I`-prefix, Solidity `I`-prefix) — those hold everywhere.
- Booleans SHOULD read as predicates (`is_active`, `has_pending_diff`).
- Functions SHOULD be verb-phrases (`resolve_diff_card`), values noun-phrases.

### Comments
- Comments MUST explain *why*, never restate *what* the next line does.
- Commented-out code MUST NOT be committed — delete it; git remembers.
- TODO comments in code MUST be mirrored as tagged items in `TODOS.md` or they
  don't exist.
- Code markers MUST use a trailing colon (`BUG:` not `BUG,`/`BUG `) — editor
  highlighting (todo-comments.nvim) requires it, no colon means no highlight.
  Recognized keywords: `TODO:`, `BUG:` (alt `FIXME:`), `HOTFIX:`, `HACK:`,
  `NOTE:`, `WARN:`, `OPTIMIZE:` (absorbs `PERF:`/`PERFORMANCE:`), `SECURITY:`,
  `TEST:` (alt `TESTING:`/`PASSED:`/`FAILED:`). `HOTFIX:` SHOULD pair with a
  `[CHORE]` or `[VERIFY]` TODOS.md entry — it marks a quick fix that still
  needs hardening. This vocabulary is separate from TODOS.md's `[TAG]`
  vocabulary — code markers point at a line, TODOS.md tags track task
  lifecycle. No skill parses code markers programmatically.

### Hygiene
- Errors MUST NOT be silently swallowed — handle, propagate, or log with context.
- No dead code: unused functions, params, imports MUST be removed in the diff
  that orphans them.
- Files MUST end with a newline; no trailing whitespace.
- Magic numbers/strings used more than once MUST become named constants.

### Commits & branches (already normative in `~/.claude/CLAUDE.md` — pointer only)
- Conventional commits, no scope parens; one file per commit on "commit changes";
  git-crypt files commit as `updated <filename>` only; branches `feature/ fix/ docs/ chore/`.

## Delegation table

| Language | File | Authoritative tooling (when present in repo) |
|---|---|---|
| Lua (Neovim) | `LUA.md` | stylua; luacheck |
| Python | `PYTHON.md` | ruff (format + lint); pyright |
| TypeScript / JS | `TYPESCRIPT.md` | prettier; eslint; tsc strict |
| Solidity | `SOLIDITY.md` | solhint; forge fmt |
| Bash | `BASH.md` | shellcheck; shfmt |
| Arduino / C++ | `ARDUINO.md` | clang-format; arduino-lint |
| HTML / CSS / JSON / YAML | (thin — rules live in `TYPESCRIPT.md` appendix) | prettier; yamllint |

Reading protocol for agents: load *only* this file + the one language file matching the
code being written. Do not load the whole directory.

## Related

- `CODE-PRINCIPLES.md` — judgment-level principles + review-stage smell vocabulary
- `~/.claude/CLAUDE.md` — commit/branch/TODO-tag conventions (canonical)
- `/trust-but-verify` — how "checkable" gets checked before claiming done
