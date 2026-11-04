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
| Copy Mode | ++ctrl+shift+x++ | ++cmd+shift+x++ |
| Open / Copy a Link by Keyboard | ++ctrl+shift+e++ / ++ctrl+shift+y++ | ++cmd+shift+e++ / ++cmd+shift+y++ |
| Save Scrollback | ++ctrl+shift+s++ | ++cmd+shift+s++ |
| Scroll Up / Down a Page | ++shift+page-up++ / ++shift+page-down++ | the same |
| Scroll to Top / Bottom | ++ctrl+shift+home++ / ++ctrl+shift+end++ | ++cmd+home++ / ++cmd+end++ |
| Clear Scrollback | ++ctrl+shift+k++ | ++cmd+k++ |
| Reset and Clear | ++ctrl+shift+r++ | ++cmd+option+k++ |
| Next Tab / Previous Tab | ++ctrl+tab++ / ++ctrl+shift+tab++ (also ++ctrl+page-down++ / ++ctrl+page-up++) | the same, or ++cmd+shift+bracket-right++ / ++cmd+shift+bracket-left++ |
| Tab 1 to 8 / Last Tab | ++alt+1++ to ++alt+8++ / ++alt+9++ | ++cmd+1++ to ++cmd+8++ / ++cmd+9++ |
| Switch to Last Tab | ++ctrl+shift+l++ | ++cmd+shift+l++ |
| Move Tab Left / Right | ++ctrl+shift+page-up++ / ++ctrl+shift+page-down++ | ++cmd+shift+page-up++ / ++cmd+shift+page-down++ |
| Split Right / Split Down | ++ctrl+shift+d++ / ++ctrl+shift+b++ | ++cmd+d++ / ++cmd+shift+d++ |
| Next Pane / Previous Pane | ++ctrl+shift+bracket-right++ / ++ctrl+shift+bracket-left++ | ++cmd+bracket-right++ / ++cmd+bracket-left++ |
| Close Pane | ++ctrl+shift+j++ | ++cmd+option+w++ |

A right click on the terminal offers the link entries, Copy, Paste, Select
All, New Tab, Split Right, Split Down, Close Pane, Find, Clear Scrollback,
Send Signal, Zoom, Show Menu Bar and Settings.

## Tabs

- A tab is named for its program until the program sets a title; its tooltip
  adds the folder it works in.
- Drag a tab to reorder it. The Tabs menu and a right click on a tab pin it,
  close the others, or close the tabs to its right. Pinned tabs sit first and
  stay open.
- A tab whose program rings the bell or posts a notification while hidden is
  marked until you look at it.
- Drag a tab out of its window, or choose **Move Tab to New Window** from its
  menu, to give it a window of its own. Drop a tab on another window's tab
  strip to move it there; a split tab moves with its panes, and a window left
  without tabs closes.
- Closing a tab, window or waftty while a program runs asks first and names
  the program. **Exit Anyway** (or ++e++, or ++left++ then ++enter++) closes
  it anyway; **Cancel** (++c++ or ++escape++) keeps it. Every dialog's buttons
  answer the letter underlined in their labels, and the arrow keys move
  between them.

## Split Panes

- **Terminal > Split Right** and **Split Down** divide the focused pane and
  start your shell in the new one, in the same folder.
- Drag the divider between two panes to resize them. A click focuses a pane;
  **Next Pane** and **Previous Pane** move through them in reading order.
- **Close Pane** closes the focused pane, and its neighbor takes the space.
  A pane whose program exits closes the same way.
- A split tab is one tab in the strip, named for its focused pane. Close Tab
  closes it with all its panes.

## Drop-Down Mode

```sh
waftty --drop-down
```

opens waftty as a drop-down terminal: a window without a frame that hangs
from the top of the screen above other windows. Its shortcut, ++f12++ unless
**Settings > Drop-Down** names another, shows and hides it from any
application; pressed while another window has focus, it brings the drop-down
to the front. It has no menu bar; a right click reaches Settings, Check for
Updates, About and Quit. It spans the display's width and half its height
until you resize it, and then keeps the size you left it at, apart from the
size waftty's other windows remember; the same page sets the width and the
height, in percent of the display.

