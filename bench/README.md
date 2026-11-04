# Terminal benchmark

Measures waftty beside other terminals on a live X11 desktop: memory (PSS, USS, RSS, GPU), CPU (idle, and the time spent printing 40 MB), output throughput, keystroke-to-screen latency idle and under load, frame smoothness under load, and startup.

```sh
uv run bench.py run                                   # waftty, xfce4-terminal, alacritty, ghostty, wezterm
uv run bench.py run --terminals waftty,alacritty --waftty ../target/release/waftty
uv run bench.py run --only throughput,latency          # just those measures (ram, throughput, cpu, latency, streaming, startup)
uv run report.py                                      # charts and RESULTS.md
```

Results go to `results.json` and the report to `report/` in the current directory (`--out` and `report.py --results` name others). The test inputs and each run's configuration folders stay in `~/.cache/waftty-bench`. Every terminal runs on its defaults from a configuration folder of its own, with the same scrollback (`--scrollback`, 10,000 lines) and a 1000x700 window (or the nearest size its size hints allow).

Needs an X server with the XTEST and DAMAGE extensions, and `xrandr`. Run it with nothing else busy on the machine: a stray process using a core shows up in every timing. With no monitor connected (all `xrandr` outputs disconnected), terminals that sync to vblank would fall back to the driver's 1 Hz pacing, so the run sets `__GL_SYNC_TO_VBLANK=0` and records that.

What each number is:

- **Memory:** the terminal's own processes once memory stops moving, idle and after `cat` of 20 MiB of plain text and 20 MiB of 256-color text. The shell and the test commands are left out.
- **CPU:** user plus system time of the terminal's processes as a share of one core, over 10 idle seconds and while 20 MiB of plain and 20 MiB of colored text print (above 100% means several cores), charted together; the table also gives the CPU seconds the heavy memory run took.
- **Throughput:** the time `cat` takes to finish a 20 MiB file inside the terminal, for plain ASCII, 256-color SGR runs and mixed scripts.
- **Latency:** from an XTEST key press until the echoed character's pixels change: each X Damage report on the window is checked against the pixels captured before the key, so only a visible change counts. 60 samples. This covers the terminal's whole path to the X server's copy of the window; keyboard hardware and the display's scanout are the same for every terminal and left out.
- **Smoothness under load:** a program floods colored lines below five fixed rows. Over 4 seconds the X server's Damage timestamps give the frames that reach the window (rectangles closer than 4 ms are one frame): frames per second, the median and 99th percentile gap, and the longest stall. Then 25 key presses, which the program echoes into the fixed first row, give the keystroke latency while output streams.
- **Startup:** from launch until the first printed line is on screen. 10 launches.
