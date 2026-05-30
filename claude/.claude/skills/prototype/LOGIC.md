# Logic Prototype

Use when the question is about **business logic, state transitions, or data shape** —
situations where a design needs hands-on testing before committing to it.

## When this is the right branch

- "Does this state machine feel right?"
- "I want to push this data model through some hard cases before I build it."
- "Does this reducer handle all the transitions I need?"
- "Try a few API shapes and let me interact with them."

If the question is about what something *looks like* rather than how it *behaves* — wrong
branch. Use `UI.md`.

## Process

### 1. State the question

Write it down at the top of the prototype file as a comment:

```python
# PROTOTYPE — answering: "Does the state machine handle concurrent task cancellation correctly?"
# Delete or absorb after question is answered.
```

This prevents the prototype from drifting into answering the wrong question.

### 2. Use the project's stack

Pick the language and runtime already in use. Do not introduce a new dependency to
build a prototype — if the project is Python, use Python. If it's bash, use bash.
The goal is minimal friction to run it, not a clean dependency tree.

### 3. Isolate the logic module

Separate the state model from the throwaway terminal interface:

```python
# logic.py  ←  keep this; it becomes the real implementation
def apply(state: dict, action: dict) -> dict:
    # pure function — no I/O, no terminal code, no side effects
    ...

# proto.py  ←  throw this away
import logic, os, sys
# screen-clearing TUI that calls logic.apply()
```

The logic module is the artifact. The terminal shell is scaffolding.

**Pure means:** no I/O, no file reads, no network, no terminal code. Input → output only.
This makes it portable to production without changes.

### 4. Build a minimal screen-clearing TUI

```python
import os

def render(state):
    os.system('clear')
    print("=== STATE ===")
    for k, v in state.items():
        print(f"  {k}: {v}")
    print()
    print("Commands: [a] action-a  [b] action-b  [r] reset  [q] quit")

state = initial_state()
while True:
    render(state)
    cmd = input("> ").strip()
    if cmd == 'q':
        break
    elif cmd == 'r':
        state = initial_state()
    elif cmd == 'a':
        state = logic.apply(state, {"type": "ACTION_A"})
    elif cmd == 'b':
        state = logic.apply(state, {"type": "ACTION_B"})
```

Surface the **full relevant state** after every action. The user must be able to see
exactly what changed.

### 5. One command to run

```bash
python proto.py       # Python
bash proto.sh         # shell
node proto.js         # Node
```

No build step, no environment setup beyond what the project already has.

### 6. Drive it through hard cases

The goal is to find the transitions that are hard to reason about on paper:
- What happens at the boundary conditions?
- What if the same action fires twice?
- What if actions arrive out of order?
- What does an empty/null state look like?

Let the user drive it. Your job is to make those cases easy to trigger.

## When done

Capture the answer (commit message, NOTES.md, or ADR if it meets the three-condition
gate). Then either delete the prototype or fold the validated logic module into the
real codebase. Never leave both the proto shell and the logic module — delete the shell,
keep only what goes to production.
