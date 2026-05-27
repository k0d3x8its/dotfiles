# dotfiles

K0d3x personal dotfiles — Ubuntu 24.04 (Noble).

## Structure

```
dotfiles/
  bash/               → ~/.bashrc
  git/                → ~/.gitconfig, ~/.gitignore_global
  claude/             → ~/.claude/ (CLAUDE.md, settings, hooks, skills)
  scripts/            → trueline.sh (symlinked to ~/dev/trueline.sh)
  fonts/              → Sauce Code Pro Nerd Font + Menlo for Powerline
  docs/               → dev-workflow-guide.md, hooks-config.json
  packages.txt        → manually installed apt packages
  install.sh          → full bootstrap script
```

Neovim config lives in its own repo: [kodex-ide](https://github.com/k0d3x8its/kodex-ide)

## Install

```bash
git clone git@github.com:k0d3x8its/dotfiles.git ~/dev/dotfiles
cd ~/dev/dotfiles
chmod +x install.sh
./install.sh
```

Pass `--packages` to also install apt packages:

```bash
./install.sh --packages
```

## Manual steps after install

| Step | Command |
|------|---------|
| kos skills | `npx skills install kos` |
| Particle CLI | `npm install -g particle-cli && particle login` |
| Antigravity | Has its own CLI installer — see https://antigravity.dev |

## What is NOT tracked

| Path | Reason |
|------|--------|
| `~/.claude/.credentials.json` | Claude OAuth token |
| `~/.claude/history.jsonl` | Chat history |
| `~/.claude/sessions/`, `projects/` | Session transcripts |
| `~/.claude/plugins/cache/`, `marketplaces/` | Downloaded at runtime |
| `~/.particle/particle.config.json` | Particle access token |

## Updating packages list

```bash
apt-mark showmanual | sort > ~/dev/dotfiles/packages.txt
```
