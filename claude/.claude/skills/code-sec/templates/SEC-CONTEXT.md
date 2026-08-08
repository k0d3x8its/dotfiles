<!--
  SEC-CONTEXT — shared project security context (TEMPLATE).

  INSTANCE LIVES AT: .work/SEC-CONTEXT.md (per-repo, git-crypted).
  This file under templates/ is the blank schema; copy it to .work/SEC-CONTEXT.md
  on first use and fill the sections your work touches.

  WHO READS/WRITES THIS (skills read what they need, fill what they learn):
    - threat-model  — writes Topology, Actors, Data stores, Trust boundaries from its
                      phase-0 interview; reads all back on re-runs instead of re-asking.
    - bounty-hunter — reads Topology & exposure + Actors & auth tiers + Trust boundaries
                      for its reachability gate; persists confirmed exposure + auth tiers.
    - code-sec      — reads Auth mechanics & sanitizers at phase 0 so it does not flag
                      the project's own auth helpers/sanitizers as missing controls.

  ONE CONTEXT FILE, FILLED ONCE, REUSED ACROSS SKILLS. A question answered by one
  skill is not re-asked by another. Leave a section blank (keep its "_not yet
  established_" line) if no skill has learned it yet — blank means unknown, not none.

  SECURITY: this file is an attacker roadmap (trust boundaries + auth mechanics + data
  value). It MUST be git-crypted — the instance path .work/SEC-CONTEXT.md is covered by
  the root-anchored .gitattributes rule. Never commit it plaintext.
-->

# Security Context — {{PROJECT_NAME}}

> Shared security context for the sec suite (threat-model / bounty-hunter / code-sec).
> Instance path: `.work/SEC-CONTEXT.md` (git-crypted). Review date: {{DATE}}.

---

## Topology & exposure

> What the system exposes and from where. One row per network entry point / listener.
> Source the rows from `~/.claude/skills/code-sec/bin/enumerate-entrypoints.sh`, then
> correct the exposure column against reality (production bind, reverse proxy, firewall).
> Exposure tiers: **public** (external / internet-reachable) · **internal** (other
> services inside the trust boundary) · **local** (loopback / same-host only).

_not yet established_

| Entry point (file:line) | Kind | Bind hint | Exposure | Confidence | Notes |
|---|---|---|---|---|---|
| | | | | | |

---

## Actors & auth tiers

> Who interacts with the system and what authentication each entry point requires.
> Auth tiers: **unauth-external** (anyone, no credentials) ·
> **authenticated-any-user** (any logged-in account — the IDOR/BOLA surface) ·
> **privileged** (admin / elevated role — escalation-only surface).

_not yet established_

**Actors:**

- <actor> — <who they are, how they reach the system, what they can do>

**Auth tier per entry point:**

| Entry point (file:line) | Auth tier required | Mechanism (how enforced) | Confirmed |
|---|---|---|---|
| | | | |

---

## Data stores & business value

> Databases, files, caches, queues holding data — and why an attacker would want them.
> Business value drives impact scoring in threat-model's risk grid.

_not yet established_

| Store | Contents / sensitivity | Business value if breached | Access control |
|---|---|---|---|
| | | | |

---

## Auth mechanics & sanitizers

> How auth/authz and input-sanitization actually work IN THIS REPO — the helpers that
> ARE the controls, so code-sec does not flag them as missing. Give 3–5 concrete code
> examples (guard name + `file:line` + a one-line snippet). This is the section that
> kills the false-positive class "flagged the project's own auth helper as unauthed".

_not yet established_

**Authentication:**

- `<guard/decorator>` (`file:line`) — <what it checks, e.g. validates session JWT>
  ```
  <snippet>
  ```

**Authorization:**

- `<guard>` (`file:line`) — <ownership / role check performed>

**Input sanitizers / validators:**

- `<sanitizer>` (`file:line`) — <what it neutralizes, e.g. parameterized query builder>

---

## Trust boundaries

> Where data crosses from a less-trusted zone to a more-trusted one — the lines every
> flow must be checked against. Read by all three skills. In DFD terms these are the
> dashed boundaries (threat-model), the "external tier" edges (bounty-hunter reachability),
> and the taint sources (code-sec).

_not yet established_

- **<boundary name>** — <what is on each side; what crosses; what validates the crossing>
