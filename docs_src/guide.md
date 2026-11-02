---
title: User Guide - waftty
description: How to use waftty - shortcuts, tabs, find, shell integration, links, character sets, settings, color schemes and custom shortcuts.
---

# User Guide

A waftty window is its menu bar and its terminal, with a slim tab strip
between them once it holds more than one tab. The window title names the tab
it shows. Each tab runs your shell and reads and writes its own character set.

## Shortcuts

Programs in the terminal need the plain Ctrl chords, so waftty's own
shortcuts use Ctrl+Shift (Command+Shift on macOS). ++f10++ opens the menu bar.

| Menu | Command | Shortcut |
|---|---|---|
| File | New Tab | ++ctrl+shift+t++ |
| | New Window | ++ctrl+shift+n++ |
| | Close Tab | ++ctrl+shift+w++ |
| | Close Window | ++ctrl+shift+q++ |
| Edit | Copy / Paste / Select All | ++ctrl+shift+c++ / ++v++ / ++a++ |
| | Open Link / Copy Link / Copy Email Address | (over a link) |
| View | Fullscreen | ++f11++ |
| | Zoom In / Zoom Out / Normal Size | ++ctrl+shift+equal++ / ++minus++ / ++0++ |
| Terminal | Find / Find Next / Find Previous | ++ctrl+shift+f++ / ++g++ / ++h++ |
| | Previous Prompt / Next Prompt | ++ctrl+shift+up++ / ++down++ |
| | Select Last Output, Reset, Send Signal, Set Encoding, Settings... | |
| Tabs | Previous Tab / Next Tab | ++ctrl+shift+tab++ / ++ctrl+tab++ |
| | Last Active Tab | ++ctrl+shift+l++ |
| | Move Tab Left / Right | ++ctrl+shift+page-up++ / ++page-down++ |
| | each open tab, by number and title | |
| Help | About waftty | |

A right click on the terminal offers the link entries, Copy, Paste, Send
Signal and Zoom.

## Tabs

- Drag a tab to reorder it, or move it with ++ctrl+shift+page-up++ and
  ++ctrl+shift+page-down++.
- Right click a tab to pin it, close it, close the others, or close every tab
  to its right. Pinned tabs sit first, show no close button, and survive
  "close others".
- When a program in a background tab rings the bell or posts a notification,
  the tab is marked until you look at it, and an unfocused window asks for
  attention.
- Closing a tab whose shell is running a job asks first.

New tabs start in the directory of the tab you open them from. Settings can
switch that to a fixed directory.

## Find

**Terminal > Find** (++ctrl+shift+f++) asks for the text, whether it is a
regular expression and whether case matters, then searches the whole
scrollback and selects the match in the terminal. ++ctrl+shift+g++ and
++ctrl+shift+h++ step to the next and previous match; ++escape++ closes the
form.

## Shell Integration

When your shell marks its prompts with OSC 133 (the semantic prompt sequence
most shell integration scripts emit), waftty knows where each command starts
and ends:

- **Previous Prompt / Next Prompt** (++ctrl+shift+up++ / ++down++) scroll from
  one prompt to the next.
- **Select Last Output** selects everything the last command printed, ready to
  copy.

## Links and Paths

waftty recognizes links that programs mark with OSC 8, plus URLs, email
addresses and file paths in the text, including ones a long line wraps
across.

- Ctrl+click (Command+click on macOS) a link to open it. Right click it to
  open it, copy it, or copy an email address.
- Ctrl+click a file path (such as `src/main.gos:42:7` in a compiler error) to
  open it. With an editor set in Settings, the path opens in a new tab in that
  editor at its line and column; otherwise it opens with the desktop's default
  application.

## Character Sets

**Terminal > Set Encoding** switches the current tab between UTF-8 and 35
other character sets, grouped by region: Western European, Central European,
Other European, Baltic, Cyrillic, Greek, Turkish, Hebrew, Arabic, Vietnamese,
Thai, Chinese, Japanese and Korean. The default for new tabs is in Settings.

## Signals

**Terminal > Send Signal** sends any of signals 1 to 30 to the job in the
foreground of the tab's terminal, which helps with a program that ignores
++ctrl+c++. Not available on Windows.

## Settings

**Terminal > Settings...** edits what new tabs and windows use. The settings
are saved in the configuration directory:

| Platform | Configuration directory |
|---|---|
| Linux | `$XDG_CONFIG_HOME/dev.gossamer.waftty` (default `~/.config/dev.gossamer.waftty`) |
| macOS | `~/Library/Application Support/dev.gossamer.waftty` |
| Windows | `%APPDATA%\dev.gossamer.waftty` |

In [portable mode](installation.md#portable-mode) the configuration directory
is `user/dev.gossamer.waftty` beside waftty instead.

| Setting | Meaning |
|---|---|
| Shell | The program new tabs run. Empty runs `$SHELL` (`cmd.exe` on Windows). |
| Working directory | Where new windows start. Empty starts where waftty did. |
| New tabs start | In the current tab's directory, or in the working directory. |
| Encoding | The character set new tabs start with. |
| Scrollback rows | Rows of history each tab keeps, up to 100,000. Default 2,000. |
| Font and size | The font family and size; the default is the bundled monospace face at 10 points. |
| Color scheme | See below. |
| Clipboard | Whether programs may write the clipboard with OSC 52. They can never read it. |
| Editor | The command a Ctrl+click on a path runs, with `{path}`, `{line}` and `{col}` filled in, such as `nvim +{line} {path}`. |

Menu text follows the desktop's menu font size.

## Color Schemes

The built-in schemes are **System theme** (light or dark with the
desktop), **Light**, **Dark**, **Solarized Light**, **Solarized Dark**,
**High Contrast Light** and **High Contrast Dark**.

To add your own, save a file named `scheme-NAME.toml` in the configuration
directory. It appears in Settings the next time you open them:

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

`appearance` is required; `ansi`, when given, lists all 16 colors in terminal
order. A scheme that does not read is reported, not silently skipped.

## Custom Shortcuts

`shortcuts.toml` in the configuration directory maps a command id to a chord
or a list of chords. An empty list removes a command's shortcut. `Primary`
means Command on macOS and Ctrl elsewhere.

```toml
"tabs.next" = ["Ctrl+Tab", "Primary+Shift+Right"]
"tabs.previous" = ["Ctrl+Shift+Tab", "Primary+Shift+Left"]
"view.fullscreen" = []
```

| Command ids | |
|---|---|
| File | `file.new-tab`, `file.new-window`, `file.close-tab`, `file.close-window` |
| Edit | `edit.copy`, `edit.paste`, `edit.select-all`, `edit.open-link`, `edit.copy-link`, `edit.copy-email` |
| View | `view.fullscreen`, `view.zoom-in`, `view.zoom-out`, `view.normal-size` |
| Terminal | `terminal.find`, `terminal.find-next`, `terminal.find-previous`, `terminal.previous-prompt`, `terminal.next-prompt`, `terminal.select-output`, `terminal.reset`, `terminal.settings` |
| Tabs | `tabs.next`, `tabs.previous`, `tabs.last-active`, `tabs.move-left`, `tabs.move-right` |
| Help | `help.about` |

waftty refuses chords the terminal needs, such as a bare letter or a plain
Ctrl+letter, and tells you which entries it could not use.
