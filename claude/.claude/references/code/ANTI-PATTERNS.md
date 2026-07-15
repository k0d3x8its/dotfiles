# ANTI-PATTERNS.md

> Full anti-pattern and code smell taxonomy. Referenced by CODE-REFERENCE.md.
> Sources: Fowler (Refactoring 2nd ed), Brown et al (AntiPatterns), Mantyla,
> Meszaros (xUnit Test Patterns), general OO literature.

---

## 1. Code Smells (Fowler — Refactoring, 2nd ed)

These are symptoms in the code itself — not bugs, but signals that refactoring
is likely needed.

### Naming & Clarity
| Smell | Symptom |
|---|---|
| **Mysterious Name** | Name doesn't communicate purpose; requires reading implementation to understand |
| **Comments** | Comment explains WHAT the code does rather than WHY — sign the code itself is unclear |

### Duplication
| Smell | Symptom |
|---|---|
| **Duplicated Code** | Same or near-identical logic in more than one place |
| **Cut-and-Paste Programming** | Blocks copied and modified slightly rather than abstracted |
| **Repeated Switches** | Same switch/match block appears in multiple places; add a new case = multiple edits |

### Size & Complexity
| Smell | Symptom |
|---|---|
| **Long Function** | Function does too many things; hard to name, hard to test |
| **Long Parameter List** | More than 3–4 parameters; usually means missing object or wrong boundary |
| **Large Class (God Class)** | One class accumulates too many responsibilities |
| **Divergent Change** | One class changed for many different reasons (low cohesion) |
| **Shotgun Surgery** | One logical change requires edits across many unrelated files |

### Data
| Smell | Symptom |
|---|---|
| **Global Data** | Mutable state reachable from anywhere; impossible to reason about scope |
| **Mutable Data** | Data that can be changed from many places; source of subtle bugs |
| **Data Clumps** | Same group of variables always travels together; should be an object |
| **Primitive Obsession** | Raw strings/ints/dicts used where a type, class, or enum would express intent |
| **Temporary Field** | Object field only set and used in certain circumstances; confusing when null/empty |
| **Data Class** | Class with only getters/setters and no behavior; data without logic belongs somewhere |

### Dependencies & Coupling
| Smell | Symptom |
|---|---|
| **Feature Envy** | Method uses another module's data more than its own; logic is in the wrong place |
| **Inappropriate Intimacy (Insider Trading)** | Module reaches into another's internals; violates encapsulation |
| **Message Chains** | `a.b().c().d()` — caller is coupled to a long chain of navigation |
| **Middle Man** | Class delegates almost everything to another class; provides no real value |
| **Alternative Classes with Different Interfaces** | Two classes do the same thing but with different function names |

### Inheritance
| Smell | Symptom |
|---|---|
| **Refused Bequest** | Subclass inherits methods/data it doesn't need or overrides to do nothing |
| **Parallel Inheritance Hierarchies** | Adding a subclass in one hierarchy forces adding one in another |

### Dead Weight
| Smell | Symptom |
|---|---|
| **Lazy Element** | Class or function so simple it adds no value; could be inlined |
| **Speculative Generality** | Hooks, abstractions, and parameters added for "future use" that never comes |
| **Dead Code** | Code that is never called or never reachable — delete it |
| **Lava Flow** | Dead/legacy code kept because no one knows what it does or whether it's safe to delete |

### Control Flow
| Smell | Symptom |
|---|---|
| **Loops** | Imperative loops that could be clearer as pipeline transforms (map/filter/reduce) |

---

## 2. OO Design Anti-Patterns

Structural problems in how objects and modules are organized.

| Name | Symptom | Fix |
|---|---|---|
| **Blob / God Object** | One object knows the state of the entire system and does most of the work | Extract classes; apply single responsibility |
| **Poltergeists** | Classes with brief lifespans and limited roles — appear, do one thing, disappear | Merge into caller or into a stateless function |
| **Boat Anchor** | Unused component kept "just in case" or "for later" | Delete it; version control is the history |
| **Golden Hammer** | One familiar tool used for every problem regardless of fit | Evaluate the problem first, then choose the tool |
| **Swiss Army Knife** | Interface tries to solve every case — complex, hard to implement, hard to use | Narrow the interface; add separate entry points for distinct use cases |
| **Spaghetti Code** | Control flow jumps unpredictably; no clear structure or module boundaries | Restructure; introduce seams and clear module boundaries |
| **Functional Decomposition** | OO language used procedurally — one God function, everything else is helpers | Reorganize around objects/modules with cohesive responsibility |
| **Input Kludge** | No consistent validation strategy for external input | Define system boundary; validate at entry, trust internally |
| **Magic Numbers/Strings** | Unexplained literals scattered through code | Named constants or enums |
| **Yo-Yo Problem** | Deep inheritance hierarchy forces constant jumping between classes to understand behavior | Prefer composition over inheritance |

