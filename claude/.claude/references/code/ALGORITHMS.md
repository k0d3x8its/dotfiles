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
not assumed).

## Decision table

| Scenario                              | Approach                                                           | Complexity               | Note                                                                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Search / lookup                       | Hash map lookup; binary search on sorted data                      | O(1) / O(log n)          | Linear scan only for genuinely small/unsorted n — state the bound, don't guess                                                       |
| Sort + sort-key                       | Stdlib sort with a key function                                    | O(n log n)               | Never hand-roll a sort; a custom comparator/key is fine, a custom algorithm isn't                                                    |
| Dedup                                 | Hash set of seen keys while iterating once                         | O(n)                     | Preserve order only if the scenario needs it — that costs an extra structure, not free                                               |
| Group-by / aggregate                  | Hash map of key → accumulator, single pass                         | O(n)                     | Stdlib groupby/reduce helpers over manual accumulation loops where available                                                         |
| Fuzzy / approximate match             | Library string-distance or search-index function                   | Varies (library-defined) | This is the row most likely to be reinvented badly — always a library, never hand-rolled                                             |
| Topological / dependency order        | Kahn's algorithm or DFS-based topo sort (library where one exists) | O(V+E)                   | Cross-link `DATA-STRUCTURES.md`'s adjacency-list row — this runs on that structure                                                   |
| Set operations (union/intersect/diff) | Native set type's built-in operators/methods                       | O(n+m)                   | Don't loop-and-compare by hand when the language's set type already does this                                                        |
| Pagination / chunking                 | Offset/cursor slicing on the existing sequence                     | O(page size)             | Cursor-based over offset-based once the underlying data can shift between pages                                                      |
| Retry / backoff                       | Exponential backoff with jitter, capped attempts                   | n/a                      | Error-handling judgment (raise vs retry vs log) is `CODE-PRINCIPLES.md`'s — this row is only the backoff shape, not whether to retry |

## Related

- `ANTI-PATTERNS.md` — Reinventing the Wheel (the governing rule for this whole file)
- `CODE-PRINCIPLES.md` — error-handling judgment (raise vs Result vs log-and-continue),
  referenced by the retry/backoff row
- `DATA-STRUCTURES.md` — sibling file; the structures these algorithms run over
- Per-language appendices (`PYTHON.md`, `TYPESCRIPT.md`, `LUA.md`, `SOLIDITY.md`,
  `BASH.md`, `ARDUINO.md`) — concrete API for each scenario in this table
- `CODE-STANDARD.md` — reading protocol (load core + one language file)
