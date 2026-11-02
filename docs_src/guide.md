---
title: User Guide - waftty
description: How to use waftty - shortcuts, tabs, find, shell integration, links, character encodings, settings, color schemes and custom shortcuts.
---

# User Guide

A waftty window is its menu bar and its terminal, with a slim tab strip
between them once it holds more than one tab. The window title names the tab
it shows. Each tab runs your shell and reads and writes its own character
encoding.

## Shortcuts

Programs in the terminal need Ctrl with a letter, so on Linux and Windows
waftty's shortcuts use Ctrl+Shift; on macOS they use Command. ++f10++ opens
the menu bar. **Edit > Settings > Shortcuts** changes any of them.

| Command | Linux and Windows | macOS |
|---|---|---|
| New Tab / New Window | ++ctrl+shift+t++ / ++ctrl+shift+n++ | ++cmd+t++ / ++cmd+n++ |
| Close Tab / Close Window | ++ctrl+shift+w++ / (the window's close button) | ++cmd+w++ / ++cmd+shift+w++ |
| Quit | ++ctrl+shift+q++ | ++cmd+q++ |
| Copy / Paste / Select All | ++ctrl+shift+c++ / ++ctrl+shift+v++ / ++ctrl+shift+a++ | ++cmd+c++ / ++cmd+v++ / ++cmd+a++ |
| Settings | ++ctrl+comma++ | ++cmd+comma++ |
| Zoom In / Zoom Out / Reset Zoom | ++ctrl+equal++ / ++ctrl+minus++ / ++ctrl+0++ | ++cmd+equal++ / ++cmd+minus++ / ++cmd+0++ |
| Fullscreen | ++f11++ | ++ctrl+cmd+f++ |
| Show Menu Bar | ++ctrl+shift+m++ | |
| Find / Find Next / Find Previous | ++ctrl+shift+f++ / ++ctrl+shift+g++ / ++ctrl+shift+h++ | ++cmd+f++ / ++cmd+g++ / ++cmd+shift+g++ |
| Previous Prompt / Next Prompt | ++ctrl+shift+up++ / ++ctrl+shift+down++ | ++cmd+up++ / ++cmd+down++ |
| Select Last Command Output | ++ctrl+shift+o++ | ++cmd+shift+o++ |
| Scroll Up / Down a Page | ++shift+page-up++ / ++shift+page-down++ | the same |
| Scroll to Top / Bottom | ++ctrl+shift+home++ / ++ctrl+shift+end++ | ++cmd+home++ / ++cmd+end++ |
| Clear Scrollback | ++ctrl+shift+k++ | ++cmd+k++ |
| Reset and Clear | ++ctrl+shift+r++ | ++cmd+option+k++ |
| Next Tab / Previous Tab | ++ctrl+tab++ / ++ctrl+shift+tab++ (also ++ctrl+page-down++ / ++ctrl+page-up++) | the same, or ++cmd+shift+bracket-right++ / ++cmd+shift+bracket-left++ |
| Tab 1 to 8 / Last Tab | ++alt+1++ to ++alt+8++ / ++alt+9++ | ++cmd+1++ to ++cmd+8++ / ++cmd+9++ |
| Switch to Last Tab | ++ctrl+shift+l++ | ++cmd+shift+l++ |
| Move Tab Left / Right | ++ctrl+shift+page-up++ / ++ctrl+shift+page-down++ | ++cmd+shift+page-up++ / ++cmd+shift+page-down++ |

A right click on the terminal offers the link entries, Copy, Paste, Select
All, New Tab, Find, Clear Scrollback, Send Signal, Zoom, Show Menu Bar and
Settings.

## Tabs

- A tab is named for its program until the program sets a title; its tooltip
  adds the folder it works in.
- Drag a tab to reorder it. The Tabs menu and a right click on a tab pin it,
  close the others, or close the tabs to its right. Pinned tabs sit first and
  stay open.
- A tab whose program rings the bell or posts a notification while hidden is
  marked until you look at it.
- Closing a tab, window or waftty while a program runs asks first and names
  the program.

## Find

**Terminal > Find** searches the whole scrollback, with options for case,
whole words and regular expressions, and shows how many matches it found.
The search field offers your earlier searches.

## Shell Integration

When your shell marks its prompts with OSC 133 (the semantic prompt sequence
most shell integration scripts emit), waftty knows where each command starts
and ends:

- **Previous Prompt / Next Prompt** scroll from one prompt to the next.
- **Select Last Command Output** selects everything the last command printed.

## Links, Paths and Files

waftty recognizes links that programs mark with OSC 8, plus URLs, email
addresses and file paths in the text, including ones a long line wraps
across.

- Ctrl+click (Command+click on macOS) a link to open it. Right click it to
  open it, copy it, or copy an email address.
- Ctrl+click a file path (such as `src/main.gos:42:7` in a compiler error) to
  open it in the editor Settings name, at its line and column, or with the
  desktop's default application.
- Drop files on the terminal to paste their paths, quoted for the shell.

## Character Encodings

**Terminal > Set Encoding** switches the current tab between UTF-8 and other
encodings, grouped by region. The default for new tabs is in Settings.

## Signals

**Terminal > Send Signal** sends a signal to the job in the foreground of the
tab: Interrupt, Terminate, Kill and the other common ones by name, the rest
under **More**. Not available on Windows.

## Settings

**Edit > Settings** opens a window with four pages. Each value has a button
that puts it back to its default; only values that differ from the defaults
are saved, so the defaults follow your desktop.

- **General**: the shell, as a command line (empty runs your login shell,
  as a login shell on macOS; PowerShell on Windows), the starting folder
  (empty is your home folder), where new tabs open, the character encoding,
  the size new windows open at, whether windows and tabs come back at the
  next start, and whether closing a running program asks first.
- **Appearance**: the font, its size and weight (empty uses the desktop's
  monospace font), ligatures, the color scheme, the cursor shape and
  blinking, bold text in bright colors, readability adjustment, padding,
  background opacity, the scrollbar, the menu bar and the tab bar.
- **Behavior**: scrollback lines, scrolling on output and typing, the
  characters a double click selects, copying on select, asking before
  pasting several lines, the bell (mark the tab, flash or sound),
  notifications, programs writing the clipboard (OSC 52; they can never read
  it), the editor for file paths (such as `nvim +{line} {path}`), and on
  macOS whether Option is Meta.
- **Shortcuts**: every command's chords.

Settings are saved in the configuration directory:

| Platform | Configuration directory |
|---|---|
| Linux | `$XDG_CONFIG_HOME/dev.gossamer.waftty` (default `~/.config/dev.gossamer.waftty`) |
| macOS | `~/Library/Application Support/dev.gossamer.waftty` |
| Windows | `%APPDATA%\dev.gossamer.waftty` |

In [portable mode](installation.md#portable-mode) the configuration directory
is `user/dev.gossamer.waftty` beside waftty instead.

Dialog text and controls follow the desktop's interface font size.

## Color Schemes

The built-in schemes are **System theme** (light or dark with the
desktop), **Light**, **Dark**, **Solarized Light**, **Solarized Dark**,
**High Contrast Light** and **High Contrast Dark**.

- **Edit Colors** opens the current scheme's colors; OK saves them as a
  scheme by the name you give it.
- **Import Scheme** reads iTerm2 (`.itermcolors`), Windows Terminal
  (`.json`), xfce4-terminal (`.theme`) and base16 (`.yaml`) schemes.
- **Open Schemes Folder** shows the folder scheme files live in.

A scheme file is `scheme-NAME.toml` in the configuration directory:

```toml
name = "Night Sky"
appearance = "dark"          # "light" or "dark": the window around the terminal
foreground = "#d8e7f2"
background = "#0c1824"
cursor = "#74c6f4"
selection = "#1f4d70"
selection_text = "#ffffff"
ansi = [
  "#0c1824", "#e06c75", "#98c379", "#e5c07b", "#4bb7ee", "#c678dd", "#56b6c2", "#d8e7f2",
  "#3b5368", "#ff7b86", "#b5e890", "#ffd88a", "#86cff5", "#de9bf0", "#7fd8e2", "#ffffff",
]
```

## Custom Shortcuts

The Shortcuts page of Settings writes `shortcuts.toml` in the configuration
directory, which maps a command id to a chord or a list of chords; an empty
list removes a command's shortcut. waftty refuses chords the terminal needs,
such as a bare letter, Ctrl with a letter, or Alt with a letter, and says
which entries it could not use.

```toml
"tabs.next" = ["Ctrl+Tab", "Ctrl+Shift+Right"]
"view.fullscreen" = []
```

The ids of the Send Signal, Set Encoding and tab-list entries
(`terminal.signal:15`, `terminal.encoding:KOI8-R`, `tabs.number:3`) can only
be bound in the file.
