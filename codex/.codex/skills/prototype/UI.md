# UI Prototype

Generate **several radically different UI variations** on a single route, switchable
from a floating bottom bar. User flips between variants in the browser, picks one
(or steals bits from each), then the rest get deleted.

If the question is about logic/state rather than what something looks like — wrong
branch. Use `LOGIC.md`.

## When this is the right branch

- "What should this page look like?"
- "Show me a few options for this dashboard before I commit."
- "Try a different layout for the settings screen."

## Two sub-shapes — strongly prefer A

A UI prototype is much easier to judge when it's against the rest of the app — real
header, real sidebar, real data. A standalone route is a vacuum; every variant looks
fine in isolation. Default to sub-shape A.

### Sub-shape A — adjustment to an existing page (preferred)

The route already exists. Variants render **on the same route**, gated by a `?variant=`
URL search param. Existing data fetching, params, and auth all stay — only the
rendering swaps.

If the prototype is for something that doesn't yet have a page but would naturally
live inside one — that's still sub-shape A. Mount the variants inside the host page.

### Sub-shape B — a new page (last resort)

Only when the thing being prototyped has no existing page to live inside.

Create a throwaway route following the project's existing routing convention. Name it
so it's obviously a prototype (include "prototype" in the path or filename). Same
`?variant=` pattern.

Before committing to sub-shape B: is there really no existing page this could be
embedded in?

## Process

### 1. State the question and pick N

Default to **3 variants**. Cap at 5. Write the plan in one line at the top of the file:

```
// Three variants of the settings page, switchable via ?variant=, on the existing /settings route.
```

### 2. Generate radically different variants

Each variant must be **structurally different** — different layout, different information
hierarchy, different primary affordance. Not just different colours or font sizes.

- Hold each to the page's purpose and the data it has access to
- Use the project's existing component library / styling system
- Export with a clear name: `VariantA`, `VariantB`, `VariantC`

If two drafts come out too similar, redo one with explicit constraint: "do not use a
card grid", "put the primary action in the header instead", etc.

### 3. Wire them together

```python
# Pseudocode — adapt to your framework (Flask, FastAPI, Django, Next.js, etc.)
variant = request.args.get('variant', 'A')

context = {
    'variant': variant,
    'data': fetch_data(),
}
# render the matching variant template + the switcher component
```

For sub-shape A: keep all existing data fetching; only the rendered section changes.
For sub-shape B: throwaway route mounts the same switcher.

### 4. Build the floating switcher

Fixed-position bar at bottom-centre of the screen:

- **Left arrow** — previous variant (wraps around)
- **Variant label** — current key + name if exported, e.g. `B — Sidebar layout`
- **Right arrow** — next variant (wraps around)

Behaviour:
- Clicking updates the URL search param (shareable, reload-stable)
- Keyboard: `←` and `→` also cycle; don't intercept when an input/textarea is focused
- Visually distinct from the page (high-contrast pill, subtle shadow)
- **Hidden in production** — gate on `DEBUG=True`, `NODE_ENV !== 'production'`, or
  equivalent so a stray merge can't ship the bar to users

### 5. Hand it over

Surface the URL and `?variant=` keys. The interesting feedback is usually:
"I want the header from B with the sidebar from C" — that's the actual design.

### 6. Capture the answer and clean up

Once a variant wins:
- **Sub-shape A** — delete losing variants and the switcher; fold the winner into the
  existing page
- **Sub-shape B** — promote the winning variant to a real route, delete the throwaway
  route and switcher

Record which variant won and why (commit message or NOTES.md).

## Anti-patterns

- **Variants that differ only in colour or copy** — that's a tweak, not a prototype
- **Sharing too much between variants** — a shared header is fine; a shared layout
  defeats the point; each variant must be free to discard the layout
- **Wiring variants to real mutations** — keep prototypes read-only; point mutations
  at a stub if needed
- **Promoting prototype code directly to production** — rewrite it properly; prototype
  code was written under "no tests, no error handling" constraints
