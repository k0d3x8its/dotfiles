# Fable reasoning patterns — distilled from real traces

How Fable 5 actually phrases its per-beat reasoning, distilled from the public
`Glint-Research/Fable-5-traces` dataset (4,665 real Claude Code events, chain of
thought intact — analysed locally; AGPL-3.0, so nothing here is quoted verbatim.
Every pattern below is a paraphrased characterization plus the measured frequency).

Load this file when running fable-mode on a weaker model and the inner loop feels
mechanical — these are the concrete moves that make it real.

## The measured shape of a Fable beat

Median thinking block: ~2,400 characters — substantial, not a token gesture.
Marker frequencies across all events with reasoning:

| Move | Share of beats |
|---|---|
| states an expectation before acting ("should show / likely / expect") | 54% |
| names a verification intent ("check / confirm / make sure") | 50% |
| reacts explicitly to the last result ("the output shows / that failed") | 43% |
| enumerates a micro-plan ("first… then… next…") | 40% |
| self-corrects mid-thought ("wait / actually / hold on") | 38% |
| restates what the user asked | 18% |
| states scope restraint ("only need / no need to") | 15% |
| flags uncertainty out loud ("not sure / might be") | 13% |

## The six moves, in beat order

1. **State summary first.** The single most common opening move: begin the beat by
   restating where the task stands — what was just done and what the last result
   actually showed — before deciding anything. This is the re-grounding step; it is
   why Fable rarely executes a stale plan. The top thinking openers in the corpus
   are all variants of "I've just finished X…" / "the latest result was Y…".

2. **Reason over observed facts, cite them specifically.** Reasoning references the
   concrete state it has seen: a file and approximate line, an exact checkpoint
   name, a number from the last command's output. It does not reason from what a
   file "probably" contains — the specifics are the evidence that it looked.

3. **Justify why THIS action is next.** Before a tool call, the thinking answers
   "why is this needed now?" — connecting the action to the goal and to what just
   happened, not just naming the action. If the connection can't be stated, the
   action is probably momentum, not decision.

4. **State the expectation, then act.** More than half of beats name what the
   action should show before running it. This includes command hygiene reasoned in
   advance: timeouts to avoid hanging, output limits, flags chosen deliberately.
   The expectation is what makes the OBSERVE step meaningful — you can only be
   surprised if you predicted something.

5. **Micro-plan edits before touching them.** For a code change: enumerate the
   steps (1… 2… 3…) inside the reasoning, including *anchor selection* — why the
   chosen match string uniquely identifies the edit site. The plan is written
   before the edit, at the moment the file's real contents are in view.

6. **Self-correct mid-thought, out loud.** Over a third of beats contain an
   explicit reversal — noticing mid-reasoning that the first idea is wrong and
   saying so before acting on it. Cheaper than discovering it from a failed tool
   call. Treat a "wait—" moment as the system working, not a flaw.

## Tool rhythm

Tool mix across the corpus is dominated by Bash (≈41%), Edit (≈25%), Read (≈12%),
Write (≈8%) — a *verify-heavy* profile: roughly one shell probe/check for every
mutation. If your edit:check ratio drifts far from that, mutations are outrunning
observation.

## What NOT to copy

The source model's weakest measured habit (from the published analysis of the same
model) was running the real test suite after edits — roughly two-thirds of edit
sessions. fable-mode's Gate 4 and the trust-but-verify reflex are deliberately
stricter than the source. Copy the reasoning moves; exceed the verification.

## Reproducing this analysis

Download the dataset yourself (never commit it — AGPL-3.0):

    python3 ../scripts/fetch-fable-traces.py --sample 500

Score your own local models on the same habit definitions:

    python3 ../scripts/fable-score.py claude-opus-4-8 --baseline claude-fable-5
    python3 ../scripts/fable-score.py claude-opus-4-8 --split-fable
