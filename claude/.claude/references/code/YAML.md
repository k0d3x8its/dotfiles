# YAML — data-format standard

Scope: YAML config/rule files with no host language of their own — CI workflows
(`.github/workflows/*.yml`), `code-sec`'s ast-grep rule files, `sgconfig.yml`,
and similar. Strength vocabulary per `CODE-STANDARD.md`.

## Rules

- 2-space indent, never tabs.
- Quote strings that look like other types (`"no"`, `"3.10"`, `"08:00"`) — YAML's
  implicit typing silently coerces unquoted lookalikes.
- Anchors/aliases (`&`/`*`) are AVOID — unreadable to reviewers scanning a diff;
  prefer duplicating the block if it's short, or a generator script if it's not.
- Keys: `snake_case` unless the consuming tool's schema mandates otherwise
  (GitHub Actions uses `kebab-case` step `id`s and `camelCase` in a few places —
  match the schema, Neighbors win over this default).
- MUST NOT hand-edit a generated YAML file (anything a tool writes and owns) —
  regenerate via its source.

## Tooling

- `yamllint` is the authoritative linter where present.
