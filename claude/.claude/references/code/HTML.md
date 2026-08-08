# HTML — markup standard

Scope: HTML — standalone static pages and templates, and HTML embedded in a
JS/TS framework (JSX/TSX handles most markup in that case; this file still
governs any literal `.html` file — entry shells, email templates, static
sites). Strength vocabulary per `CODE-STANDARD.md`.

## Document structure

- `<!DOCTYPE html>` MUST be the first line — no quirks mode.
- `<html lang="...">` MUST declare a language — screen readers and translation
  tools depend on it; missing `lang` is a WCAG 3.1.1 failure.
- `<head>` MUST include `<meta charset="utf-8">` (first child of `<head>`,
  before any content that could be misinterpreted without it) and
  `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- One `<title>` per document, descriptive of the page, not the site name alone.
- `<meta name="description">` SHOULD be present for any page meant to be
  indexed or shared.

## Semantic elements — MUST over `div`/`span` soup

- Use the element whose native semantics match the content's role:
  `<header>`, `<nav>`, `<main>` (exactly one per page), `<article>`,
  `<section>`, `<aside>`, `<footer>`. A `<div>` is the fallback only when no
  semantic element fits — not the default.
- Headings (`<h1>`–`<h6>`) MUST form a single logical outline — no skipped
  levels (`<h2>` directly to `<h4>`), and exactly one `<h1>` per page/document
  (per the current HTML spec's single-`<h1>`-per-document guidance, not the
  older every-`<section>`-resets-the-outline model — don't rely on the
  deprecated outline algorithm).
- Lists (`<ul>`/`<ol>`/`<dl>`) for actual list content, not `<br>`-separated
  `<div>`s — screen readers announce list semantics ("list, 4 items").
- `<button>` for actions, `<a href>` for navigation — MUST NOT use a `<div
onclick>` for either; keyboard/focus/role semantics come free with the
  correct element and are easy to get wrong reimplementing them.

## Accessibility (WCAG 2.1 AA baseline) — MUST

- Every `<img>` MUST have an `alt` attribute — descriptive text for meaningful
  images, `alt=""` (empty, not omitted) for purely decorative ones.
- Every form control MUST have an associated `<label>` (`for`/`id` pair, or
  the control nested inside the label) — a `placeholder` is not a label
  substitute (it disappears on input and fails contrast checks).
- Interactive elements MUST be reachable and operable by keyboard alone (tab
  order follows DOM order; avoid positive `tabindex` values — they fight the
  natural order).
- Color MUST NOT be the only signal conveying information (error states,
  required fields, status) — pair it with text, icon, or pattern.
- ARIA is a last resort, not a first choice: prefer the native semantic
  element; when ARIA is genuinely needed (a custom widget with no native
  equivalent), follow the WAI-ARIA Authoring Practices Guide (APG) patterns
  exactly — a wrong `role`/`aria-*` value is worse than none, since it
  overrides the browser's own accessibility tree.
- Every interactive element needs a visible focus indicator — MUST NOT
  `outline: none` without providing an equivalent replacement.
- See also `HTMX.md` (hx-* attributes have their own accessibility rules —
  focus management on swap, `aria-live` regions) and `TESTING-STANDARD.md`
  (the testing side of these same rules).

## Attributes & syntax

- Attribute values MUST be quoted (double quotes, matching this repo's other
  markup conventions).
- Boolean attributes (`disabled`, `checked`, `required`) are written bare —
  no `disabled="disabled"` (HTML5 syntax, not XHTML).
- Void elements (`<img>`, `<br>`, `<input>`, `<hr>`, `<meta>`, `<link>`)
  MUST NOT be self-closed with `/>` in standard HTML parsing (harmless but
  non-idiomatic outside XHTML/JSX contexts) — plain `<img src="...">`.
- Custom data MUST use `data-*` attributes, never invented non-standard
  attributes.
- Inline `style=` and inline event handlers (`onclick=`) are AVOID — CSS
  belongs in a stylesheet, behavior in a script with an addEventListener,
  both for CSP compatibility and separation of concerns.

## Forms

- `<form>` MUST declare `method` explicitly (`get` for idempotent
  read/search, `post` for anything mutating).
- Input `type` MUST match the data (`email`, `tel`, `number`, `date`, ...) —
  gets the right mobile keyboard and browser-native validation for free.
- Every submit-capable form SHOULD have client-side validation as a UX
  convenience, but the server MUST re-validate — client validation is never
  the security boundary.

## Performance & loading

- Scripts SHOULD load with `defer` (execute in order, after parse) unless the
  script has no DOM dependency (`async` acceptable for fully independent
  scripts, e.g. analytics).
- Images SHOULD declare `width`/`height` (or `aspect-ratio` via CSS) to
  reserve layout space and prevent cumulative layout shift.
- `loading="lazy"` SHOULD be set on below-the-fold `<img>`s.

## File layout (SHOULD — top to bottom)

1. `<!DOCTYPE html>`, `<html lang>`
2. `<head>`: charset, viewport, title, description, then stylesheet links,
   then any preload/prefetch hints
3. `<body>`: `<header>` → `<nav>` (if present) → `<main>` → `<footer>`
4. Scripts at the end of `<body>` (or `<head>` with `defer`) — never
   render-blocking mid-body unless the script writes to that exact point.

## Tooling

- Prettier is the authoritative formatter where configured.
- An accessibility linter (axe, `eslint-plugin-jsxa11y` for JSX contexts) is
  the authoritative check for the WCAG rules above where present — treat its
  findings as MUST-fix, not suggestions.
- HTML validator (W3C validator or `html-validate`) catches structural
  errors (unclosed tags, duplicate `id`s, invalid nesting) a formatter won't.
