# Terminal benchmark

Scrollback 10000 lines, window [1000, 700], vsync off: False.

| Terminal | Version |
| --- | --- |
| waftty | waftty 0.5.7 |
| waftty quick | waftty 0.5.7 |
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
| waftty | 14.5 MiB | 12.9 MiB | 26.7 MiB | 25.1 MiB | 0.0 MiB | 0 MiB |
| waftty quick | 19.2 MiB | 17.7 MiB | 27.3 MiB | 25.8 MiB | 0.0 MiB | 0 MiB |
| xfce4-terminal | 15.0 MiB | 10.1 MiB | 23.4 MiB | 18.4 MiB | 0.1 MiB | 0 MiB |
| guake | 48.1 MiB | 41.1 MiB | 57.2 MiB | 50.2 MiB | 0.0 MiB | 0 MiB |
| alacritty | 59.3 MiB | 55.4 MiB | 77.9 MiB | 74.0 MiB | 0.0 MiB | 9 MiB |
| kitty | 75.3 MiB | 69.8 MiB | 101.2 MiB | 95.6 MiB | 0.0 MiB | 3 MiB |
| ghostty | 179.5 MiB | 172.2 MiB | 181.5 MiB | 174.2 MiB | 1.0 MiB | 44 MiB |
| wezterm | 133.9 MiB | 129.8 MiB | 162.8 MiB | 158.7 MiB | 0.0 MiB | 3 MiB |
| rio | 143.8 MiB | 140.1 MiB | 165.7 MiB | 162.0 MiB | 0.0 MiB | 14 MiB |

### Where the memory comes from

![Memory under load by source](ram-sources.png)

Each figure is the PSS of the terminal's own processes after 40 MiB of output. Left out are the shell and test commands, and the session bus a run starts for a single-instance terminal with the desktop services on it (the portal, and for xfce4-terminal xfconfd and gvfsd), which a desktop already runs. Private data is heap and other anonymous memory, scrollback included; code and libraries are mapped from files, each shared page divided among the processes that map it; X server pixmaps and GPU memory are held outside the terminal on its behalf and are not in its PSS.

| Terminal | Processes counted (MiB) | Left out (MiB) |
| --- | --- | --- |
| waftty | waftty 26.7 | sleep 0.2 |
| waftty quick | waftty 27.3 | sleep 0.2 |
| xfce4-terminal | xfce4-terminal 23.4 | sleep 0.2 |
| guake | guake 57.2 | sh 0.2, sleep 0.2 |
| alacritty | alacritty 77.9 | sleep 0.2 |
| kitty | kitty 101.2 | sleep 0.2 |
| ghostty | ghostty 181.5 | sleep 0.2 |
| wezterm | wezterm-gui 162.8 | sleep 0.2 |
| rio | rio 165.7 | sleep 0.2 |

| Terminal | Private data (heap, scrollback) | Code and libraries | Shared memory | X server pixmaps | GPU memory | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 17.1 MiB | 8.3 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 26.7 MiB |
| waftty quick | 13.4 MiB | 12.5 MiB | 1.3 MiB | 0.0 MiB | 0.0 MiB | 27.3 MiB |
| xfce4-terminal | 15.1 MiB | 8.2 MiB | 0.1 MiB | 0.1 MiB | 0.0 MiB | 23.4 MiB |
| guake | 36.7 MiB | 20.5 MiB | 0.0 MiB | 0.0 MiB | 0.0 MiB | 57.2 MiB |
| alacritty | 35.1 MiB | 42.8 MiB | 0.0 MiB | 0.0 MiB | 9.0 MiB | 86.9 MiB |
| kitty | 58.8 MiB | 42.4 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 104.2 MiB |
| ghostty | 61.8 MiB | 118.6 MiB | 1.0 MiB | 1.0 MiB | 44.0 MiB | 226.5 MiB |
| wezterm | 57.5 MiB | 105.3 MiB | 0.0 MiB | 0.0 MiB | 3.0 MiB | 165.8 MiB |
| rio | 51.2 MiB | 114.5 MiB | 0.0 MiB | 0.0 MiB | 14.0 MiB | 179.7 MiB |

## Throughput

![Throughput](throughput.png)

## Smoothness under load

![Smoothness](smoothness.png)

| Terminal | Frames/s | Median gap | p99 gap | Longest gap | Echo median | Echo p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 120 | 8 ms | 13 ms | 16 ms | 6.3 ms | 10.8 ms |
| waftty quick | 121 | 8 ms | 11 ms | 15 ms | 6.5 ms | 9.7 ms |
| xfce4-terminal | 10 | 104 ms | 130 ms | 130 ms | 94.0 ms | 169.2 ms |
| guake | 10 | 100 ms | 126 ms | 126 ms | 112.5 ms | 167.2 ms |
| alacritty | 120 | 8 ms | 9 ms | 9 ms | 9.6 ms | 13.3 ms |
| kitty | 96 | 8 ms | 17 ms | 17 ms | 17.7 ms | 23.2 ms |
| ghostty | 60 | 17 ms | 17 ms | 17 ms | 10.4 ms | 16.2 ms |
| wezterm | 59 | 17 ms | 25 ms | 26 ms | 43.0 ms | 56.7 ms |
| rio | 120 | 8 ms | 9 ms | 9 ms | 18.9 ms | 25.0 ms |

## CPU

![CPU](cpu.png)

| Terminal | Idle | While 40 MiB print | CPU time for 40 MiB |
| --- | ---: | ---: | ---: |
| waftty | 0.10% | 141% | 0.34 s |
| waftty quick | 0.10% | 142% | 0.33 s |
| xfce4-terminal | 0.00% | 84% | 0.30 s |
| guake | 0.00% | 84% | 0.30 s |
| alacritty | 0.00% | 103% | 0.31 s |
| kitty | 0.20% | 2% | 0.73 s |
| ghostty | 0.40% | 36% | 0.49 s |
| wezterm | 0.10% | 120% | 1.10 s |
| rio | 0.40% | 93% | 0.32 s |

## Latency and startup

![Latency](latency.png)

![Startup](startup.png)

| Terminal | Plain | SGR | Unicode | Latency median | Latency p95 | Startup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 170 MB/s | 179 MB/s | 167 MB/s | 0.8 ms | 1.1 ms | 63 ms |
| waftty quick | 193 MB/s | 181 MB/s | 167 MB/s | 0.9 ms | 1.4 ms | 47 ms |
| xfce4-terminal | 113 MB/s | 115 MB/s | 69 MB/s | 1.1 ms | 1.3 ms | 66 ms |
| guake | 104 MB/s | 139 MB/s | 69 MB/s | 0.8 ms | 1.0 ms | 177 ms |
| alacritty | 115 MB/s | 153 MB/s | 112 MB/s | 2.7 ms | 2.9 ms | 88 ms |
| kitty | 60 MB/s | 106 MB/s | 60 MB/s | 8.9 ms | 12.3 ms | 383 ms |
| ghostty | 167 MB/s | 147 MB/s | 161 MB/s | 18.4 ms | 25.8 ms | 557 ms |
| wezterm | 36 MB/s | 67 MB/s | 38 MB/s | 21.4 ms | 25.1 ms | 130 ms |
| rio | 222 MB/s | 210 MB/s | 124 MB/s | 12.1 ms | 17.0 ms | 168 ms |
