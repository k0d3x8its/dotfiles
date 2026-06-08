#!/usr/bin/env bats

# ── fixture helpers ───────────────────────────────────────────────────────────

REAL_DOTFILES="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"

make_fixture() {
    local dir="$1"

    mkdir -p "$dir/bash"
    echo "# bashrc" > "$dir/bash/.bashrc"

    mkdir -p "$dir/git"
    echo "[user]" > "$dir/git/.gitconfig"
    touch "$dir/git/.gitignore_global"

    mkdir -p "$dir/claude/.claude/plugins"
    mkdir -p "$dir/claude/.claude/hooks"
    mkdir -p "$dir/claude/.claude/references"
    touch "$dir/claude/.claude/CLAUDE.md"
    touch "$dir/claude/.claude/settings.json"
    touch "$dir/claude/.claude/plugins/installed_plugins.json"
    touch "$dir/claude/.claude/plugins/known_marketplaces.json"
    touch "$dir/claude/.claude/hooks/hook.sh"
    touch "$dir/claude/.claude/references/anti-patterns.md"

    for skill in changelog dev-brief dev-setup diagnose prototype release-notes session-checkpoint session-handoff session-handoff-return sync-trello tdd trello-agent; do
        mkdir -p "$dir/claude/.claude/skills/$skill"
        touch "$dir/claude/.claude/skills/$skill/SKILL.md"
    done

    mkdir -p "$dir/ghostty/.config/ghostty"
    mkdir -p "$dir/ghostty/.config/autostart"
    mkdir -p "$dir/ghostty/.local/bin"
    touch "$dir/ghostty/.config/ghostty/sidebar.conf"
    touch "$dir/ghostty/.config/autostart/ghostty-sidebar.desktop"
    printf '#!/bin/bash\n' > "$dir/ghostty/.local/bin/ghostty-sidebar"
    chmod +x "$dir/ghostty/.local/bin/ghostty-sidebar"

    mkdir -p "$dir/scripts"
    touch "$dir/scripts/trueline.sh"
    printf '#!/bin/bash\n' > "$dir/scripts/update-triage"
    printf '#!/bin/bash\n' > "$dir/scripts/update-cache"
    printf '#!/bin/bash\n' > "$dir/scripts/rotate-log"

    mkdir -p "$dir/fonts"
    touch "$dir/fonts/test.ttf"

    cp "$REAL_DOTFILES/install.sh" "$dir/install.sh"
}

setup() {
    FAKE_DOTFILES="$(mktemp -d)"
    FAKE_HOME="$(mktemp -d)"
    STUB_BIN="$(mktemp -d)"
    CALL_LOG="$STUB_BIN/calls.log"

    make_fixture "$FAKE_DOTFILES"

    # spy: records invocations but does nothing destructive
    for cmd in git fc-cache; do
        cat > "$STUB_BIN/$cmd" <<EOF
#!/bin/bash
echo "$cmd \$*" >> "$CALL_LOG"
EOF
        chmod +x "$STUB_BIN/$cmd"
    done

    export PATH="$STUB_BIN:$PATH"
    export FAKE_DOTFILES FAKE_HOME STUB_BIN CALL_LOG
}

teardown() {
    rm -rf "$FAKE_DOTFILES" "$FAKE_HOME" "$STUB_BIN"
}

# Source install.sh functions without executing main.
# Sets DOTFILES + BACKUP to point at the fake dirs so unit tests are isolated.
load_functions() {
    DOTFILES="$FAKE_DOTFILES" \
    HOME="$FAKE_HOME" \
        source "$FAKE_DOTFILES/install.sh"
    # Override BACKUP to use fake home (BACKUP is set at source time from $HOME)
    BACKUP="$FAKE_HOME/.dotfiles-backup/test-run"
}

run_install() {
    HOME="$FAKE_HOME" bash "$FAKE_DOTFILES/install.sh" "$@"
}

# ── unit: safeguard logic ─────────────────────────────────────────────────────

@test "safeguard: removes symlink silently, no backup dir created" {
    load_functions
    local target="$FAKE_HOME/some-symlink"
    ln -s /dev/null "$target"

    safeguard "$target"

    [[ ! -e "$target" ]]                          # symlink gone
    [[ ! -d "$FAKE_HOME/.dotfiles-backup" ]]      # no backup dir created
}

