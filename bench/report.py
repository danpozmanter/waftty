"""Charts and a RESULTS.md from a benchmark run's results file.

    uv run report.py linux|mac [--results FILE] [--out DIR]

Reads <system>/results.json and writes <system>/report unless --results and
--out name others.
"""

import argparse
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from timing import duration

MB = 20 * 1024 * 1024 / 1e6  # each input is 20 MiB
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
# Validated categorical order (CVD pass); value labels and tables give relief
# for the third color's contrast warning.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
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
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=30 if n > 1 else 12)
    if n > 1:
        # Above the plot, where no bar can run under it.
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=n, fontsize=9,
                  handlelength=1.2, borderaxespad=0.2)
    if note:
        fig.text(0.01, 0.01, note, fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 1))
    fig.savefig(out / f"{name}.png", dpi=150)
    plt.close(fig)


def stacked(out, order, name, title, unit, parts, fmt, note):
    """One horizontal bar per terminal split into `parts`, (label, values) in
    palette order, with each bar's total at its end."""
    fig, ax = plt.subplots(figsize=(9, 0.55 * len(order) + 2.0))
    starts = [0.0] * len(order)
    for i, (label, vals) in enumerate(parts):
        # A surface-colored edge leaves a 2px gap between touching segments.
        ax.barh(range(len(order)), vals, left=starts, height=0.62, color=PALETTE[i], label=label,
                edgecolor=SURFACE, linewidth=2, zorder=2)
        starts = [a + b for a, b in zip(starts, vals)]
    top = max(starts) or 1
    for k, total in enumerate(starts):
        ax.text(total + top * 0.012, k, fmt(total), va="center", fontsize=9, color=INK)
    ax.set_yticks(range(len(order)), order)
    ax.invert_yaxis()
    ax.set_xlim(0, top * 1.12)
    ax.set_xlabel(unit)
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=30)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(parts), fontsize=8,
              handlelength=1.2, columnspacing=1.2, borderaxespad=0.2)
    fig.text(0.01, 0.01, note, fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
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
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("system", choices=["linux", "mac"])
    ap.add_argument("--results", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    here = Path(__file__).resolve().parent / a.system
    a.results = a.results or here / "results.json"
    a.out = a.out or here / "report"
    res = json.loads(a.results.read_text())
    meta = res.pop("_meta", {})
    # macOS has no proportional set size: memory there is each process's
    # physical footprint, the figure Activity Monitor shows.
    macos = meta.get("platform") == "macos"
    memory_key = "footprint" if macos else "pss"
    order = list(res)
    a.out.mkdir(parents=True, exist_ok=True)

    # A run with --only or --terminals updates part of a file, and an
    # interrupted run leaves a terminal with the measures it finished, so each
    # chart and table shows the terminals that have its measures.
    def having(*keys):
        return [t for t in order if all(k in res[t] for k in keys)]

    memory = having("ram_idle", "ram_heavy")
    cpus = having("cpu_idle", "cpu_load")
    rates = having("tp_plain", "tp_sgr", "tp_unicode")
    streams = having("streaming")
    keys = having("latency", "streaming")
    starts = having("startup")
    summary = having("tp_plain", "tp_sgr", "tp_unicode", "latency", "startup")

    # Memory is one run's own figure, the low median, so it matches the split
    # below for any number of runs.
    def mem(t, phase, key=memory_key):
        return statistics.median_low(r[key] for r in res[t][f"ram_{phase}"])

    def mbps(t, name):
        return MB / (med(res[t][f"tp_{name}"]) / 1000)

    hbars(a.out, memory, "ram",
          f"Memory ({'physical footprint' if macos else 'PSS'}), idle and after 40 MiB of output",
          "MiB (lower is better)",
          [("Idle", [mem(t, "idle") for t in memory]),
           ("Heavy: 20 MiB plain + 20 MiB colored text", [mem(t, "heavy") for t in memory])],
          lambda v: f"{v:.1f}",
          note="Median of launches; terminal processes only (shell excluded).")

    # Under load, where each terminal's memory sits. Older results lack the split.
    split = [t for t in memory if all("kinds" in r for r in res[t]["ram_heavy"])]

    # The split is of one run, the one whose PSS is the median, so its parts add
    # up to that run's total; medians taken part by part need not.
    def heavy(t, pick):
        runs = sorted(res[t]["ram_heavy"], key=lambda r: r["pss"])
        return pick(runs[(len(runs) - 1) // 2])

    sources = [("Private data (heap, scrollback)", lambda r: r["kinds"]["anon"]),
               ("Code and libraries", lambda r: r["kinds"]["file"]),
               ("Shared memory", lambda r: r["kinds"]["shmem"]),
               ("X server pixmaps", lambda r: r.get("xserver", 0.0)),
               ("GPU memory", lambda r: r.get("vram", 0.0))]
    if split:
        stacked(a.out, split, "ram-sources", "Where memory goes under load (after 40 MiB of output)",
                "MiB (lower is better)",
                [(label, [heavy(t, pick) for t in split]) for label, pick in sources],
                lambda v: f"{v:.1f}",
                note="Median of launches. The terminal's PSS split by kind, plus what the X server "
                     "and the GPU hold for it.")

    def cpu(t, key, field=None):
        values = [v[field] if field else v for v in res[t].get(key, [])]
        return med(values) if values else 0.0

    panels(a.out, cpus, "cpu", "CPU use",
           [("Idle", "% of one core", [cpu(t, "cpu_idle") for t in cpus], lambda v: f"{v:.1f}"),
            ("Printing 40 MiB", "seconds of CPU", [cpu(t, "cpu_load", "seconds") for t in cpus],
             lambda v: f"{v:.2f}")],
           note="User and system time of the terminal's processes; lower is better.")
    hbars(a.out, rates, "throughput", "Output throughput", "MB/s (higher is better)",
          [(label, [mbps(t, key) for t in rates])
           for label, key in (("Plain ASCII", "plain"), ("256-color SGR", "sgr"),
                              ("Unicode mix", "unicode"))],
          lambda v: f"{v:.0f}", note="Time for `cat` of a 20 MiB file to finish in the terminal.")

    def streaming(t, key):
        return res[t].get("streaming", {}).get(key, [])

    def fps(t):
        gaps = streaming(t, "gaps")
        return 1000 * len(gaps) / sum(gaps) if gaps else 0.0

    hbars(a.out, keys, "latency", "Keystroke to screen latency", "ms (lower is better)",
          [("Idle terminal", [med(res[t]["latency"]) for t in keys]),
           ("While output streams", [med(streaming(t, "latency") or [0]) for t in keys])],
          lambda v: f"{v:.1f}",
          note=("Median from a Quartz key event until a capture of the window shows the echo."
                if macos else "Median from an X key press until the echoed character's pixels change."))
    # Frame timing comes from X Damage, which macOS has no counterpart to.
    streams = [t for t in streams if streaming(t, "gaps")]
    if streams:
        panels(a.out, streams, "smoothness", "Frames while colored output streams",
               [("Frames per second", "higher is better", [fps(t) for t in streams],
                 lambda v: f"{v:.0f}"),
                ("99th percentile frame gap", "ms (lower is better)",
                 [pct(streaming(t, "gaps") or [0], 0.99) for t in streams], lambda v: f"{v:.0f}")],
               note="X Damage reports during 4 s of a flood, timed by the X server.")
    hbars(a.out, starts, "startup", "Startup: launch to a screenful of text on screen",
          "ms (lower is better)", [("Median", [med(res[t]["startup"]) for t in starts])],
          lambda v: f"{v:.0f}", note="Median of 10 launches.")

    lines = ["# Terminal benchmark", ""]
    versions = meta.get("versions", {})
    setup = (f"macOS {meta.get('os', '')}, scrollback {meta.get('scrollback')} lines, "
             f"window {meta.get('window')}." if macos else
             f"Scrollback {meta.get('scrollback')} lines, window {meta.get('window')}, "
             f"vsync off: {meta.get('vsync_off')}.")
    # Older results do not record how long their run took.
    if "run_seconds" in meta:
        setup += f" The run took {duration(meta['run_seconds'])}, finishing {meta['finished']}."
    lines += [setup, ""]
    lines += [row(["Terminal", "Version"]), row(["---", "---"])]
    lines += [row([t, versions.get(t, "")]) for t in order] + [""]
    lines += ["## Memory", "", "![Memory](ram.png)", ""]
    if macos:
        lines += [("Physical footprint is the memory a process dirtied, compressed memory "
                   "included, the figure Activity Monitor shows as Memory; RSS also counts the "
                   "shared library pages it touches. Terminal processes only, shell excluded."),
                  ""]
        lines += [row(["Terminal", "Idle footprint", "Idle RSS", "Heavy footprint", "Heavy RSS"]),
                  row(["---"] + ["---:"] * 4)]
        lines += [row([t, f"{mem(t, 'idle'):.1f} MiB", f"{mem(t, 'idle', 'rss'):.1f} MiB",
                       f"{mem(t, 'heavy'):.1f} MiB", f"{mem(t, 'heavy', 'rss'):.1f} MiB"])
                  for t in memory]
    else:
        lines += [("PSS shares each library page among the processes that map it; USS is the "
                   "terminal's own. X server pixmaps and GPU memory are held elsewhere on the "
                   "terminal's behalf."), ""]
        lines += [row(["Terminal", "Idle PSS", "Idle USS", "Heavy PSS", "Heavy USS",
                       "X server pixmaps", "GPU"]),
                  row(["---"] + ["---:"] * 6)]
    for t in [] if macos else memory:
        held = [r["xserver"] for r in res[t]["ram_idle"] if "xserver" in r]
        lines.append(row([t, f"{mem(t, 'idle'):.1f} MiB", f"{mem(t, 'idle', 'uss'):.1f} MiB",
                          f"{mem(t, 'heavy'):.1f} MiB", f"{mem(t, 'heavy', 'uss'):.1f} MiB",
                          f"{med(held):.1f} MiB" if held else "-",
                          f"{mem(t, 'idle', 'vram'):.0f} MiB"]))
    if split:
        lines += ["", "### Where the memory comes from", "", "![Memory under load by source](ram-sources.png)", ""]
        lines += [("Each figure is the PSS of the terminal's own processes after 40 MiB of output. "
                  "Left out are the shell and test commands, and the session bus a run starts "
                  "for a single-instance terminal with the desktop services on it (the portal, "
                  "and for xfce4-terminal xfconfd and gvfsd), which a desktop already runs. "
                  "Private data "
                  "is heap and other anonymous memory, scrollback included; code and libraries "
                  "are mapped from files, each shared page divided among the processes that map "
                  "it; X server pixmaps and GPU memory are held outside the terminal on its behalf "
                  "and are not in its PSS."), ""]

        def named(t, field):
            names = {n for r in res[t]["ram_heavy"] for n in r[field]}
            return ", ".join(f"{n} {heavy(t, lambda r, n=n: r[field].get(n, 0.0)):.1f}"
                             for n in sorted(names)) or "-"

        lines += [row(["Terminal", "Processes counted (MiB)", "Left out (MiB)"]),
                  row(["---", "---", "---"])]
        lines += [row([t, named(t, "processes"), named(t, "left_out")]) for t in split]
        lines += ["", row(["Terminal"] + [label for label, _ in sources] + ["Total"]),
                  row(["---"] + ["---:"] * (len(sources) + 1))]
        for t in split:
            parts = [heavy(t, pick) for _, pick in sources]
            lines.append(row([t] + [f"{v:.1f} MiB" for v in parts] + [f"{sum(parts):.1f} MiB"]))
    lines += ["", "## Throughput", "", "![Throughput](throughput.png)", ""]
    if streams:
        lines += ["## Smoothness under load", "", "![Smoothness](smoothness.png)", ""]
        lines += [row(["Terminal", "Frames/s", "Median gap", "p99 gap", "Longest gap",
                       "Echo median", "Echo p95"]),
                  row(["---"] + ["---:"] * 6)]
    for t in streams:
        gaps, echo = streaming(t, "gaps"), streaming(t, "latency")
        if not gaps:
            lines.append(row([t] + ["-"] * 6))
            continue
        lines.append(row([t, f"{fps(t):.0f}", f"{med(gaps):.0f} ms", f"{pct(gaps, 0.99):.0f} ms",
                          f"{max(gaps):.0f} ms", f"{med(echo):.1f} ms",
                          f"{pct(echo, 0.95):.1f} ms"]))
    lines += ["", "## CPU", "", "![CPU](cpu.png)", ""]
    lines += [row(["Terminal", "Idle", "While 40 MiB print", "CPU time for 40 MiB"]),
              row(["---"] + ["---:"] * 3)]
    for t in cpus:
        lines.append(row([t, f"{cpu(t, 'cpu_idle'):.2f}%",
                          f"{cpu(t, 'cpu_load', 'percent'):.0f}%",
                          f"{cpu(t, 'cpu_load', 'seconds'):.2f} s"]))
    lines += ["", "## Latency and startup", "", "![Latency](latency.png)", "",
              "![Startup](startup.png)", ""]
    lines += [row(["Terminal", "Plain", "SGR", "Unicode", "Latency median", "Latency p95",
                   "Startup"]),
              row(["---"] + ["---:"] * 6)]
    for t in summary:
        lat = res[t]["latency"]
        lines.append(row([t] + [f"{mbps(t, k):.0f} MB/s" for k in ("plain", "sgr", "unicode")]
                         + [f"{med(lat):.1f} ms", f"{pct(lat, 0.95):.1f} ms",
                            f"{med(res[t]['startup']):.0f} ms"]))
    (a.out / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(a.out / "RESULTS.md")


if __name__ == "__main__":
    main()
