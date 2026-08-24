# LUA (Neovim) — language standard

Scope: Neovim configuration and plugin code (kodex-ide and future nvim work).
Evidence base: `~/dev/kodex-ide`. Strength vocabulary per `CODE-STANDARD.md`.

## Naming & casing

| Kind                                | Casing                                            | Example                             |
| ----------------------------------- | ------------------------------------------------- | ----------------------------------- |
| variables / functions               | `snake_case`                                      | `resolve_diff_card`, `session_cost` |
| constants (true immutables)         | `UPPER_SNAKE`                                     | `MAX_FRAME_COUNT`                   |
| your own modules (`utils/`,`core/`) | `snake_case.lua`                                  | `claude_burn.lua`                   |
| plugin specs (`lua/plugins/`)       | `kebab-case.lua`, named after the upstream plugin | `nvim-tree.lua`, `which-key.lua`    |
| user commands / augroups            | `PascalCase`                                      | `KodexReload`                       |
| highlight groups                    | `PascalCase`                                      | `ClaudeBarBorder`                   |

- MUST follow the universal naming rules (no single-letter identifiers) with **one
  carved exception**: `local M = {}` … `return M` as the module-table idiom — it is
  Neovim-ecosystem standard and pervasive in this codebase. The exception is `M`
  only, only as the returned module table. Any _other_ table (helpers, config,
  a second returned table) takes a descriptive name (`state`, not `S`).

## Modules & structure

- Every module MUST be a table returned at end of file (`local M = {} … return M`).
  MUST NOT set globals (`_G`, bare assignments).
- Plugin specs live one-per-file under `lua/plugins/`, shared logic under `lua/utils/`,
  bootstrap under `lua/core/`. New code MUST follow that split.
- Dependencies SHOULD be injected via a `wire{}`-style table (the local DI idiom) when
  a module has collaborators — it is the seam tests substitute (DIP, see
  CODE-PRINCIPLES.md). Reaching into another module's internals via `require` chains
  is AVOID.

## File layout (SHOULD — top to bottom)

1. `require`s — plugin/external first, then `utils.*` internal
2. Local constants (`UPPER_SNAKE`)
3. Module table + state (`local M = {}`, `M.state` or wired-in state)
4. Functions — newspaper order: public `M.fn` high-level first, `local` helpers
   above their first caller (Lua has no hoisting — a helper must exist before use)
5. Wiring at the bottom: autocmds, keymaps, user commands, `wire{}` setup
6. `return M` — always the last line

## Directory structure (canonical minimum — Neovim config/plugin)

Structure below is what Neovim's runtime path itself mandates/expects. An existing
repo's layout always wins over this — check before creating directories.

```
<config-or-plugin>/
├── init.lua                # entry, bootstrap only — no logic
├── lua/                    # everything require()-able lives here (runtime path)
│   └── <namespace>/        # your module namespace; snake_case.lua files
│       └── <feature>/      # feature outgrowing one file → package:
│           └── init.lua    #   facade; consumers' require() path unchanged
├── plugin/                 # (plugins only) auto-sourced on startup
├── ftplugin/               # (optional) per-filetype
├── tests/                  # *_spec.lua, headless runner
└── Makefile                # `make test` verify gate
```

- Minimum viable: `init.lua` + `lua/<namespace>/` + `tests/`.
- Conventional namespace split for configs: `core/` (options/keymaps/autocmds),
  `plugins/` (one spec per file), `utils/` (shared logic).

## Neovim API

- MUST use `vim.keymap.set` — never the legacy `nvim_set_keymap`.
- MUST use `vim.api.nvim_create_autocmd`/`nvim_create_augroup` — never `vim.cmd"autocmd"`.
- SHOULD use `vim.opt`/`vim.o` for options, `vim.g` only for plugin globals that
  require it.
- Keymaps MUST carry a `desc` — which-key and discoverability depend on it.
- Anything that can error at startup (require of an optional plugin, fs access)
  MUST be wrapped in `pcall` with a graceful fallback — a broken plugin must not
  take the editor down.
- Timers/async: MUST use `vim.uv`/`vim.loop` handles and close them; a leaked timer
  outlives its buffer. Callbacks touching the UI MUST go through `vim.schedule`.

## Language gotchas (MUST know)

- Indexing is 1-based; off-by-one bugs cluster at `string.sub`/table boundaries.
- `nil` in the middle of a table breaks `#length` and `ipairs` — never build sparse
  arrays; use `table.insert`.
- `local` everything: an undeclared assignment is a silent global (luacheck catches).
- Truthiness: only `nil` and `false` are falsy — `0` and `""` are truthy.
- String concat in loops is O(n²) — accumulate in a table, `table.concat` once.
- **200 locals per function** hard ceiling — and a file's top-level chunk IS a
  function, so every top-level `local` (including each `local function`) counts.
  A growing single-file module hits it (the 5680-line claude.lua monolith did —
  see kodex-ide KNOWLEDGE.md). Nearing it = the file is screaming to be split
  into a package (SRP anyway). Related: 60-upvalue limit per function.

## Data structures & algorithms

Scenario names match `DATA-STRUCTURES.md`/`ALGORITHMS.md` — this is the concrete API only.
Lua has one universal structure: the table. Selection is really "which table idiom."

- Key → value / membership test: table used as a map (`t[key] = true` for a set;
  `t[key] = value` for a map) — `pairs()` to iterate, no guaranteed order.
- Ordered / sequence: table used as an array (`1..n`, no holes) — `ipairs()` to
  iterate, `table.insert`/`table.remove` for FIFO/LIFO/stack behavior at either end.
- Sort + sort-key: `table.sort(t, comparator)` — mutates in place, no stable-sort
  guarantee in stock Lua; write the comparator, don't hand-roll the sort.
- Priority / smallest-next: no stdlib heap — a small binary-heap-over-array module
  if genuinely needed (rare in this codebase's scale); state the reason before adding one.
- Dedup: build a seen-table (map idiom above) while iterating an array once.
- **Never mix the two idioms in one table** — a table with both array indices and
  string keys breaks `#length`/`ipairs` in ways that are hard to spot (see Language
  gotchas above).

## Testing

- Headless specs: `tests/*_spec.lua`, run via `make test` (`nvim --headless`).
  New logic MUST arrive with a spec (red-green, per `/tdd`).
- Pure state-machine logic SHOULD be separated from rendering so it is
  headless-testable (established pattern: Clawd pet SM vs renderer split).

## Tooling

- kodex-ide has `stylua.toml` (added 2026-08-24, tabs — settled after a line-count
  survey showed the `utils/claude/` engine, the bulk of the codebase, was already
  100% tabs; a handful of newer plugin-spec files were 2-space and got reformatted
  in the same pass). No luacheck config yet — `[CHORE]` candidate.
- Other Neovim-config/plugin projects without a `stylua.toml` yet: match the file
  you're in; do not reformat neighbors until one exists.
