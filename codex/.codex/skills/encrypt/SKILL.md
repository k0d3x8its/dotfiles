---
name: encrypt
description: Add git-crypt encryption to an existing or new repo. Inits git-crypt, writes root-anchored .gitattributes (KNOWLEDGE.md, TODOS.md, .memory/SESSION-LOG.md, .work/*), adds .gitignore negations, stores the binary key as base64 in Proton Pass Personal vault as <repo>-gitcrypt with full unlock instructions in the item note, and verifies every filter=git-crypt pattern. Use when setting up encryption for a repo, adding git-crypt to an existing project, or when a repo has plaintext session/planning files that should be encrypted before committing.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# /encrypt

Add git-crypt to any repo in one shot — new or existing.

## Quick start

```bash
cd ~/dev/<project>
# then trigger /encrypt
```

Handles everything: init → `.gitattributes` → `.gitignore` negations → Proton Pass key → verify.

See [REFERENCE.md](REFERENCE.md) for Proton Pass JSON template and verification details.

---

## Patterns

### .gitattributes (root-anchored — append-if-missing)

```
# git-crypt: root-anchored patterns (/ prefix = match only at repo root, not subdirs)
# WARNING: never remove the / prefix — unanchored patterns encrypt files of the same name
# in every subdirectory, breaking templates, test fixtures, and other unintended files.
/KNOWLEDGE.md            filter=git-crypt diff=git-crypt
/TODOS.md                filter=git-crypt diff=git-crypt
/.memory/SESSION-LOG.md  filter=git-crypt diff=git-crypt
/.work/*                 filter=git-crypt diff=git-crypt

# Design documents — encrypted to protect IP
/docs/GDD-*.md           filter=git-crypt diff=git-crypt
/docs/PRD-*.md           filter=git-crypt diff=git-crypt
/docs/ARD-*.md           filter=git-crypt diff=git-crypt
```

`/.work/*` encrypts all current and future files in `.work/` without revisiting `.gitattributes`.
`docs/GDD-*.md`, `docs/PRD-*.md`, `docs/ARD-*.md` protect IP in public repos — commit messages for these must be `"updated <filename>"` only.

### .gitignore negations (append-if-missing)

```
# git-crypt repo — override global ignore so encrypted files can commit
!/KNOWLEDGE.md
!/TODOS.md
!/.memory/SESSION-LOG.md
!/.work/PLAN.md
!/.work/FINDINGS.md
!/.work/PROGRESS.md
```

Glob negations not supported in `.gitignore` — list `.work/` files individually.

---

## Workflow

- [ ] **Preflight** — confirm git repo + `git-crypt` installed; if `.gitattributes` already has `filter=git-crypt` entries, warn and ask before proceeding (re-init is destructive)
- [ ] **Repo name** — `REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")`
- [ ] **Init** — `git-crypt init`
- [ ] **`.gitattributes`** — Read file first (may have EOL/LFS rules); append git-crypt block if no `filter=git-crypt` lines exist; print what was added (see [REFERENCE.md § .gitattributes handling](REFERENCE.md))
- [ ] **`.gitignore`** — append-if-missing negations from § Patterns above
- [ ] **Export key** — `git-crypt export-key` to a `chmod 600` tempfile → base64 → Proton Pass Personal vault as `<REPO_NAME>-gitcrypt` with full unlock note (see [REFERENCE.md § Proton Pass](REFERENCE.md))
- [ ] **Shred temp key** — `shred -u "$KEY_FILE"` immediately after Proton Pass write, even on failure
- [ ] **Verify** — `git-crypt status 2>&1`; if WARNING present run `git-crypt status -f`; confirm all target files show `encrypted:` with no warnings (see [REFERENCE.md § Verify](REFERENCE.md))
- [ ] **Summary** — print completion table + next steps

---

## Rules

- All `.gitattributes` patterns **must be root-anchored** (`/` prefix) — unanchored patterns encrypt files of the same name in every subdirectory and corrupt templates and test fixtures
- `.gitattributes` is committed source — never add it to `.gitignore`
- Shred the temp key file even if Proton Pass write fails
- Gitignore negations must list `.work/` files individually — glob negations are not supported in `.gitignore`
