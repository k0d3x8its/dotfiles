# DATA-STRUCTURES

Scenario-first selection: map the _problem_ to a structure, not the other way round.
Language-agnostic here. Where a language has a notable API or constraint for a
scenario below, its appendix's own `## Data structures & algorithms` subsection
records it — an absent row there means nothing language-specific worth stating,
not a gap (YAGNI applies to the reference itself, same as `CODE-PRINCIPLES.md`'s
stance on the appendices).

**Rule strength vocabulary (RFC 2119, matches `CODE-STANDARD.md`):**

- **MUST / MUST NOT** — mandatory; a violation is a review finding.
- **SHOULD / SHOULD NOT** — recommended; deviate only with a stated reason.
- **AVOID** — allowed but a smell; expect it questioned at review.

**Default** biases to the boring stdlib structure. **Escalate-when** names the specific
measured pain that earns the fancier one — same YAGNI/rule-of-three tone as
`CODE-PRINCIPLES.md`. Escalating without that measured pain is premature optimization,
not selection.

## Decision table

| Scenario                                      | Default                                              | Escalate when                                                                          | Complexity (default)   |
| --------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------- |
| Membership test ("is X in this set?")         | Hash set                                             | Set is huge + memory-bound and false positives are tolerable → bloom filter            | O(1) avg lookup        |
| Ordered + unique                              | Sorted array / tree-backed ordered set               | Frequent inserts into the middle at scale → balanced-tree structure                    | O(log n) insert/lookup |
| Key → value                                   | Hash map                                             | Need insertion-order iteration cheaply, or key range queries → ordered map             | O(1) avg get/set       |
| LRU / bounded cache                           | Hash map + doubly-linked list (or stdlib LRU helper) | Cache is distributed/shared across processes → external cache (Redis etc.)             | O(1) get/put           |
| FIFO / LIFO                                   | Array-backed deque / stack                           | Producer and consumer run on different threads/processes → a real queue                | O(1) push/pop          |
| Priority / "smallest (or largest) next"       | Binary heap                                          | Need to change an item's priority in place frequently → indexed/decrease-key heap      | O(log n) push/pop      |
| Adjacency / graph relationships               | Adjacency list (map of node → neighbors)             | Dense graph (edges ≈ n²) → adjacency matrix instead                                    | O(V+E) traversal       |
| Append-heavy sequence                         | Dynamic array (amortized append)                     | Frequent inserts/removals at the front or middle → linked list or deque                | O(1) amortized append  |
| Random-access sequence                        | Dynamic array                                        | Access pattern is actually sequential-only → don't pay for random access you don't use | O(1) index             |
| Immutable / frozen record                     | Language's immutable record/tuple type               | Record has 4+ related fields threatening Primitive Obsession → see cross-link below    | O(1) field access      |
| Bag of loose primitives being passed together | Stop — this is a smell, not a structure choice       | Always — see cross-link below                                                          | n/a                    |

## Related

- `ANTI-PATTERNS.md` — Primitive Obsession, Data Clumps (the "bag of primitives" row above
  is a pointer here, not a structure recommendation)
- `CODE-PRINCIPLES.md` — YAGNI, rule-of-three (governs every "escalate when" column)
- `ALGORITHMS.md` — sibling file; algorithm selection over these structures
- Per-language appendices (`PYTHON.md`, `TYPESCRIPT.md`, `LUA.md`, `SOLIDITY.md`,
  `BASH.md`, `ARDUINO.md`) — concrete API for each scenario in this table
- `CODE-STANDARD.md` — reading protocol (load core + one language file)
