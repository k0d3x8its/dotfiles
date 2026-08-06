# Mining VibeSec-Skill — Findings

**Date:** 2026-08-01
**Subject repo:** `BehiSecc/VibeSec-Skill` (Apache-2.0, 1.1k stars, 13 commits)
**Compared against:** `k0d3x8its/dotfiles` branch `chore/code-quality-refs` (`d433600`, ~40 commits ahead of `main`)
**Status:** Discussion notes. No implementation planned or performed.

> **Partially superseded by `security-standard-architecture.md`.** Two recommendations
> below have been replaced by a later design:
> - **§3 Gap 1** proposed a flat `references/code/SECURITY.md`. Replaced by a
>   `SECURITY-STANDARD.md` router plus per-domain sector files, paralleling
>   `CODE-STANDARD.md`.
> - **§3 Gap 2** proposed a standalone `BYPASS-CATALOG.md`. Replaced by a
>   "Guards that don't work" section inside each sector file, so the rows sit beside the
>   guidance they qualify and there is no second file to drift.
>
> The *analysis* in both sections still stands — only the proposed file layout changed.

---

## 1. What VibeSec actually is

A single ~8,500-word `SKILL.md` telling an AI how not to write vulnerable web code,
organized by vulnerability type with code examples and attack-technique tables. Plus a
README and a LICENSE. That is the entire repository.

It is popular because it fills a real need, but structurally it is crude next to the
existing suite: no confidence tiers, no taint-trace requirement, no suppress-list, no
reachability gate, no shared context file.

**Conclusion: do not adopt its shape.** Read it instead as a checklist of questions the
existing suite does not answer, then answer them independently.

---

## 2. What already exists on `chore/code-quality-refs`

### Detection layer — four skills, deliberately non-overlapping territories

| Skill | Territory | Location |
|---|---|---|
| `code-sec` | Bottom-up repo sweep: gitleaks full history, dependency audit, git-crypt coverage, input-handling scan | `claude/.claude/skills/code-sec/` |
| `bounty-hunter` | Remote-reachability filter over the same engine; three auth tiers | `claude/.claude/skills/bounty-hunter/` |
| `threat-model` | Top-down STRIDE; living `docs/threat-model.md` | `claude/.claude/skills/threat-model/` |
| `code-crit` SECURITY persona | Diff-local regressions only | `claude/.claude/skills/code-crit/personas/SECURITY.md` |

Supporting assets: `rules/{precise,normal,noisy}/` ast-grep pack with `sgconfig.yml`,
`fixtures/vuln-app/` red-green bed with `MANIFEST.md` ground truth,
`bin/enumerate-entrypoints.sh`, `templates/SEC-CONTEXT.md`.

The territories are explicitly demarcated — `personas/SECURITY.md` names by hand what it
defers to each of the other three. **A fifth overlapping security skill would break this.**

### Write-time layer — `claude/.claude/references/code/`

Router `CODE-STANDARD.md`, plus `CODE-PRINCIPLES.md`, `ANTI-PATTERNS.md`,
`TESTING-STANDARD.md`, `CODE-REFERENCE.md`, and 12 language files (`LUA`, `PYTHON`,
`TYPESCRIPT`, `SOLIDITY`, `BASH`, `ARDUINO`, `SWIFT`, `HTML`, `HTMX`, `CSS`, `JSON`,
`YAML`).

Reading protocol, from `CODE-STANDARD.md`:

> "load *only* this file + the one language file matching the code being written."

### Current rule-pack coverage

Covered: SQL injection, OS command injection, SSRF, path traversal, deserialization
(pickle/yaml), IDOR/BOLA, auth bypass, buffer overflow (embedded C/C++).
Languages with rules that actually execute: **Python and JavaScript only** — `.ts`, `.tsx`,
`.go`, `.lua`, `.sol` are model-only, which `bounty-hunter` already declares openly.

---

## 3. The gaps VibeSec exposes

### Gap 1 — nothing assists while code is being written

All four security skills run *after* code exists. There is no security file anywhere in the
write-time reference layer, and the reading protocol loads only two files.

