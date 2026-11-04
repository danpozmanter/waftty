# Terminal benchmark

Scrollback 10000 lines, window [1000, 700], vsync off: False.

| Terminal | Version |
| --- | --- |
| waftty | waftty 0.3.0 |
| xfce4-terminal | xfce4-terminal 1.1.3 (Xfce 4.18) |
| alacritty | alacritty 0.13.2 |
| ghostty | Ghostty 1.4.1-main+93967b7f9 |
| wezterm | wezterm 20240203-110809-5046fc22 |

## Memory

![Memory](ram.png)

PSS shares each library page among the processes that map it; USS is the terminal's own. X server pixmaps and GPU memory are held elsewhere on the terminal's behalf.

| Terminal | Idle PSS | Idle USS | Heavy PSS | Heavy USS | X server pixmaps | GPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 16.1 MB | 14.4 MB | 29.6 MB | 27.9 MB | 0.0 MiB | 0 MiB |
| xfce4-terminal | 16.2 MB | 11.4 MB | 26.0 MB | 21.2 MB | 0.1 MiB | 0 MiB |
| alacritty | 61.7 MB | 55.2 MB | 89.5 MB | 82.9 MB | 0.0 MiB | 9 MiB |
| ghostty | 178.5 MB | 170.8 MB | 179.9 MB | 172.2 MB | 1.0 MiB | 44 MiB |
| wezterm | 132.3 MB | 127.7 MB | 161.2 MB | 156.6 MB | 0.0 MiB | 3 MiB |

## Throughput

![Throughput](throughput.png)

## Smoothness under load

![Smoothness](smoothness.png)

| Terminal | Frames/s | Median gap | p99 gap | Longest gap | Echo median | Echo p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 65 | 16 ms | 19 ms | 20 ms | 10.9 ms | 16.1 ms |
| xfce4-terminal | 10 | 98 ms | 133 ms | 133 ms | 56.3 ms | 108.1 ms |
| alacritty | 120 | 8 ms | 9 ms | 10 ms | 6.9 ms | 10.8 ms |
| ghostty | 60 | 17 ms | 17 ms | 18 ms | 16.6 ms | 23.2 ms |
| wezterm | 55 | 17 ms | 25 ms | 26 ms | 12.0 ms | 19.4 ms |

## CPU

![CPU](cpu.png)

| Terminal | Idle | While 40 MB print | CPU time for 40 MB |
| --- | ---: | ---: | ---: |
| waftty | 0.00% | 110% | 0.28 s |
| xfce4-terminal | 0.00% | 80% | 0.28 s |
| alacritty | 0.00% | 104% | 0.35 s |
| ghostty | 0.40% | 201% | 0.60 s |
| wezterm | 0.20% | 126% | 1.15 s |

## Latency and startup

![Latency](latency.png)

![Startup](startup.png)

| Terminal | Plain | SGR | Unicode | Latency median | Latency p95 | Startup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| waftty | 161 MB/s | 145 MB/s | 110 MB/s | 1.0 ms | 1.1 ms | 62 ms |
| xfce4-terminal | 88 MB/s | 136 MB/s | 69 MB/s | 1.2 ms | 1.5 ms | 90 ms |
| alacritty | 106 MB/s | 147 MB/s | 107 MB/s | 1.9 ms | 2.4 ms | 102 ms |
| ghostty | 162 MB/s | 147 MB/s | 155 MB/s | 19.3 ms | 25.8 ms | 276 ms |
| wezterm | 36 MB/s | 66 MB/s | 38 MB/s | 21.9 ms | 24.9 ms | 83 ms |