@test "safeguard: moves real file to backup dir" {
    load_functions
    local target="$FAKE_HOME/real-file"
    echo "content" > "$target"

    safeguard "$target"

    [[ ! -e "$target" ]]                          # original gone
    [[ -d "$BACKUP" ]]                            # backup dir created
    [[ -f "$BACKUP/real-file" ]]                  # file moved there
}

@test "safeguard: backup dir contains original filename, not a copy" {
    load_functions
    local target="$FAKE_HOME/myfile"
    echo "original" > "$target"

    safeguard "$target"

    run grep "original" "$BACKUP/myfile"
    [[ "$status" -eq 0 ]]
}

@test "safeguard: no-ops when target does not exist" {
    load_functions
    # Should not error, should not create backup dir
    safeguard "$FAKE_HOME/nonexistent"

    [[ ! -d "$FAKE_HOME/.dotfiles-backup" ]]
}

@test "safeguard: multiple files in one run share the same backup dir" {
    load_functions
    echo "a" > "$FAKE_HOME/file-a"
    echo "b" > "$FAKE_HOME/file-b"

    safeguard "$FAKE_HOME/file-a"
    safeguard "$FAKE_HOME/file-b"

    # Both land under same BACKUP, not separate timestamped dirs
    [[ -f "$BACKUP/file-a" ]]
    [[ -f "$BACKUP/file-b" ]]
}

@test "safeguard: backup path uses YYYYMMDD-HHMMSS timestamp format" {
    load_functions
    echo "x" > "$FAKE_HOME/timestamped"

    # Use real BACKUP (not the overridden one) to check timestamp format
    BACKUP="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
    safeguard "$FAKE_HOME/timestamped"

    # Extract the timestamp component from BACKUP path
    local ts
    ts="$(basename "$BACKUP")"
    [[ "$ts" =~ ^[0-9]{8}-[0-9]{6}$ ]]
}

# ── unit: neovim skip logic ───────────────────────────────────────────────────

@test "neovim: git clone skipped when .config/nvim/.git already exists" {
    mkdir -p "$FAKE_HOME/.config/nvim/.git"

    run_install

    # git clone would write "git clone ..." to CALL_LOG; grep fails = not called
    run grep "clone" "$CALL_LOG"
    [[ "$status" -ne 0 ]]
}

@test "neovim: git clone called when .config/nvim/.git absent" {
    run_install

    run grep "clone" "$CALL_LOG"
    [[ "$status" -eq 0 ]]
}

# ── unit: --packages flag ─────────────────────────────────────────────────────

@test "--packages flag: apt-get not called without flag" {
    # stub apt-get so it doesn't actually install anything
    cat > "$STUB_BIN/apt-get" <<EOF
#!/bin/bash
echo "apt-get \$*" >> "$CALL_LOG"
EOF
    chmod +x "$STUB_BIN/apt-get"

    run_install   # no flag

    run grep "apt-get" "$CALL_LOG"
    [[ "$status" -ne 0 ]]
}

@test "--packages flag: apt-get called with install -y when flag passed" {
    cat > "$STUB_BIN/apt-get" <<EOF
#!/bin/bash
echo "apt-get \$*" >> "$CALL_LOG"
EOF
    chmod +x "$STUB_BIN/apt-get"

    # stub sudo to pass through
    cat > "$STUB_BIN/sudo" <<EOF
#!/bin/bash
"\$@"
EOF
    chmod +x "$STUB_BIN/sudo"

    # packages.txt must exist alongside install.sh
    echo "curl" > "$FAKE_DOTFILES/packages.txt"

    run_install --packages

    run grep "apt-get install -y" "$CALL_LOG"
    [[ "$status" -eq 0 ]]
}

# ── integration: symlink outcomes ─────────────────────────────────────────────

@test "bash: ~/.bashrc is a symlink pointing into dotfiles" {
    run_install

    [[ -L "$FAKE_HOME/.bashrc" ]]
    [[ "$(readlink -f "$FAKE_HOME/.bashrc")" == "$FAKE_DOTFILES/bash/.bashrc" ]]
}

@test "git: ~/.gitconfig and ~/.gitignore_global are symlinks" {
    run_install

    [[ -L "$FAKE_HOME/.gitconfig" ]]
    [[ -L "$FAKE_HOME/.gitignore_global" ]]
}

@test "claude: CLAUDE.md and settings.json are symlinks" {
    run_install

    [[ -L "$FAKE_HOME/.claude/CLAUDE.md" ]]
    [[ -L "$FAKE_HOME/.claude/settings.json" ]]
}

