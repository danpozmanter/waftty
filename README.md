# waftty

[![Test](https://github.com/danpozmanter/waftty/actions/workflows/test.yml/badge.svg)](https://github.com/danpozmanter/waftty/actions/workflows/test.yml)
[![Build](https://github.com/danpozmanter/waftty/actions/workflows/release.yml/badge.svg)](https://github.com/danpozmanter/waftty/actions/workflows/release.yml)

**[Documentation](https://danpozmanter.github.io/waftty/)** | **[Releases](https://github.com/danpozmanter/waftty/releases)**

![waftty with two tabs, the first split into two panes: git log on the left, neofetch and ls on the right](docs_src/assets/screenshot.png)

A tabbed terminal emulator written in [Gossamer](https://github.com/gossamer-lang/gossamer)
on gui-gos - built on Rust and SDL 3. A window is its menu bar and its terminal, with a slim tab strip
between them once it holds more than one tab. The window title names the tab
it shows. Each tab runs your shell and reads and writes its own character
encoding, and splits into panes side by side or one above the other.
`waftty --quick` runs it as a quick terminal, hung from any edge of the
screen, that a global shortcut (F12 by default) shows and hides.

```sh
gos fetch
gos run .                  # your shell
gos run . -e htop          # a program in the first tab
gos run . --fixture        # self-test: runs every menu command and checks the window
gos build --release
./install.sh               # build and install: ~/.local, or /Applications on macOS
./install.sh --system      # Linux: build and install to /usr/local
```

Building requires Gossamer 0.76.0 or newer and Rust 1.95.0 through rustup.

Release packages are built for Linux x86_64 (glibc 2.39 or newer, as on
Ubuntu 24.04) as a .deb, an .rpm, an AppImage and a tarball; for Windows
x86_64 as a setup program and zips; and for macOS 15 or newer, with one
package for Intel Macs and one for Apple Silicon. On macOS, unzip the
package and double-click `install.command` (the first time, allow it under
System Settings > Privacy & Security > Open Anyway), or run
`bash install.command` from the unzipped folder in Terminal. See
[Installation](https://danpozmanter.github.io/waftty/installation/) for details.

A `user` folder beside waftty puts it in portable mode: settings stay in that
folder instead of your profile. The Windows `-portable.zip` comes with one.

The [guide](https://danpozmanter.github.io/waftty/guide/) lists every command
and setting: a tabbed Settings window for the shell, font, color scheme
(edited or imported from iTerm2, Windows Terminal, xfce4-terminal and base16),
cursor, scrollbar, bell, paste safety, the quick terminal and shortcuts.
**Help > Check for Updates** says whether a newer release is out.
