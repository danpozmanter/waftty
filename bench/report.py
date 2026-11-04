"""Charts and a RESULTS.md from a `bench.py run` results file.

    uv run report.py [--results FILE] [--out DIR]
"""

import argparse
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

MB = 20 * 1024 * 1024 / 1e6  # each input is 20 MiB
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
# Validated categorical order (CVD pass); value labels and tables give relief
# for the third color's contrast warning.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a"]
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": INK,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})
med = statistics.median


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(q * (len(xs) - 1)))]


def hbars(out, order, name, title, unit, series, fmt, note=None, extra=None, ends=None):
    """Horizontal bars, terminals top to bottom; `series` is (label, values) per color."""
    n = len(series)
    h = 0.8 / n
    fig, ax = plt.subplots(figsize=(8, 0.62 * len(order) * max(1, n * 0.75) + 1.3))
    ends = ends or [0] * len(order)
    top = max([v for _, vals in series for v in vals] + ends) or 1
    for i, (label, vals) in enumerate(series):
        ys = [k + (i - (n - 1) / 2) * h for k in range(len(order))]
        ax.barh(ys, vals, height=h - 0.04, color=PALETTE[i], label=label, zorder=2)
        for y, v, end in zip(ys, vals, ends):
            ax.text(max(v, end) + top * 0.015, y, fmt(v), va="center", fontsize=9, color=INK)
    if extra:
        extra(ax)
    ax.set_yticks(range(len(order)), order)
    ax.invert_yaxis()
    ax.set_xlim(0, top * 1.18)
    ax.set_xlabel(unit)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12)
    if n > 1:
        ax.legend(frameon=False, loc="lower right", fontsize=9)
    if note:
        fig.text(0.01, 0.01, note, fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 1))
    fig.savefig(out / f"{name}.png", dpi=150)
    plt.close(fig)


