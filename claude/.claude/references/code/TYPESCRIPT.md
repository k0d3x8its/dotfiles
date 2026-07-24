# TYPESCRIPT / JS — language standard

Scope: TypeScript and JavaScript (trello-cli pnpm workspace, kos-portal Obsidian
plugin, web work). Strength vocabulary per `CODE-STANDARD.md`.
Appendix below covers HTML / CSS / JSON / YAML.

## Naming & casing

| Kind                                 | Casing                   | Example                               |
| ------------------------------------ | ------------------------ | ------------------------------------- |
| variables / functions                | `camelCase`              | `resolveBoardId`                      |
| constants (true immutables)          | `UPPER_SNAKE`            | `DEFAULT_LIST_ORDER`                  |
| classes / types / interfaces / enums | `PascalCase`             | `ChecklistItem`                       |
| files                                | `kebab-case.ts`          | `board-sync.ts`                       |
| type params                          | descriptive `PascalCase` | `TCard` acceptable, bare `T` is AVOID |

- Interfaces MUST NOT carry an `I` prefix (`Card`, not `ICard`).

## Rules

- `strict: true` is already the baseline (trello-cli tsconfig) — MUST stay on;
  new tsconfigs MUST enable it.
- `any` is banned. Unknown shapes are `unknown` + narrowing. `as` casts are AVOID —
  each one requires a why-comment.
- MUST use `const` by default, `let` when reassigned, `var` never.
- MUST use `===`/`!==`; `==` only for the deliberate `== null` (null-or-undefined) check.
- `async/await` over raw `.then()` chains. Every promise MUST be awaited or
  explicitly voided with a reason — no floating promises.
- Errors in `catch` are `unknown` — MUST narrow before use; rethrow with context,
  never swallow (universal hygiene rule).
- SHOULD prefer plain functions + object literals over classes unless state +
  behavior genuinely cohere (Obsidian/framework base classes are the exception).
- SHOULD model data with discriminated unions over optional-field blobs;
  exhaustiveness via `never` check in the default branch.
- Module boundaries: export types alongside functions; AVOID `export default`
  (breaks rename-refactors and grep).
- Node scripts in the workspace follow the same rules; plain `.js` files SHOULD
  carry `// @ts-check`.

## File layout (SHOULD — top to bottom)

1. Imports — external packages first, then internal, blank line between
2. Types / interfaces
3. Constants (`UPPER_SNAKE`)
4. Module-level state (AVOID having any; if unavoidable, declare here, not scattered)
5. Functions — newspaper order: exported/high-level first, private helpers below them
6. Event listeners / wiring / registration (DOM listeners, command registration,
   plugin `onload` bindings) — the "main" lives at the bottom, after everything
   it references exists

- Export at the declaration site (`export function …`) — no export block at the
  bottom, no `export default`.
- Hoisting note: `function` declarations hoist (order is free); `const` arrow
  functions do not — another reason helpers sit above the wiring that calls them.
- Same layout applies to plain JavaScript files.

## Directory structure (canonical minimum)

Ecosystem-standard shape. An existing repo's layout always wins over this — check
before creating directories.

```
<project>/                      # single package
├── package.json
├── tsconfig.json               # strict: true
├── src/                        # kebab-case.ts; index.ts = entry, thin
│   └── *.test.ts               # tests colocated with source
└── dist/                       # build output — gitignored, never edited

<monorepo>/                     # workspace variant (pnpm)
├── pnpm-workspace.yaml
├── tsconfig.json               # strict base; packages extend
└── packages/
    └── <pkg>/                  # each = the single-package shape above
```

- Minimum viable: `package.json` + `tsconfig.json` + `src/index.ts`.
- Entry files stay thin — wiring only, logic in modules (same rule every language).

## Testing

- jest (workspace configs exist). Tests colocated per package convention;
  red-green per `/tdd`.

## Tooling

- prettier + eslint NOT yet configured in trello-cli — `[CHORE]` candidate.
  Until then: 2-space indent, semicolons, single quotes, match the file you're in.
- `tsc --noEmit` is the cheap verify gate; run it before claiming done.
- ESLint: real projects SHOULD own a project-local `eslint.config.js` — flat
  config's ancestor-directory search resolves the nearest one first, so a
  project config always wins over the global fallback with zero setup. The
  global `~/dev/eslint.config.js` exists only to catch loose scratch files
  under `~/dev` that have no project of their own; it is not a substitute for
  a project deciding its own rules (react rules firing on a non-react repo,
  wrong parser version, etc. are the failure mode of relying on it long-term).

## Appendix — HTML / CSS / JSON / YAML (thin rules)

- HTML: semantic elements over `div` soup; every `img` has `alt`; forms have labels.
- CSS: class naming `kebab-case`; SHOULD use custom properties for repeated values
  (DRY knowledge rule); AVOID `!important`.
- JSON: no comments, no trailing commas (it's data, not config prose); 2-space indent.
- YAML: 2-space indent, never tabs; quote strings that look like other types
  (`"no"`, `"3.10"`, `"08:00"`); anchors/aliases are AVOID (unreadable to reviewers).
