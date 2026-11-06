# Terminal benchmark

Scrollback 10000 lines, window [1000, 700], vsync off: False.

| Terminal | Version |
| --- | --- |
| waftty | waftty 0.5.2 |
| waftty quick | waftty 0.5.2 |
| xfce4-terminal | xfce4-terminal 1.1.3 (Xfce 4.18) |
| guake | Guake Terminal: 3.10 |
| alacritty | alacritty 0.13.2 |
| kitty | kitty 0.32.2 created by Kovid Goyal |
| ghostty | Ghostty 1.4.1-main+93967b7f9 |
| wezterm | wezterm 20240203-110809-5046fc22 |
| rio | rioterm 0.5.29 |

## Memory

![Memory](ram.png)

PSS shares each library page among the processes that map it; USS is the terminal's own. X server pixmaps and GPU memory are held elsewhere on the terminal's behalf.

| Terminal | Idle PSS | Idle USS | Heavy PSS | Heavy USS | X server pixmaps | GPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 10.6 MiB | 6.2 MiB | 22.3 MiB | 17.8 MiB | 0.0 MiB | 0 MiB |
| waftty quick | 12.2 MiB | 7.0 MiB | 24.0 MiB | 18.6 MiB | 0.0 MiB | 0 MiB |
| xfce4-terminal | 15.8 MiB | 10.6 MiB | 23.7 MiB | 18.6 MiB | 0.1 MiB | 0 MiB |
| guake | 48.4 MiB | 40.8 MiB | 56.4 MiB | 48.8 MiB | 0.0 MiB | 0 MiB |
| alacritty | 61.5 MiB | 57.2 MiB | 80.0 MiB | 75.6 MiB | 0.0 MiB | 9 MiB |
| kitty | 77.8 MiB | 72.0 MiB | 103.6 MiB | 97.7 MiB | 0.0 MiB | 3 MiB |
| ghostty | 179.4 MiB | 171.3 MiB | 182.5 MiB | 174.4 MiB | 1.0 MiB | 44 MiB |
| wezterm | 135.5 MiB | 131.0 MiB | 165.0 MiB | 160.6 MiB | 0.0 MiB | 3 MiB |
| rio | 145.2 MiB | 141.8 MiB | 167.7 MiB | 164.3 MiB | 0.0 MiB | 14 MiB |

### Where the memory comes from

![Memory under load by source](ram-sources.png)

Each figure is the PSS of the terminal's own processes after 40 MiB of output. Left out are the shell and test commands, and the session bus a run starts for a single-instance terminal (dbus-run-session, dbus-daemon, and for xfce4-terminal xfconfd and gvfsd), which a desktop already runs. Private data is heap and other anonymous memory, scrollback included; code and libraries are mapped from files, each shared page divided among the processes that map it; X server pixmaps and GPU memory are held outside the terminal on its behalf and are not in its PSS.

| Terminal | Processes counted (MiB) | Left out (MiB) |
| --- | --- | --- |
| waftty | waftty 22.3 | sleep 0.2 |
| waftty quick | waftty 24.0 | sleep 0.2 |
| xfce4-terminal | xfce4-terminal 23.7 | sleep 0.2 |
| guake | guake 56.4 | sh 0.2, sleep 0.2 |
| alacritty | alacritty 80.0 | sleep 0.2 |
| kitty | kitty 103.6 | sleep 0.2 |
| ghostty | ghostty 182.5 | sleep 0.2 |
| wezterm | wezterm-gui 165.0 | sleep 0.2 |
| rio | rio 167.7 | sleep 0.2 |

