# ALGORITHMS

Scenario-first selection: map the _problem_ to an approach, not the other way round.
Language-agnostic here. Where a language has a notable API or constraint for a
scenario below, its appendix's own `## Data structures & algorithms` subsection
records it — an absent row there means nothing language-specific worth stating,
not a gap (YAGNI applies to the reference itself, same as `CODE-PRINCIPLES.md`'s
stance on the appendices).

**Rule strength vocabulary (RFC 2119, matches `CODE-STANDARD.md`):**

- **MUST / MUST NOT** — mandatory; a violation is a review finding.
- **SHOULD / SHOULD NOT** — recommended; deviate only with a stated reason.
- **AVOID** — allowed but a smell; expect it questioned at review.

**MUST**: reach for a stdlib/library implementation before hand-rolling any row below —
see _Reinventing the Wheel_ in `ANTI-PATTERNS.md`. A hand-rolled sort/search/hash is a
review finding unless the library genuinely lacks the needed variant (stated explicitly,
not assumed). **Why** states the tradeoff the approach is actually buying — read it
before reaching for a fancier technique on a hunch.

## Decision table

| Scenario                                                  | Approach                                                                 | Why                                                                                                                                                    | Complexity                               | Note                                                                                                                                 |
| --------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Search / lookup                                           | Hash map lookup; binary search on sorted data                            | O(1)/O(log n) beat a linear scan once n is large enough to matter                                                                                      | O(1) / O(log n)                          | Linear scan only for genuinely small/unsorted n — state the bound, don't guess                                                       |
| Sort + sort-key                                           | Stdlib sort with a key function                                          | Stdlib sorts are tuned (often hybrid/adaptive) beyond what a hand-rolled sort will match                                                               | O(n log n)                               | Never hand-roll a sort; a custom comparator/key is fine, a custom algorithm isn't                                                    |
| Dedup                                                     | Hash set of seen keys while iterating once                               | One pass, O(1) avg membership check per item — nothing beats it for unordered dedup                                                                    | O(n)                                     | Preserve order only if the scenario needs it — that costs an extra structure, not free                                               |
| Group-by / aggregate                                      | Hash map of key → accumulator, single pass                               | Avoids sorting just to group; O(n) beats a sort-then-group's O(n log n) when order is irrelevant                                                       | O(n)                                     | Stdlib groupby/reduce helpers over manual accumulation loops where available                                                         |
| Fuzzy / approximate match                                 | Library string-distance or search-index function                         | Correct edit-distance/similarity math is easy to get subtly wrong by hand                                                                              | Varies (library-defined)                 | This is the row most likely to be reinvented badly — always a library, never hand-rolled                                             |
| Topological / dependency order                            | Kahn's algorithm or DFS-based topo sort (library where one exists)       | Both run in O(V+E) and correctly detect cycles as a side effect; ad hoc ordering doesn't                                                               | O(V+E)                                   | Cross-link `DATA-STRUCTURES.md`'s adjacency-list row — this runs on that structure                                                   |
| Set operations (union/intersect/diff)                     | Native set type's built-in operators/methods                             | The stdlib implementation is O(n+m) and correct; a hand-rolled double loop is O(n·m)                                                                   | O(n+m)                                   | Don't loop-and-compare by hand when the language's set type already does this                                                        |
| Pagination / chunking                                     | Offset/cursor slicing on the existing sequence                           | Reuses the existing sequence instead of materializing pages up front                                                                                   | O(page size)                             | Cursor-based over offset-based once the underlying data can shift between pages                                                      |
| Retry / backoff                                           | Exponential backoff with jitter, capped attempts                         | Jitter avoids synchronized retry storms; the cap bounds worst-case latency                                                                             | n/a                                      | Error-handling judgment (raise vs retry vs log) is `CODE-PRINCIPLES.md`'s — this row is only the backoff shape, not whether to retry |
| Shortest path / minimum steps                             | BFS (unweighted) or Dijkstra (weighted, non-negative)                    | BFS's O(V+E) is wasted precision-for-nothing on weighted graphs; Dijkstra is wasted complexity on unweighted ones — match the tool to the edge weights | O(V+E) (BFS) / O((V+E) log V) (Dijkstra) | Negative edge weights → Bellman-Ford instead of Dijkstra; state why negative weights exist                                           |
| Fixed-size window over a sequence (running sum/max/count) | Two-pointer / sliding window, incrementally updating as the window moves | Reuses the previous window's computed state instead of recomputing per window — turns an O(n·k) brute force into O(n)                                  | O(n)                                     | Only applies when the aggregate can be updated incrementally (sum, count, min/max via deque) — not every aggregate can               |
| Overlapping subproblems with optimal substructure         | Memoized recursion or bottom-up DP table                                 | Caching subproblem results avoids the exponential blowup of naive recursion                                                                            | O(n) to O(n²) (problem-dependent)        | Confirm optimal substructure actually holds before reaching for DP — see cross-link below                                            |

## Related

- `ANTI-PATTERNS.md` — Reinventing the Wheel (the governing rule for this whole file)
- `CODE-PRINCIPLES.md` — error-handling judgment (raise vs Result vs log-and-continue),
  referenced by the retry/backoff row; YAGNI/rule-of-three, referenced by the DP row's
  substructure check
- `DATA-STRUCTURES.md` — sibling file; the structures these algorithms run over
- Per-language appendices (`PYTHON.md`, `TYPESCRIPT.md`, `LUA.md`, `SOLIDITY.md`,
  `BASH.md`, `ARDUINO.md`) — concrete API for each scenario in this table
- `CODE-STANDARD.md` — reading protocol (load core + one language file)
