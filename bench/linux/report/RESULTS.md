# Terminal benchmark

Scrollback 10000 lines, window [1000, 700], vsync off: False. The run took 11m 44s, finishing 2026-11-10 08:28 EST.

| Terminal | Version |
| --- | --- |
| waftty | waftty 0.5.13 |
| waftty quick | waftty 0.5.13 |
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
| waftty | 15.5 MiB | 14.0 MiB | 27.8 MiB | 26.3 MiB | 0.0 MiB | 0 MiB |
| waftty quick | 18.6 MiB | 17.1 MiB | 31.7 MiB | 30.2 MiB | 0.0 MiB | 0 MiB |
| xfce4-terminal | 12.0 MiB | 7.4 MiB | 21.8 MiB | 17.0 MiB | 0.1 MiB | 0 MiB |
| guake | 44.4 MiB | 36.8 MiB | 52.1 MiB | 44.5 MiB | 0.0 MiB | 0 MiB |
| alacritty | 52.2 MiB | 37.5 MiB | 70.6 MiB | 55.9 MiB | 0.0 MiB | 9 MiB |
| kitty | 68.1 MiB | 51.9 MiB | 93.6 MiB | 77.6 MiB | 0.0 MiB | 3 MiB |
| ghostty | 150.9 MiB | 114.0 MiB | 151.9 MiB | 115.1 MiB | 1.0 MiB | 44 MiB |
| wezterm | 105.6 MiB | 72.5 MiB | 134.5 MiB | 101.6 MiB | 0.0 MiB | 3 MiB |
| rio | 117.5 MiB | 85.7 MiB | 140.7 MiB | 108.8 MiB | 0.0 MiB | 14 MiB |

### Where the memory comes from

![Memory under load by source](ram-sources.png)

Each figure is the PSS of the terminal's own processes after 40 MiB of output. Left out are the shell and test commands, and the session bus a run starts for a single-instance terminal with the desktop services on it (the portal, and for xfce4-terminal xfconfd and gvfsd), which a desktop already runs. Private data is heap and other anonymous memory, scrollback included; code and libraries are mapped from files, each shared page divided among the processes that map it; X server pixmaps and GPU memory are held outside the terminal on its behalf and are not in its PSS.

| Terminal | Processes counted (MiB) | Left out (MiB) |
| --- | --- | --- |
| waftty | waftty 27.8 | sleep 0.1 |
| waftty quick | waftty 31.7 | sleep 0.2 |
| xfce4-terminal | xfce4-terminal 21.8 | sleep 0.1 |
| guake | guake 52.1 | sh 0.2, sleep 0.2 |
| alacritty | alacritty 70.6 | sleep 0.2 |
| kitty | kitty 93.6 | sleep 0.2 |
| ghostty | ghostty 151.9 | sleep 0.2 |
| wezterm | wezterm-gui 134.5 | sleep 0.1 |
| rio | rio 140.7 | sleep 0.2 |

| Terminal | Private data (heap, scrollback) | Code and libraries | Shared memory | X server pixmaps | GPU memory | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 17.0 MiB | 9.5 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 27.8 MiB |
| waftty quick | 18.0 MiB | 12.4 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 31.7 MiB |
| xfce4-terminal | 16.5 MiB | 5.3 MiB | 0.1 MiB | 0.1 MiB | 0.0 MiB | 21.9 MiB |
| guake | 35.4 MiB | 16.6 MiB | 0.0 MiB | 0.0 MiB | 0.0 MiB | 52.1 MiB |
| alacritty | 35.1 MiB | 35.5 MiB | 0.0 MiB | 0.0 MiB | 9.0 MiB | 79.6 MiB |
| kitty | 58.9 MiB | 34.8 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 96.6 MiB |
| ghostty | 62.0 MiB | 88.8 MiB | 1.0 MiB | 1.0 MiB | 44.0 MiB | 196.9 MiB |
| wezterm | 57.5 MiB | 77.0 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 137.5 MiB |
| rio | 52.3 MiB | 88.4 MiB | 0.0 MiB | 0.0 MiB | 14.0 MiB | 154.7 MiB |

## Throughput

![Throughput](throughput.png)

## Smoothness under load

![Smoothness](smoothness.png)

| Terminal | Frames/s | Median gap | p99 gap | Longest gap | Echo median | Echo p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 120 | 8 ms | 13 ms | 15 ms | 5.6 ms | 11.4 ms |
| waftty quick | 122 | 8 ms | 11 ms | 14 ms | 7.4 ms | 9.6 ms |
| xfce4-terminal | 10 | 103 ms | 125 ms | 125 ms | 72.8 ms | 164.0 ms |
| guake | 10 | 103 ms | 125 ms | 125 ms | 37.4 ms | 132.5 ms |
| alacritty | 120 | 8 ms | 9 ms | 9 ms | 10.9 ms | 14.4 ms |
| kitty | 95 | 8 ms | 17 ms | 17 ms | 19.4 ms | 25.8 ms |
| ghostty | 60 | 17 ms | 17 ms | 17 ms | 6.3 ms | 15.1 ms |
| wezterm | 57 | 17 ms | 26 ms | 26 ms | 42.7 ms | 59.4 ms |
| rio | 120 | 8 ms | 9 ms | 9 ms | 18.6 ms | 26.8 ms |

## CPU

![CPU](cpu.png)

| Terminal | Idle | While 40 MiB print | CPU time for 40 MiB |
| --- | ---: | ---: | ---: |
| waftty | 0.00% | 128% | 0.33 s |
| waftty quick | 0.01% | 133% | 0.31 s |
| xfce4-terminal | -0.00% | 86% | 0.30 s |
| guake | -0.00% | 81% | 0.30 s |
| alacritty | 0.00% | 103% | 0.31 s |
| kitty | 0.03% | 98% | 0.55 s |
| ghostty | 0.36% | 186% | 0.59 s |
| wezterm | 0.00% | 123% | 1.10 s |
| rio | 0.72% | 97% | 0.31 s |

## Latency and startup

![Latency](latency.png)

![Startup](startup.png)

| Terminal | Plain | SGR | Unicode | Latency median | Latency p95 | Startup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 197 MB/s | 161 MB/s | 165 MB/s | 1.0 ms | 1.1 ms | 66 ms |
| waftty quick | 190 MB/s | 162 MB/s | 164 MB/s | 0.8 ms | 0.9 ms | 50 ms |
| xfce4-terminal | 123 MB/s | 120 MB/s | 70 MB/s | 1.3 ms | 1.5 ms | 68 ms |
| guake | 105 MB/s | 112 MB/s | 65 MB/s | 0.9 ms | 1.0 ms | 179 ms |
| alacritty | 112 MB/s | 149 MB/s | 101 MB/s | 3.1 ms | 3.5 ms | 93 ms |
| kitty | 57 MB/s | 107 MB/s | 60 MB/s | 7.8 ms | 11.7 ms | 386 ms |
| ghostty | 157 MB/s | 141 MB/s | 158 MB/s | 23.4 ms | 33.8 ms | 671 ms |
| wezterm | 34 MB/s | 64 MB/s | 38 MB/s | 22.6 ms | 25.4 ms | 138 ms |
| rio | 196 MB/s | 194 MB/s | 135 MB/s | 11.4 ms | 15.1 ms | 167 ms |
