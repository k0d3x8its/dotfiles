# git-crypt lock precheck

Before reading any planning file — `TODOS.md`, `findings.md`, `progress.md`,
`task_plan.md`, `SESSION-LOG.md`, `KNOWLEDGE.md` — in a repo that may use
git-crypt, confirm the file isn't locked. A git-crypt-locked file is ciphertext
on disk and parses as garbage; ingesting it silently corrupts context.

## Detect

git-crypt ciphertext begins with the magic bytes `\0GITCRYPT`:

```bash
head -c 9 <file> | grep -q $'\x00GITCRYPT' && echo LOCKED
```

## On LOCKED

Skip the file. Surface, do not parse:

```
<repo>: git-crypt locked — unlock first (see below); skipped.
```

Never treat ciphertext as content. This applies per-file, so in a multi-repo
sweep (e.g. `/dev-brief`) one locked repo skips only its own files — the rest of
the brief proceeds normally.

## How to unlock (the actual command)

`pass-cli login` on its own does **not** unlock anything — it only authenticates
the CLI. And bare `git-crypt unlock` (no key argument) only works if this machine
unlocked the repo before (`.git/git-crypt/keys/default` exists); on a fresh clone
it fails. You must supply the key.

**Any repo (including dotfiles), manual one-liner** — run from inside the locked
repo. Key is stored base64 in Proton Pass because git-crypt keys are binary:
```bash
k="$(mktemp)"; chmod 600 "$k"
echo '{{ pass://Personal/git-crypt/key }}' | pass-cli inject | base64 -d > "$k"
git-crypt unlock "$k"
shred -u "$k"
```
(Run `pass-cli login` first if the CLI isn't authenticated.)

**Offline fallback:** `git-crypt unlock ~/git-crypt-key` if the bare keyfile is present.

> Don't re-run `./install.sh` just to unlock — its unlock block is a
> *bootstrap-time* convenience; running the whole script re-stows and re-symlinks
> everything (heavy side effects) when all you need is the one-liner above. The
> dotfiles repo unlocks with the same command as any other repo.

See `docs/git-crypt-encryption.md` (in the dotfiles repo) for the full setup.
