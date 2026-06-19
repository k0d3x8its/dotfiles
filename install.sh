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

    # ── git-crypt unlock ──────────────────────────────────────────────────────
    # KNOWLEDGE.md (symlinked just below) is git-crypt ciphertext in the working
    # tree until unlocked. This MUST run before the symlink is relied on, else
    # Claude reads garbage through it with no error. Key is pulled from Proton
    # Pass (stored base64 because git-crypt keys are binary) and never persisted
    # bare in $HOME; a plain ~/git-crypt-key is the offline fallback.
    if [ -f "$DOTFILES/.git/git-crypt/keys/default" ]; then
        : # already unlocked — no-op
    elif command -v git-crypt >/dev/null 2>&1; then
        keyfile="$(mktemp)"; chmod 600 "$keyfile"
        if command -v pass-cli >/dev/null 2>&1 \
           && echo '{{ pass://Private/git-crypt/key }}' \
                | pass-cli inject 2>/dev/null | base64 -d > "$keyfile" 2>/dev/null \
                && [ -s "$keyfile" ]; then
            log "unlocking git-crypt (Proton Pass)"
            ( cd "$DOTFILES" && git-crypt unlock "$keyfile" )
        elif [ -f "$HOME/git-crypt-key" ]; then
            log "unlocking git-crypt (keyfile fallback)"
            ( cd "$DOTFILES" && git-crypt unlock "$HOME/git-crypt-key" )
        else
            log "WARN: git-crypt key unavailable — run \`pass-cli login\` then re-run ./install.sh (or place ~/git-crypt-key); until then KNOWLEDGE.md stays ciphertext"
        fi
        command -v shred >/dev/null 2>&1 && shred -u "$keyfile" || rm -f "$keyfile"
    else
        log "WARN: git-crypt not installed — encrypted files unreadable (./install.sh --packages)"
    fi

    # individual files
    safeguard "$HOME/.claude/CLAUDE.md"
    ln -sf "$DOTFILES/claude/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"

    safeguard "$HOME/.claude/KNOWLEDGE.md"
    ln -sf "$DOTFILES/claude/.claude/KNOWLEDGE.md" "$HOME/.claude/KNOWLEDGE.md"

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

    # references dir (on-demand vocabulary files read by skills at runtime)
    safeguard "$HOME/.claude/references"
    ln -sf "$DOTFILES/claude/.claude/references" "$HOME/.claude/references"

    # manual skills (plugin-installed skills like kos* are reinstalled separately)
    # glob every tracked skill dir so adding/removing a skill never desyncs this list
    for skill_dir in "$DOTFILES"/claude/.claude/skills/*/; do
        skill_dir="${skill_dir%/}"
        skill="$(basename "$skill_dir")"
        safeguard "$HOME/.claude/skills/$skill"
        ln -sf "$skill_dir" "$HOME/.claude/skills/$skill"
    done

    # ── ghostty sidebar ───────────────────────────────────────────────────────
    # Requires: xdotool  (sudo nala install xdotool)
    # Runs Ghostty under XWayland at boot — right-edge sidebar, btop top pane.

    log "stowing ghostty sidebar"
    mkdir -p "$HOME/.config/ghostty" "$HOME/.config/autostart" "$HOME/.local/bin"
    safeguard "$HOME/.config/ghostty/config"
    safeguard "$HOME/.config/ghostty/sidebar.conf"
    safeguard "$HOME/.config/autostart/ghostty-sidebar.desktop"
    safeguard "$HOME/.local/bin/ghostty-sidebar"
    stow --no-folding --dir="$DOTFILES" --target="$HOME" ghostty
    chmod +x "$HOME/.local/bin/ghostty-sidebar"

    # ── trueline ──────────────────────────────────────────────────────────────

    log "installing trueline"
    mkdir -p "$HOME/dev"
    safeguard "$HOME/dev/trueline.sh"
    ln -sf "$DOTFILES/scripts/trueline.sh" "$HOME/dev/trueline.sh"

    # ── scripts ───────────────────────────────────────────────────────────────

    log "installing scripts"
    mkdir -p "$HOME/.local/bin"

    safeguard "$HOME/.local/bin/update-triage"
    ln -sf "$DOTFILES/scripts/update-triage" "$HOME/.local/bin/update-triage"
    chmod +x "$DOTFILES/scripts/update-triage"

    safeguard "$HOME/.local/bin/update-cache"
    ln -sf "$DOTFILES/scripts/update-cache" "$HOME/.local/bin/update-cache"
    chmod +x "$DOTFILES/scripts/update-cache"

    safeguard "$HOME/.local/bin/rotate-log"
    ln -sf "$DOTFILES/scripts/rotate-log" "$HOME/.local/bin/rotate-log"
    chmod +x "$DOTFILES/scripts/rotate-log"

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
    echo "  • Packages:    run with --packages flag to install apt packages
  • Ghostty sidebar: sudo nala install xdotool  (required for window positioning)"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
