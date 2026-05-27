#!/usr/bin/env bash
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"

# ── helpers ───────────────────────────────────────────────────────────────────

log() { echo "→ $*"; }

# Back up a real file/dir, remove symlinks silently
safeguard() {
    local target="$1"
    if [[ -L "$target" ]]; then
        rm "$target"
    elif [[ -e "$target" ]]; then
        mkdir -p "$BACKUP"
        log "backing up $target → $BACKUP/"
        mv "$target" "$BACKUP/"
    fi
}

# ── main ──────────────────────────────────────────────────────────────────────

main() {
    # ── stow packages ─────────────────────────────────────────────────────────

    log "stowing bash"
    safeguard "$HOME/.bashrc"
    stow --no-folding --dir="$DOTFILES" --target="$HOME" bash

    log "stowing git"
    safeguard "$HOME/.gitconfig"
    safeguard "$HOME/.gitignore_global"
    stow --no-folding --dir="$DOTFILES" --target="$HOME" git

    # ── claude ────────────────────────────────────────────────────────────────
    # Stow can't replace a live ~/.claude/ dir wholesale — symlink specific
    # subdirs and files manually so runtime state is left untouched.

    log "wiring claude config"
    mkdir -p "$HOME/.claude/plugins" "$HOME/.claude/skills"

    # individual files
    safeguard "$HOME/.claude/CLAUDE.md"
    ln -sf "$DOTFILES/claude/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"

    safeguard "$HOME/.claude/settings.json"
    ln -sf "$DOTFILES/claude/.claude/settings.json" "$HOME/.claude/settings.json"

    safeguard "$HOME/.claude/plugins/installed_plugins.json"
    ln -sf "$DOTFILES/claude/.claude/plugins/installed_plugins.json" \
        "$HOME/.claude/plugins/installed_plugins.json"

    safeguard "$HOME/.claude/plugins/known_marketplaces.json"
    ln -sf "$DOTFILES/claude/.claude/plugins/known_marketplaces.json" \
        "$HOME/.claude/plugins/known_marketplaces.json"

    # hooks dir
    safeguard "$HOME/.claude/hooks"
    ln -sf "$DOTFILES/claude/.claude/hooks" "$HOME/.claude/hooks"

    # manual skills (plugin-installed skills like kos* are reinstalled separately)
    for skill in dev-setup release-notes session-handoff sync-trello trello-agent; do
        safeguard "$HOME/.claude/skills/$skill"
        ln -sf "$DOTFILES/claude/.claude/skills/$skill" "$HOME/.claude/skills/$skill"
    done

    # ── trueline ──────────────────────────────────────────────────────────────

    log "installing trueline"
    mkdir -p "$HOME/dev"
    safeguard "$HOME/dev/trueline.sh"
    ln -sf "$DOTFILES/scripts/trueline.sh" "$HOME/dev/trueline.sh"

    # ── neovim ────────────────────────────────────────────────────────────────

    log "setting up neovim config"
    if [[ -d "$HOME/.config/nvim/.git" ]]; then
        log "  kodex-ide already cloned, skipping"
    else
        mkdir -p "$HOME/.config"
        safeguard "$HOME/.config/nvim"
        git clone git@github.com:k0d3x8its/kodex-ide.git "$HOME/.config/nvim"
    fi

    # ── fonts ─────────────────────────────────────────────────────────────────

    log "installing fonts"
    mkdir -p "$HOME/.local/share/fonts"
    cp "$DOTFILES/fonts/"*.ttf "$HOME/.local/share/fonts/"
    fc-cache -fv

    # ── packages ──────────────────────────────────────────────────────────────

    if [[ "${1:-}" == "--packages" ]]; then
        log "installing apt packages from packages.txt"
        xargs sudo apt-get install -y < "$DOTFILES/packages.txt"
    fi

    # ── post-install notes ────────────────────────────────────────────────────

    echo ""
    echo "✓ dotfiles installed"
    echo ""
    echo "Manual steps remaining:"
    echo "  • kos skills:  npx skills install kos"
    echo "  • Particle:    npm install -g particle-cli && particle login"
    echo "  • Antigravity: has its own CLI installer — see https://antigravity.dev"
    echo "  • Packages:    run with --packages flag to install apt packages"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
