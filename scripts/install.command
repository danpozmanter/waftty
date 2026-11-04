#!/usr/bin/env bash
# Installs waftty.app to /Applications, clears its download quarantine,
# re-signs it ad hoc for its new place, and links a `waftty` command.
#
# Double-click this file to run it in Terminal, or run: bash install.command
# Opened from Finder, the downloaded script is itself checked by Gatekeeper,
# which asks once (System Settings > Privacy & Security > Open Anyway); run
# by bash, it is not checked.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "error: $*" >&2; exit 1; }

install_app() {
    local src="$1"
    local name
    name="$(basename "$src")"
    local dest="/Applications/$name"

    [ -d "$src" ] || die "$name not found at $src"

    echo "Installing $name..."
    rm -rf "$dest"
    cp -R "$src" "$dest"
    xattr -dr com.apple.quarantine "$dest" 2>/dev/null || true
    codesign --force --deep --sign - --timestamp=none "$dest" >/dev/null 2>&1 || true
    echo "  Installed to $dest"
}

install_app "$SCRIPT_DIR/waftty.app"

install_cli_symlink() {
    local binary="$1"
    local linkname="$2"
    local target_dir="$3"

    [ -f "$binary" ] || return 0
    [ -d "$target_dir" ] || return 0

    sudo ln -sf "$binary" "$target_dir/$linkname" 2>/dev/null || return 0
    echo "  CLI: $target_dir/$linkname"
}

echo ""
echo "Installing the CLI symlink (may prompt for sudo)..."
[ -d /usr/local/bin ] || sudo mkdir -p /usr/local/bin 2>/dev/null || true
install_cli_symlink "/Applications/waftty.app/Contents/MacOS/waftty" waftty /usr/local/bin

echo ""
echo "Done. Launch from /Applications or run:"
echo "  waftty"

path_has() {
    case ":${PATH}:" in *":$1:"*) return 0 ;; *) return 1 ;; esac
}
if ! path_has /usr/local/bin; then
    case "${SHELL##*/}" in
        zsh)  shell_rc="$HOME/.zshrc" ;;
        bash) shell_rc="$HOME/.bash_profile" ;;
        fish) shell_rc="$HOME/.config/fish/config.fish" ;;
        *)    shell_rc="your shell profile" ;;
    esac
    echo ""
    echo "Note: /usr/local/bin is not in your PATH, so 'waftty' won't resolve"
    echo "in the shell. Add it to $shell_rc. For zsh or bash:"
    echo ""
    echo "    export PATH=\"/usr/local/bin:\$PATH\""
    echo ""
fi
