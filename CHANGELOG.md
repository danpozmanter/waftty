# Changelog

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
