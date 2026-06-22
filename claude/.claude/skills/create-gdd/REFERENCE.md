# create-gdd — Reference

Detailed guidance per section, real examples from shipped GDDs, and anti-patterns to avoid.

---

## Game Type Classification

| Signal | Type |
|---|---|
| Board, tiles, cards, dice, meeples | Physical |
| App, browser, blockchain, NFT, smart contract | Digital |
| Companion app + physical board | Hybrid |
| Tabletop RPG with digital rolls | Hybrid |

When unclear: ask one question — "Is this played on a screen or a table?"

---

## Section Guidance

### §1 — Game Overview

The concept must answer: **what do you DO, and why does it feel good?**

Bad: "A Web3 game where players collect pets."
Good: "Players adopt digital pets on Avalanche, keep them alive through daily feeding and mini-games, and earn NFT gear through time-locked foraging missions — a Tamagotchi with a player-driven economy."

USP should be one sentence naming the mechanic that no competitor has.

---

### §2 — Core Game Loop

Most games have 2–3 nested loops:
- **Micro loop** — moment-to-moment action (feed pet, scan node, draw card)
- **Session loop** — one play session arc (forage → collect materials → craft)
- **Macro loop** — long-term progression (evolve pet epoch by epoch)

**Asymmetric games** need one loop per faction. The loops should mirror each other structurally but diverge in output.

**Real example — Cyber Warfare:**
```
Red: Scan Node → Roll Bug → Win Combat → Place Exploit → Deploy Payload → Generate Data Packets → Convert to Bytes → Exfil
Blue: Scan Node → Roll Bug → Win Combat → Place Signature → Develop Patch → Generate Traces → Convert to Octets → Identify IP
```
Same structure. Opposite ends.

**Real example — Ava Pets:**
```
Micro:   Feed pet → restore Emotion → avoid Critical State
Session: Spend Chi → Forage/Mission/Adventure → collect Materials/Runes/Relics
Macro:   Accumulate resources → Craft NFT gear → Evolve pet epoch
```

---

### §3 — Player Goals & Win Conditions

Always define BOTH the primary win condition AND what failure looks like. Many GDDs skip failure — this causes balance blind spots.

For idle/persistent games with no hard win: define the **engagement hook** — the pull that brings players back (pet death risk, Chi expiry, limited-time events).

---

### §4 — Core Mechanics

Each mechanic needs all five fields: **name, trigger, cost, output, constraint.** Missing the constraint is the most common gap — it's what prevents exploits.

**Real example — Chi Energy System (Ava Pets):**
- Name: Chi Energy
- Trigger: Player initiates Forage / Mission / Adventure
- Cost: Low / Medium / High Chi respectively
- Output: Materials (Forage), Runes (Mission), Relics + Gear (Adventure)
- Constraint: Pet time-locked during activity; re-staking delay (24h) prevents stake/unstake abuse

**Real example — Combat (Cyber Warfare):**
- Name: Card Combat / Counter-Chain
- Trigger: Player plays card on a Node, opponent contests
- Cost: Initial card requires resource payment; subsequent counters free
- Output: Winner places Exploit (Red) or Signature (Blue)
- Constraint: Counter must match Domain AND Color of top card on Combat Stack

**Anti-pattern:** Defining what a mechanic does without defining when it CAN'T be used.

---

### §5 — Economy & Resources

Fill every cell of the table. `[TBD]` is fine; blank is not — blank means you forgot to think about it.

**Conversion chains must be explicit.** Write out the full chain with rates:

Real example — Cyber Warfare resource chains:
```
Red:  Data Packets (1/turn/exploited node) → 8 = 1 Byte → 2 Bytes = Exfil Data → WIN
Blue: Traces (various sources)            → 4 = 1 Octet → 4 Octets = IP Address → WIN
```

Real example — Ava Pets $RAGE staking tiers:
```
Tier 1 (1K RAGE)  → +1.5% Chi regen
Tier 2 (5K RAGE)  → +3.0% Chi regen
Tier 3 (10K RAGE) → +5.0% Chi regen
Tier 4 (20K RAGE) → +7.0% Chi regen
Tier 5 (25K+)     → +10.0% Chi regen (cap)
```

**Design risk to flag:** Any resource with a source but no sink (or vice versa) will cause inflation or starvation. Always balance both sides.

---

### §6 — Progression System

Name every stage. Include gating condition AND what unlocks. Vague stages ("early, mid, late game") are useless.

**Real example — Ava Pets epochs:**

| Epoch | Duration | Gate | Unlock |
|---|---|---|---|
| Egg | 24 hrs | Time | Hatches to Hatchling |
| Hatchling | 7 days | Care + feeding | Evolves to Common |
| Common | 14 days | Time | Wearable / consumable access |
| Uncommon | 30 days | Time | Forgecrafting + Arena training |
| Rare | 60 days | Time | Arena Battles |
| Epic | 90 days | Time | TBD |
| Legendary | 120 days | Time | TBD |

