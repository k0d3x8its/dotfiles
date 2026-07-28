# HTMX — hypermedia standard

Scope: htmx-driven markup — server-rendered HTML augmented with `hx-*`
attributes instead of a client-side JS framework. Read alongside `HTML.md`
(document structure, semantics, accessibility all still apply); this file
covers only what htmx adds. Strength vocabulary per `CODE-STANDARD.md`.

## Core discipline — hypermedia, not JSON-API-in-disguise

- Endpoints hit by `hx-get`/`hx-post`/etc. MUST return HTML fragments, not
  JSON — htmx's entire model is swapping server-rendered markup into the DOM.
  A JSON endpoint reused for htmx (with client-side templating bolted on) is
  the anti-pattern this tool exists to avoid (HATEOAS/hypermedia-as-the-
  engine-of-application-state, per the htmx project's own stated philosophy).
- Server-side templates render partial fragments for htmx requests and full
  pages for direct navigation — detect via the `HX-Request` header (htmx sets
  it on every htmx-issued request) rather than duplicating routes.
- Locality of Behaviour (htmx's own stated principle): the `hx-*` attributes
  on an element MUST make its behavior legible by reading that element alone
  — avoid scattering the wiring for one interaction across a separate JS file
  the reader has to cross-reference.

## Attributes

- `hx-target` SHOULD be explicit (`hx-target="#result"`) rather than relying
  on the implicit default (the triggering element itself) once a swap
  target isn't the element that triggered it — implicit targeting reads
  fine until the DOM shifts around it.
- `hx-swap` SHOULD be stated explicitly when it's not the default
  (`innerHTML`) — `outerHTML`, `beforeend`, `afterbegin` etc. change the
  DOM structure, not just content, and are easy to get backwards.
- `hx-trigger` MUST be explicit for anything other than the element's natural
  default event — don't rely on guessing htmx's per-element default
  (`click` for most, `change` for `select`/`input`/`textarea`, `submit` for
  `form`).
- `hx-indicator` SHOULD be set on any request with perceptible latency — a
  swap with no loading state reads as a stall, not a slow request.
- `hx-confirm` MUST guard destructive actions (delete, irreversible mutation)
  — same principle as a confirmation dialog in any other UI, just declared
  inline.
- `hx-boost` on a `<form>`/`<a>` progressively enhances normal navigation into
  an ajax swap — SHOULD be preferred over hand-written `hx-get`/`hx-post` on
  every link/form when the goal is just "make normal navigation feel like an
  SPA," since the non-JS fallback (plain link/form submit) keeps working for
  free.

## Progressive enhancement

- Every htmx-augmented element MUST function (degraded, full-page-reload
  behavior) with JavaScript disabled — `hx-boost`'d links/forms have this
  automatically since they layer onto real `href`/`action` attributes;
  anything using `hx-get`/`hx-post` directly on a non-link/non-form element
  (a `<button>` with `hx-post`) does not get this for free and needs a
  `<noscript>` fallback or a deliberate accepted exception, stated as such.
- MUST NOT put the only path to core functionality behind an htmx-only
  interaction with no server-rendered fallback route.

## Security

- CSRF: htmx requests carry cookies like any other browser request — the
  server's normal CSRF-token mechanism (hidden form field or a header htmx is
  configured to send via `hx-headers`/a `htmx:configRequest` listener) MUST
  still run; htmx does not exempt a request from the app's CSRF policy.
- Server MUST treat `HX-Request`/`HX-Target`/`HX-Trigger` headers as hints
  for response shaping only, never as an auth or authorization signal — they
  are client-supplied and trivially spoofable.
- Fragment responses MUST escape/sanitize the same way full-page responses
  do — a partial is still HTML reaching the browser; templating-engine
  auto-escaping applies equally.

## Accessibility

- A swapped-in fragment that changes page state meaningfully (new content,
  error message, form result) SHOULD update inside (or be paired with) an
  `aria-live` region so screen-reader users get the update announced —
  htmx doesn't do this automatically, since it's a DOM diff, not a page
  navigation the AT can hook.
- Focus management: after a swap that removes the focused element (e.g. a
  "delete row" swap), move focus somewhere sensible (the next row, a
  container, back to a trigger) — don't leave focus lost on a
  now-detached node.

## Testing

- Server-rendered fragment routes are testable as plain HTTP endpoints
  (request in, HTML string out) — no browser needed for the bulk of
  coverage; reserve a browser-driven test (Playwright/Cypress) for the
  actual swap/interaction behavior, not for re-verifying markup shape.

## Tooling

- No htmx-specific linter exists; `HTML.md`'s tooling (Prettier, an
  accessibility linter, an HTML validator) still applies to the markup
  htmx attributes sit on.
