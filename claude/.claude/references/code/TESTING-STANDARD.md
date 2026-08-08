# TESTING-STANDARD

Decision layer for "which test(s) does this change need" — this file does not teach
testing theory or restate what a skill already owns. Where a skill exists, this file
routes to it and stops. It only carries real content where no skill/tag already does.

**Rule strength vocabulary (RFC 2119, matches `CODE-STANDARD.md`):**

- **MUST / MUST NOT** — mandatory; a violation is a review finding.
- **SHOULD / SHOULD NOT** — recommended; deviate only with a stated reason.
- **AVOID** — allowed but a smell; expect it questioned at review.

**Read this before writing the first test of a change** — `/tdd`'s planning step
points here. Read the whole file once; after that, just the sections relevant to
what you're building (CLI/plugin/script vs. a browser app or game).

## Picking a test type — decision table

| Question about the change                                                                                                  | Test type                   | Route to                                                                                                                      |
| -------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Does one function/module do the right thing in isolation?                                                                  | Unit                        | `/tdd`                                                                                                                        |
| Do two or more real modules/processes/files work together correctly?                                                       | Integration                 | `/tdd` — see _Unit vs Integration_ below                                                                                      |
| Does the whole app actually run, end to end?                                                                               | System / E2E                | `/run` skill + `[UX]` tag                                                                                                     |
| Does it _feel_ right — fun, responsive, satisfying (games/interactive apps)?                                               | Playtesting                 | See _Playtesting_ below                                                                                                       |
| Does an exposed HTTP/RPC surface behave per its contract?                                                                  | API                         | Treat as integration testing against the real protocol (conditional — only when a project actually exposes one)               |
| Is the build minimally alive before you start working?                                                                     | Smoke                       | `make test` (or the project's fast suite) as pre-flight — same pattern `/mutation-testing` already requires before mutating   |
| Did this specific fix/change hold, narrowly?                                                                               | Sanity                      | `/trust-but-verify`                                                                                                           |
| Is it fast/scalable enough?                                                                                                | Performance                 | `[PERFORMANCE]` tag, `ce-performance-reviewer`/`ce-performance-oracle`                                                        |
| Is it exploitable?                                                                                                         | Security                    | `/code-sec`, `/threat-model`, `/bounty-hunter`, `ce-security-reviewer`                                                        |
| Is it usable/clear for a human?                                                                                            | Usability                   | `[UX]` tag                                                                                                                    |
| Does it work across the browsers/devices/OSes you target?                                                                  | Compatibility               | See _Compatibility_ below                                                                                                     |
| Does it work for a keyboard/screen-reader/low-vision user?                                                                 | Accessibility               | See _Accessibility_ below                                                                                                     |
| Does it hold up under concurrent users or sustained load?                                                                  | Load/Stress                 | See _Load/Stress_ below                                                                                                       |
| Did this change break something that worked before?                                                                        | Regression                  | `make test` (full suite, every time — see _Regression_ below)                                                                 |
| Is the _test suite itself_ strong, not just green? (white-box: does it exercise internal branches, not just entry points?) | Coverage/mutation/white-box | `/mutation-testing` — see _Coverage stance_ below                                                                             |
| Does a non-game app meet business/user requirements before shipping?                                                       | Acceptance                  | No formal UAT process here — `[VERIFY]`/`[UX]` tags are this environment's acceptance gate (games: see _Playtesting_ instead) |

If a row's route is a skill or tag, invoke it — do not restate its steps here.

## Unit vs Integration — the split `/tdd`'s own examples blur

`tdd/tests.md` calls good tests "integration-style" while showing single-function
Python examples — that phrasing describes _behavior-first_ testing, not literal
integration testing. The two are different tests with different costs:

- **Unit**: one function/module, in isolation, through its public interface. Fast,
  no real I/O, no real file system, no real subprocess. Mocks only at the boundaries
  `tdd/mocking.md` names.
- **Integration**: two or more REAL collaborators wired together — real buffers,
  real files, real subprocesses, a real headless runtime. Slower, but proves the
  seams actually fit.

This environment already writes real integration tests and just doesn't label them:
`claude_diff_spec.lua` drives real Neovim buffers and real disk writes;
`opencode_diff_spec.lua` drives a real toggleterm child process. Both are correctly
integration-level — keep writing this way, just know which kind you're writing so you
choose the right isolation (mock a payment API in a unit test; don't mock your own
buffer/file layer in an integration test that exists to prove it works for real).

**MUST**: know which kind you're writing before you write it. A test file mixing both
without saying so makes failures ambiguous — did the LOGIC break, or did the WIRING
break?

## Test pyramid stance

Unit at the base (most, fastest), integration in the middle (fewer, proves seams),
system/E2E and playtesting at the top (fewest, slowest, most valuable per test). AVOID
the inverted pyramid (`ANTI-PATTERNS.md` § Testing — "Ice Cream Cone"): more E2E/UI
tests than unit tests is slow and fragile. If you notice you're writing an E2E test to
check what a unit test could check faster, write the unit test instead.

## Playtesting (games and interactive/creative apps)

A distinct category from correctness testing: it answers "does this feel right," not
"is this correct." A perfectly-passing test suite can still ship an unfun game.

- **MUST NOT** substitute automated tests for playtesting on feel-driven mechanics
  (movement, timing, difficulty curve, input responsiveness) — write correctness
  tests for the systems (score math, save/load, collision detection), then playtest
  the feel separately.
- **SHOULD** capture playtesting as a `[UX]` TODO checklist (per that tag's existing
  "requires manual verification, don't automate" contract) with concrete success
  criteria — not a vague "try it and see."
- **SHOULD** playtest at a milestone, not only at the end: after core movement/input
  lands, after the first full level/loop, before any public share. Late-only
  playtesting finds "this isn't fun" too late to cheaply fix.
- AVOID confusing a bug (violates a spec) with a feel problem (matches spec, still
  doesn't feel good) — the fix for the first is code; the fix for the second is
  tuning numbers/timing, often through iteration, not a single patch.

## Compatibility (browser apps/games)

Real guidance, not a stub — this environment now targets browser delivery.

- **MUST** declare a target matrix explicitly before shipping: which browsers
  (current-2 versions of Chromium/Firefox/Safari is a sane default unless the user
  states otherwise) and which device classes (desktop/mobile/tablet) the project
  actually supports. An undeclared matrix means nothing was tested against anything.
- **MUST** use feature detection (`if ('IntersectionObserver' in window)`), never
  user-agent sniffing — UA strings lie and drift; feature checks don't.
- **SHOULD** test the real rendering engines, not just "looks fine in one browser."
  A local multi-browser check (or a service like BrowserStack if the project's scale
  justifies the cost) before any public release.
- **SHOULD** treat CSS/layout compatibility as a `[UX]` checklist item (visual, so
  it needs a human look) and JS-API compatibility as something `tsc`/`eslint`'s
  target settings can catch mechanically (set `target`/`lib` in `tsconfig.json` to
  match the declared matrix, don't guess).
- For games specifically: input compatibility (touch vs mouse vs gamepad) is its own
  compatibility axis, separate from browser/device — test each input method the game
  claims to support, don't assume mouse-tested implies touch-works.

## Accessibility (browser apps/games)

- **MUST**: semantic HTML over `div` soup, every `img`/icon-only control has an
  accessible name, every form control has a label — already stated in
  `HTML.md`'s Accessibility section; this is the testing side of that same rule.
- **MUST**: every interactive element reachable and operable by keyboard alone (Tab
  order makes sense, focus is visible, no keyboard trap). Test this by literally
  unplugging the mouse for one pass, not by reading the markup and assuming it works.
- **SHOULD**: run an automated baseline (axe-core, Lighthouse accessibility audit)
  as a cheap first pass — it catches contrast/label/ARIA mechanical violations — then
  a manual keyboard-only + screen-reader spot check for what automation can't judge
  (does the reading order make sense, is the experience actually usable, not just
  technically compliant).
- For games: full WCAG compliance is often not realistic for a canvas-rendered game
  (a game board isn't a form), but SHOULD still cover what's cheap and matters —
  colorblind-safe palettes or a colorblind mode for anything color-coded, remappable
  controls, a way to reduce motion/flashing (photosensitivity), and captions/visual
  cues for any audio-only signal. Don't let "it's a game, WCAG doesn't apply" become
  an excuse to skip the parts that cost little and help real players.

## Load/Stress

- For a client-rendered browser game/app with no backend: this is really a
  Performance question — frame-rate budget under worst-case scene complexity, memory
  growth over a long session, asset-load time on a throttled connection. Route to
  `[PERFORMANCE]`/`ce-performance-reviewer`, don't build separate load-testing infra
  for a system that has no server to load.
- The moment a project adds a backend/multiplayer/concurrent-user surface, classic
  load/stress testing becomes real: concurrent-connection ceilings, response time
  under N simultaneous users, graceful degradation vs. hard failure at the ceiling.
  At that point this file gets a real backend-load section — not written speculatively
  now (YAGNI — `CODE-PRINCIPLES.md`), because no current project has that surface.

## Structural — static analysis and coverage

- **Static analysis** is already policy, not a gap: the ALE/linter/formatter pipeline
  and `CODE-STANDARD.md`'s per-language delegation table ARE this environment's
  static-analysis story. Nothing new needed here.
- **Coverage stance — mutation testing over line-coverage %.** Line coverage answers
  "was this line executed," not "would a bug here be caught." `/mutation-testing`
  already answers the harder, more honest question — a mutation the suite doesn't
  catch is a real gap; a covered line with no meaningful assertion is a false sense
  of safety that coverage % can't see. **MUST NOT** adopt a generic "aim for N%
  coverage" target in this environment — if suite strength needs measuring, run
  `/mutation-testing` and act on survived mutations (they become `[TEST]` TODOs,
  closed via `/tdd`).

## Regression

`make test` (or the project's equivalent full-suite command) running the ENTIRE
suite on every change already IS full regression testing at this environment's scale
— cheap enough locally that partial/selective/progressive regression schemes would be
solving a problem that doesn't exist yet. **SHOULD NOT** build selective-test-run
infrastructure until suite runtime is itself painful enough to be a `[PERFORMANCE]`
concern — until then, running everything is the discipline, not a compromise.

## Manual vs Automated

Already a mature pattern, not a gap: the `[UX]` TODO tag IS this environment's manual-
testing contract ("requires manual verification of a flow or experience... don't try
to automate or simulate"). Automated is the default everywhere else. No new rule
needed — route manual-verification needs through `[UX]`, everything else is automated
by default.

## Related

- `/tdd` — unit/integration red-green methodology, mocking, interface design, deep
  modules, refactoring
- `/mutation-testing` — suite-strength measurement (this file's coverage stance)
- `/trust-but-verify` — sanity-check discipline before any done/works/fixed claim
- `/run` — system/E2E: launch and drive the real app
- `/code-sec`, `/threat-model`, `/bounty-hunter` — security testing
- `ANTI-PATTERNS.md` § 4 — testing anti-patterns (Ice Cream Cone, Fragile Test, Mock
  Everything, Happy-Path-Only, etc.) — read when a test smells wrong, not just when
  writing one
- `CODE-STANDARD.md` — error handling MUSTs (see its Hygiene section) and the
  per-language delegation table this file assumes
- `CODE-PRINCIPLES.md` — error-handling judgment (raise vs return-Result vs
  log-and-continue), TDD precedence, Deletion Test
