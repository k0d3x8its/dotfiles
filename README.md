# dotfiles

[![CI](https://img.shields.io/github/actions/workflow/status/k0d3x8its/dotfiles/ci.yml?style=flat&label=CI)](https://github.com/k0d3x8its/dotfiles/actions/workflows/ci.yml) [<img alt="TARS" src="https://img.shields.io/badge/TARS-dev-%23E84142.svg?logo=data:image/png;base64,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">](https://github.com/k0d3x8its)

K0d3x personal dotfiles — Ubuntu 24.04 (Noble).

## Features

- **Triage system** — zero-token `TODOS.md` → `TRIAGE-BLOCK.md` pipeline with stale age bands and tier classification → [docs/triage-system.md](docs/triage-system.md)
- **Hooks** — auto-refresh triage on edit, session timer warnings, live cost/burn/context statusline → [docs/hooks.md](docs/hooks.md)
- **Episodic memory** — per-session auto-capture, progressive `/recall`, gated `/consolidate` → [docs/episodic-memory.md](docs/episodic-memory.md)
- **Memory architecture** — 5-store system (semantic, episodic, prospective, procedural, working) → [claude/.claude/references/MEMORY-ARCHITECTURE.md](claude/.claude/references/MEMORY-ARCHITECTURE.md)
- **Dev workflow** — session tools, skills, per-project setup → [docs/dev-workflow-guide.md](docs/dev-workflow-guide.md)
- **Git-crypt encryption** — sensitive files encrypted at rest → [docs/git-crypt-encryption.md](docs/git-crypt-encryption.md)

## Structure

```
dotfiles/
  bash/               → ~/.bashrc
  git/                → ~/.gitconfig, ~/.gitignore_global
  claude/             → ~/.claude/ (CLAUDE.md, settings, hooks, skills, references, plugins)
  ghostty/            → ~/.config/ghostty/sidebar.conf, autostart .desktop, ~/.local/bin/ghostty-sidebar
  scripts/            → trueline.sh, update-triage, update-cache, update-episodic, rotate-log
  fonts/              → Sauce Code Pro Nerd Font + Menlo for Powerline
  docs/               → dev-workflow-guide.md, triage-system.md, hooks.md, episodic-memory.md, git-crypt-encryption.md
  tests/              → install.bats, statusline_bars.bats (bats suite), test_update_triage.py, test_rotate_log.py, test_refresh_triage.py (Python unit tests)
  .github/workflows/  → ci.yml (shellcheck + bats + Python tests on push/PR)
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
| Ghostty sidebar | `sudo nala install xdotool` (required for window positioning) |

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
