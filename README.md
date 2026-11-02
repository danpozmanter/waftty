# waftty

[![Test](https://github.com/danpozmanter/waftty/actions/workflows/test.yml/badge.svg)](https://github.com/danpozmanter/waftty/actions/workflows/test.yml)
[![Build](https://github.com/danpozmanter/waftty/actions/workflows/release.yml/badge.svg)](https://github.com/danpozmanter/waftty/actions/workflows/release.yml)

**[Documentation](https://danpozmanter.github.io/waftty/)** | **[Releases](https://github.com/danpozmanter/waftty/releases)**

A tabbed terminal emulator written in [Gossamer](https://github.com/gossamer-lang/gossamer)
on gui-gos - built on Rust and SDL 3. A window is its menu bar and its terminal, with a slim tab strip
between them once it holds more than one tab. The window title names the tab
it shows. Each tab runs your shell and reads and writes its own character
set.

```sh
gos fetch
gos run .                  # your shell
gos run . -e htop          # a program in the first tab
gos run . --fixture        # the scripted journey the checks run
gos build --release
./install.sh               # build and install: ~/.local, or /Applications on macOS
./install.sh --system      # Linux: build and install to /usr/local
```

Building requires Gossamer 0.75.13 or newer and a Rust toolchain.

Release packages are built for Linux x86_64 (glibc 2.39 or newer, as on
Ubuntu 24.04) as a .deb, an .rpm, an AppImage and a tarball; for Windows
x86_64 as a setup program and zips; and for macOS 15 or newer, with one
package for Intel Macs and one for Apple Silicon. On macOS, unzip the
package and run `bash install-mac.sh` in Terminal.

A `user` folder beside waftty puts it in portable mode: settings stay in that
folder instead of your profile. The Windows `-portable.zip` comes with one.

## Shortcuts

The terminal keeps plain Ctrl chords for its program, so waftty's shortcuts
use Ctrl+Shift (Command+Shift on macOS). F10 opens the menu bar.

| Menu | Command | Shortcut |
|---|---|---|
| File | New Tab | Ctrl+Shift+T |
| | New Window | Ctrl+Shift+N |
| | Close Tab | Ctrl+Shift+W |
| | Close Window | Ctrl+Shift+Q |
| Edit | Copy / Paste / Select All | Ctrl+Shift+C / V / A |
| View | Fullscreen | F11 |
| | Zoom In / Zoom Out / Normal Size | Ctrl+Shift+= / - / 0 |
| Terminal | Find... / Find Next / Find Previous | Ctrl+Shift+F / G / H |
| | Previous Prompt / Next Prompt | Ctrl+Shift+Up / Down |
| | Select Last Output, Reset, Send Signal (1-30), Set Encoding, Settings... | |
| Tabs | Previous / Next Tab | Ctrl+Shift+Tab / Ctrl+Tab |
| | Last Active Tab | Ctrl+Shift+L |
| | Move Tab Left / Right | Ctrl+Shift+PageUp / PageDown |
| | each open tab, by number and title | |
| Help | About waftty | |

Find asks for the text, whether it is a regular expression and whether case
matters, then searches the whole scrollback, selecting the match in the
terminal. Send Signal reaches the job in the foreground of the
tab's terminal (not available on Windows). Settings hold the shell, working
directory, default character set, scrollback, font and theme, saved in the
configuration directory. Menu text follows the desktop's menu font size.