def panels(out, order, name, title, parts, note):
    """Side-by-side horizontal bars, one panel per measure, each on its own axis."""
    fig, axes = plt.subplots(1, len(parts), figsize=(10, 0.62 * len(order) + 1.6), sharey=True)
    for ax, (label, unit, vals, fmt) in zip(axes, parts):
        top = max(vals) or 1
        ax.barh(range(len(order)), vals, height=0.6, color=PALETTE[0], zorder=2)
        for k, v in enumerate(vals):
            ax.text(v + top * 0.03, k, fmt(v), va="center", fontsize=9, color=INK)
        ax.set_yticks(range(len(order)), order)
        ax.set_xlim(0, top * 1.25)
        ax.set_xlabel(unit)
        ax.set_title(label, loc="left", fontsize=10, color=MUTED)
        ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].invert_yaxis()
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK)
    fig.text(0.01, 0.01, note, fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(out / f"{name}.png", dpi=150)
    plt.close(fig)


def row(cells):
    return "| " + " | ".join(cells) + " |"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=Path("results.json"))
    ap.add_argument("--out", type=Path, default=Path("report"))
    a = ap.parse_args()
    res = json.loads(a.results.read_text())
    meta = res.pop("_meta", {})
    order = list(res)
    a.out.mkdir(parents=True, exist_ok=True)

    def mem(t, phase, key="pss"):
        return med(r[key] for r in res[t][f"ram_{phase}"])

    def mbps(t, name):
        return MB / (med(res[t][f"tp_{name}"]) / 1000)

    hbars(a.out, order, "ram", "Memory (PSS), idle and after 40 MB of output",
          "MB (lower is better)",
          [("Idle", [mem(t, "idle") for t in order]),
           ("Heavy: 20 MB plain + 20 MB colored text", [mem(t, "heavy") for t in order])],
          lambda v: f"{v:.1f}",
          note="Median of launches; terminal processes only (shell excluded).")

    def cpu(t, key, field=None):
        values = [v[field] if field else v for v in res[t].get(key, [])]
        return med(values) if values else 0.0

    panels(a.out, order, "cpu", "CPU use",
           [("Idle", "% of one core", [cpu(t, "cpu_idle") for t in order], lambda v: f"{v:.1f}"),
            ("Printing 40 MB", "seconds of CPU", [cpu(t, "cpu_load", "seconds") for t in order],
             lambda v: f"{v:.2f}")],
           note="User and system time of the terminal's processes; lower is better.")
    hbars(a.out, order, "throughput", "Output throughput", "MB/s (higher is better)",
          [(label, [mbps(t, key) for t in order])
           for label, key in (("Plain ASCII", "plain"), ("256-color SGR", "sgr"),
                              ("Unicode mix", "unicode"))],
          lambda v: f"{v:.0f}", note="Time for `cat` of a 20 MiB file to finish in the terminal.")

    def streaming(t, key):
        return res[t].get("streaming", {}).get(key, [])

    def fps(t):
        gaps = streaming(t, "gaps")
        return 1000 * len(gaps) / sum(gaps) if gaps else 0.0

    hbars(a.out, order, "latency", "Keystroke to screen latency", "ms (lower is better)",
          [("Idle terminal", [med(res[t]["latency"]) for t in order]),
           ("While output streams", [med(streaming(t, "latency") or [0]) for t in order])],
          lambda v: f"{v:.1f}",
          note="Median from an X key press until the echoed character's pixels change.")
    panels(a.out, order, "smoothness", "Frames while colored output streams",
           [("Frames per second", "higher is better", [fps(t) for t in order],
             lambda v: f"{v:.0f}"),
            ("99th percentile frame gap", "ms (lower is better)",
             [pct(streaming(t, "gaps") or [0], 0.99) for t in order], lambda v: f"{v:.0f}")],
           note="X Damage reports during 4 s of a flood, timed by the X server.")
    hbars(a.out, order, "startup", "Startup: launch to first line of text on screen",
          "ms (lower is better)", [("Median", [med(res[t]["startup"]) for t in order])],
          lambda v: f"{v:.0f}", note="Median of 10 launches.")

    lines = ["# Terminal benchmark", ""]
    versions = meta.get("versions", {})
    lines += [f"Scrollback {meta.get('scrollback')} lines, window {meta.get('window')}, "
              f"vsync off: {meta.get('vsync_off')}.", ""]
    lines += [row(["Terminal", "Version"]), row(["---", "---"])]
    lines += [row([t, versions.get(t, "")]) for t in order] + [""]
    lines += ["## Memory", "", "![Memory](ram.png)", ""]
    lines += ["PSS shares each library page among the processes that map it; USS is the "
              "terminal's own. X server pixmaps and GPU memory are held elsewhere on the "
              "terminal's behalf.", ""]
    lines += [row(["Terminal", "Idle PSS", "Idle USS", "Heavy PSS", "Heavy USS",
                   "X server pixmaps", "GPU"]),
              row(["---"] + ["---:"] * 6)]
    for t in order:
        held = [r["xserver"] for r in res[t]["ram_idle"] if "xserver" in r]
        lines.append(row([t, f"{mem(t, 'idle'):.1f} MB", f"{mem(t, 'idle', 'uss'):.1f} MB",
                          f"{mem(t, 'heavy'):.1f} MB", f"{mem(t, 'heavy', 'uss'):.1f} MB",
                          f"{med(held):.1f} MiB" if held else "-",
                          f"{mem(t, 'idle', 'vram'):.0f} MiB"]))
    lines += ["", "## Throughput", "", "![Throughput](throughput.png)", ""]
    lines += ["## Smoothness under load", "", "![Smoothness](smoothness.png)", ""]
    lines += [row(["Terminal", "Frames/s", "Median gap", "p99 gap", "Longest gap",
                   "Echo median", "Echo p95"]),
              row(["---"] + ["---:"] * 6)]
    for t in order:
        gaps, echo = streaming(t, "gaps"), streaming(t, "latency")
        if not gaps:
            lines.append(row([t] + ["-"] * 6))
            continue
        lines.append(row([t, f"{fps(t):.0f}", f"{med(gaps):.0f} ms", f"{pct(gaps, 0.99):.0f} ms",
                          f"{max(gaps):.0f} ms", f"{med(echo):.1f} ms",
                          f"{pct(echo, 0.95):.1f} ms"]))
    lines += ["", "## CPU", "", "![CPU](cpu.png)", ""]
    lines += [row(["Terminal", "Idle", "While 40 MB print", "CPU time for 40 MB"]),
              row(["---"] + ["---:"] * 3)]
    for t in order:
        lines.append(row([t, f"{cpu(t, 'cpu_idle'):.2f}%",
                          f"{cpu(t, 'cpu_load', 'percent'):.0f}%",
                          f"{cpu(t, 'cpu_load', 'seconds'):.2f} s"]))
    lines += ["", "## Latency and startup", "", "![Latency](latency.png)", "",
              "![Startup](startup.png)", ""]
    lines += [row(["Terminal", "Plain", "SGR", "Unicode", "Latency median", "Latency p95",
                   "Startup"]),
              row(["---"] + ["---:"] * 6)]
    for t in order:
        lat = res[t]["latency"]
        lines.append(row([t] + [f"{mbps(t, k):.0f} MB/s" for k in ("plain", "sgr", "unicode")]
                         + [f"{med(lat):.1f} ms", f"{pct(lat, 0.95):.1f} ms",
                            f"{med(res[t]['startup']):.0f} ms"]))
    (a.out / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(a.out / "RESULTS.md")


if __name__ == "__main__":
    main()
