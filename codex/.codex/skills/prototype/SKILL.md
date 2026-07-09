---
name: prototype
description: Build throwaway code to answer a design question before committing. Routes to a terminal app (logic/state model) or several switchable UI variants (look/feel). Use to prototype, sanity-check a data model or state machine, or mock up UI.
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding
code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → Read `~/.codex/skills/prototype/LOGIC.md`.
  Build a tiny interactive terminal app that pushes state through cases hard to reason
  about on paper.

- **"What should this look like?"** → Read `~/.codex/skills/prototype/UI.md`.
  Generate several radically different UI variations on a single route, switchable via
  a URL search param and a floating bottom bar.

Getting this wrong wastes the whole prototype. If the question is genuinely ambiguous
and the user isn't reachable, default to whichever better matches the surrounding code
(a backend module → logic; a page or component → UI) and state the assumption up front.

## Rules that apply to both branches

1. **Throwaway from day one, clearly marked.** Locate close to where it will actually be
   used so context is obvious. Name it so a reader can see it's a prototype, not production.

2. **One command to run.** Whatever the project's task runner supports — `python path/to/proto.py`,
   `bash proto.sh`, `node proto.js`, etc. User must be able to start it without thinking.

3. **No persistence by default.** State lives in memory. If the question explicitly involves
   a database, hit a scratch DB or local file with a clear "PROTOTYPE — wipe me" name.

4. **Skip the polish.** No tests, no error handling beyond runnable, no abstractions.
   The point is to learn something fast and then delete it.

5. **Surface the state.** After every action (logic) or on every variant switch (UI),
   print or render the full relevant state so the user can see what changed.

6. **Delete or absorb when done.** Either delete it or fold the validated decision into
   real code — don't leave it rotting.

## When done

The **answer** is the only thing worth keeping. Capture it somewhere durable — commit
message, ADR (if it meets the three-condition gate in `~/.codex/references/kos-code-reference.md`),
or a `NOTES.md` next to the prototype — along with the question it was answering.