Ask the harness for an invoice download endpoint. It loads `CODE-STANDARD.md` + `PYTHON.md`,
neither of which mentions security:

```python
@app.route("/invoice/<name>")
def invoice(name):
    return send_file("/var/invoices/" + name)
```

Passes every existing standard — good naming, ruff-clean, correct structure. Also
`../../../etc/passwd`. `/code-sec` catches it later, *if* run.

**Candidate fix:** a `SECURITY.md` in `references/code/`, conditionally loaded alongside the
language file when the code touches untrusted input, authn/authz, or a trust boundary
(mirroring how `TESTING-STANDARD.md` is conditionally routed).

**Use case:** any generated code handling a request, file path, or user ID. Prevention
rather than cleanup.

**Caveat:** biggest behavioral change of the four, but the most speculative — it only pays
off if the conditional trigger reliably fires.

### Gap 2 — the sweep cannot distinguish a real guard from a fake one

**Highest-value gap.** `code-sec`'s Finding discipline suppresses "defense-in-depth
suggestions on already-protected code." Sensible rule — but there is no means to judge
whether a defense is sound.

```python
if url.startswith("https://myapp.com"):
    return redirect(url)
```

A guard exists, so `code-sec` suppresses and moves on. But `https://myapp.com.evil.com`
passes `startswith`. An open redirect with a guard sitting on top of it.

The same failure mode recurs:

| Defense that looks real | Why it isn't |
|---|---|
| SSRF filter blocking `169.254.169.254` | `0251.0376.0251.0376` is the same address in octal |
| Upload restricted to `.jpg` | Real JPEG magic bytes prepended to a PHP payload; or `shell.php.jpg` |
| CSRF token validated on `POST` | Route also accepts `GET` |
| Path check via `startswith(base)` | No canonicalization — `base/../..` still escapes |

Every one currently reads as protected and is dropped.

**Candidate fix:** a bypass-catalog reference consulted *before* suppressing. Four columns,
not VibeSec's three — theirs is an attack catalog (`Technique | Example | Why It Works`);
this gets consumed at a suppression decision, so it needs `Defense as written | Bypass |
Why it works | Sound form`. Without the fourth column it says a guard is broken but not
what to write instead.

**Use case:** fixes *wrong suppressions* — the failures that never surface. A false positive
is dismissed in two seconds; a false negative is silent forever.

**Shared by:** `code-sec` (suppress clause), `bounty-hunter` (ground rules), `code-crit`
SECURITY persona (the `verified` confidence claim should not rest on a bypassable guard).

### Gap 3 — vulnerability classes nothing looks for

Not covered by any skill or rule: **JWT flaws** (`alg:none`, decode-vs-verify, missing
`exp`/`aud`), **mass assignment**, **XXE**, **open redirect**, **CSRF**, **insecure file
upload**, **GraphQL** (introspection enabled, no depth/complexity limit, batching),
**session fixation**.

```js
const user = jwt.decode(token);        // decode ≠ verify — no signature check at all
if (user.role === "admin") { ... }     // token is trivially forged
```

```js
Object.assign(user, req.body);         // attacker posts {"role":"admin"}
await user.save();
```

Both are two-line ast-grep rules. Both are invisible to every existing skill.

**Use case:** plain coverage. Cheap to write, permanently on, fixture-backable in the
existing `fixtures/vuln-app`.

### Gap 4 — the business-logic lens

`bounty-hunter/domains/` is a deliberately empty seam for abuse patterns that structural
matching cannot catch. Example: a checkout route validates the item ID, quantity is a
well-formed integer, every rule passes — and quantity `-1` credits the account. No matcher
finds this; it needs a lens stating "on commerce routes, check sign and bounds on money and
quantity."

**Open tension:** `domains/TEMPLATE.md` states — *"Fill packs EMPIRICALLY — after a real
sweep of a codebase in this domain, not up front."* Filling it from published taxonomy
contradicts that rule. User has elected to proceed anyway; the mitigation is to mark the
pack provisional so the first real sweep corrects or deletes each family, and to leave
`TEMPLATE.md` unedited rather than rewriting the rule to fit the exception.

