# Mining `alibaba/open-code-review` for the code-analysis suite

> Working document, 2026-07-28. Produced from a read of branch
> `chore/code-quality-refs` (k0d3x8its/dotfiles) against a fresh clone of
> `alibaba/open-code-review` (main, Apache-2.0).
>
> **Status: discussion output. Not a plan, not grilled.** Feed this to a future
> session as input to `/brainstorm` → `/grill-me` → `/write-plan`, or to
> `/write-plan` directly for the items marked LOW RISK.
>
> **Framing rule for any session consuming this document:** the goal is not to
> port OCR. It is to use OCR as evidence about which mechanisms are worth
> having, then build those mechanisms natively against the existing suite's
> architecture and conventions. Where a mechanism does not change shape on
> contact with this environment, that is a signal it may not fit — re-examine
> rather than copy.
>
> **Reviewed 2026-07-28** (same session, before `/grill-me`): premises
> checked against the live repo. Findings + revisions live at
> `.work/todos/ocr-code-review-mining.md` — read that file alongside this one,
> it supersedes §9's sequencing for §4.1/§4.2/§4.3/§4.5.

---

## 1. Source material

**Local:** branch `chore/code-quality-refs`. Read via `git show
origin/chore/code-quality-refs:<path>` — no checkout required. Note that
`.work/todos/*`, `KNOWLEDGE.md`, `TODOS.md`, and `.memory/SESSION-LOG.md` are
git-crypted; a session without the key sees ciphertext.

**Upstream:** `https://github.com/alibaba/open-code-review`, Apache-2.0, Go +
TypeScript. Clone shallow to scratch to re-read:

```bash
git clone --depth 1 --filter=blob:none \
  https://github.com/alibaba/open-code-review.git
```

The documentation site (`open-codereview.ai/docs`) returns 403 to automated
fetches and the GitHub tree API is proxy-blocked in the web sandbox. Read the
repo directly; the README overstates and the source is more precise.

### Upstream files that matter

| Path                                                      | What lives there                                                        |
| --------------------------------------------------------- | ----------------------------------------------------------------------- |
| `internal/config/rules/system_rules.json`                 | glob → rule-doc map (26 entries + `default_rule`)                       |
| `internal/config/rules/rule_docs/*.md`                    | 27 per-file-type review checklists                                      |
| `internal/config/rules/system_rules.go`                   | 4-layer rule resolution + provenance + file filter                      |
| `internal/config/template/prompts/*.md`                   | the five prompt pairs (main / plan / filter / relocation / compression) |
| `internal/config/toolsconfig/tools.json`                  | the entire toolset — 6 tools                                            |
| `internal/config/allowlist/*.json`                        | supported file types, default exclude patterns                          |
| `internal/tool/code_comment.go`                           | comment parsing, category/severity normalisation                        |
| `internal/diff/relocation.go`                             | `ReLocateComment` — the positioning fallback                            |
| `internal/delegate/rulegroup.go`                          | `GroupRules` — file bundling by resolved rule text                      |
| `internal/scan/batch.go`                                  | batch strategies (`none` / `by-language` / `by-directory`)              |
| `skills/open-code-review-delegate/SKILL.md`               | the LLM-free delegation contract                                        |
| `plugins/open-code-review/claude-code/commands/review.md` | their Claude Code slash command                                         |

---

## 2. Constraints — the conventions any port must be rewritten into

These are observable signatures of the existing suite. They are the difference
between "we adopted an idea" and "we pasted a competitor's file." Every item in
§4 is filtered through them.

1. **Deterministic work becomes a tested Python script under `scripts/`, not
   prose.** Precedent: code-decay ships `percentile.py`, `scorer.py`,
   `labeler.py`, `interpret_selection.py`, `report_renderer.py`,
   `file_universe.py`, `shallow_guard.py` — each landed with its own test
   commit. OCR does the equivalent work in Go internals. Same instinct,
   different substrate. Anything mechanical borrowed from OCR lands as a
   tested script, not as instructions to the model.

