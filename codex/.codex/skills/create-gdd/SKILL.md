---
name: create-gdd
description: Create a Game Design Document (GDD) for any game type — digital, physical, hybrid, Web3, mobile, board game, card game, tabletop RPG. Use when writing a GDD, documenting game mechanics, speccing a game system, or reviewing an existing GDD.
---

# Create a Game Design Document

## Quick start

```
/create-gdd "2-player asymmetric card game: hacker vs defender battling for network control"
/create-gdd "Web3 idle pet game on Avalanche with emotion, crafting, and NFT evolution"
/create-gdd  # no args → ask for concept first
```

Output saved to `docs/GDD-<GameName>.md`. Creates `docs/` if missing.

## Workflow

You are an experienced game designer creating a GDD for $ARGUMENTS.

1. **Read inputs** — any files, links, or notes provided.
2. **Identify** — game type (digital / physical / hybrid), concept, players, platform, core loop, win condition. Infer from context; only ask what's truly missing.
3. **Generate** — use the 14-section template below. Skip `[digital only]` or `[physical only]` sections that don't apply. For hybrid, include both.
4. **Flag gaps** — mark unknowns `[TBD]`, unproven beliefs `[ASSUMPTION]`, balance concerns `[DESIGN RISK]`.
5. **Save** — write `docs/GDD-<GameName>.md`. Report path, completed sections, and flagged risks.

## Section map

| § | Section | Digital | Physical |
|---|---|---|---|
| 1 | Game Overview | ✓ | ✓ |
| 2 | Core Game Loop | ✓ | ✓ |
| 3 | Player Goals & Win Conditions | ✓ | ✓ |
| 4 | Core Mechanics | ✓ | ✓ |
| 5 | Economy & Resources | ✓ | ✓ |
| 6 | Progression System | ✓ | ✓ |
| 7 | Components & Assets | ✓ | ✓ |
| 8 | Turn / Phase Structure | ✓ | ✓ |
| 9 | Factions / Roles / Characters | ✓ | ✓ |
| 10 | Art Direction | ✓ | ✓ |
| 11 | Tech Stack | ✓ | — |
| 12 | Phases & Milestones | ✓ | ✓ |
| 13 | Economy & Monetization | ✓ | — |
| 14 | Open Questions & Assumptions | ✓ | ✓ |

## GDD Template

### 1. Game Overview
- **Concept**: One-paragraph pitch.
- **Genre**: (e.g. strategy, RPG, idle, puzzle, deck-builder, survival)
- **Platform/Medium**: (e.g. Web app on Avalanche, tabletop card game, iOS, PC)
- **Players**: Count, structure (PvP, co-op, solo, async)
- **Target session length**: (e.g. <60 min, 10 min idle loop, persistent)
- **Theme & tone**: Visual/narrative identity in 2-3 sentences.
- **Unique selling point**: What makes this game different?

### 2. Core Game Loop
The essential cycle a player repeats. Be specific — name each step.

```
[Action] → [Result] → [Decision] → [Repeat]
```

If the game has asymmetric factions or roles, define a loop per faction.

### 3. Player Goals & Win Conditions
- **Primary win condition**: What ends the game? How does a player win?
- **Secondary objectives**: Optional goals that shape strategy.
- **Loss condition**: How does a player lose, if applicable?
- **Progression hook**: What keeps players engaged between sessions or turns?

### 4. Core Mechanics
Define each mechanical system. For each:
- Name and purpose
- How it's triggered
- Resource costs / inputs
- Outputs / rewards
- Constraints / limits

Use subsections (4.1, 4.2…) per system. Examples: combat, resource generation, progression, randomness (dice/RNG/draws), special states (critical, death, lock, cooldown).

### 5. Economy & Resources
List every resource:

| Resource | Type | Source | Sink (how spent) | Cap |
|---|---|---|---|---|
| [Name] | Currency / Token / Stat | [how gained] | [how used] | [max] |

Include conversion rates if resources chain (e.g. 8 Data Packets → 1 Byte → 2 Bytes → Exfil).

### 6. Progression System
- Stages / tiers / epochs — name each, duration, what it unlocks
- What gates progression? (time, resources, actions, win conditions)

### 7. Components & Assets

**[Physical only]** — Bill of materials:
- Cards (types, counts), tiles / boards, tokens / meeples / dice, player aid cards

**[Digital only]** — Asset inventory:
- Sprites / animations per entity (idle, happy, sad, critical, death states)
- UI screens, audio (SFX, music), on-chain assets (NFT types, ERC standards)

Priority-order all assets — lowest-priority items cut first.

### 8. Turn / Phase Structure

**[Physical]** — Each phase of a round in order:
`Phase name → what happens → who acts → cost/rules`

**[Digital]** — Each game loop tick or session flow:
`State → trigger → system response → player feedback`

### 9. Factions / Roles / Characters
For each distinct playable side, class, or entity:
- Name and identity
- Unique mechanics or abilities
- Resource asymmetry vs other factions
- Strategic identity (aggressive, defensive, tempo, attrition)

### 10. Art Direction
- **Style**: (e.g. pixel art, card illustration, 3D, flat UI)
- **Resolution / format**: (e.g. 64×64px sprites, portrait card, hex tile)
- **Color palette / tone**: (e.g. dark cyber aesthetic, retro pastel)
- **Priority asset list**: ordered; lowest = cut first

### 11. Tech Stack **[Digital only]**
- Frontend framework
- Backend / game logic
- Blockchain / smart contracts (if applicable)
- Database / storage
- Real-time / event system

### 12. Phases & Milestones
Relative scope — no exact dates.

| Phase | Scope | Cut criteria |
|---|---|---|
| Demo / Alpha | Minimum playable experience | |
| Beta | Full core loop | |
| Launch | Polished, balanced | |
| Post-launch | Expansions, economy tuning | |

### 13. Economy & Monetization **[Digital only]**
- Revenue streams (entry fees, transactions, secondary market, subscriptions)
- Token / currency distribution
- Revenue splits (team wallet, reward pool, DAO)
- Secondary market fee structure

### 14. Open Questions & Assumptions
- `[TBD]` — decision deferred
- `[ASSUMPTION]` — assumed true, needs validation
- `[DESIGN RISK]` — known balance or UX concern

## Rules

- **Infer, don't interrogate.** Rough concept is enough. Generate first, refine after.
- **Precise economy tables.** Vague numbers cause balance problems. Exact values or `[TBD]`.
- **Feature creep goes in §14**, not the main doc.
- **Cross-reference systems.** When a mechanic depends on another, cite it (e.g. "see §4.2 Chi System").
- **Honest gaps beat invented details.** Use `[TBD]` liberally.
