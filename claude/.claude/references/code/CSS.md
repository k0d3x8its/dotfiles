# CSS — stylesheet standard

Scope: CSS — plain stylesheets, and CSS embedded via CSS-in-JS/CSS modules in
a JS/TS project (this file governs the styling rules; `TYPESCRIPT.md` governs
the surrounding component code). Strength vocabulary per `CODE-STANDARD.md`.

## Naming

- Class names: `kebab-case` (`nav-item`, not `navItem`/`nav_item`).
- BEM (`block__element--modifier`) SHOULD be used for component-scoped styles
  in a non-framework stylesheet (`card__title--active`) — makes specificity
  and ownership legible from the name alone. Not required inside a
  CSS-Modules/styled-components/Tailwind-class context, which already scopes
  by construction.
- IDs are AVOID as style hooks (`#header` in a stylesheet) — reserve `id` for
  JS hooks and anchor targets; an ID selector's specificity (0,1,0,0) is hard
  to override later and usually signals a one-off that should've been a class.

## Specificity & selectors

- Prefer the lowest-specificity selector that does the job — a single class
  selector over a chained descendant selector (`.card-title` over
  `.card .header .title`) where possible; deep nesting couples the selector
  to a DOM shape that will eventually change.
- `!important` is AVOID — it breaks the cascade's normal override order and
  the next person has no clean way to beat it except another `!important`.
  Legitimate uses (utility classes that must always win, third-party CSS
  overrides) MUST carry a why-comment.
- Universal (`*`) and overly broad tag selectors (`div { ... }`) are AVOID
  outside a deliberate reset/normalize stylesheet.

## Custom properties (variables)

- Repeated literal values (colors, spacing units, font sizes used more than
  once) MUST become CSS custom properties (`--color-primary`, `--space-md`) —
  same DRY-knowledge rule as a magic number in code (`CODE-STANDARD.md`).
- Declare custom properties at `:root` for global tokens; scope
  component-local ones to the component's own selector.
- Naming: `--<category>-<name>[-<variant>]` (`--color-border-hover`,
  `--space-4`) — grouped by category so related tokens sort together.

## Layout

- Flexbox for one-dimensional layout (a row or a column of items); CSS Grid
  for two-dimensional layout (rows AND columns together) — picking the tool
  that matches the actual layout shape avoids fighting the model later.
- `position: absolute`/`fixed` are AVOID for layout that flex/grid can express
  natively — reserve them for genuine overlay/sticky-UI cases (tooltips,
  modals, sticky headers).
- Units: `rem` for font sizes and spacing (scales with user's root font-size
  preference — an accessibility win over hardcoded `px`); `px` acceptable for
  borders and other true single-pixel details; `%`/`fr`/`vw`/`vh` for
  proportional/viewport-relative sizing.

## Responsive design

- Mobile-first: base styles unqualified, `min-width` media queries layer on
  larger-viewport overrides — not the reverse (`max-width` cascading down),
  which fights the natural cascade order.
- Breakpoints SHOULD be defined as custom properties or a documented constant
  set, not repeated magic pixel values scattered across media queries.
- `clamp()`/`min()`/`max()` SHOULD be preferred over a media-query breakpoint
  when the goal is smooth scaling (fluid type/spacing) rather than a genuine
  layout change at a threshold.

## Accessibility

- Contrast: text MUST meet WCAG 2.1 AA contrast ratio (4.5:1 normal text,
  3:1 large text/UI components) against its background.
- `:focus-visible` MUST style a visible focus state — do not remove the
  browser default (`outline: none`) without replacing it.
- `prefers-reduced-motion` SHOULD be respected — wrap non-essential
  animation/transition in `@media (prefers-reduced-motion: no-preference)`.
- `prefers-color-scheme` SHOULD drive dark/light theming where the project
  supports both, rather than a JS-only toggle with no OS-preference default.

## Hygiene

- No dead/unused selectors left behind by markup changes — same dead-code
  rule as everywhere else (`CODE-STANDARD.md`).
- Vendor prefixes (`-webkit-`, `-moz-`) are AVOID hand-written — let
  Autoprefixer (via the build tool) generate them from a browserslist config,
  so the source stays prefix-free and the target matrix lives in one place.
- `@import` inside a CSS file is AVOID (blocks parallel download, serializes
  loading) — use the build tool's bundling/`<link>` tags instead.

## File layout (SHOULD — top to bottom, per stylesheet)

1. Custom property declarations (`:root { ... }`)
2. Reset/normalize rules (if not pulled from a library)
3. Base element styles (typography defaults, body, headings)
4. Layout/structural classes
5. Component classes
6. Utility/override classes
7. Media queries — colocated with the rule they modify (mobile-first,
   nested via a preprocessor/nesting spec) is preferred over one big
   media-query block at the file's end, for locality.

## Tooling

- Prettier is the authoritative formatter where configured; Stylelint is the
  authoritative linter — treat its findings as MUST-fix, not suggestions,
  where a project has it configured.
- Autoprefixer (via PostCSS/build tool) is the authoritative source of vendor
  prefixes — never hand-add one that a browserslist-driven tool would.