---

### §7 — Components & Assets

**Physical:** Count matters. Exact counts drive manufacturing cost. "Some cards" is not a spec.

Minimum per card type: name, count, which domain/faction it belongs to.

**Digital:** Priority-order everything. The list IS the cut plan when scope shrinks. Assets at the bottom get cut first.

Real example — Ava Pets priority asset list (demo scope):
1. Base sprites per species: Egg (static), Hatchling (idle/happy/sad), Common (idle/happy/sad)
2. Eating animation (Wolfi: standing)
3. Weak/struggling animation (Critical State)
4. 1 Common wearable, 1 Uncommon wearable, 1 Rare wearable
5. Death animation — `[DESIGN RISK: may cut from demo]`
6. Mini-game reaction animation — cut for public release

---

### §8 — Turn / Phase Structure

Physical games: every phase needs a clear **who acts** (active player, both players, passive/automatic). Missing this causes rules disputes.

**Real example — Cyber Warfare turn structure:**
```
Update Phase  → automatic: collect tokens, conversions, upkeep
Recon Phase   → active player: draw cards
Scan Phase    → active player: spend Epoch actions, roll dice per Node
Control Phase → both players: card combat counter-chain
Secure Phase  → active player: spend Intent actions (Patch or Payload)
```

Note: "All Epoch actions must be exhausted before Secure Phase" — this kind of ordering constraint is critical and often missing.

---

### §9 — Factions / Roles / Characters

For asymmetric games, define the **strategic identity in one word**: Aggressive, Defensive, Tempo, Attrition, Control, Engine. That word guides every card/ability design decision downstream.

**Real example — Cyber Warfare:**
- Red Team: Aggressive. Scales offense via exploitation chain. Wins by accumulation (data exfil).
- Blue Team: Defensive/Attrition. Disrupts Red's chain. Wins by identification (IP assembly).

Both start from the same mechanic (Bug roll). Same origin, opposite trajectory. This is strong asymmetric design — document it explicitly.

---

### §10 — Art Direction

Priority asset list here should match §7. If they diverge, §7 wins (it's the implementation spec).

Flag wearable complexity: head accessories = easy (near-static, minor bobbing). Body items = hard (arms, legs require full re-animation per action state).

---

### §11 — Tech Stack [Digital only]

Only include what's decided. `[TBD]` is better than a guess. Stack choices affect §12 milestone timing.

Real example — Ava Pets:
```
Frontend:   React + Next.js, Tailwind CSS
Web3:       wagmi.sh + ethers.js
Blockchain: Avalanche C-Chain, Solidity smart contracts, Hardhat
Storage:    IPFS (NFT metadata)
Backend:    Node.js API
Database:   PostgreSQL (interactions), Redis (cache), WebSockets (real-time)
```

---

### §12 — Phases & Milestones

"Cut criteria" column is the most important and most skipped. Define what gets dropped if the phase runs over scope.

Real example — Ava Pets Phase 0 (Demo) cut criteria:
- Tiers beyond Common: cut
- Mini-game reaction animation: cut for public release
- Funeral/death certificate NFT: cut (post-launch)
- Pet dialogue / Animalese: cut (feature creep)

---

### §13 — Economy & Monetization [Digital only]

Every revenue stream needs: who pays, when they pay, where the money goes.

Real example — Ava Pets:
```
Food purchase (0.05 AVAX):  45% → genesis holder reward pool | 55% → team wallet
Secondary market sale:      5%  → Ava Pets DAO reward pool   | 5%  → team wallet
Pet revival:                0.25 AVAX (50% Emotion) or 0.5 AVAX (100% Emotion) → team wallet
```

Flag any revenue stream that depends on player-to-player activity (secondary market) — these require minimum active user counts to function. `[DESIGN RISK]` if launch player count is uncertain.

---

### §14 — Open Questions & Assumptions

Dump everything here that would otherwise pollute the main doc. Organize by section number.

Real signals that something belongs in §14 instead of the main doc:
- Any sentence with "maybe", "possibly", "we could"
- Any mechanic that depends on a number not yet determined
- Any feature the team debated but didn't resolve
- Any assumption about player behavior that hasn't been tested

---

## Common Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Vague economy ("players earn rewards") | Unbalanceable | Name every resource, source, and sink |
| Missing failure state | No tension | Define loss condition or critical-state equivalent |
| Features in §14 format in main doc | Scope confusion | Move to §14 with `[TBD]` tag |
| Asset list with no priority order | Cut decisions become arguments | Priority-order everything |
| Progression stages without unlock content | Players have no reason to progress | Every stage must unlock something concrete |
| Asymmetric factions with same win condition | Removes strategic identity | Each faction needs a distinct escalation path |
| Tech stack guesses | Misaligns engineering estimates | Mark undecided choices `[TBD]` |
