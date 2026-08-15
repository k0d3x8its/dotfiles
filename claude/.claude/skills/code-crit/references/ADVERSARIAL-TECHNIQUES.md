# Adversarial techniques

Artifact-agnostic attack substance, shared by two call sites: `code-crit`'s
`personas/ADVERSARIAL.md` (attacks a diff) and code-mode's Gate 3 (attacks a
design/plan/claim artifact). Identical reasoning either way — only the target
differs.

## The four techniques

1. **Assumption violation.** Find every unstated assumption the artifact
   relies on (input is well-formed, caller is trusted, this runs after that,
   the list is never empty) and construct the case where it's false.
2. **Composition failures.** Two things that are each individually correct
   can combine into a bug — a retry wrapped around a non-idempotent write, two
   caches with different TTLs backing the same value, a plan step that's fine
   alone but wrong given the step before it.
3. **Cascade construction.** Chain a small, plausible failure into a large
   consequence — a dropped error becomes a silent data-loss path, a missing
   auth check on one internal endpoint becomes a privilege-escalation chain
   once combined with another endpoint that trusts it.
4. **Abuse cases.** Read the artifact as an attacker/adversarial user, not a
   well-intentioned one — what does someone gain by misusing this exactly as
   built (not exploiting a separate bug)? Rate-limit bypass via legitimate
   retries, a "trusted" flag anyone can set on their own request.

## Anchored confidence rubric

Rate each candidate finding before reporting it — don't report a technique
just because it was tried:

| Score | Meaning                    | Self-test                                                                                               |
| ----- | -------------------------- | ------------------------------------------------------------------------------------------------------- |
| 100   | Mechanically constructible | You can name the exact input/sequence that triggers it, no unstated assumptions of your own             |
| 75    | Strong, one assumption     | Triggers under one plausible-but-unverified condition (e.g. "if this endpoint is actually public")      |
| 50    | Plausible                  | Reasoning holds, but requires several unverified conditions to align                                    |
| ≤25   | Speculative                | "Could imagine a world where..." — no concrete trigger, mostly pattern-matching to a known attack class |

**Binary collapse (code-crit only):** code-crit's `confidence` field is
binary, not 4-level. Collapse: **100 → `verified`; 75/50/≤25 → `unverified`.**
Only a mechanically-constructible finding counts as verified — anything that
leans on an unverified condition, however plausible, is `unverified`. This is
the ADVERSARIAL persona's confidence self-test; code-mode Gate 3 has no
`verified`/`unverified` field and doesn't use this line.

## What you don't flag

Never repeat a finding the artifact's own review pass already covers —
adversarial territory is failure modes that require adopting an attacker's
frame, not "run the same review again but call it adversarial." Don't
re-derive a plain correctness bug, a style issue, or a Spec mismatch someone
else already checks — those aren't attacks, they're the artifact's baseline
review.

## Caller policy on the ≤25 band

The rubric above is descriptive, not prescriptive — each call site decides
what to DO with a ≤25/speculative finding, and the two call sites disagree on
purpose:

- **code-mode Gate 3** (design/plan/claim artifacts): **drop.** A
  speculative attack on a plan that doesn't exist yet as code is usually
  noise; the gate's job is to catch real gaps before building, not catalog
  every hypothetical.
- **`code-crit`'s `personas/ADVERSARIAL.md`** (a real diff): **never drop.**
  code-crit has no suppression gate — every finding surfaces labeled with its
  confidence, including speculative ones tagged `unverified`. A reviewer
  looking at real, already-written code should see the low-confidence flag
  and decide for themselves, not have it silently withheld.

State this rule explicitly wherever this file is consumed — "speculative"
must never become an emitted output tag on its own; it's an internal rating
that resolves to either "drop" or "surface as unverified" depending on the
caller.
