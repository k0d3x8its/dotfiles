# SOLIDITY — language standard

Scope: smart contracts. **Security-critical language** — treat every contract change
as `[SECURITY]`-tagged work: careful prose, blast-radius stated, `/code-sec` sweep
before ship. Evidence base is thin (learning stage) — rules below are
industry-standard seeds, marked *(unvalidated)* where no local code has exercised
them yet. Strength vocabulary per `CODE-STANDARD.md`.

## Naming & casing

| Kind | Casing | Example |
|---|---|---|
| contracts / interfaces / libraries / structs / enums | `PascalCase` | `EscrowVault` |
| interfaces | `I` prefix (Solidity convention — opposite of TS) | `IEscrowVault` |
| functions / variables | `camelCase` | `releaseFunds` |
| constants / immutables | `UPPER_SNAKE` | `MAX_LOCK_PERIOD` |
| internal/private members | `_leadingUnderscore` | `_pendingWithdrawals` |
| events | `PascalCase`, past tense | `FundsReleased` |
| errors | `PascalCase` custom errors | `error LockNotExpired();` |

## Security MUSTs (non-negotiable)

- **Checks-Effects-Interactions** in every state-changing function: validate,
  mutate state, external calls LAST. Reentrancy lives in violations of this order.
- Every function and state variable MUST declare explicit visibility — no defaults.
- External calls: assume hostile. MUST handle failure (check return / use custom
  errors); MUST NOT assume callee behavior.
- Withdrawals: pull over push — recipients withdraw; contracts don't broadcast sends.
- MUST use custom errors + `revert`, not `require(string)` (cheaper, greppable).
- Access control on every state-changing external function — who may call this,
  enforced in code, stated in a comment.
- No `tx.origin` for auth. No `block.timestamp` as randomness or fine-grained clock.
- Arithmetic: solc >=0.8 checked math is the floor; `unchecked` blocks require a
  why-comment proving bounds.
- SHOULD prefer OpenZeppelin audited implementations over hand-rolling
  (ownership, reentrancy guard, token standards). *(unvalidated locally)*
- Upgradeability, delegatecall, assembly: AVOID until a concrete requirement +
  a `/grill-me` session justifies each.

## File layout (SHOULD — top to bottom, one contract per file)

1. SPDX license identifier + `pragma solidity` (pinned, not floating `^` in
   deployable contracts)
2. Imports
3. Custom errors
4. Contract: events → constants/immutables → state variables → modifiers →
   constructor → external/public functions → internal/private helpers
   (newspaper order within each visibility band)

## Directory structure (canonical minimum — Foundry)

Ecosystem-standard shape. An existing repo's layout always wins.

```
<project>/
├── foundry.toml
├── src/                    # contracts, one per file, PascalCase.sol
├── test/                   # *.t.sol — Foundry tests
├── script/                 # *.s.sol — deploy scripts
└── lib/                    # dependencies (forge install) — never edited
```

- Minimum viable: `foundry.toml` + `src/` + `test/`.

## Testing

- Tests are not optional in this language — every state transition and every
  revert path MUST have a test (red-green per `/tdd`, but coverage bar is higher
  than other languages).
- Fuzz the value-bearing entry points (`forge test` fuzzing). *(unvalidated locally)*

## Tooling

- solhint + `forge fmt` when a Foundry project exists — none in ~/dev yet;
  first real contract project sets them up as part of scaffold (`/dev-setup`).
