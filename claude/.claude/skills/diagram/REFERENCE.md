# diagram — engine syntax reference

## Mermaid

Flowchart, top-down. Decisions `{}`, process steps `[]`, branches as labeled arrows.

```
flowchart TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```

Rendered with `mmdc -i <in.mmd> -o <out>`. Output format follows the `-o` extension (`.svg`/`.png`/`.pdf`).

## PlantUML

Activity diagram. Conditionals `if/then/else/endif`, parallel work `fork/fork again/end fork`, swimlanes `|Lane|`.

```
@startuml
start
if (condition?) then (yes)
  :action 1;
else (no)
  :action 2;
endif
fork
  :parallel task A;
fork again
  :parallel task B;
end fork
stop
@enduml
```

Swimlane variant:

```
@startuml
|User|
start
:submit form;
|System|
:validate;
if (valid?) then (yes)
  :persist;
else (no)
  |User|
  :show error;
endif
stop
@enduml
```

PlantUML writes output next to the `.puml` file by default (same basename). Force format with `-tsvg`/`-tpng`; `render.sh` handles the format flag and moves the result to the requested output-path.

## DFD

Data-flow diagram in the Microsoft SDL / Shostack convention — process-centric,
trust boundaries explicit. Engine is **Mermaid** (`flowchart LR`). `/threat-model`
owns the semantics and hands over an element table; this section is the render spec.

### Notation

| Element | Symbol | Mermaid mapping |
|---|---|---|
| External entity (actor, third party, anything you don't control) | rectangle | `E1[Customer]` |
| Process (code that transforms data) | circle / rounded | `P1((Wire System))` |
| Data store (DB, file, queue, log, backup) | cylinder | `S1[(Core DB)]` |
| Data flow | one-way labeled arrow (bidirectional = two arrows) | `E1 -- "wire request: PII, amount" --> P1` |
| Trust boundary (network perimeter, machine, privilege level, org boundary) | dashed box | `subgraph TB1 [Internet boundary]` + a `classDef` with `stroke-dasharray` |

Trust boundaries are `subgraph` blocks styled dashed via `classDef`. Assign the
class with `class TB1 boundary`:

```
flowchart LR
    classDef boundary fill:none,stroke:#c33,stroke-width:2px,stroke-dasharray:6 4

    E1[Customer]
    E2[Federal Reserve]

    subgraph TB1 [Bank network perimeter]
        P1((Wire System))
        S1[(Core DB)]
        S2[(Audit log)]
    end
    class TB1 boundary

    E1 -- "wire request: PII, amount" --> P1
    P1 -- "store txn: PII, amount" --> S1
    P1 -- "append: actor, amount" --> S2
    P1 -- "settlement: account, amount" --> E2
```

Rendered with `scripts/render.sh mermaid <in.mmd> <out.svg>` (same path as any
Mermaid diagram — DFD is a `flowchart`, no separate engine).

### Method rules

- **Label flows with the DATA, not the verb** — "PII + account number", not "sends".
  Carry a sensitivity tag (PII / credentials / regulated / public); risk-rank consumes it.
- **A DFD without trust boundaries is just a flowchart.** Every boundary crossing is
  where STRIDE threats concentrate — the crossing list IS the threat-enumeration input.
- **Level discipline:** L0 context diagram (whole system = one process) → L1 per critical
  business process. Stop decomposing when going deeper crosses no NEW trust boundary
  (Shostack's rule) — deeper adds noise, not threats.
- **Process-centric scoping:** diagram one critical business process end-to-end —
  people, technology, third parties. Mark where regulated/customer data crosses the
  network perimeter.
- **Stable numbered IDs** (`E1/P2/S3/F4/TB1`) on every element — the element table and
  the diagram share IDs, so update-mode diffs and code-sec mitigation greps stay mechanical.
- **Reject these at build time:** unlabeled arrows; a flow with no process at either end
  (data doesn't move itself); missing log/backup/monitoring stores (data exits there too);
  omitted third-party vendors; modeling every microservice instead of the critical process.