---

## 4. What to discard from VibeSec

- **Its single-file structure** — collides simultaneously with four carefully bounded skill
  territories.
- **Its framework code snippets** (Apollo Server, Express middleware config) — these rot
  quickly, and the language reference files already own idiom and tooling.
- **Its checklists** — largely duplicated by `code-sec` phase-5 close-out.
- **The "covers 60–70% of common vulnerabilities" framing** — unsubstantiated.

---

## 5. Provenance

VibeSec is itself an uncited compilation of OWASP Top 10 / ASVS, PortSwigger Web Security
Academy, and CWE. The existing references cite primaries — `CODE-REFERENCE.md` credits
Ousterhout, Feathers, and Fowler.

**Decision taken:** re-derive any retained material from those primaries and cite them in a
`Sources:` line matching existing convention. VibeSec is the prompt, not a source; mention
it in a commit body only. Techniques and taxonomies are facts — Apache-2.0 attaches no
obligation to them provided no prose is lifted.

---

## 6. Structural findings (discovered while investigating; independent of VibeSec)

These are pre-existing conditions in the repo, worth knowing regardless of what happens
with this mining exercise.

### 6.1 The codex mirror is inconsistent

Six skills are **symlinks** into the claude tree (`bounty-hunter`, `create-gdd`,
`grill-me`, `mutation-testing`, `write-a-skill`, `zoom-out`):

```
codex/.codex/skills/bounty-hunter -> ../../../claude/.claude/skills/bounty-hunter
```

But `codex/.codex/skills/code-sec/` is a **real duplicated `SKILL.md`** that has drifted. It
lacks the entire `rules/`, `fixtures/`, `bin/`, and `templates/` tree, and is missing the
Prompt Defense Baseline line present in the claude copy. **Codex has been running a
materially weaker `code-sec` than claude.**

Note the divergence is invisible from a file listing — it only shows up in `git ls-tree`
mode bits (`120000` = symlink).

Options, in increasing order of scope: leave and document; add the `CODE_SEC_ROOT`
resolution fallback already proven in `bounty-hunter/SKILL.md` Step 2; or convert to a
symlink like its six siblings. The last is a structural call, not a mechanical one.

### 6.2 References need no codex copy

`codex/.codex/AGENTS.md:27` states that `~/.codex/references/code/` is symlinked from the
canonical `claude/.claude/references/code/`. Any new reference file is therefore live for
both harnesses from one location — only the file list at `AGENTS.md:28` would need updating.

### 6.3 `fixtures/vuln-app/MANIFEST.md` is line-number anchored

Route inventory and planted-vuln tables reference exact positions (`/order`@27,
`python/vuln.py:32`). Inserting fixture routes shifts every downstream number, so those
tables must be **re-derived from the edited files, not appended to** — otherwise rule tests
assert against stale lines and pass while checking the wrong code. Per-file route counts are
the stable assertion targets; the total (31 today) is derived and will move.

---

## 7. Ranking and open question

| Gap | Value | Cost | Confidence |
|---|---|---|---|
| 2 — bypass catalog | Highest — makes an existing skill stop silently dropping real findings | Low | High |
| 3 — missing CWE families | Solid, permanent coverage | Low–medium | High |
| 1 — write-time reference | Largest behavioral change | Medium | Speculative — depends on the trigger firing |
| 4 — web-abuse pack | Real, but unvalidated by construction | Medium | Contradicts own `TEMPLATE.md` rule |

**Open question to resolve before building anything:** does the Gap 2 suppression problem
match real experience from actual sweeps? If `code-sec` has not in practice been dropping
findings behind bypassable guards, the ranking above changes and Gap 3 should lead instead.

A useful validation before committing effort: run `/code-sec` against a small web codebase
and check whether any hit was suppressed as "already protected" where the protection was in
fact bypassable. If none, Gap 2 is theoretical here.

---

## 8. Sources for any retained material

- OWASP Top 10 (2021) and OWASP ASVS 4.0
- PortSwigger Web Security Academy
- MITRE CWE
