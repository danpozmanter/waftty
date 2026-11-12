# Changelog

## 0.6.0 - Command palette

- A command palette: Ctrl+Shift+P (Cmd+Shift+P on macOS) finds and runs any command by part of its name.
- Tabs and the window title name the command in front and its folder, as "claude: ~/dev/waftty".
- Recent Directories: Ctrl+Shift+R (Cmd+Shift+R on macOS) goes back to a folder a tab worked in; Terminal > Clear Recent Directories forgets them.
- Private windows and tabs to work in a temporary directory or run dangerous commands without history pollution.
- Private tabs work with bash, zsh, fish, nushell, xonsh, PowerShell, sh and cmd.
- Shell integration for nushell and xonsh.
- Reset and Clear has no shortcut on Linux and Windows; Ctrl+Shift+R opens Recent Directories.
- Closing a tab or window, or quitting, no longer loses bash history.
- The menu bar can be hidden (View > Show Menu Bar); it shows by default.
- A shell's first prompt no longer flickers at startup, in new tabs or in split panes.
- Builds on gui-engine-gos 0.2.14 and gui-gos 0.2.5.

## 0.5.16 - Cursor blinks without repaint

- macOS: a blinking cursor no longer repaints the window and uses less of a core.
- macOS: an idle window uses less RAM, and memory used during heavy output is freed sooner.
- Builds on windowing-gos 0.1.17 and gui-engine-gos 0.2.13.

## 0.5.15 - Less CPU while output streams

- macOS: a scrolling terminal is shown in layers of its own, so scrolling no longer copies the whole screen each frame. A line of output every 16 ms takes about 9% of a core instead of 21%.
- macOS: the terminal's reader thread only reads while output streams and hands output to the parser in batches. Plain output prints about 60% faster (48 to 78 MB/s), colored output about 40% faster (38 to 53 MB/s), and 40 MiB of output takes about a fifth less CPU (1.63 to 1.29 s). Typed characters echo as fast as before, and while output streams the slowest echoes are faster (p95 62 to 48 ms).
- Unicode text in mixed scripts parses faster: about 13% on Linux, and on macOS it prints at 53 MB/s instead of 48.
- While output streams, the window wakes once per frame instead of once per write.
- macOS: whether VoiceOver is running is checked at most once a second instead of on every frame.
- Builds on Gossamer 0.78.5, windowing-gos 0.1.16, gui-engine-gos 0.2.12 and wezterm-lite 0.1.10.

## 0.5.14 - Lighter scrolling, faster colors

- Output that scrolls takes less CPU to show: a frame copies only what it does not repaint, macOS no longer copies the screen in from the last two frames first, and scrolled rows reach the window without swapping their colors' bytes.
- Colored output and mixed scripts print faster.
- macOS: output that keeps coming is read with one read per wake and parsed on its own thread, instead of switching threads for each kilobyte.
- macOS: a window gives back its spare display buffers soon after it stops painting, and a blinking cursor no longer keeps them.
- While output floods, the window repaints no more often than its paints leave time for, and rendering leaves a core to the parser.
- Memory used to draw output goes back sooner after the output stops.
- Starting takes much less memory, most of all on macOS: the list of every installed font no longer passes through waftty's own code at launch.
- macOS: `vmmap` and `footprint` list waftty's heap as its own memory instead of as graphics memory.
- Builds on Gossamer 0.78.3, windowing-gos 0.1.15, gui-engine-gos 0.2.11 and wezterm-lite 0.1.9.

## 0.5.13 - Faster output on macOS, lighter repaints

- macOS: output no longer wakes a second thread for each kilobyte the pseudo-terminal hands over; a small read is parsed on the thread that read it, and the terminal's reading and parsing threads run at the priority of interactive work.
- Colored output prints about 12% faster on Linux.
- Every repaint, a cursor blink included, takes less time: the engine no longer asks the system how many processors it has on each frame, which on Linux reads files, and no longer copies the window's command list.
- macOS: waftty's windows are not restorable, so macOS no longer rewrites their saved state as they move and change.
- Builds on windowing-gos 0.1.14 and gui-engine-gos 0.2.10.

## 0.5.12 - Quieter when idle, faster when scrolling