2. **Rules are tiered and fixture-backed.** Precedent: code-sec's
   `rules/{precise,normal,noisy}/*.yml`, red-green against
   `fixtures/vuln-app/`, CWE-tagged, driven through one `sgconfig.yml`. OCR's
   `rule_docs/*.md` are unvalidated prose with no fixtures and no tiering —
   by this suite's own standard they would all be `noisy/`. This is the
   single strongest argument against taking OCR's rule text.

3. **Confidence is an argued choice, per skill.** code-crit uses binary
   `verified | unverified` — the 5-value behaviourally-anchored enum from
   `ce-code-review` was considered and deliberately rejected on KISS grounds.
   code-sec uses three tiers (`CONFIRMED` / `TRACED` / `CANDIDATE`). OCR has
   `category` and `severity` enums and **no confidence axis at all**. Do not
   import a third scheme.

4. **Field-test annotations.** Existing skills carry `(field-test 2026-07-07)`
   against claims that were actually run — the `grep -a` NUL-byte gotcha, the
   `ast-grep scan -r` vs `-c` distinction, the `rg` stdin hang. Nothing enters
   a skill as an assertion; it enters as a verified claim with a date. Ported
   mechanisms inherit this obligation.

5. **Cross-runtime obligation (ADR-0001).** Skills live at
   `claude/.claude/skills/<name>/` and mirror to `codex/.codex/skills/`.
   Anything depending on Claude-Code-only mechanics (the `Agent` tool's `model`
   parameter, `run_in_background`) cannot live in the shared core — it belongs
   in the Claude-side orchestration layer, with the portable half factored out.

6. **Findings exit through the planning-format layer.** `references/
planning-format-detect.md` decides FLAT vs NEW format; findings route to
   `TODOS.md` and spill to `.work/todos/<slug>.md` past ~150 words. OCR emits
   to stdout, a VS Code panel, or a PR comment. Any new output path must land
   in the existing routing, not beside it.

7. **Report-time honesty.** code-crit's existing discipline: a failed
   Sonnet-tier mega-spawn must be reported explicitly, because "a failed tier
   and a clean tier must never look the same to the reader," and "a clean run
   still emits both sections — no findings is signal, not silence." Any new
   stage that can fail inherits this.

---

## 3. Current state of the suite

Partitioned by **axis / territory**:

- **`code-crit`** — diff review. 12 personas. 4 Opus frontline (correctness,
  security, spec-compliance, adversarial) always fully isolated; Sonnet tier
  either mega-spawned (fast, default) or isolated (thorough). Stage-2 Opus
  advisor does normalisation → dedup → rerank. `scripts/fingerprint_group.py`
  proposes candidate dupe clusters (`file + line±3 + normalized-title`) but
  never decides. Output: Spec section + severity-grouped findings table.
- **`code-sec`** — repo-wide sweep. 6 phases: attack-surface inventory,
  gitleaks full-history, dependency audit, git-crypt coverage vs File Taxonomy,
  ast-grep tiered pack + rg, app-layer pass, harness surface. Taint-tracing
  discipline, 3 confidence tiers, an explicit Suppress list.
- **`code-decay`** — churn × complexity. Scripts and tests landed on this
  branch. **No `SKILL.md` yet.**

Supporting assets already owned: `references/code/{CODE-PRINCIPLES,
CODE-STANDARD,ANTI-PATTERNS,TESTING-STANDARD,PYTHON,TYPESCRIPT,BASH,LUA,
SOLIDITY,ARDUINO,CODE-REFERENCE}.md`.

OCR by contrast is partitioned by **file type**, is a single agent, and invests
most of its engineering in _not trusting the model_ for mechanical steps. The
overlap is small, which is what makes it worth mining.

---

## 4. Candidates — ranked, with the shape they take here

### 4.1 Glob → reference routing ★ highest value / low risk

**What OCR does.** `system_rules.json` maps 26 globs to `rule_docs/*.md`:
`"**/*.py": "python.md"`, `".github/workflows/**/*.{yaml,yml}":
"github_workflows.md"`, `"**/package.json": "package_json.md"`,
`"**/*{mapper,dao}*.xml"`, `"**/Cargo.toml"`, `"**/*.tf"`, and so on, with
`default.md` as fallback. Brace expansion is handled in `expandBraces`. Single
agent, one resolved checklist per file.

