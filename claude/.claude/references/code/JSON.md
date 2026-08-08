# JSON — data-format standard

Scope: JSON config/state files not already covered by an ecosystem-specific file
(`package.json`/`tsconfig.json` stay documented in `TYPESCRIPT.md`'s directory
structure — this file is for JSON with no host language, e.g. `settings.json`,
hook configs, session/state files). Strength vocabulary per `CODE-STANDARD.md`.

## Rules

- No comments — it's data, not config prose. A file that needs comments SHOULD
  be YAML or TOML instead, not JSON with a `_comment` key worked around it.
- No trailing commas.
- 2-space indent.
- Keys: match the casing convention of the tool/schema consuming the file
  (Neighbors win — `CODE-STANDARD.md`'s casing hatch applies here too); default
  to `camelCase` for hand-authored config with no external schema.
- MUST NOT hand-edit a generated/lockfile-shaped JSON (anything with a header
  comment or tool saying so, or a `*-lock.json` name) — regenerate via its tool.

## Tooling

- `jq` is the authoritative validator/formatter where present — `jq empty
file.json` confirms parse-validity; `jq . file.json` reformats.
