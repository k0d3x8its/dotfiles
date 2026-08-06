# {{PROJECT_NAME}} — Claude Config

## Project Overview
**Type:** {{TYPE}}
**Stack:** {{STACK}}
**Goal:** {{DESCRIPTION}}

## Conventions
- Commit format: conventional commits (feat:, fix:, docs:, chore:)
- Commit granularity: one file per commit, brief message per file
- Branch naming: feature/, fix/, docs/, chore/
- NEVER add `Co-Authored-By` lines to commit messages
- Code comments: explain the why, not the what

## Trello
- Board: {{BOARD}}

## Skills

### Session
| Skill | When to use |
|---|---|
| `/handoff` | Lean fork — spin off side-issue, main session stays alive |
| `/handoff-return` | Merge tangent back, auto-sync findings to TODOS.md |
| `/close` | Lightweight session close + resume prompt (no decisions made) |
| `/checkpoint` | Durable close — writes `.memory/SESSION-LOG.md` narrative (decisions made) |

### Planning
| Skill | When to use |
|---|---|
| `/brainstorm` | Design doc with approaches + tradeoffs before planning |
| `/grill-me` | Stress-test a plan before committing |
| `/write-plan` | Create/update `.work/PLAN.md` Goals/Micro-Goals/Tasks |
| `/write-prd` | Write a product requirements doc |
| `/discover` | Open-ended research / discovery sweep |
| `/prototype` | Spike mode — fast throwaway proof of concept |

### Code Quality
| Skill | When to use |
|---|---|
| `/tdd` | Red-green-refactor vertical slices |
| `/diagnose` | Bug RCA → fix → post-mortem |
| `/trust-but-verify` | Verify claimed-done work before closing TODO |
| `/code-crit` | Structured code review (report-only) |
| `/code-refactor` | Fix a smell `/code-crit` named |
| `/review-response` | Review Claude's own response for accuracy |

### Docs & Release
| Skill | When to use |
|---|---|
| `/changelog` | Update CHANGELOG.md after changelog-worthy session |
| `/release-notes` | Generate release notes from CHANGELOG |
| `/dev-brief` | Dev brief summary of recent work |

### Knowledge
| Skill | When to use |
|---|---|
| `/remember` | Save a fact to KNOWLEDGE.md (runs promotion + dedup) |
| `/recall` | Retrieve a saved fact |
| `/consolidate` | Merge/deduplicate knowledge entries |

### Utilities
| Skill | When to use |
|---|---|
| `/sync-trello` | Push `.work/PLAN.md` Goals to Trello |
| `/find-skills` | List or search available skills |

## Session Rules
- Always read `.work/PLAN.md`, `.work/FINDINGS.md`, and `.work/PROGRESS.md` if they exist
- When I paste a re-entry prompt, treat it as ground truth for project state
- KNOWLEDGE.md writes: use `/remember` — never raw-append

## Current State
See `.work/PLAN.md` for active goals and progress.
See `.memory/SESSION-LOG.md` for recent session history.