**Why it matters here.** The per-language references already exist and
**nothing routes them per-file into a review**. A persona reviewing a `.py`
hunk today gets `CODE-STANDARD.md` wholesale or nothing at all. `ARDUINO.md`
and `SOLIDITY.md` currently have no reader.

**How it changes shape.** OCR has one agent, so routing means "swap the whole
checklist." This suite has a persona axis OCR lacks, so routing is a **second
dimension**, and it should be targeted: inject the routed references into the
`PROJECT-STANDARDS` persona's prompt only. Correctness and security personas
do not need Python idiom rules — that separation is the entire reason the
roster is territory-partitioned.

Two consequences OCR structurally cannot have:

- A glob that matches files in the diff but resolves to **no reference file is
  a reportable coverage gap** — routes to `TODOS.md` as a `[CHORE]`. OCR's map
  is complete by construction, so it never surfaces one.
- Routing is testable in isolation. A `route_refs.py` with a table-driven test
  suite (path in → reference list out) fits convention #1 exactly, and gives a
  place for the brace-expansion and precedence edge cases to be pinned.

**Insertion points.**

- new: `claude/.claude/skills/code-crit/scripts/route_refs.py` + tests
- new: a routing table — colocate with the script or under
  `references/code/`; decide during `/write-plan`
- edit: `claude/.claude/skills/code-crit/personas/PROJECT-STANDARDS.md`
- edit: `code-crit/SKILL.md` Dispatch section (routed refs join the prompt)

**Depends on:** nothing. Can ship alone.

---

### 4.2 Finding anchoring — verbatim snippet + match ★ high value / low risk

**What OCR does.** The `code_comment` tool **requires** an `existing_code`
field — a verbatim snippet copied from the diff, described in the tool schema
as: _"uses a dynamic sliding window algorithm to match corresponding
consecutive lines in diff text... you must ensure the provided `existing_code`
actually exists in the diff text with exactly matching format."_ Comments carry
`category` (bug/security/performance/maintainability/test/style/documentation/
other) and `severity` (critical/high/medium/low), both normalised in
`internal/tool/code_comment.go`.

On match failure, `internal/diff/relocation.go` runs a **separate small LLM
call** (`re_location_task`) whose entire job is: _"Copy the relevant lines
VERBATIM from the diff — do not rewrite, reformat, or add anything. Strip
leading diff markers. Output ONLY a fenced code block."_ Then it retries the
match.

**Why it matters here.** code-crit personas emit `file:line` freehand. Nothing
verifies the line exists or that the described code is at it. Hallucinated
anchors are the signature failure mode of the entire LLM-review genre, and the
current pipeline has no defence against it.

**How it changes shape — and this is the interesting part.** Stage 2 already
builds canonical records `(file, line, title, persona, severity, confidence,
fix)`. Adding `existing_code` to that tuple makes anchoring a script in the
slot `fingerprint_group.py` already occupies.

OCR needs a second LLM call because it has no other model in the loop. **This
suite already has Stage-2 Opus sitting there with the diff.** So a failed
anchor is not a new call — it is an input to Stage 2. Cheaper, one fewer
moving part, and it fits the existing pipeline instead of bolting a stage onto
it.

And the failure behaviour differs on principle: OCR silently drops what it
cannot anchor. code-crit's stated rule is _"No suppression — every finding
surfaces with its confidence label."_ So an unanchorable finding is **forced to
`unverified` and surfaced**, not dropped. Same mechanism, opposite disposition,
derived from this suite's own commitments.

**Insertion points.**

- new: `code-crit/scripts/anchor_findings.py` + tests
- edit: `code-crit/SKILL.md` — persona output contract gains `existing_code`;
  Synthesis canonical-record step gains the anchor pass
- edit: every file in `code-crit/personas/` — output format line

**Depends on:** nothing, but touches all 12 persona files, so sequence it
before or well after 4.5.

**Watch:** the fast-mode Sonnet mega-spawn writes JSON to
`.work/scratch/code-crit-sonnet-findings.json`; the schema change lands in both
that shape and the inline pipe-row shape from isolated spawns. The SKILL.md
already documents both — keep them in sync.