---

## 3. Architectural Anti-Patterns

*(Brown et al — AntiPatterns, 1998)*

System and design-level problems.

| Name | Symptom | Fix |
|---|---|---|
| **Big Ball of Mud** | No discernible architecture; everything depends on everything | Enforce module boundaries; introduce seams gradually |
| **Stovepipe System** | Each subsystem is independent and non-reusable; no shared components | Extract shared modules; define integration contracts |
| **Vendor Lock-In** | System so tightly coupled to a specific tool/service that switching is prohibitive | Adapter pattern at the boundary; abstract external dependencies |
| **Reinventing the Wheel** | Building something that already exists as a well-supported library | Research before building |
| **Architecture by Implication** | No documented architecture; everyone assumes differently | Document decisions as ADRs; create architectural snapshot |
| **Design by Committee** | Architecture designed by consensus leads to inconsistency and compromise | Single architect owns decisions; others review |
| **Magic Pushbutton** | Business logic lives in UI handlers or event callbacks rather than a domain layer | Extract domain layer; UI only calls it |
| **Ambiguous Viewpoint** | Architecture diagrams mix concerns (runtime, code structure, deployment) in one view | Separate views: code structure, runtime, deployment |
| **Abstraction Inversion** | High-level constructs built on lower-level ones that are re-exposed upward | Keep abstractions directional — only build upward |
| **Accidental Complexity** | Complexity introduced by the implementation choices, not by the problem | Simplify; ask "does this complexity come from the domain or from our solution?" |

---

## 4. Testing Anti-Patterns

*(Meszaros — xUnit Test Patterns; general practice)*

| Name | Symptom | Fix |
|---|---|---|
| **Ice Cream Cone** | More UI/E2E tests than unit tests — inverted pyramid; slow and fragile | Shift coverage down to unit and integration layer |
| **Obscure Test** | Hard to understand what behavior is being verified or why | Rename; extract setup; one logical assertion per test |
| **Eager Test** | Single test verifies multiple unrelated behaviors | Split into focused tests |
| **Mystery Guest** | Test depends on external file, database state, or global variable not set in the test | Make all setup explicit in the test body |
| **Fragile Test** | Test breaks when refactoring internal structure, not behavior | Test through public interface only |
| **Slow Test** | Test suite too slow to run on every change | Mock at system boundaries; reduce I/O in unit tests |
| **Mock Everything** | Internal collaborators mocked; tests verify wiring not behavior | Only mock at system boundaries (external APIs, time, FS) |
| **Happy Path Only** | Tests cover only the expected case; no edge cases, error paths, or boundary conditions | Add tests for each failure mode the code handles |
| **Test the Framework** | Tests verify behavior of the language or library, not application logic | Test only code you own |
| **Interacting Tests** | Tests share state; order-dependent; one failure cascades | Isolate each test; reset state in setup/teardown |
| **Irrelevant Information** | Test contains data that has no bearing on what is being verified | Use minimal, intentional fixtures |
| **Hard-Coded Test Data** | Magic values in assertions with no explanation | Named constants or factory functions |

---

## Quick Reference — When You Smell Something

Not sure what you're looking at? Start here:

- Hard to name → **Mysterious Name**, **Large Class**, **Long Function**
- Breaks in many places at once → **Shotgun Surgery**
- Changes for many reasons → **Divergent Change**
- Reaching into another module → **Inappropriate Intimacy**, **Feature Envy**
- Test keeps breaking after refactor → **Fragile Test**, **Mock Everything**
- Nobody knows what the code does → **Lava Flow**, **Mysterious Name**, **Spaghetti Code**
- "Just in case" code → **Speculative Generality**, **Boat Anchor**
- Every problem uses same tool → **Golden Hammer**
- No one knows the architecture → **Architecture by Implication**, **Big Ball of Mud**