- A cursor stops blinking and stays lit 10 seconds after the last input or output, and blinks again on the next, so an untouched window asks almost nothing of the system.
- Output that scrolls past a full scrollback parses about 20% faster: the row it recycles keeps its buffers.
- macOS: a window that has painted nothing for 2 seconds gives back its spare display buffers instead of only marking them reclaimable.
- macOS: waftty no longer loads CloudKit, CoreData, CoreImage, CoreLocation and similar system frameworks it never uses.
- Builds on windowing-gos 0.1.13, gui-engine-gos 0.2.9 and gui-gos 0.2.4.

## 0.5.11 - UI fixes

- Check for Updates no longer flashes an error dialog before showing its answer.
- The About window no longer has a Report a problem link or a Copy button.
- The About window shows its license text as plain text, without a box.
- The About window lists what waftty is built on (Gossamer, gui-gos and SDL versions) and names the platform as, for example, `OS/Platform: Linux/x86_64`.

## 0.5.10 - macOS benchmark with the Dock on screen

- The macOS benchmark no longer stops with "its window did not come to the front" while the Dock or another application's floating window is on screen.

## 0.5.9 - Smaller binary, no lost wakes

- The Linux binary is 2.4 MB smaller (42.8 to 40.4 MB), 2.4 MB of it code: Gossamer 0.78 links waftty's Rust libraries and the Gossamer runtime as one unit, with one standard library and one copy of each crate they share, and waftty leaves out the engine's rich text import, SVG, JPEG and GIF decoders, which a terminal does not use.
- A large paste no longer stalls part way: the program taking the paste could wake waftty at the moment it handled the program's output, and that wake was lost.
- Output that arrives while the window is idle shows at once: SDL could lose the wake waftty's terminal threads send, and the screen then waited for the next key, click or timer.
- The About window names waftty's toolchain once, in its diagnostics.
- Builds on Gossamer 0.78.1, windowing-gos 0.1.12, gui-engine-gos 0.2.8 and gui-gos 0.2.3.

## 0.5.8 - Less CPU for streaming output

- Output that scrolls costs less CPU: rows already drawn turn with the text instead of being drawn again, and only the rows that came in are drawn.
- An idle window keeps about 1 to 2 MB less of waftty's code in memory: the functions startup and idle drawing run sit together in the binary.
- Builds on windowing-gos 0.1.11, gui-engine-gos 0.2.7 and gui-gos 0.2.2.

## 0.5.7 - Leaner memory, quick terminal relaunch

- A window showing Claude Code's symbols uses about 30 MB less: the emoji and CJK fallback fonts those symbols need are mapped from disk instead of read into memory.
- On Wayland waftty no longer loads the GPU driver, Vulkan and LLVM to show its windows, which took over 100 MB per window.
- A hidden quick terminal lets go of its frame, and a window that went quiet lets go of the pixels it cached for redraws.
- Launching `waftty --quick` while the quick terminal runs shows it docked along its edge with focus; it appeared at a size of the window manager's choosing and kept that size as its own.
- Builds on windowing-gos 0.1.11, gui-engine-gos 0.2.6 and gui-gos 0.2.1.

## 0.5.6 - Quick terminal cursor on macOS, leaner macOS windows

- On macOS the quick terminal shows its cursor again after it is hidden and shown; it stayed invisible until the window was clicked.
- A window without keyboard focus shows a hollow cursor instead of none.
- The cursor blinks when Blinking cursor is on; it stayed solid.
- macOS windows use less memory: a window keeps in memory only the frame it shows, and hands the buffers it painted earlier frames into back to the system.
- Builds on windowing-gos 0.1.9 and gui-engine-gos 0.2.4.

## 0.5.5 - macOS 12 support

- The macOS packages, Intel and Apple Silicon, run on macOS 12 and later; (Previously macOS 15).

## 0.5.4 - Faster streaming output

- Colored output, and text in Greek, Cyrillic, CJK, Hangul and other non-Latin scripts, streams faster: output is parsed on a thread of its own while the next is read.
- A soft hyphen or a combining mark at the start of a piece of output joins the character before it only when the two form one grapheme, as they would if the output arrived whole.
- Builds on gui-engine-gos 0.2.3.

## 0.5.3 - Faster repaints

- Typing, and programs that redraw a few lines of a full screen, repaint only the rows that changed, so a keystroke shows sooner while other output streams.
- Output paints once per refresh of the display, up to 120 frames a second on a 120 Hz display, instead of at most 60.
- Colored output paints faster.
- Builds on gui-engine-gos 0.2.2.