Add `waftty --drop-down` to your desktop's startup applications to have it
ready at login. Launching it again while it runs shows the running one.

- On X11, Windows and macOS waftty takes the key itself. If another
  application, such as another drop-down terminal, already holds it, waftty
  says so; choose another key on the Drop-Down page.
- On Wayland the desktop's GlobalShortcuts portal takes it, and the desktop
  may ask you to confirm or change the key. Where the desktop has no such
  portal, bind a desktop shortcut to `waftty --drop-down`, which shows the
  running drop-down.

## Find

**Terminal > Find** searches the whole scrollback, with options for case,
whole words and regular expressions, and shows how many matches it found.
The search field offers your earlier searches.

## Copy Mode

**Terminal > Copy Mode** selects and copies text without the mouse, anywhere
in the screen and the scrollback. A cursor of its own starts where the
program's is, and a frame round the terminal shows the mode is on. While it
is, keys go to copy mode, not the program.

| Key | Does |
|---|---|
| Arrows, or ++h++ ++j++ ++k++ ++l++ | Move a cell or a row |
| ++w++ / ++b++ | Next / previous word |
| ++0++ or ++home++ / `$` or ++end++ | Start / end of the line |
| ++page-up++ / ++page-down++ | A screen up / down |
| ++g++ / ++shift+g++ | The oldest row kept / the program's cursor |
| ++v++ or ++space++ | Start or drop a selection |
| ++y++, ++enter++ or ++ctrl+shift+c++ | Copy the selection (the cursor's line without one) and leave |
| ++escape++ or ++q++ | Leave |

## Link Hints

**Edit > Open a Link by Keyboard** labels every link and file path on the
screen with a letter or two; type a label to open that link, as a Ctrl+click
would. **Copy a Link by Keyboard** copies it instead. ++escape++ leaves
without choosing, and ++backspace++ takes back a typed key.

## Saving Output

**File > Save Scrollback** writes everything the tab keeps, the oldest row
first, to a text file; **Save Selection** writes what is selected. A long
line that wrapped on screen comes back as one line. **Open Scrollback in
Editor** saves the scrollback to a file in the system's temporary folder and
opens it in the editor Settings name, or with the desktop's default
application.

A saved terminal holds only what the scrollback kept: a full-screen program
redraws its screen in place, and the oldest rows leave once the scrollback
is full. For a complete record of an agent's work, keep the agent's own log.

## Pasting

With **Ask before pasting several lines** on in Settings, a paste of several
lines or of control characters asks first; it is off by default. Pastes of up to 16 MiB reach the program as fast as it reads
them, as one paste: typing meanwhile follows the paste, and ++escape++ or
++ctrl+c++ stops it where the program has got to. A paste that can't be
sent says why.

## Shell Integration

When the shell marks its prompts and its commands' output (OSC 133) and says
which folder it is in (OSC 7), waftty knows where each command starts and
ends:

- **Previous Prompt / Next Prompt** scroll from one prompt to the next.
- **Select Last Command Output** selects everything the last command printed.
- New tabs and windows open in the folder the shell is in.

waftty carries the scripts that do this for bash, zsh, fish and PowerShell;
`waftty --shell-integration SHELL` prints one. Add the line for your shell to
its startup file. Each runs only in waftty and leaves your prompt as it is.

=== "bash"

    ```sh
    # ~/.bashrc
    [ "$TERM_PROGRAM" = waftty ] && eval "$(waftty --shell-integration bash)"
    ```

=== "zsh"

    ```sh
    # ~/.zshrc
    [[ $TERM_PROGRAM == waftty ]] && eval "$(waftty --shell-integration zsh)"
    ```

=== "fish"

    ```fish
    # ~/.config/fish/config.fish
    test "$TERM_PROGRAM" = waftty; and waftty --shell-integration fish | source
    ```

=== "PowerShell"

    ```powershell
    # $PROFILE
    if ($env:TERM_PROGRAM -eq 'waftty') { waftty --shell-integration powershell | Out-String | Invoke-Expression }
    ```

To check it works, run a command, then press ++ctrl+shift+o++: the command's
output should be selected. Without integration, the prompt commands say that
shell integration is off.

## Keyboard Protocol

Programs that ask for it (with kitty's keyboard protocol) get keys other
terminals can't tell apart, such as ++shift+enter++, ++ctrl+i++ apart from
++tab++, and key releases. Programs that don't ask get the classic xterm keys
they always had.

## Notifications from Agents

waftty marks a hidden tab whose program rings the bell or posts a desktop
notification (OSC 9 or OSC 777), and passes the notification to the desktop.
Coding agents in a background tab can tell you when they need you:

- **Claude Code:** turn on the terminal bell in its `/config` (Notifications),
  or add a hook for its `Notification` and `Stop` events that posts one:

    ```sh
    printf '\033]777;notify;Claude Code;%s\007' "Waiting for you" > /dev/tty
    ```

- **Codex:** set `notify` in `~/.codex/config.toml` to a script that posts a
  notification the same way when a turn finishes.
- **Any long command:** end it with `; printf '\a'` to ring the bell when it
  finishes.

## Starting waftty

```sh
waftty --working-directory ~/dev/project     # the first tab starts there
waftty --title review -e codex               # the tab keeps this name
waftty --hold -e ./run-checks                # the tab stays open after it ends
```

`waftty --drop-down` starts the [drop-down terminal](#drop-down-mode).
Every argument after `-e` is the program's own. `--hold` keeps the
program's last screen and adds the status it exited with; close the tab when
you are done. A folder or a program on the command line starts a new session
rather than reopening the last one.

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

**Edit > Settings** opens a window with five pages. Each value has a button
that puts it back to its default; only values that differ from the defaults
are saved, so the defaults follow your desktop.

- **General**: the shell, as a command line (empty runs your login shell,
  as a login shell on macOS; PowerShell on Windows), the starting folder
  (empty is your home folder), where new tabs open, the character encoding,
  whether new windows open at their last size or at the columns and rows
  set there, whether windows and tabs come back at the next start, and whether closing a running program asks first.
- **Appearance**: the font, its size and weight (empty uses the desktop's
  monospace font), ligatures, the color scheme, the cursor shape and
  blinking, bold text in bright colors, readability adjustment, padding,
  background opacity (below 100 percent the desktop shows through the
  terminal, where it blends windows), the scrollbar and its side, the menu
  bar and the tab bar.
- **Behavior**: scrollback lines, scrolling on output and typing, the
  characters a double click selects, copying on select, asking before
  pasting several lines, the bell (mark the tab, flash or sound),
  notifications, programs writing the clipboard (OSC 52; they can never read
  it), the editor for file paths (such as `nvim +{line} {path}`), on macOS
  whether Option is Meta, and on Linux whether keys go through the input
  method (see below).
- **Drop-Down**: the shortcut that shows and hides the
  [drop-down terminal](#drop-down-mode), and its width and height.
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

### Input Method

On Linux, an input method such as ibus or fcitx composes Chinese, Japanese
and Korean text, and every key waits for it, about a millisecond. **Use the
input method** decides whether waftty sends keys through it:

- **When it has more than keyboard layouts** (the default): waftty asks ibus
  (its preloaded engines) or fcitx5 (its profile) which engines are set up,
  and uses the input method only when one of them is more than a keyboard
  layout.
- **Always** or **Never**.

The choice applies at the next start. Programs in the tabs keep the
desktop's input method either way.

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

## Updates

**Help > Check for Updates** asks GitHub for the latest release. When it is
newer than the waftty running, Download opens its page; otherwise waftty says
it is up to date. waftty checks only when asked.

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
