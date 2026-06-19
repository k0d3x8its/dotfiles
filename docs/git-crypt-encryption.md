# git-crypt Encryption — Implementation Guide

> Brief for a future Claude Code session. Read this top-to-bottom, then execute.
> Scope was confirmed with the user: **both** the dotfiles repo's own sensitive files
> **and** the per-project planning-files pattern. Key sharing: **symmetric key, stored in
> Proton Pass** (bare `~/git-crypt-key` as offline fallback) — see §7.

---

## 1. Context & goal

The dotfiles repo is public (the README links to it publicly). Today it protects
sensitive data two ways:

- **`.gitignore`** for runtime credentials (`.credentials.json`, Particle token, etc.).
- **Global gitignore** (`git/.gitignore_global` → `~/.gitignore_global` via
  `core.excludesfile`) for planning files — `TODOS.md`, `findings.md`, `progress.md`,
  `task_plan.md`, `SESSION-LOG.md`, `RELEASE-NOTES.md`, `ARCHIVE-LOG.md`. These are
  "machine-local by design" and are **never committed**.

Two problems this guide solves:

1. **`KNOWLEDGE.md` leaks in plaintext.** It is deliberately *not* ignored and commits
   normally. The global `claude/.claude/KNOWLEDGE.md` contains a personal email, Proton
   VPN usage, and detailed system/toolchain facts — all readable by anyone on a public
   repo.
2. **Planning files are lost across machines.** Because they're globally ignored, work
   notes (`TODOS.md`, `findings.md`, `progress.md`, …) never sync. The user wants them
   committed so they travel — but they can't go into a public repo as plaintext.

**git-crypt** solves both: it transparently encrypts chosen files on commit and decrypts
them on checkout (for anyone holding the key). Plaintext locally, ciphertext in the repo.

**Success looks like:** `KNOWLEDGE.md` and the chosen planning files are committed as
ciphertext, render as garbage on GitHub, and appear as normal plaintext in any local
checkout that has been unlocked with the symmetric key (fetched from Proton Pass; see §7).

---

## 1.5 First: the plaintext is already public — purge history (REQUIRED)

Encrypting `KNOWLEDGE.md` going forward protects only *new* commits. It is already
committed in plaintext across many past commits (`git log -p -- claude/.claude/KNOWLEDGE.md`)
on a **public** repo. Switching to git-crypt does **not** remove that exposure.

Two distinct actions, do both:

1. **Remediate (the data is compromised).** Rewriting history does not un-leak —
   forks, the GitHub API cache, and archive sites may already hold copies. So treat
   anything sensitive that was in plaintext as exposed:
   - The author **email** is also in every commit's author metadata → consider it
     permanently public; do not rely on encryption to hide it.
   - **Rotate** anything that is an actual credential (any token/account detail that
     appeared in `KNOWLEDGE.md`). Encryption protects the *future*, rotation handles
     the *past*.

2. **Rewrite history (hygiene — stops further casual scraping).** After git-crypt is
   set up (§5), strip the plaintext blobs and re-add the file encrypted:
   ```bash
   pipx install git-filter-repo        # or: sudo nala install git-filter-repo
   # back up the repo first — filter-repo rewrites ALL history
   git filter-repo --path claude/.claude/KNOWLEDGE.md --invert-paths --force
   # re-add encrypted as a fresh commit (git-crypt init + .gitattributes done, §5)
   git add claude/.claude/KNOWLEDGE.md
   git commit -m "chore(claude): re-add KNOWLEDGE.md under git-crypt"
   git push --force-with-lease origin main
   ```
   The file's old history dies — but that history *is* the leak, so this is
   acceptable. Every existing clone must re-clone after the force-push (solo user → fine).

---

## 2. How git-crypt works — 5 constraints you must respect

1. **git-crypt is per-repo.** `git-crypt init` runs once *inside each repository*. The
   dotfiles repo is one setup (Scope A below). Every `~/dev/<project>` repo is its own
   setup — so the per-project case (Scope B) is a **workflow pattern wired into
   `/dev-setup`**, not a one-time action.

2. **A file cannot be both gitignored and git-crypt-encrypted.** git-crypt only encrypts
   *tracked* files; git never stages an ignored file, so the encryption filter never
   runs on it. The planning files are globally ignored, so they must be **un-ignored
   first**. Do this with **per-repo `.gitignore` negations** (`!TODOS.md`, …), *not* by
   deleting lines from `git/.gitignore_global`. Repo-level `.gitignore` patterns override
   the global excludesfile, so "machine-local by default" stays intact for every repo
   that does **not** opt into encryption — only repos with git-crypt set up un-ignore and
   encrypt those files.

