# {{PROJECT_NAME}} — Claude Config

## Project Overview
**Type:** {{TYPE}}
**Stack:** {{STACK}}
**Goal:** {{DESCRIPTION}}

## Conventions
- Commit format: conventional commits (feat:, fix:, docs:, chore:)
- Branch naming: feature/, fix/, docs/, chore/
- NEVER add `Co-Authored-By` lines to commit messages
- Code comments: explain the why, not the what

## Trello
- Board: {{BOARD}}

## Skills
- `/sync-trello` — push task_plan.md Goals to Trello
- `/handoff`     — end-of-session context preservation
- `/plan`        — create/update task_plan.md

## Session Rules
- Always read task_plan.md, findings.md, and progress.md if they exist
- When I paste a re-entry prompt, treat it as ground truth for project state

## Current State
See task_plan.md for active goals and progress.
See session-log.md for recent session history.
