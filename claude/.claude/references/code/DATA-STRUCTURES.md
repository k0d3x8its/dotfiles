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
not selection. **Why** states the tradeoff the default is actually buying — read it
before arguing for the escalated structure on a hunch; if the stated tradeoff doesn't
apply to your scenario, the escalation likely doesn't either.

## Decision table

| Scenario                                       | Default                                              | Why                                                                                          | Escalate when                                                                                 | Complexity (default)                      |
| ---------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Membership test ("is X in this set?")          | Hash set                                             | O(1) avg beats every ordered alternative when order doesn't matter                           | Set is huge + memory-bound and false positives are tolerable → bloom filter                   | O(1) avg lookup                           |
| Ordered + unique                               | Sorted array / tree-backed ordered set               | Sorted storage buys binary search and range queries for free; a hash set can't order         | Frequent inserts into the middle at scale → balanced-tree structure                           | O(log n) insert/lookup                    |
| Key → value                                    | Hash map                                             | O(1) avg get/set with no ordering cost paid unless the scenario needs order                  | Need insertion-order iteration cheaply, or key range queries → ordered map                    | O(1) avg get/set                          |
| One key → many values                          | Hash map of key → list/set                           | Reuses the plain hash map instead of a bespoke multimap type most stdlibs lack               | Values need dedup per key → hash map of key → set, not list                                   | O(1) avg get, O(k) per key                |
| LRU / bounded cache                            | Hash map + doubly-linked list (or stdlib LRU helper) | The two structures combined give O(1) touch+evict; either alone can't do both                | Cache is distributed/shared across processes → external cache (Redis etc.)                    | O(1) get/put                              |
| FIFO / LIFO                                    | Array-backed deque / stack                           | Both ends O(1) without the pointer-chasing overhead of a linked list                         | Producer and consumer run on different threads/processes → a real queue                       | O(1) push/pop                             |
| Priority / "smallest (or largest) next"        | Binary heap                                          | O(log n) push/pop beats a sorted structure's O(n) insert for a stream of arriving items      | Need to change an item's priority in place frequently → indexed/decrease-key heap             | O(log n) push/pop                         |
| Adjacency / graph relationships                | Adjacency list (map of node → neighbors)             | Sparse graphs (edges ≪ n²) waste no space on absent edges, unlike a matrix                   | Dense graph (edges ≈ n²) → adjacency matrix instead                                           | O(V+E) traversal                          |
| Dynamic connectivity ("are X and Y linked?")   | Union-Find / disjoint-set (with path compression)    | Near-O(1) amortized union/find beats re-traversing the graph on every connectivity query     | Need to also enumerate a component's members often → adjacency list/set alongside             | ~O(1) amortized (α(n))                    |
| Append-heavy sequence                          | Dynamic array (amortized append)                     | Amortized O(1) append with cache-friendly contiguous storage beats linked-list overhead      | Frequent inserts/removals at the front or middle → linked list or deque                       | O(1) amortized append                     |
| Random-access sequence                         | Dynamic array                                        | O(1) index is the whole point; anything else pays for access you're not using                | Access pattern is actually sequential-only → don't pay for random access you don't use        | O(1) index                                |
| Prefix / autocomplete search over strings      | Hash set/map of the whole strings                    | A flat set is simpler and fine until prefix queries actually dominate the workload           | Prefix queries (autocomplete, routing tables) are frequent and the string set is large → trie | O(m) per prefix (trie, m = prefix length) |
| Dense boolean flags over a small integer range | Bitset / bit vector                                  | Packs one bit per flag instead of a byte-or-more per bool — memory win at scale              | Range isn't small/dense (sparse indices, non-integer keys) → hash set instead                 | O(1) per flag, O(n/w) space               |
| Spatial / range query (nearest, "within box")  | Sort + binary search on one dimension                | Sorting is the boring default; a spatial index only earns its complexity under real 2D+ load | True multi-dimensional nearest-neighbor/range queries at scale → k-d tree / R-tree / quadtree | O(log n) (1D), varies (spatial index)     |
| Immutable / frozen record                      | Language's immutable record/tuple type               | Prevents accidental mutation and documents intent; no runtime cost over a mutable struct     | Record has 4+ related fields threatening Primitive Obsession → see cross-link below           | O(1) field access                         |
| Bag of loose primitives being passed together  | Stop — this is a smell, not a structure choice       | No structure fixes a design smell — see cross-link below                                     | Always — see cross-link below                                                                 | n/a                                       |

## Related

- `ANTI-PATTERNS.md` — Primitive Obsession, Data Clumps (the "bag of primitives" row above
  is a pointer here, not a structure recommendation)
- `CODE-PRINCIPLES.md` — YAGNI, rule-of-three (governs every "escalate when" column)
- `ALGORITHMS.md` — sibling file; algorithm selection over these structures
- Per-language appendices (`PYTHON.md`, `TYPESCRIPT.md`, `LUA.md`, `SOLIDITY.md`,
  `BASH.md`, `ARDUINO.md`) — concrete API for each scenario in this table
- `CODE-STANDARD.md` — reading protocol (load core + one language file)
