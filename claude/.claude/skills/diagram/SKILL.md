---
name: diagram
description: Generate a diagram image from a text description. Defaults to a Mermaid flowchart; renders a true UML activity diagram (fork/join, swimlanes) via PlantUML when the request says "uml" or passes -uml; renders a Shostack/SDL data-flow diagram with trust boundaries when the request says "dfd"/"data flow diagram" or passes -dfd (used by /threat-model). Outputs SVG/PNG/PDF, no editor dependency. Use when the user asks to draw a flowchart, decision tree, process flow, UML activity diagram, swimlane diagram, or DFD.
---

# diagram

Turn a plain-English description into a rendered diagram image. Two engines, one skill — the skill picks the engine, the user never has to.

## Quick start

`/diagram "user signs up, verify email, then activate"` → renders `./diagram.svg` (Mermaid).

`/diagram -uml "checkout: validate cart, then in parallel charge card and reserve stock, then confirm"` → renders `./diagram.svg` (PlantUML activity).

## Engine selection

Check these in order — **first match wins** (a request naming more than one is resolved
by this precedence, e.g. "UML-style DFD" is a DFD):

1. **DFD mode** — `-dfd` flag, the word "dfd", or "data flow diagram". Render a
   data-flow diagram. Engine is **Mermaid** (a DFD is a styled `flowchart`), but the
   notation and method differ — see [REFERENCE.md § DFD](REFERENCE.md#dfd). Input is
   either an element table (handed over by `/threat-model`, which owns DFD semantics)
   or a plain description. DFD wins over the `-uml`/"uml" triggers below.
2. **PlantUML** — `-uml` flag, the word "uml"/"UML", OR the request mentions swimlanes,
   fork/join, or explicit parallel branches (Mermaid can't do real swimlanes).
3. **Mermaid flowchart** — the default for everything else.

Do not ask the user which engine — infer it, state which you picked in the final report.

## Invocation

`/diagram [-uml|-dfd] "<description>" [output-path]`

- `-uml` — force PlantUML activity diagram
- `-dfd` — force Mermaid DFD (Shostack/SDL notation, trust boundaries)
- `output-path` — defaults to `./diagram.svg`. Extension (`.svg`/`.png`/`.pdf`) sets the format.

## Workflow

1. Pick engine per the rule above.
2. Translate the description into the engine's syntax:
   - **Mermaid**: decisions → `{}`, steps → `[]`, branches → labeled arrows. See [REFERENCE.md](REFERENCE.md#mermaid).
   - **PlantUML**: conditionals → `if/then/else/endif`, parallel → `fork/fork again/end fork`, lanes → `|Lane|`. See [REFERENCE.md](REFERENCE.md#plantuml).
   - **DFD**: element table / description → `flowchart LR` with `E/P/S` shapes, labeled data flows, trust boundaries as dashed `subgraph`s. See [REFERENCE.md § DFD](REFERENCE.md#dfd). Render via the `mermaid` engine — no separate render path.
3. Write the syntax to a temp file (`/tmp/diagram.mmd` or `/tmp/diagram.puml`).
4. Render via the helper, which checks the binary exists:
   ```
   scripts/render.sh <mermaid|plantuml> <temp-file> <output-path>
   ```
   It emits TWO files beside each other, same basename:
   - the rendered image (`<output-path>`)
   - the editable source — `.mmd` (Mermaid) or `.puml` (PlantUML)
5. Report BOTH paths. The source is the editable artifact: `.mmd` opens in
   mermaid.live / Miro / VS Code; `.puml` opens in any PlantUML editor or server.

## Requirements

- **Mermaid**: Node + `@mermaid-js/mermaid-cli` global (`npm install -g @mermaid-js/mermaid-cli`); `mmdc` on PATH.
- **PlantUML**: a JVM on PATH, plus either a `plantuml` command or `plantuml.jar` with `$PLANTUML_JAR` pointing at it. Many distro packages ship a `plantuml` wrapper that bundles the jar — `render.sh` prefers the wrapper and falls back to `$PLANTUML_JAR`.

`render.sh` prints a clear error naming the missing dependency if an engine isn't installed.
