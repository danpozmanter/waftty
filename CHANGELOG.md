# Changelog

## 0.3.0 - Copy mode, link hints, resource usage, and speed

- Copy mode (**Terminal > Copy Mode**, Ctrl+Shift+X) selects and copies with the keyboard, anywhere in the screen and the scrollback.
- Link hints label the links and file paths on the screen: type a label to open one (Ctrl+Shift+E) or copy it (Ctrl+Shift+Y).
- **File > Save Scrollback**, **Save Selection** and **Open Scrollback in Editor** write the terminal's text to a file, with wrapped lines joined.
- Pastes of up to 16 MiB go to the program as fast as it reads them; typing meanwhile follows the paste, and Escape or Ctrl+C stops it. A paste that can't be sent says why instead of doing nothing.
- Programs that ask for kitty's keyboard protocol get keys classic terminals can't tell apart, such as Shift+Enter; others get the keys they always had.
- `waftty --shell-integration bash` (or `zsh`, `fish`, `powershell`) prints a script that marks prompts and output for the prompt commands; the guide has the line to add to each shell's startup file.
- `--working-directory`, `--title` and `--hold` start the first tab in a folder, give it a name its program can't change, or keep it open after its program exits.
- A typed character shows as soon as the program echoes it, about 1 ms, instead of up to a frame later.
- Output shows faster than in 0.2: plain and colored text about twice as fast, and mixed Unicode about 2.5 times.
- A flood of output draws a steady 60 frames a second, and typing during it shows in about 12 ms.
- After a flood of output waftty holds about 5 MB less in RAM (27 MB instead of 32 MB). Colored output history compresses with its colors, and compressing waits until the flood ends.
- A scrollback of more than about 30,000 lines no longer stops waftty from starting. The scrollback setting goes up to 100,000 lines, history well above the screen takes about a third of the memory it did, and a long history is bounded by memory as well as by lines.
- Holding a spin box's - or + button in Settings keeps stepping.
- On Linux, keys skip the input method (ibus or fcitx) when it has only keyboard layouts set up, so a typed character shows in about 1 ms instead of 2.3 ms. **Settings > Behavior > Use the input method** sets it to always or never instead.
- The Help menu no longer has Report a Problem; the About window still links the issue tracker.
- **Settings > General > Open windows at their last size** can be turned off, so new windows open at the configured columns and rows; those settings are now labeled Columns and Rows.
- On Linux, waftty keeps about 5 MB less of its code in memory while it runs: 3.3 MB at idle instead of 8.2 MB.
- Building from source with `install.sh` lays out the code the same way the release packages do.

## 0.2.2 - macOS installer fix

- The macOS installer links the `waftty` command into `/opt/homebrew/bin` only when Homebrew is installed, instead of creating that folder.

## 0.2.1 - macOS installer and Settings shortcut

- The macOS package installs with `install.command`, which runs in Terminal when double-clicked.
- Saving Settings keeps the Settings shortcut (Ctrl+, or Cmd+,) instead of reporting "Cmd+" as a chord waftty does not read. If 0.2.0 reported it, reset the Settings shortcut on the Shortcuts page.

## 0.2.0 - Settings, shortcuts, and defaults

- Settings is a tabbed window: General, Appearance, Behavior and Shortcuts. Every value resets on its own, and only changed values are saved, so defaults follow the desktop.
- The shell setting takes a command line. Empty runs the login shell (as a login shell on macOS, PowerShell on Windows), starting in the home folder.
- New settings: font weight, ligatures, cursor shape and blinking, bold as bright, readability, padding, background opacity, scrollbar, menu bar and tab bar, scrolling on output and typing, word characters, copy on select, asking before risky pastes, the bell, notifications, window size, reopening windows and tabs, close confirmation, and Option as Meta on macOS.
- Color schemes can be edited, and imported from iTerm2, Windows Terminal, xfce4-terminal and base16.
- macOS shortcuts use Command alone. New shortcuts: Settings, Quit, tabs by number, zoom with Ctrl, Clear Scrollback, scrolling, and Select Last Command Output.
- New commands: Quit, Clear Scrollback, Reset and Clear, Scroll to Top and Bottom, Show Menu Bar, Reset Window Size, Pin Tab, Close Other Tabs, Close Tabs to the Right, and Help links.
- The font defaults to the desktop's monospace font, size and weight. Scrollback keeps 1,000 lines by default, as in other terminals.
- Background opacity changes open windows too.
- Linux release builds lay out their code from a correct profile of a session.
- Tabs are named for their program, close prompts name the running program, a double click selects a word, dropped files paste as paths, and Find offers earlier searches.
- Dialog text and controls follow the desktop's font size.
- Clearer wording throughout.

## 0.1.1 - Settings window

- Settings opens in a window of its own that can be moved and resized.
- The color scheme list scrolls, so every scheme, your own included, can be chosen again.
- Setting descriptions wrap.
- "Follow the system" is now "System theme".

## 0.1.0 - Initial release

- A tabbed terminal emulator for Linux, macOS and Windows, with find in scrollback, shell integration, links, terminal images, color schemes and character sets.
- Packages: a tar.gz, deb, rpm and AppImage for Linux, zips for both macOS architectures, and a zip, portable zip and setup program for Windows.
- Memory work: the Linux build lays out its code by how a session uses it, releases code used only at startup once the first window is shown, and stores scrollback lines at their exact size.