---

### 4.3 Falsification discipline ★ high value / medium risk — consolidation

**What OCR does.** `review_filter_task` is a distinct stage that sees **only
the diff, no tools**, and is told:

> _"your task is NOT to verify whether all review comments are correct, but to
> filter out only those review comments that can be confirmed as incorrect
> based solely on the current diff... For review comments whose correctness
> cannot be determined from the diff alone, even if you find them suspicious,
> you should let them pass — because the Agent may have access to context that
> you cannot see."_

Core principle, stated outright: _"You need to falsify, not verify."_ Only kill
a comment when the diff supplies **direct counter-evidence**. Output is a bare
JSON array of comment IDs.

**Why it matters here.** Stage 2's responsibility #1 is "rerank, prune weak
ones, and may revise their `confidence` flag" — with full context and **no
stated burden of proof**. It can prune findings it merely dislikes. OCR's
version is both cheaper and epistemically tighter.

**How it changes shape — the real prize is not a new stage.** OCR needs a
separate pass because its reviewer is one agent and it needs an independent
checker. Stage 2 already exists; what it lacks is the burden of proof. That is
a paragraph, not a stage.

The larger opportunity: **this suite currently runs three different noise
policies that contradict each other.**

| Skill           | Policy                                                     |
| --------------- | ---------------------------------------------------------- |
| `code-sec`      | CONFIRMED / TRACED / CANDIDATE + an explicit Suppress list |
| `code-crit`     | _"No suppression — every finding surfaces"_                |
| `bounty-hunter` | reachability triage (separate scheme again)                |

A shared `references/code/FINDING-SURVIVAL.md` — cited by code-crit Stage 2,
code-sec's Suppress list, and bounty-hunter's triage — resolves a live
contradiction in the repo. OCR cannot have this: one tool, one pipeline. This
is the most genuinely-original item on the list, and OCR's contribution is one
principle sentence, not an architecture.

**Insertion points.**

- new: `claude/.claude/references/code/FINDING-SURVIVAL.md`
- edit: `code-crit/SKILL.md` Synthesis responsibility #1
- edit: `code-sec/SKILL.md` "Finding discipline" section — cite rather than
  restate
- edit: `bounty-hunter/SKILL.md`

**Depends on:** nothing mechanically, but it is a **judgement change across
three skills** and should be grilled before it is written. This is the item
most likely to be got wrong by writing it quickly.

---

### 4.4 Deterministic file selection ★ medium value / low risk — reuse

**What OCR does.** `internal/config/allowlist/supported_file_types.json` and
`default_exclude_patterns.json`, plus gitignore handling
(`internal/diff/gitignore.go`) and a user include/exclude filter layered into
rule resolution (`FileFilter`, `IsUserExcluded` / `IsUserIncluded`).

**Why it matters here.** code-crit pastes raw `git diff`. Lockfiles, generated
code, minified bundles, and vendored trees burn tokens and generate noise —
multiplied by persona count, and in fast mode multiplied again by diff size.

**How it changes shape.** **Reuse, do not write.** code-decay's
`scripts/file_universe.py` already enumerates and filters the repo. Diff-scoping
it is a parameter, not a new module — and sharing it means code-crit and
code-decay agree on what counts as a source file, which they currently do not.

OCR's `default_exclude_patterns.json` is tuned for Java/Maven monorepos and
should not be copied; the exclusion set here should be derived from this
repo's actual shape (`.work/`, `codex/` mirrors, `fixtures/vuln-app/` — note
that last one is _deliberately_ vulnerable code and must never be reviewed as
if it were production).

**Insertion points.**

- edit: `code-decay/scripts/file_universe.py` — add diff scoping + tests
- edit: `code-crit/SKILL.md` Quick start step 2

**Depends on:** code-decay's `SKILL.md` existing would help but is not required.

---

### 4.5 Strict-focus as persona territory ★ medium value / low risk

**What OCR does.** From `main_task_system.md`, under a heading of its own:

> **Strict Focus Rules**
> _"Context tools are for understanding purposes only. Findings from other
> files must NOT become the subject of your comments. If you discover a
> potential issue in another file while gathering context, ignore it — your
> task is limited to the current diffs."_

