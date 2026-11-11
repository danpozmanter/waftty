# Terminal benchmark

Scrollback 10000 lines, window [1000, 700], vsync off: False. The run took 25m 41s, finishing 2026-11-11 15:33 EST.

| Terminal | Version |
| --- | --- |
| waftty | waftty 0.5.16 |
| waftty quick | waftty 0.5.16 |
| xfce4-terminal | xfce4-terminal 1.1.3 (Xfce 4.18) |
| guake | Guake Terminal: 3.10 |
| alacritty | alacritty 0.13.2 |
| kitty | kitty 0.32.2 created by Kovid Goyal |
| ghostty | Ghostty 1.4.1-main+93967b7f9 |
| wezterm | wezterm 20240203-110809-5046fc22 |
| rio | rioterm 0.5.29 |

## Memory

![Memory](ram.png)

The cursor-rested figures read the same memory again 13 seconds after the output, once a terminal that stops blinking its cursor has; what goes only then is held all the while the cursor blinks.

PSS shares each library page among the processes that map it; USS is the terminal's own. X server pixmaps and GPU memory are held elsewhere on the terminal's behalf.

| Terminal | Idle PSS | Idle USS | Heavy PSS | Heavy USS | Idle, cursor rested | Heavy, cursor rested | X server pixmaps | GPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 17.0 MiB | 15.3 MiB | 25.2 MiB | 23.5 MiB | 17.1 MiB | 25.2 MiB | 0.0 MiB | 0 MiB |
| waftty quick | 19.7 MiB | 18.1 MiB | 27.8 MiB | 26.2 MiB | 19.7 MiB | 27.8 MiB | 0.0 MiB | 0 MiB |
| xfce4-terminal | 13.8 MiB | 7.7 MiB | 24.8 MiB | 18.7 MiB | 13.9 MiB | 24.8 MiB | 0.1 MiB | 0 MiB |
| guake | 45.5 MiB | 35.9 MiB | 53.5 MiB | 43.9 MiB | 45.5 MiB | 53.5 MiB | 0.0 MiB | 0 MiB |
| alacritty | 60.8 MiB | 54.5 MiB | 79.2 MiB | 72.9 MiB | 60.8 MiB | 79.2 MiB | 0.0 MiB | 9 MiB |
| kitty | 76.7 MiB | 68.8 MiB | 102.1 MiB | 94.1 MiB | 78.7 MiB | 102.1 MiB | 0.0 MiB | 3 MiB |
| ghostty | 178.8 MiB | 168.2 MiB | 180.9 MiB | 170.2 MiB | 176.8 MiB | 180.9 MiB | 1.0 MiB | 44 MiB |
| wezterm | 133.7 MiB | 128.0 MiB | 162.7 MiB | 157.0 MiB | 137.5 MiB | 166.5 MiB | 0.0 MiB | 3 MiB |
| rio | 141.9 MiB | 135.3 MiB | 164.9 MiB | 158.3 MiB | 141.9 MiB | 164.8 MiB | 0.0 MiB | 14 MiB |

### Where the memory comes from

![Memory under load by source](ram-sources.png)

Each figure is the PSS of the terminal's own processes after 40 MiB of output. Left out are the shell and test commands, and the session bus a run starts for a single-instance terminal with the desktop services on it (the portal, and for xfce4-terminal xfconfd and gvfsd), which a desktop already runs. Private data is heap and other anonymous memory, scrollback included; code and libraries are mapped from files, each shared page divided among the processes that map it; X server pixmaps and GPU memory are held outside the terminal on its behalf and are not in its PSS.

| Terminal | Processes counted (MiB) | Left out (MiB) |
| --- | --- | --- |
| waftty | waftty 25.2 | sleep 0.2 |
| waftty quick | waftty 27.8 | sleep 0.2 |
| xfce4-terminal | xfce4-terminal 24.8 | sleep 0.2 |
| guake | guake 53.5 | sh 0.2, sleep 0.2 |
| alacritty | alacritty 79.2 | sleep 0.2 |
| kitty | kitty 102.1 | sleep 0.2 |
| ghostty | ghostty 180.9 | sleep 0.2 |
| wezterm | wezterm-gui 162.7 | sleep 0.2 |
| rio | rio 164.9 | sleep 0.2 |