## 0.5.2 - Typing after full screen TUI apps

- The first character typed after leaving a full screen TUI app that used kitty's keyboard protocol with Ctrl+C or Ctrl+D reaches the shell; it used to be dropped.
- Builds on gui-gos 0.2.0 and gui-engine-gos 0.2.1.

## 0.5.1 - Close prompt and post full screen program fix

- Closing a window again while it asks whether to end a running program keeps the question open; the second close used to dismiss it and leave the program running without an answer.
- A shell prompt returns to its own line, at the left edge, when a full screen TUI app exits after the window was resized while it ran with a full scrollback; it used to land a row up or partway along a line.

## 0.5.0 - Quick terminal, single instance and tab drops

- `--drop-down` is now `--quick` (or `--quick-terminal`), and its Settings page is **Quick Terminal**. `--quick-position=top|bottom|left|right` picks the edge for one launch.
- On X11 one press of the quick terminal's shortcut always shows or hides it, whether or not it has focus; it used to take a second press after hiding it or after a click elsewhere.
- **Settings > Quick Terminal > Position** hangs it from the top (the default), bottom, left or right edge. **Length** and **Depth**, formerly Width and Height, size it along its edge and out from it.
- A line marks the quick terminal's edge facing the rest of the screen, and dragging that edge resizes it.
- The quick terminal shows on whichever virtual desktop you are on (X11 and macOS).
- `--single-instance` opens the window in the waftty already started with `--single-instance`, with its own folder, program, title and `--hold`, so tabs move between all of those windows.
- A tab dropped anywhere on another window showing one tab, and so no tab strip, moves there.

## 0.4.0 - Split panes, drop-down mode, and Check for Updates

- Building needs Gossamer 0.76.0 or later.
- A paste of several lines no longer asks first unless **Ask before pasting several lines** is on in Settings.
- Tabs split into panes: **Terminal > Split Right** (Ctrl+Shift+D) and **Split Down** (Ctrl+Shift+B) open a shell beside or below the focused pane, in its folder. Drag a divider to resize; **Next Pane** and **Previous Pane** (Ctrl+Shift+] and Ctrl+Shift+[) move between them, a click focuses one, and **Close Pane** (Ctrl+Shift+J) closes it. Close Tab closes the tab with all its panes.
- `waftty --drop-down` opens a drop-down terminal that hangs from the top of the screen above other windows. Its shortcut, F12 unless **Settings > Drop-Down** names another, shows and hides it from any application; the same page sets its width and height. On Wayland the desktop's portal takes the shortcut and may ask to confirm it. A shortcut another application holds is reported.
- Tabs move between windows: drag one out of its window, or choose **Move Tab to New Window** from its menu, to give it a window of its own; drop it on another window's tab strip to move it there. A split tab moves with its panes, and a window left without tabs closes.
- Every dialog button answers a letter, underlined in its label: **E** for **Exit Anyway**, **C** for **Cancel**. Left and Right move between the buttons and Enter presses the focused one, so Left and Enter close over a running program.
- Closing a tab, pane or window over a running program, or quitting, asks under a title that says a program is still running, with **Exit Anyway** beside Cancel.
- Windows reuse their numbers, so waftty remembers the size and place of as many windows as were open at once, rather than of every window ever opened.
- The drop-down window shows no menu bar; its right-click menu reaches Settings, Check for Updates, About and Quit. It starts at half the display's height and keeps the size you resize it to, separately from the size of waftty's other windows.
- **Help > Check for Updates** asks GitHub for the latest release and offers its download page when it is newer.
- The scrollbar shows by default, and **Settings > Appearance > Scrollbar side** puts it on the left or the right.
- With a color scheme of its own, the menu bar and the tab strip take the scheme's colors: the active tab matches the terminal and the bars a shade of it, instead of a near-black bar that matched neither the terminal nor the dialogs.
- Delete deletes forward in programs that turn on the kitty keyboard protocol, which received a Backspace.
- A right click opens the terminal's menu and leaves it open even where the menu opens under the pointer, rather than choosing the item under it.
- Settings reports a Ctrl+Alt shortcut with a letter, which the terminal gives to its program, instead of keeping one that never runs.
- The macOS installer links the `waftty` command into `/usr/local/bin` only.

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
