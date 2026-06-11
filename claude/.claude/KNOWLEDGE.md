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