Reinforced elsewhere: focus on newly added code, do not comment on deleted
code (reference context only), do not comment on unchanged code.

**Why it matters here.** `docs/brainstorm/code-review-skill-2026-07-20.md`
raises this as an **open question that was never closed**:

> _"Adding a `/code-review` security persona is a FIFTH security surface... draw
> this persona's territory boundary against the other three explicitly... or
> drop it."_

**How it changes shape.** Not a global prose rule — the persona files already
carry "territory / what it flags / what it defers." This becomes an explicit
`territory:` boundary line per persona, in the format that already exists. The
suite closes its own open question, using OCR as corroborating evidence rather
than as a source to copy.

**Insertion points.**

- edit: all 12 files in `code-crit/personas/`, `SECURITY.md` first
- edit: `code-crit/SKILL.md` — the `route` column semantics already point at
  `/code-sec` and `/diagnose`; make the boundary explicit rather than implied

**Depends on:** ideally lands with 4.3, since both are about what a finding has
to clear to survive.

---

### 4.6 Review-run memory compression ◇ speculative / defer

**What OCR does.** `memory_compression_task` compresses a long review
conversation into five fixed dimensions: Identified Code Issues (severity-
sorted, `- [HIGH] \`file:line\` — description`), Tool Call Conclusions,
Completed Tasks, Pending Tasks, Current Focus. Rule: *"Do not include specific
code details; only reference file paths and issue types."* Paired with
`ocr session list`and`--resume <session-id>` (`internal/session/`).

**Why it might matter.** The existing handoff skills (`session-handoff`,
`session-checkpoint`, `session-close`) operate at _session_ level. There is
nothing at _review-run_ level — a long thorough-mode run that exhausts context
mid-roster has no resume path.

**Why defer.** Unclear whether this is a real failure mode in practice or a
theoretical one. **Establish the need before building** — if thorough mode has
never actually blown context, this is over-engineering, which
`CODE-PRINCIPLES.md` names as the primary failure mode of coding agents.

---

## 5. Rejected — with rationale, so it is not relitigated

### 5.1 The plan-before-review pass — REJECTED

`plan_task_system.md` emits `{change_summary, issues[{severity, description,
tool_guidance[{name, reason, arguments}]}]}`, planning which tool to call for
which risk point, explicitly forbidden from invoking anything at plan time.

**Why not:** OCR plans because a single agent must decide what to look at.
code-crit's conditional-persona dispatch _is_ that plan — and it is already
LLM-judgment-over-the-diff, not keyword matching. Adding a plan stage duplicates
existing machinery for no gain.

### 5.2 Rule-group bundling / batch strategies — REJECTED

`delegate.GroupRules` clusters files by identical resolved rule text (keyed
`source|pattern|text`, so provenance stays accurate per group);
`scan/batch.go` adds `by-language` / `by-directory` / chunk-size.

**Why not:** OCR's unit of work is file × rule. This suite's is persona × diff.
These do not compose — adopting bundling means choosing one, and the
persona-shaped one is what produces cross-persona agreement, which the whole
Hybrid design leans on. Revisit only if diff size becomes a demonstrated
bottleneck, and then as batching _within_ a persona, not as a replacement for
persona dispatch.

### 5.3 `rule_docs/*.md` prose — REJECTED as content, KEPT as coverage input

The docs are decent. `python.md` opens _"Favor precision over recall: only
raise an issue when you are confident it is a real defect... a false alarm
costs more reviewer trust than a missed minor issue,"_ and every section closes
with explicit **"Do not report..."** clauses — e.g. _"Do not report local
variables (each thread has its own), read-only access to shared data, or code
with no evidence of concurrent use."_

**Why not:** unvalidated prose with no fixtures and no tiering fails convention
#2. It is also the clearest derivative-work exposure in the repo. **Read them
for coverage ideas; write the prose fresh.** The precision-over-recall framing
and the "Do not report" pattern are worth adopting as _structure_ in this
suite's own reference files.

### 5.4 A `scan`-shaped whole-file review skill — REJECTED for now

`ocr scan` reviews whole files against rules with no diff constraint.

