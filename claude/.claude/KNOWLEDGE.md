# Global Knowledge

> Curated facts about my environment, toolchain, and cross-project workflow.
> Promoted via /checkpoint or /remember. Committed via dotfiles.

---

- Solo developer and maker. Ubuntu 24.04 (Noble). Primary tools: Neovim, Ghostty, Nala, Git, GitHub.
- references/ in dotfiles is a whole-dir symlink — files added to dotfiles/claude/.claude/references/ are immediately available at ~/.claude/references/ without re-running install.sh.
- Proton suite (Mail, VPN, Drive) for privacy. Brave as primary browser. Godot for game development.
- KOS (Kodex OS) is a personal knowledge management system built on Obsidian — the overarching meta-project tying all other projects together.
- Git identity is global only: user.name `K0d3x`, user.email `k0d3x@pm.me` (Proton) — no per-repo overrides.
- Global gitignore (`~/.gitignore_global` via core.excludesfile) ignores root-level planning files in every repo — SESSION-LOG.md, TODOS.md, task_plan.md, findings.md, progress.md, RELEASE-NOTES.md, ARCHIVE-LOG.md — plus `.claude/plugins/` and `.claude/skills/`. Planning files are machine-local by design; KNOWLEDGE.md is deliberately not ignored and commits normally.
- `~/.bashrc` is a symlink to `dotfiles/bash/.bashrc` — shell edits land in the dotfiles repo, not a loose home file.
- Shell prompt is trueline — bashrc sources `~/dev/trueline.sh`, itself a symlink to `dotfiles/scripts/trueline.sh`.
- Node runs via nvm (currently v24.15.0); npm prefix points into the nvm version dir, so `npm i -g` and pnpm live there. Legacy `~/.npm-global/bin` is still on PATH and holds older tools (agent-browser, qmd, tree-sitter).
- `~/.config/nvim` is a symlink to `~/dev/kodex-ide` — that repo IS the Neovim config (running a 0.12 dev build).
- Claude Code installed via native installer (`~/.local/share/claude/versions/`), not npm — `~/.local/bin/claude` symlinks the active version.
- Ghostty config is fully stowed from dotfiles (2026-06-10) — both `config` and `sidebar.conf` in `~/.config/ghostty/` are symlinks into `dotfiles/ghostty/`; edit the repo files.
- `kos` bash alias activates the kos-capture venv and cds into `~/dev/kos-capture`.
- claude-monitor installed via `uv tool` (aliases ccm/ccmonitor/cmonitor); whisper and yt-dlp are system-python pip installs in `~/.local/bin`.
- OpenCode lives at `~/.opencode/bin`, added to PATH in bashrc.
- Neovim `FileChangedShell` never fires for edits made by a child process inside `:terminal` — no FocusGained happens (same process). Must trigger `:checktime` manually (TermLeave/WinEnter/CursorHold autocmds).
- opencode TUI accepts `--prompt "<text>"` at launch to seed the first message (also `-c`/`-s` to continue sessions); `opencode run` is one-shot non-interactive, never starts the TUI (verified v1.16.2).
- Claude Code's Edit/Write tools refuse to write through symlinks — edit the real target under dotfiles/claude/.claude/ (CLAUDE.md, settings.json, KNOWLEDGE.md, skills), not the ~/.claude/ symlink.
- ~/.claude is deliberately NOT stow-managed (runtime state coexists with config) — install.sh wires absolute `ln -sf` links and globs the skills dir. After adding/removing a skill, re-run `bash install.sh` (idempotent); `stow --restow claude` is the wrong tool and aborts on the absolute links.
- ~/.claude/plugins/{installed_plugins,known_marketplaces}.json are runtime-mutated — install.sh seed-copies them (cp once if absent, never symlinks, since 2026-06-12); repo copies are fresh-machine bootstrap seeds, updated deliberately when adding a marketplace.
