# Terminal benchmark

Measures waftty beside other terminals: memory, CPU (idle, and the time spent printing 40 MB), output throughput, keystroke-to-screen latency idle and under load, and startup. There is a harness per system, each with its own results and report: `linux/` on a live X11 desktop, and `mac/` on macOS.

## Linux

```sh
uv run linux/bench.py run                             # waftty, waftty-quick, xfce4-terminal, guake, alacritty, kitty, ghostty, wezterm, rio
uv run linux/bench.py run --terminals waftty,alacritty --waftty ../target/release/waftty
uv run linux/bench.py run --only throughput,latency    # just those measures (ram, throughput, cpu, latency, streaming, startup)
uv run report.py linux                                # charts and RESULTS.md in linux/report
```

Results go to `linux/results.json` and the report to `linux/report/` (`--out` and `report.py --results` name others). A run replaces the samples of each terminal and measure it takes and keeps the others, so `--only` and `--terminals` update part of a file. A run prints how long it took when it ends and records that, with the time it finished, in the results; the report shows it, and charts each measure for the terminals that have it, each named with the version the run recorded from its `--version`. A figure whose label reads 0 draws no bar. It also reads a run that stopped early, prints which measures are absent and the command that takes them, and leaves out what was not measured instead of charting a zero. When a terminal has no CPU run, its CPU seconds for printing come from its heavy memory runs, which print the same text; idle CPU has no such source. The test inputs and each run's configuration folders stay in `~/.cache/waftty-bench`. Every terminal runs on its defaults from a configuration folder of its own, with the same scrollback (`--scrollback`, 10,000 lines) and a 1000x700 window (or the nearest size its size hints allow).

Guake only runs as a drop-down terminal, so waftty also runs as its quick terminal (`waftty-quick`, `waftty --quick`, sized to the same share of the work area, the unit both size themselves in, and once they have placed themselves, to the same window) for a like-for-like comparison. The quick terminal runs on a session bus of its own, so it opens beside any quick terminal already running; that bus starts the desktop portal it reads its color scheme and font from, and ending a run ends the services its bus started. Ghostty's quick terminal is left out: Ghostty does not support it on X11.

Needs an X server with the XTEST and DAMAGE extensions, and `xrandr`. Run it with nothing else busy on the machine: a stray process using a core shows up in every timing. With no monitor connected (all `xrandr` outputs disconnected), terminals that sync to vblank would fall back to the driver's 1 Hz pacing, so the run sets `__GL_SYNC_TO_VBLANK=0`, and kitty's own `sync_to_monitor=no`, and records that. Rio presents through Vulkan's FIFO mode, which nothing turns off, so it runs only with a monitor connected; and rio 0.5.29 crashes when keyboard or mouse input arrives while it starts, so leave the desktop alone while it runs.

What each number is:

- **Memory:** the terminal's own processes once memory stops moving, idle and after `cat` of 20 MiB of plain text and 20 MiB of 256-color text. The shell, the test commands, and the session bus a single-instance terminal's run starts, with the desktop services it reads at startup already running on it (the portal, and xfce4-terminal's `xfconfd` and `gvfsd`, which a desktop already runs), are left out; startup is timed from the terminal's own launch. Each run records the PSS of every process it counts and every one it leaves out, and splits the counted PSS into private data (heap, scrollback), code and libraries mapped from files, and shared memory; the report charts that split under load beside the X server's pixmaps and GPU memory held for the terminal, and lists the processes per terminal.
- **CPU:** user plus system time of the terminal's processes as a share of one core, over 10 idle seconds, starting 13 seconds after the last output so a terminal that rests its cursor has done so, and while 20 MiB of plain and 20 MiB of colored text print (above 100% means several cores), charted together; the table also gives the CPU seconds the heavy memory run took.
- **Throughput:** the time `cat` takes to finish a 20 MiB file inside the terminal, for plain ASCII, 256-color SGR runs and mixed scripts.
- **Latency:** from an XTEST key press until the echoed character's pixels change: each X Damage report on the window is checked against the pixels captured before the key, so only a visible change counts. 60 samples. This covers the terminal's whole path to the X server's copy of the window; keyboard hardware and the display's scanout are the same for every terminal and left out.
- **Smoothness under load:** a program floods colored lines below five fixed rows, setting that layout again whenever the terminal resizes. Over 4 seconds the X server's Damage timestamps give the frames that reach the window (rectangles closer than 4 ms are one frame): frames per second, the median and 99th percentile gap, and the longest stall. Then 25 key presses, which the program echoes into the fixed first row, give the keystroke latency while output streams; a key counts once the pixels above the scrolling rows change, wherever the terminal's tab bar and padding put them.
- **Startup:** from launch until a screenful of printed lines is on screen, read in the middle of the window so tab bars and padding do not count. 10 launches.

## macOS

```sh
uv run mac/bench.py run                               # waftty, waftty-quick, iterm2, alacritty, kitty, ghostty, wezterm, rio
uv run mac/bench.py run --terminals waftty,iterm2 --waftty /Applications/waftty.app/Contents/MacOS/waftty
uv run report.py mac                                  # charts and RESULTS.md in mac/report
```

The same measures through macOS's own interfaces, written to `mac/results.json` and reported in `mac/report/`. The terminal that runs the script needs Accessibility (to size windows and type) and Screen Recording (to read pixels) in System Settings, Privacy & Security; leave the desktop alone while it runs, since keys go to the frontmost window. The run keeps the display awake with `caffeinate`, since a display that sleeps or locks takes the windows off screen. Terminals are found on the `PATH` or in `/Applications`; Ghostty and iTerm2 start through Launch Services. The inputs and each run's folders stay in `~/Library/Caches/waftty-bench`.

What differs from Linux:

- **Memory:** each process's physical footprint, the memory it dirtied, compressed memory included, which Activity Monitor shows as Memory; RSS is recorded beside it. macOS has no proportional set size, and the window server and GPU memory a terminal uses are not attributed to it.
- **Latency:** from a Quartz key event until the end of the capture of the window that shows the echo, idle and while output streams. A reading includes up to one capture's time, so the report lists how long captures took; the display's refresh rate, also in the report, sets how often a new frame can appear.
- **Quick terminal:** sized to the same whole percentages of the work area as Linux's, so its memory compares with the normal window's. It cannot match 1000x700 exactly.
- **Smoothness:** not measured. macOS has no counterpart to X Damage's per-frame timestamps, so only the latency while output streams is recorded.
- **Isolation:** waftty runs with a `HOME` of the run's own, which holds its settings and its single-instance claim, so it opens beside any waftty already running. iTerm2 runs every window in one process, so the run asks you to quit it first, and loads its scrollback from a dynamic profile it removes afterwards.