**Why not:** code-decay already ranks hot files; code-crit already reviews. A
scan skill risks being exactly what the brainstorm doc warned about — _"a FIFTH
security surface"_ and _"how not to do it."_ And **code-decay has scripts,
tests, and no `SKILL.md`.** Finishing the skill whose engine is already built
beats starting another one. Revisit only after code-decay ships and a concrete
gap between the two is demonstrated.

### 5.5 The 6-tool restriction — NOTED, not adopted

OCR ships exactly six tools: `task_done`, `code_comment`, `file_read`,
`file_read_diff`, `code_search`, `file_find` — and only three
(`code_search`, `file_read_diff`, `file_find`) are exposed to the plan task.
Selected from production call-trace analysis. Most of the README's "~1/9
tokens" claim comes from this plus bundling.

**Why not adopted:** the `Agent` tool supports tool restriction, but the
personas benefit from breadth, and the token argument is weaker here because
persona spawns are short-lived. Worth remembering as a lever if cost becomes
real; not worth pulling pre-emptively.

### 5.6 CI / PR-comment plumbing — OUT OF SCOPE

`action.yml`, `scripts/github-actions/post-review-comments.js`, and GitLab /
Gerrit / GitFlic / Bitbucket examples. Only relevant if code-crit should run on
PRs — currently it does not. Note it exists; revisit if that changes.

---

## 6. Content that must be authored (not ported)

Routing (4.1) creates demand for reference files that do not exist. These are
**writing tasks in the existing `references/code/*.md` house format**, informed
by but not copied from OCR's equivalents:

| Needed                         | OCR's version, for coverage reference only                   |
| ------------------------------ | ------------------------------------------------------------ |
| GitHub Actions workflows       | `rule_docs/github_workflows.md`                              |
| `package.json`                 | `rule_docs/package_json.md`                                  |
| YAML / JSON                    | `rule_docs/{yaml,json}.md` (both are near-stubs — low value) |
| A default / fallback checklist | `rule_docs/default.md`                                       |

This repo ships `.github/workflows/ci.yml` and hook `package.json` files, so
the first two have real local drivers. YAML/JSON are thin in OCR and probably
not worth a file — fold into the default.

Consider, per convention #2, whether these should be fixture-backed the way
code-sec's rules are. Probably yes for anything making a security claim.

---

## 7. Contradictions in the current suite this work would resolve

Worth stating plainly, because these exist independently of OCR and are
arguably more valuable to fix than anything imported:

1. **Noise policy disagreement** — code-crit "no suppression" vs code-sec's
   Suppress list vs bounty-hunter's reachability triage. (→ 4.3)
2. **The security-territory open question** — raised in the 2026-07-20
   brainstorm, never closed. (→ 4.5)
3. **No anchor verification anywhere** — neither code-crit nor code-sec checks
   that a reported `file:line` exists. (→ 4.2)
4. **Per-language references with no reader** — `ARDUINO.md`, `SOLIDITY.md`,
   `LUA.md` are unreferenced by any skill. (→ 4.1)
5. **code-decay has no `SKILL.md`** — engine without an entry point.
   Independent of this document; arguably higher priority than all of it.

---

## 8. Licensing

Apache-2.0. Practical position:

- **Mechanisms are ideas** — glob routing, snippet anchoring, falsify-don't-
  verify, provenance-tracked rule layering. Reimplementing them against a
  different architecture, in a different language, with different content is
  not derivative work in any meaningful sense.
- **Prose and prompt text are expression.** `rule_docs/*.md` and the five
  prompt files are the real exposure. §5.3 already rejects taking them, so the
  question mostly evaporates.
- **If any verbatim text is taken after all:** keep it in a clearly-attributed
  vendored directory with the Apache-2.0 header and a NOTICE, rather than
  pasting into owned reference files. Never mix licensed prose into
  `references/code/*.md`.

Convenient convergence: the clean-room answer and the better-engineering
answer are the same answer. In four of the six adopted items the mechanism
genuinely changes shape on contact with the persona roster and the existing
scripts — which is the actual test of whether an idea has been absorbed or
merely copied.

---

## 9. Suggested sequencing

