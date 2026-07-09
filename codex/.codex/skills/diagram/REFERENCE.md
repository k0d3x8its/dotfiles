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
