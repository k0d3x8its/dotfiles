# format-triage.md — TRIAGE-BLOCK.md visual output format

Used by `/dev-brief triage` (instruction 14) to write `~/dev/TRIAGE-BLOCK.md`.
Open in Neovim → `:LivePreview` to render in browser with live-preview.nvim.

---

## Color Palette

### Tier headers

| Tier     | Hex       | Usage                        |
|----------|-----------|------------------------------|
| CRITICAL | `#ff1a1a` | `[BROKEN]` or keyword-match  |
| HIGH     | `#cc0000` | `[BLOCKER]` or keyword-match |
| MEDIUM   | `#e05000` | Default (no priority tag)    |
| LOW      | `#ffd700` | `[LOW]`                      |
| BACKLOG  | `#4d94ff` | `[BACKLOG]`                  |

### Annotation tags

| Tag             | Hex       |
|-----------------|-----------|
| `[BUG]`         | `#ff6b6b` |
| `[FEAT]`        | `#51cf66` |
| `[CHORE]`       | `#868e96` |
| `[TEST]`        | `#74c0fc` |
| `[RELEASE]`     | `#da77f2` |
| `[DECISION]`    | `#ffa94d` |
| `[INVESTIGATE]` | `#a855f7` |
| `[SYNC]`        | `#a9e34b` |
| `[WAITING]`     | `#adb5bd` |
| `[SECURITY]`    | `#2563eb` |
| `[DOCS]`        | `#63e6be` |
| `[PERFORMANCE]` | `#fd7e14` |

### Priority tags (match their tier color)

| Tag        | Hex       |
|------------|-----------|
| `[BROKEN]` | `#ff1a1a` |
| `[BLOCKER]`| `#cc0000` |
| `[LOW]`    | `#ffd700` |
| `[BACKLOG]`| `#4d94ff` |

---

## Output Structure

Write the file exactly as shown below. Replace `{...}` placeholders with live data.
Omit any tier section that has no TODOs. Do not add extra blank lines between items.

```markdown
# Triage Block

*Updated: {YYYY-MM-DD HH:MM} — run `/dev-brief triage` to refresh*
*{N} open TODOs across {P} projects*

---

## <span style="color:#ff1a1a;font-weight:bold;">🔴 CRITICAL</span>

- **[{project}]** <span style="color:{tag-hex};">[TAG]</span> {todo text truncated to 80 chars…}

## <span style="color:#cc0000;font-weight:bold;">🟥 HIGH</span>

- **[{project}]** <span style="color:{tag-hex};">[TAG]</span> {todo text}

## <span style="color:#e05000;font-weight:bold;">🔶 MEDIUM</span>

- **[{project}]** {todo text}

## <span style="color:#ffd700;font-weight:bold;">🟡 LOW</span>

- **[{project}]** <span style="color:{tag-hex};">[TAG]</span> {todo text}

## <span style="color:#4d94ff;font-weight:bold;">🔵 BACKLOG</span>

- **[{project}]** <span style="color:{tag-hex};">[TAG]</span> {todo text}

---

<span style="color:#555;font-size:0.85em;">~/dev/TRIAGE-BLOCK.md · powered by /dev-brief</span>
```

---

## Rules

- Strip priority tags (`[BROKEN]`, `[BLOCKER]`, `[LOW]`, `[BACKLOG]`) from displayed text — tier header already communicates that. Keep annotation tags visible with their color spans.
- Multiple annotation tags: render each as its own colored span inline.
- `⚠` and `⚑` prefixes: keep them before the project name.
- Sort within each tier: `⚠`/`[BROKEN]` items first, then alphabetically by project.
- Text truncation: 80 chars max, append `…` if longer (same as terminal output but slightly wider).
- No HTML comments, no cache data in this file — cache lives in `~/dev/.triage-cache`.
