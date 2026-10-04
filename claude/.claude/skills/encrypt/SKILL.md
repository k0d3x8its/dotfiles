---
name: encrypt
description: Add git-crypt encryption to an existing or new repo. Inits git-crypt, writes root-anchored .gitattributes (KNOWLEDGE.md, TODOS.md, .memory/SESSION-LOG.md, and .work/ at any depth), adds .gitignore negations, stores the binary key as base64 in Proton Pass Personal vault as <repo>-gitcrypt with full unlock instructions in the item note, then verifies every filter=git-crypt pattern and round-trip-verifies the stored key. Use when setting up encryption for a repo, adding git-crypt to an existing project, or when a repo has plaintext session/planning files that should be encrypted before committing.
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

# .work/ is encrypted wholesale — no exceptions, current and future files alike.
# BOTH lines are required. .gitattributes uses gitignore glob rules, where `*` does NOT
# match `/`: `/.work/*` covers only top-level files, so nested paths such as
# .work/todos/, .work/plan/ and .work/findings/ (the index+detail planning format)
# fall through and commit in PLAINTEXT. Use `/.work/**/*.md` instead of the second line
# only if that repo's .work/ is markdown-only.
/.work/*                 filter=git-crypt diff=git-crypt
/.work/**/*              filter=git-crypt diff=git-crypt

# Design documents — encrypted to protect IP
/docs/GDD-*.md           filter=git-crypt diff=git-crypt
/docs/PRD-*.md           filter=git-crypt diff=git-crypt
/docs/ARD-*.md           filter=git-crypt diff=git-crypt

# Security artifacts — attacker roadmaps (SEC-CONTEXT covered by the /.work/ lines above)
/docs/threat-model.md        filter=git-crypt diff=git-crypt
/docs/threat-model.dfd.mmd   filter=git-crypt diff=git-crypt
```

The `/.work/*` + `/.work/**/*` pair encrypts all current and future files in `.work/`, at any
depth, without revisiting `.gitattributes`. Verify the nested half actually took:

```bash
git check-attr filter .work/todos/anything.md   # must print: filter: git-crypt
```

`unspecified` means the nested pattern is missing or mistyped — that file would commit in
plaintext.

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
!/.work/SEC-CONTEXT.md
```

Glob negations not supported in `.gitignore` — list `.work/` files individually.
Any git-crypt file that `gitignore.core` also ignores as "local context" needs a
matching negation here, or it stays ignored and never commits (never persists).

---

## Workflow

- [ ] **Preflight** — confirm git repo + `git-crypt` installed; if `.gitattributes` already has `filter=git-crypt` entries, warn and ask before proceeding (re-init is destructive)
- [ ] **Repo name** — `REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")`
- [ ] **Init** — `git-crypt init`
- [ ] **`.gitattributes`** — Read file first (may have EOL/LFS rules); append git-crypt block if no `filter=git-crypt` lines exist; print what was added (see [REFERENCE.md § .gitattributes handling](REFERENCE.md))
- [ ] **`.gitignore`** — append-if-missing negations from § Patterns above
- [ ] **Duplicate-title guard** — BEFORE creating anything, check for an existing item:
      `pass-cli item list --vault-name Personal | grep "]: ${REPO_NAME}-gitcrypt "`.
      If any match exists — **including `state=Trashed`** — stop and report. Do not create a
      second one. `pass-cli` resolves `pass://` and `--item-title` across active _and_
      trashed items and returns the **oldest** match, so a duplicate silently makes `inject`
      return the wrong item (or 0 bytes). Resolve the existing item first.
- [ ] **Export key** — `git-crypt export-key` to a `chmod 600` tempfile → base64 → Proton Pass Personal vault as `<REPO_NAME>-gitcrypt` with full unlock note (see [REFERENCE.md § Proton Pass](REFERENCE.md))
- [ ] **Round-trip verify the key** — prove the backup works, don't assume it. Retrieve
      through the exact command in the item note and compare hashes:
      `bash
  echo "{{ pass://Personal/${REPO_NAME}-gitcrypt/key }}" | pass-cli inject \
    | base64 -d | sha256sum
  `
      Must equal `sha256sum` of the exported key file. An item existing is **not** evidence
      of a working backup — only a hash match is.
- [ ] **Shred temp key** — `shred -u "$KEY_FILE"` immediately after Proton Pass write, even on failure
- [ ] **Verify encryption** — `git-crypt status 2>&1`; if WARNING present run `git-crypt status -f`; confirm all target files show `encrypted:` with no warnings (see [REFERENCE.md § Verify](REFERENCE.md))
- [ ] **Verify nested coverage** — `git check-attr filter .work/todos/x.md` must print
      `filter: git-crypt`, not `unspecified`
- [ ] **Summary** — print completion table + next steps

---

## Rules

- All `.gitattributes` patterns **must be root-anchored** (`/` prefix) — unanchored patterns encrypt files of the same name in every subdirectory and corrupt templates and test fixtures
- A directory needs **both** `/dir/*` and `/dir/**/*` — in gitattributes, `*` does not match `/`, so a single-star pattern silently leaves nested files unencrypted
- Never create a second Proton Pass item with an existing `<repo>-gitcrypt` title — trashed items shadow active ones in title lookup, and `inject` returns the oldest
- A stored key is not a backup until a round-trip hash match proves it
- `.gitattributes` is committed source — never add it to `.gitignore`
- Shred the temp key file even if Proton Pass write fails
- Gitignore negations must list `.work/` files individually — glob negations are not supported in `.gitignore`
