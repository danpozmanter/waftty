#!/usr/bin/env bash
# Build and install waftty for the host platform.
# Delegates building and packaging to scripts/package.sh.
#
# Usage: ./install.sh [--system]
#   --system  Install system-wide to /usr/local (Linux and FreeBSD; requires sudo)
#   Default:  Install to ~/.local (Linux, FreeBSD) or /Applications (macOS)
#
# Needs the Gossamer toolchain (gos), rustup with the Rust toolchain
# rust-toolchain.toml names, and the libraries beside this checkout at
# ../goose-libs, where project.toml reaches them.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

system=0
for arg in "$@"; do
    case "$arg" in
        --system) system=1 ;;
        -h | --help)
            sed -n '2,11p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "error: unknown argument: $arg" >&2; exit 1 ;;
    esac
done

die() { echo "error: $*" >&2; exit 1; }

command -v gos >/dev/null 2>&1 || die "gos is not on the PATH; install the Gossamer toolchain"
os="$(uname)"
case "$os" in
    Linux | FreeBSD | Darwin) ;;
    *) die "unsupported OS: $os (on Windows, use the release zip)" ;;
esac
[ "$system" -eq 0 ] || [ "$os" != Darwin ] || die "--system is for Linux and FreeBSD only"

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

echo "Building waftty..."
package="$(bash "$here/scripts/package.sh" "$stage/dist")"
[ -f "$package" ] || die "the package was not built"

case "$os" in
    Linux | FreeBSD)
        tar -xzf "$package" -C "$stage"
        installer="$stage/$(basename "$package" .tar.gz)/install.sh"
        if [ "$system" -eq 1 ]; then
            sudo env PREFIX=/usr/local sh "$installer"
        else
            PREFIX="$HOME/.local" sh "$installer"
            case ":${PATH}:" in
                *":$HOME/.local/bin:"*) ;;
                *) echo "Note: $HOME/.local/bin is not in PATH; add it to your shell profile." ;;
            esac
        fi
        ;;
    Darwin)
        mkdir -p "$stage/app"
        ditto -x -k "$package" "$stage/app"
        bash "$stage/app/install.command"
        ;;
esac