| Terminal | Private data (heap, scrollback) | Code and libraries | Shared memory | X server pixmaps | GPU memory | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 12.9 MiB | 11.0 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 25.2 MiB |
| waftty quick | 12.9 MiB | 13.6 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 27.8 MiB |
| xfce4-terminal | 17.8 MiB | 6.9 MiB | 0.1 MiB | 0.1 MiB | 0.0 MiB | 24.9 MiB |
| guake | 35.7 MiB | 17.8 MiB | 0.0 MiB | 0.0 MiB | 0.0 MiB | 53.5 MiB |
| alacritty | 35.1 MiB | 44.1 MiB | 0.0 MiB | 0.0 MiB | 9.0 MiB | 88.2 MiB |
| kitty | 58.4 MiB | 43.7 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 105.1 MiB |
| ghostty | 62.3 MiB | 117.6 MiB | 1.0 MiB | 1.0 MiB | 44.0 MiB | 225.9 MiB |
| wezterm | 57.5 MiB | 105.2 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 165.7 MiB |
| rio | 52.2 MiB | 112.7 MiB | 0.0 MiB | 0.0 MiB | 14.0 MiB | 178.9 MiB |

## Throughput

![Throughput](throughput.png)

## Smoothness under load

![Smoothness](smoothness.png)

| Terminal | Frames/s | Median gap | p99 gap | Longest gap | Echo median | Echo p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 120 | 8 ms | 13 ms | 17 ms | 6.5 ms | 12.4 ms |
| waftty quick | 121 | 8 ms | 12 ms | 16 ms | 6.2 ms | 9.2 ms |
| xfce4-terminal | 11 | 98 ms | 127 ms | 127 ms | 66.9 ms | 184.3 ms |
| guake | 10 | 102 ms | 130 ms | 130 ms | 87.3 ms | 168.1 ms |
| alacritty | 120 | 8 ms | 9 ms | 9 ms | 9.3 ms | 16.4 ms |
| kitty | 96 | 9 ms | 17 ms | 18 ms | 19.3 ms | 23.0 ms |
| ghostty | 60 | 17 ms | 17 ms | 17 ms | 15.5 ms | 22.9 ms |
| wezterm | 58 | 17 ms | 25 ms | 26 ms | 43.5 ms | 58.9 ms |
| rio | 120 | 8 ms | 9 ms | 9 ms | 20.9 ms | 25.3 ms |

## CPU

![CPU](cpu.png)

| Terminal | Idle | One line every 16 ms | While 40 MiB print | CPU time for 40 MiB |
| --- | ---: | ---: | ---: | ---: |
| waftty | 0.01% | 10.6% | 138% | 0.30 s |
| waftty quick | 0.01% | 10.9% | 148% | 0.26 s |
| xfce4-terminal | 0.00% | 4.1% | 82% | 0.29 s |
| guake | 0.00% | 6.0% | 81% | 0.31 s |
| alacritty | 0.00% | 2.6% | 103% | 0.30 s |
| kitty | 0.03% | 2.4% | 96% | 0.53 s |
| ghostty | 0.30% | 5.3% | 185% | 0.58 s |
| wezterm | 0.00% | 5.3% | 123% | 1.13 s |
| rio | 0.98% | 3.4% | 99% | 0.32 s |

## Latency and startup

![Latency](latency.png)

![Startup](startup.png)

| Terminal | Plain | SGR | Unicode | Latency median | Latency p95 | Startup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 162 MB/s | 247 MB/s | 185 MB/s | 1.0 ms | 1.3 ms | 73 ms |
| waftty quick | 205 MB/s | 246 MB/s | 206 MB/s | 0.8 ms | 0.9 ms | 50 ms |
| xfce4-terminal | 105 MB/s | 112 MB/s | 67 MB/s | 1.2 ms | 1.5 ms | 68 ms |
| guake | 100 MB/s | 108 MB/s | 71 MB/s | 1.0 ms | 1.1 ms | 178 ms |
| alacritty | 124 MB/s | 150 MB/s | 116 MB/s | 3.2 ms | 3.4 ms | 94 ms |
| kitty | 60 MB/s | 109 MB/s | 60 MB/s | 8.6 ms | 12.3 ms | 393 ms |
| ghostty | 170 MB/s | 149 MB/s | 159 MB/s | 24.2 ms | 33.1 ms | 745 ms |
| wezterm | 36 MB/s | 67 MB/s | 38 MB/s | 23.3 ms | 27.4 ms | 144 ms |
| rio | 203 MB/s | 190 MB/s | 135 MB/s | 11.8 ms | 16.7 ms | 179 ms |
