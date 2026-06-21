# /encrypt Reference

## § Proton Pass — key storage

Item structure:

| Field        | Value                                  |
|---|---|
| Title        | `<REPO_NAME>-gitcrypt`                 |
| Vault        | `Personal`                             |
| Type         | Custom item                            |
| Section name | `git-crypt`                            |
| Field name   | `key` (type: hidden)                   |
| Field value  | `$(base64 -w 0 < "$KEY_FILE")`         |

Item note (substitute `<REPO_NAME>`):

```
git-crypt symmetric key for the <REPO_NAME> repo.
Encrypts planning/session files at rest so they commit safely to a (potentially public) remote.

The value stored in this item is BASE64-ENCODED — the raw key is binary and cannot be stored as plain text.

To unlock on a fresh machine (run from inside the repo):
  k="$(mktemp)"; chmod 600 "$k"
  echo '{{ pass://Personal/<REPO_NAME>-gitcrypt/key }}' | pass-cli inject | base64 -d > "$k"
  git-crypt unlock "$k"
  shred -u "$k"

Run `pass-cli login` first if the CLI is not authenticated.
```

Create command — use `section_name`/`field_name`/`field_type` (verified against `pass-cli item create custom --get-template`):

```bash
pass-cli item create custom --vault-name "Personal" --from-template - << JSON
{
  "title": "${REPO_NAME}-gitcrypt",
  "note": "...",
  "sections": [{
    "section_name": "git-crypt",
    "fields": [{"field_name": "key", "field_type": "hidden", "value": "${KEY_B64}"}]
  }]
}
JSON
```

---

## § Verify

Use `git-crypt status` — the authoritative tool. Do NOT use `head -c 9 | grep $'\x00GITCRYPT'`; null-byte grep patterns produce false positives.

### Step 1 — run status

```bash
git-crypt status 2>&1
```

Exit code 1 is expected when a previously-committed plaintext file now needs encryption — not a fatal error. Always capture output; do not rely on exit code alone.

### Step 2 — check for WARNING lines

Scan output for `*** WARNING: staged/committed version is NOT ENCRYPTED! ***`.

If any WARNING present, re-stage those files through the clean filter:

```bash
git-crypt status -f
```

Then re-run `git-crypt status 2>&1` and confirm no WARNINGs remain.

**Important:** `git-crypt status -f` pre-stages the encrypted blobs. Those staged files will bundle into the next `git commit` automatically — no separate commit is needed. When you commit `.gitattributes`, the re-encrypted files come along. If you then try `git add <file> && git commit` for those same files, you'll get "nothing to commit."

### Step 3 — confirm target files

All files matching the `.gitattributes` patterns should appear as `encrypted:` in the output. Report any that do not.

```
    encrypted: .memory/SESSION-LOG.md     ✓
    encrypted: .work/FINDINGS.md          ✓
    encrypted: .work/PLAN.md              ✓
    encrypted: .work/PROGRESS.md          ✓
    encrypted: TODOS.md                   ✓
    encrypted: KNOWLEDGE.md               ✓
```

Untracked files that haven't been committed yet will still show as `encrypted:` — correct, they will encrypt on first commit.

---

## § .gitattributes handling

If `.gitattributes` exists (EOL rules, LFS config, etc): Read first, then append — never overwrite existing content. Add only the git-crypt block if no `filter=git-crypt` lines are present yet.

If `.gitattributes` does not exist: Write directly (no Read needed).