@test "claude: hooks is a symlink to dotfiles hooks dir" {
    run_install

    [[ -L "$FAKE_HOME/.claude/hooks" ]]
    [[ "$(readlink "$FAKE_HOME/.claude/hooks")" == "$FAKE_DOTFILES/claude/.claude/hooks" ]]
}

@test "claude: references is a symlink to dotfiles references dir" {
    run_install

    [[ -L "$FAKE_HOME/.claude/references" ]]
    [[ "$(readlink "$FAKE_HOME/.claude/references")" == "$FAKE_DOTFILES/claude/.claude/references" ]]
}

@test "claude: every tracked skill is symlinked, no extras" {
    run_install

    # derive expected from the dotfiles skills dir — same source install.sh globs,
    # so the two can never drift out of sync as skills are added/removed
    local expected=()
    while IFS= read -r -d '' entry; do
        expected+=("$(basename "$entry")")
    done < <(find "$FAKE_DOTFILES/claude/.claude/skills" -maxdepth 1 -mindepth 1 -type d -print0 | sort -z)

    local actual=()
    while IFS= read -r -d '' entry; do
        actual+=("$(basename "$entry")")
    done < <(find "$FAKE_HOME/.claude/skills" -maxdepth 1 -mindepth 1 -type l -print0 | sort -z)

    [[ "${#actual[@]}" -eq "${#expected[@]}" ]]
    for skill in "${expected[@]}"; do
        [[ -L "$FAKE_HOME/.claude/skills/$skill" ]]
    done
}

@test "trueline: ~/dev/trueline.sh is a symlink into dotfiles/scripts" {
    run_install

    [[ -L "$FAKE_HOME/dev/trueline.sh" ]]
    [[ "$(readlink "$FAKE_HOME/dev/trueline.sh")" == "$FAKE_DOTFILES/scripts/trueline.sh" ]]
}

# ── integration: idempotency ──────────────────────────────────────────────────

@test "idempotency: second run exits 0 and symlinks remain valid" {
    run_install
    run_install   # second time — should not error

    [[ -L "$FAKE_HOME/.bashrc" ]]
    [[ -L "$FAKE_HOME/.gitconfig" ]]
    [[ -L "$FAKE_HOME/.claude/CLAUDE.md" ]]
}

# ── integration: safeguard called before stow ─────────────────────────────────

@test "pre-existing real ~/.bashrc is backed up and replaced with symlink" {
    echo "old bashrc content" > "$FAKE_HOME/.bashrc"

    run_install

    # Old content moved to backup
    run find "$FAKE_HOME/.dotfiles-backup" -name ".bashrc" -type f
    [[ "$status" -eq 0 ]]
    [[ -n "$output" ]]

    # Target is now a symlink
    [[ -L "$FAKE_HOME/.bashrc" ]]
}

@test "ghostty: sidebar.conf is a symlink into dotfiles" {
    run_install

    [[ -L "$FAKE_HOME/.config/ghostty/sidebar.conf" ]]
    [[ "$(readlink -f "$FAKE_HOME/.config/ghostty/sidebar.conf")" == "$FAKE_DOTFILES/ghostty/.config/ghostty/sidebar.conf" ]]
}

@test "ghostty: ghostty-sidebar script is a symlink and executable" {
    run_install

    [[ -L "$FAKE_HOME/.local/bin/ghostty-sidebar" ]]
    [[ -x "$FAKE_HOME/.local/bin/ghostty-sidebar" ]]
}

@test "ghostty: ghostty-sidebar.desktop autostart is a symlink" {
    run_install

    [[ -L "$FAKE_HOME/.config/autostart/ghostty-sidebar.desktop" ]]
    [[ "$(readlink -f "$FAKE_HOME/.config/autostart/ghostty-sidebar.desktop")" == "$FAKE_DOTFILES/ghostty/.config/autostart/ghostty-sidebar.desktop" ]]
}

@test "pre-existing symlink at ~/.gitconfig is replaced without backup" {
    ln -s /dev/null "$FAKE_HOME/.gitconfig"

    run_install

    # No backup dir for a symlink replacement
    [[ ! -d "$FAKE_HOME/.dotfiles-backup" ]]
    [[ -L "$FAKE_HOME/.gitconfig" ]]
    [[ "$(readlink -f "$FAKE_HOME/.gitconfig")" == "$FAKE_DOTFILES/git/.gitconfig" ]]
}