3. **Stow/symlink + unlock ordering.** `~/.claude/KNOWLEDGE.md` is a symlink into the
   dotfiles working tree (`install.sh` line ~49). On a freshly cloned, **not-yet-unlocked**
   machine the working-tree file is ciphertext, so Claude would read garbage through the
   symlink. **`git-crypt unlock` must run during bootstrap before the symlinks are
   relied on.** Wire this into `install.sh`.

4. **Do NOT encrypt `git/.gitconfig` (recommended).** Two reasons: (a) the email is
   already exposed in every commit's author metadata, so encrypting the config file gains
   nothing; (b) a ciphertext `~/.gitconfig` on a not-yet-unlocked machine breaks git
   itself. If the user still insists, document it as opt-in with these caveats — but the
   default is **encrypt `KNOWLEDGE.md` only** for the dotfiles repo.

5. **Filenames are not encrypted.** `.gitattributes` itself is committed in plaintext, so
   the *names* of encrypted files stay visible — only contents are protected. Don't put
   secrets in filenames.

---

## 3. Prerequisites — install git-crypt, pass-cli, git-filter-repo

```bash
sudo nala install git-crypt   # or: sudo apt-get install -y git-crypt
git-crypt --version           # confirm it's on PATH
```

Add `git-crypt` to `packages.txt` so `./install.sh --packages` provisions it on new
machines (it's consumed at `install.sh` line ~138: `xargs sudo apt-get install -y < packages.txt`).

Also needed:
- **`pass-cli`** (official Proton Pass CLI) — holds the symmetric key; `install.sh`
  fetches it at unlock time. Requires Pass Plus / Family / Pro or any Proton bundle
  (the CLI is gated; free plans must use the bare-keyfile fallback). On a new machine
  run `pass-cli login` before the first unlock. See §7.
- **`git-filter-repo`** — only for the one-time history purge (§1.5), not on the hot
  path: `pipx install git-filter-repo` or `sudo nala install git-filter-repo`.

---

## 4. What to encrypt — decision table

### Per-project planning files (Scope B)

| File | Action | Why |
|---|---|---|
| `TODOS.md` | **Encrypt + commit** | Open work / next steps; may name internal targets. Worth syncing. |
| `findings.md` | **Encrypt + commit** | Investigation notes; can hold sensitive detail. |
| `progress.md` | **Encrypt + commit** | Progress log; worth syncing. |
| `task_plan.md` | **Encrypt + commit** | Structured plan; may hold sensitive detail. |
| `SESSION-LOG.md` | **Encrypt + commit** | Session narrative + decisions; the durable record. |
| `KNOWLEDGE.md` | **Encrypt + commit** | Already committed today — switch it to encrypted. |
| `RELEASE-NOTES.md` | **Keep local** | Generated by `/release-notes`; regenerated, not source. |
| `ARCHIVE-LOG.md` | **Keep local** (opt-in encrypt) | Rotated archive of `SESSION-LOG.md`; large, low value to sync. |
| `TRIAGE-BLOCK.md` | **Keep local** (opt-in encrypt) | Derived from `TODOS.md` by the triage script; regenerated, so committing it is redundant. |
| `.claude/trello-board` | **Keep local** | Just a board name; low value. |

### Dotfiles repo's own files (Scope A)

| File | Action | Why |
|---|---|---|
| `claude/.claude/KNOWLEDGE.md` | **Encrypt** | Email, Proton VPN usage, system/toolchain facts on a public repo. |
| `git/.gitconfig` | **Skip (not recommended)** | Email already in commit metadata; ciphertext config breaks git pre-unlock. See constraint #4. |

---

## 5. Scope A — set up the dotfiles repo

Run from the dotfiles repo root.

```bash
# 1. Initialise git-crypt in this repo (creates .git-crypt/, generates the key)
git-crypt init

# 2. Tell git which files to encrypt
cat >> .gitattributes <<'EOF'
claude/.claude/KNOWLEDGE.md filter=git-crypt diff=git-crypt
EOF

# 3. Re-stage KNOWLEDGE.md so it gets re-written through the encryption filter
git rm --cached claude/.claude/KNOWLEDGE.md
git add .gitattributes claude/.claude/KNOWLEDGE.md

# 4. Verify BEFORE committing — it must list KNOWLEDGE.md as "encrypted"
git-crypt status -e
```

Then:

- **`install.sh`** — a bootstrap unlock block is already wired in (right after
  `mkdir -p "$HOME/.claude/..."`, before the KNOWLEDGE.md symlink). It:
  - treats `[ -f "$DOTFILES/.git/git-crypt/keys/default" ]` as "already unlocked" (reliable
    idempotency — *not* the `git config --get-regexp '^git-crypt'` guess, which git-crypt
    doesn't reliably set);
  - fetches the key from Proton Pass (`pass-cli inject | base64 -d` into a `chmod 600`
    tempfile), falls back to a bare `~/git-crypt-key`, then `( cd "$DOTFILES" && git-crypt
    unlock "$keyfile" )` — note `git -C "$DOTFILES" git-crypt unlock` is **wrong** (git
    resolves subcommand `git-crypt` → `git-git-crypt`, not found; the subcommand is `crypt`);
  - shreds the tempfile and prints a **loud WARN** (not a silent no-op) when no key is
    available, so a locked machine fails visibly instead of feeding Claude ciphertext.
- **`docs/dev-workflow-guide.md`** — in Part 1 ("Install Everything"), add a note that a
  fresh machine must run `pass-cli login` (or place `~/git-crypt-key`) before
  `KNOWLEDGE.md` and other encrypted files are readable; see §7.

---

## 6. Scope B — per-project pattern + `/dev-setup` integration

Make encryption an **optional, opt-in** step so existing behaviour is unchanged unless
the user asks for it. Files to edit:

**A. New template — `claude/.claude/skills/dev-setup/templates/gitattributes`** (static):
```
TODOS.md        filter=git-crypt diff=git-crypt
findings.md     filter=git-crypt diff=git-crypt
progress.md     filter=git-crypt diff=git-crypt
task_plan.md    filter=git-crypt diff=git-crypt
SESSION-LOG.md  filter=git-crypt diff=git-crypt
KNOWLEDGE.md    filter=git-crypt diff=git-crypt
```

**B. `templates/gitignore.core`** — add commented negation lines that the new step
un-comments (or the step appends them) when encryption is enabled, so the encrypted
planning files override the global ignore:
```
# Uncomment when git-crypt is enabled for this repo (see /dev-setup encryption step):
# !TODOS.md
# !findings.md
# !progress.md
# !task_plan.md
# !SESSION-LOG.md
```
(`KNOWLEDGE.md` is already not ignored, so it needs no negation.)

**C. `claude/.claude/skills/dev-setup/SKILL.md`** — add a new optional step (place it
**after** Step 14 "Git check", since `git-crypt init` needs a git repo). Step logic:

> **Step: Enable encrypted planning files? (optional)**
> Ask: *"Encrypt this project's planning files (TODOS.md, findings.md, progress.md,
> task_plan.md, SESSION-LOG.md, KNOWLEDGE.md) with git-crypt so they commit safely? (yes / skip)"*
> If **yes**:
> 1. Verify `git-crypt` is installed and a git repo exists (Step 14 ran). If not, print
>    the install command and skip gracefully.
> 2. `git-crypt init`.
> 3. Write `templates/gitattributes` → `.gitattributes` (append-if-missing, same merge
>    discipline as the `.gitignore` step).
> 4. Add the `!`-negation lines for the planning files to `.gitignore` (under the
>    `# --- added by /dev-setup ---` marker), so they're no longer globally ignored.
> 5. Unlock with the shared key fetched from Proton Pass (see §7):
>    ```bash
>    k="$(mktemp)"; chmod 600 "$k"
>    echo '{{ pass://Private/git-crypt/key }}' | pass-cli inject | base64 -d > "$k"
>    git-crypt unlock "$k"; shred -u "$k"
>    ```
>    If `pass-cli` isn't logged in / available, fall back to `git-crypt unlock ~/git-crypt-key`;
>    if neither key source is present, tell the user and leave the repo locked.
> 6. Remind: the key lives in Proton Pass (and nowhere committed); losing it loses the data.
> Update Step 17 (completion summary) to report whether encryption was enabled.

Keep it idempotent and safe to re-run, like the rest of the wizard.

---

## 7. Symmetric key management (Proton Pass)

One symmetric key is shared across all machines and all repos that opt in. It lives in
**Proton Pass**, not as a bare file in `$HOME` — `install.sh` and `/dev-setup` fetch it
at unlock time and shred the temp copy. (Symmetric over GPG on purpose: this is a
single user across their own machines, so GPG's multi-user access control buys nothing
while adding onboarding ceremony and a passphrase prompt that fights the unattended
`install.sh` unlock. GPG would only pay off with collaborators.)

**Store the key once** (from the machine that ran `git-crypt init`). git-crypt keys are
binary, so base64-encode it for a text vault field:
```bash
git-crypt export-key /dev/stdout | base64 -w0
# → paste into Proton Pass: vault "Private", item "git-crypt", field "key"
```

**On a new machine**, after cloning a repo:
```bash
pass-cli login                       # authenticate the CLI once
cd <repo>
k="$(mktemp)"; chmod 600 "$k"
echo '{{ pass://Private/git-crypt/key }}' | pass-cli inject | base64 -d > "$k"
git-crypt unlock "$k"; shred -u "$k"
```
For the dotfiles repo specifically, `./install.sh` does this automatically at bootstrap.

- **Never commit the key** to any repo — it's the master key; anyone with it decrypts
  everything (and all history).
- **Offline fallback:** a bare `~/git-crypt-key` (`git-crypt export-key ~/git-crypt-key`)
  still works if `pass-cli` is unavailable. `chmod 600` it and keep it out of any synced
  or backed-up dir — otherwise the key travels next to the decrypted working trees and
  the encryption buys nothing.
- **Key loss = permanent data loss.** No recovery; encrypted history can't be decrypted
  without it. Proton Pass *is* the backup — don't also delete it from the vault.
- The *same* key unlocks the dotfiles repo and every per-project repo, because each was
  `init`'d and then `unlock`'d from this one key.
- **No cheap revocation.** git-crypt can't rotate the master key in place; if the key
  leaks, the only real fix is re-`init` + re-encrypt every repo (old key still decrypts
  all existing history). Storing it in Proton Pass improves transport/at-rest, not
  revocation.

---

## 8. Docs to update for consistency

After the mechanics work, fix the now-stale "model truth" so future sessions aren't
misled:

- **`claude/.claude/KNOWLEDGE.md`** — the line stating planning files are "machine-local
  by design" and "KNOWLEDGE.md is deliberately not ignored and commits normally" needs a
  follow-up fact: planning files and `KNOWLEDGE.md` are now **git-crypt-encrypted** in
  repos that opt in, committed as ciphertext, unlocked via the Proton Pass key (§7).
  Route real edits through `/remember` per the existing direct-write rule.
- **`claude/.claude/CLAUDE.md`** — the `KNOWLEDGE.md` / "Always read KNOWLEDGE.md" notes
  should mention that on a locked checkout the file is ciphertext and must be unlocked
  first (pointer to `references/git-crypt-lock-check.md`).
- **`claude/.claude/skills/dev-setup/SKILL.md`** Step 12 / Notes — note that `KNOWLEDGE.md`
  is committed and, when the encryption step is enabled, committed *encrypted*.

---

## 9. Verification

```bash
# In the dotfiles repo, after committing:
git-crypt status -e            # KNOWLEDGE.md listed as encrypted
git show HEAD:claude/.claude/KNOWLEDGE.md | head   # ciphertext (GITCRYPT… binary)
cat claude/.claude/KNOWLEDGE.md | head             # plaintext locally (unlocked)

# Round-trip:
git-crypt lock                 # working tree now ciphertext
cat claude/.claude/KNOWLEDGE.md   # garbage
# unlock from Proton Pass (or: git-crypt unlock ~/git-crypt-key)
k="$(mktemp)"; chmod 600 "$k"; echo '{{ pass://Private/git-crypt/key }}' \
  | pass-cli inject | base64 -d > "$k"; git-crypt unlock "$k"; shred -u "$k"
cat claude/.claude/KNOWLEDGE.md   # plaintext again

# Fresh-clone simulation (no key): file is ciphertext, symlink reads garbage —
# confirms install.sh must unlock during bootstrap.
```

For a project repo (Scope B), after `/dev-setup` enables encryption: `git-crypt status -e`
lists the planning files, `git check-ignore TODOS.md` reports it is **no longer ignored**,
and a locked checkout shows ciphertext.

---

## 10. Rollback & gotchas

- **Unlock before use.** Until `git-crypt unlock` runs, encrypted files (and the symlinks
  pointing at them) are ciphertext. Bootstrap order matters.
- **GitHub web.** Encrypted files don't render or diff in the GitHub UI — expected.
- **Merge conflicts on a locked machine** can't be resolved (you'd be editing ciphertext).
  Always unlock first.
- **Filenames stay visible** (constraint #5) — don't encode secrets in names.
- **To stop encrypting a file:** remove its line from `.gitattributes`, then
  `git rm --cached <file> && git add <file>` to re-commit it in plaintext. Note the
  ciphertext remains in history.
- **`.gitconfig`:** left in plaintext on purpose (constraint #4).