| Terminal | Private data (heap, scrollback) | Code and libraries | Shared memory | X server pixmaps | GPU memory | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 17.0 MiB | 4.0 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 22.3 MiB |
| waftty quick | 16.9 MiB | 5.7 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 24.0 MiB |
| xfce4-terminal | 14.9 MiB | 8.7 MiB | 0.1 MiB | 0.1 MiB | 0.0 MiB | 23.8 MiB |
| guake | 35.7 MiB | 20.7 MiB | 0.0 MiB | 0.0 MiB | 0.0 MiB | 56.4 MiB |
| alacritty | 35.2 MiB | 44.8 MiB | 0.0 MiB | 0.0 MiB | 9.0 MiB | 89.0 MiB |
| kitty | 58.9 MiB | 44.7 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 106.6 MiB |
| ghostty | 61.2 MiB | 120.3 MiB | 1.0 MiB | 1.0 MiB | 44.0 MiB | 227.5 MiB |
| wezterm | 57.8 MiB | 107.2 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 168.0 MiB |
| rio | 52.2 MiB | 115.5 MiB | 0.0 MiB | 0.0 MiB | 14.0 MiB | 181.7 MiB |

## Throughput

![Throughput](throughput.png)

## Smoothness under load

![Smoothness](smoothness.png)

| Terminal | Frames/s | Median gap | p99 gap | Longest gap | Echo median | Echo p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 62 | 16 ms | 20 ms | 21 ms | 11.2 ms | 17.4 ms |
| waftty quick | 63 | 16 ms | 18 ms | 20 ms | 7.4 ms | 17.4 ms |
| xfce4-terminal | 11 | 96 ms | 125 ms | 125 ms | 130.0 ms | 195.4 ms |
| guake | 11 | 91 ms | 128 ms | 128 ms | 36.3 ms | 118.4 ms |
| alacritty | 120 | 8 ms | 9 ms | 9 ms | 9.0 ms | 12.3 ms |
| kitty | 96 | 8 ms | 17 ms | 18 ms | 19.2 ms | 26.4 ms |
| ghostty | 60 | 17 ms | 18 ms | 18 ms | 12.1 ms | 20.5 ms |
| wezterm | 59 | 17 ms | 25 ms | 26 ms | 39.9 ms | 55.3 ms |
| rio | 120 | 8 ms | 9 ms | 9 ms | 18.1 ms | 23.8 ms |

## CPU

![CPU](cpu.png)

| Terminal | Idle | While 40 MiB print | CPU time for 40 MiB |
| --- | ---: | ---: | ---: |
| waftty | 0.00% | 112% | 0.29 s |
| waftty quick | 0.00% | 113% | 0.29 s |
| xfce4-terminal | 0.00% | 84% | 0.30 s |
| guake | 0.00% | 82% | 0.29 s |
| alacritty | 0.00% | 102% | 0.30 s |
| kitty | 0.20% | 94% | 0.54 s |
| ghostty | 0.30% | 197% | 0.58 s |
| wezterm | 0.10% | 125% | 1.16 s |
| rio | 1.10% | 96% | 0.31 s |

## Latency and startup

![Latency](latency.png)

![Startup](startup.png)

| Terminal | Plain | SGR | Unicode | Latency median | Latency p95 | Startup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 156 MB/s | 142 MB/s | 104 MB/s | 1.2 ms | 1.6 ms | 68 ms |
| waftty quick | 185 MB/s | 145 MB/s | 107 MB/s | 1.0 ms | 1.1 ms | 46 ms |
| xfce4-terminal | 113 MB/s | 120 MB/s | 67 MB/s | 1.3 ms | 1.7 ms | 54 ms |
| guake | 109 MB/s | 98 MB/s | 65 MB/s | 1.0 ms | 1.1 ms | 156 ms |
| alacritty | 128 MB/s | 148 MB/s | 120 MB/s | 2.5 ms | 3.0 ms | 85 ms |
| kitty | 63 MB/s | 109 MB/s | 59 MB/s | 10.0 ms | 13.4 ms | 322 ms |
| ghostty | 171 MB/s | 145 MB/s | 160 MB/s | 24.5 ms | 32.6 ms | 428 ms |
| wezterm | 36 MB/s | 67 MB/s | 37 MB/s | 22.4 ms | 25.7 ms | 62 ms |
| rio | 193 MB/s | 221 MB/s | 138 MB/s | 12.4 ms | 17.1 ms | 28 ms |