> **Superseded 2026-07-28** — see `.work/todos/ocr-code-review-mining.md` for
> the revised sequencing. Left below verbatim for the record; do not follow
> as written.

Grouped by risk, not by value.

**Wave 1 — mechanical, independently testable, no judgement changes**

1. 4.1 glob routing (`route_refs.py` + table + PROJECT-STANDARDS wiring)
2. 4.4 file selection (extend `file_universe.py`, share with code-crit)

**Wave 2 — pipeline change, one schema migration** 3. 4.2 anchoring (`anchor_findings.py`, persona output contract, Stage-2 wiring)

**Wave 3 — judgement changes, grill before writing** 4. 4.3 `FINDING-SURVIVAL.md` + the three citing skills 5. 4.5 persona `territory:` lines

**Not in this stream, but arguably first:** code-decay's `SKILL.md`.

**Deferred pending demonstrated need:** 4.6 memory compression.

Waves 1 and 2 are `/write-plan`-ready. Wave 3 should go through `/grill-me`
first — it changes what three skills consider a real finding, which is exactly
the kind of decision that should not be made quickly.

---

## 10. Verification

Per convention #4 — nothing lands as an assertion.

- **Routing:** table-driven unit tests, path in → reference list out. Cover
  brace expansion, precedence between overlapping globs (`.github/workflows/**`
  vs `**/*.yml` — OCR orders these deliberately), and the no-match →
  coverage-gap path. Then run code-crit against a real mixed-language diff and
  confirm PROJECT-STANDARDS received the right references and nothing else did.
- **Anchoring:** unit tests for exact match, whitespace-variant match, and
  no-match. Then a live run — deliberately induce a bad anchor and confirm the
  finding surfaces as `unverified` rather than disappearing.
- **File selection:** run against a diff containing a lockfile and a
  `fixtures/vuln-app/` file; confirm both are excluded and that the exclusion
  is _reported_, not silent (convention #7).
- **Falsification / territory:** no unit tests possible. Validate by re-running
  code-crit on a diff with known findings, before and after, and diffing the
  reports. Record the result as a field-test annotation with a date.
- **Regression floor:** the branch already has tests for the code-decay
  scripts. New scripts match that bar — `/tdd` and `/mutation-testing` are both
  available.

---

## 11. Open questions for `/grill-me`

Ordered by how much they can invalidate the above.

1. **[LOAD-BEARING] Does routing belong in PROJECT-STANDARDS alone?** The
   argument above says yes — territory separation is why the roster exists. But
   correctness reviewing a `.py` diff arguably wants Python's boundary-condition
   idioms, and OCR's `python.md` puts correctness, security, performance, and
   resource management in one document. If routed references need to reach
   multiple personas, the injection design changes materially. Resolve before
   building.
2. **[LOAD-BEARING] Does the falsification burden of proof conflict with
   "prune weak ones"?** Stage 2 currently has licence to rerank and prune. A
   counter-evidence requirement narrows that. Is the intent to narrow it fully
   (Stage 2 may only prune what it can disprove) or partially (disprove to
   _drop_, judgement to _downrank_)? These are different systems.
3. **Does `existing_code` inflate the Sonnet mega-spawn's output past what the
   scratch-file indirection was designed to avoid?** The JSON handoff exists
   specifically to keep the mega-spawn response cheap. Adding a verbatim code
   snippet per finding grows the _file_, not the response — probably fine, but
   confirm against a high-finding-count run.
4. **Is the coverage-gap report worth its noise?** Every diff touching an
   unrouted file type emits a `[CHORE]`. On this repo that could fire on
   `.sh`, `.json`, `.yml`, and `.md` immediately. Threshold it, batch it, or
   accept a burst of one-time TODOs?
5. **Should `FINDING-SURVIVAL.md` live in `references/code/` or one level up?**
   It is cited by code-sec and bounty-hunter, which are not strictly "code"
   references. Placement affects the cross-runtime mirror.
6. **Does any of this change `/code-review` (the built-in) vs `/code-crit`
   boundary?** code-crit's SKILL.md opens by insisting they are different
   tools. Nothing here changes that, but the anchoring work overlaps with what
   `ReportFindings` already structures — worth a look before building a
   parallel shape.
