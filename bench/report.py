"""Charts and a RESULTS.md from a benchmark run's results file.

    uv run report.py linux|mac [--results FILE] [--out DIR]

Reads <system>/results.json and writes <system>/report unless --results and
--out name others.
"""

import argparse
import json
import re
import statistics
import sys
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
# What each system's memory chart compares, and the name its harness records.
MEMORY = {"linux": "pss", "mac": "footprint"}
PLATFORM = {"linux": "linux", "mac": "macos"}
CHARTS = ("ram", "ram-sources", "cpu", "throughput", "latency", "smoothness", "startup")
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": INK,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})
med = statistics.median


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(q * (len(xs) - 1)))]


# A version is the first word of a `--version` line that starts with a digit.
VERSION = re.compile(r"(?<!\S)\d\S*")


def short_version(text):
    """The version number in a terminal's `--version` line, or the line itself."""
    found = VERSION.search(text)
    return found.group() if found else text.strip()


def drawn(value, fmt):
    """The length of `value`'s bar: none when its label reads zero, so a figure
    shown as 0.0 never looks like more."""
    try:
        return 0.0 if float(fmt(value)) == 0 else value
    except ValueError:
        return value


def number(value, spec):
    """`value` formatted by `spec`, with no sign when it rounds to zero."""
    text = f"{value:{spec}}"
    return text[1:] if text.startswith("-") and float(text) == 0 else text


def heading(fig, ax, title, fontsize):
    """Puts `title` at the figure's top left with the legend of `ax`'s bars under
    it, in as many columns as fit the figure's width, and answers the share of
    the figure's height the two take."""
    height = fig.get_figheight()
    fig.text(0.01, 1 - 0.12 / height, title, fontsize=12, color=INK, va="top")
    used = 0.5
    handles, labels = ax.get_legend_handles_labels()
    if len(handles) > 1:
        renderer = fig.canvas.get_renderer()
        for ncol in range(len(handles), 0, -1):
            legend = fig.legend(handles, labels, frameon=False, loc="upper left",
                                bbox_to_anchor=(0.005, 1 - used / height), ncol=ncol,
                                fontsize=fontsize, handlelength=1.2, columnspacing=1.2,
                                borderaxespad=0.2)
            box = legend.get_window_extent(renderer)
            if box.x1 <= fig.bbox.x1 - 0.01 * fig.bbox.width or ncol == 1:
                break
            legend.remove()
        used += box.height / fig.dpi + 0.05
    return used / height


def hbars(out, order, name, title, unit, series, fmt, note=None, extra=None, ends=None):
    """Horizontal bars, terminals top to bottom; `series` is (label, values) per color."""
    if not order:
        return
    n = len(series)
    h = 0.8 / n
    fig, ax = plt.subplots(figsize=(8, 0.62 * len(order) * max(1, n * 0.75) + 1.3))
    ends = ends or [0] * len(order)
    series = [(label, [drawn(v, fmt) for v in vals]) for label, vals in series]
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
    # Above the plot, where no bar can run under it.
    top = heading(fig, ax, title, 9)
    if note:
        fig.text(0.01, 0.01, note, fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03 if note else 0, 1, 1 - top))
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
    top = heading(fig, ax, title, 8)
    fig.text(0.01, 0.01, note, fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1 - top))
    fig.savefig(out / f"{name}.png", dpi=150)
    plt.close(fig)


def panels(out, order, name, title, parts, note):
    """Side-by-side horizontal bars, one panel per measure, each on its own axis.
    A value of None is a measure that terminal has not had taken; a panel with
    nothing but those is left out."""
    parts = [part for part in parts if any(v is not None for v in part[2])]
    if not order or not parts:
        return
    fig, axes = plt.subplots(1, len(parts), figsize=(10, 0.62 * len(order) + 1.6), sharey=True,
                             squeeze=False)
    axes = axes[0]
    for ax, (label, unit, vals, fmt) in zip(axes, parts):
        vals = [None if v is None else drawn(v, fmt) for v in vals]
        top = max(v for v in vals if v is not None) or 1
        measured = [(k, v) for k, v in enumerate(vals) if v is not None]
        ax.barh([k for k, _ in measured], [v for _, v in measured], height=0.6, color=PALETTE[0],
                zorder=2)
        for k, v in enumerate(vals):
            if v is None:
                ax.text(0, k, " not measured", va="center", fontsize=9, color=MUTED)
            else:
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


def mib(value, places=1):
    return "-" if value is None else f"{value:.{places}f} MiB"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("system", choices=["linux", "mac"])
    ap.add_argument("--results", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    here = Path(__file__).resolve().parent / a.system
    a.results = a.results or here / "results.json"
    a.out = a.out or here / "report"
    measure = f"uv run {a.system}/bench.py run"
    try:
        res = json.loads(a.results.read_text())
    except FileNotFoundError:
        raise SystemExit(f"{a.results} does not exist: take the results with `{measure}`")
    except json.JSONDecodeError as e:
        raise SystemExit(f"{a.results} is not valid JSON ({e}): take the results again with `{measure}`")
    meta = res.pop("_meta", {})
    versions = meta.get("versions", {})

    # Charts name each terminal with the version the run measured beneath it.
    def ticks(terminals):
        return [f"{t}\n{short_version(versions[t])}" if versions.get(t) else t for t in terminals]

    if meta.get("platform", PLATFORM[a.system]) != PLATFORM[a.system]:
        raise SystemExit(f"{a.results} holds results from {meta['platform']}, and this is the "
                         f"{a.system} report: name the system they were taken on")
    if not res:
        raise SystemExit(f"{a.results} holds no measurements: take them with `{measure}`")
    # macOS has no proportional set size: memory there is each process's
    # physical footprint, the figure Activity Monitor shows. The two count
    # shared pages differently, so a report compares only its system's own.
    macos = a.system == "mac"
    memory_key = MEMORY[a.system]
    order = list(res)
    a.out.mkdir(parents=True, exist_ok=True)
    # A chart this run has no data for must not survive from an earlier one.
    for chart in CHARTS:
        (a.out / f"{chart}.png").unlink(missing_ok=True)

    # A run with --only or --terminals updates part of a file, and an
    # interrupted run leaves a terminal with the measures it finished, so each
    # chart and table shows the terminals that have its measures.
    def having(*keys):
        return [t for t in order if all(res[t].get(k) for k in keys)]

    memory = having("ram_idle", "ram_heavy")
    rates = having("tp_plain", "tp_sgr", "tp_unicode")
    streams = having("streaming")
    keys = having("latency", "streaming")
    starts = having("startup")
    summary = having("tp_plain", "tp_sgr", "tp_unicode", "latency", "startup")

    for t in memory:
        for phase in ("ram_idle", "ram_heavy"):
            if any(memory_key not in r for r in res[t][phase]):
                raise SystemExit(
                    f"{a.results}: a {phase} sample of {t} has no {memory_key}, the figure the "
                    f"{a.system} report compares. Results from another system belong in that "
                    f"system's report; otherwise measure again with `{measure} --only ram`")

    # Memory is one run's own figure, the low median, so it matches the split
    # below for any number of runs. Older results may lack the secondary figures.
    def mem(t, phase, key=memory_key):
        values = [r[key] for r in res[t][f"ram_{phase}"] if key in r]
        return statistics.median_low(values) if values else None

    # The same figure read again once a cursor that rests has, which older
    # results lack.
    def rested(t, phase, key=memory_key):
        values = [r["rested"][key] for r in res[t][f"ram_{phase}"]
                  if key in r.get("rested", {})]
        return statistics.median_low(values) if values else None

    def mbps(t, name):
        return MB / (med(res[t][f"tp_{name}"]) / 1000)

    hbars(a.out, ticks(memory), "ram",
          f"Memory ({'physical footprint' if macos else 'PSS'}), idle and after 40 MiB of output",
          "MiB (lower is better)",
          [("Idle", [mem(t, "idle") for t in memory]),
           ("Heavy: 20 MiB plain + 20 MiB colored text", [mem(t, "heavy") for t in memory])]
          + ([("Heavy, 13 s after the output (cursor rested)",
               [rested(t, "heavy") for t in memory])]
             if all(rested(t, "heavy") is not None for t in memory) else []),
          lambda v: f"{v:.1f}",
          note="Median of launches; terminal processes only (shell excluded).")

    # Under load, where each terminal's memory sits. Older results lack the split.
    split = [t for t in memory if all("kinds" in r for r in res[t]["ram_heavy"])]

    # The split is of one run, the one whose PSS is the median, so its parts add
    # up to that run's total; medians taken part by part need not.
    def heavy(t, pick):
        runs = sorted(res[t]["ram_heavy"], key=lambda r: r[memory_key])
        return pick(runs[(len(runs) - 1) // 2])

    sources = [("Private data (heap, scrollback)", lambda r: r["kinds"]["anon"]),
               ("Code and libraries", lambda r: r["kinds"]["file"]),
               ("Shared memory", lambda r: r["kinds"]["shmem"]),
               ("X server pixmaps", lambda r: r.get("xserver", 0.0)),
               ("GPU memory", lambda r: r.get("vram", 0.0))]
    if split:
        stacked(a.out, ticks(split), "ram-sources", "Where memory goes under load (after 40 MiB of output)",
                "MiB (lower is better)",
                [(label, [heavy(t, pick) for t in split]) for label, pick in sources],
                lambda v: f"{v:.1f}",
                note="Median of launches. The terminal's PSS split by kind, plus what the X server "
                     "and the GPU hold for it.")

    def cpu(t, key, field=None):
        values = [v[field] if field else v for v in res[t].get(key, []) if not field or field in v]
        return med(values) if values else None

    # The heavy memory runs print the same 40 MiB and time the same span as the
    # CPU runs, so their seconds are that measure. Their idle counterpart spans
    # no idle period, and idle CPU comes only from `cpu_idle`.
    def print_seconds(t):
        seconds = cpu(t, "cpu_load", "seconds")
        return cpu(t, "ram_heavy", "cpu") if seconds is None else seconds

    cpus = [t for t in order
            if any(v is not None for v in (cpu(t, "cpu_idle"), print_seconds(t), cpu(t, "cpu_lines")))]
    borrowed = [t for t in cpus if cpu(t, "cpu_load", "seconds") is None and print_seconds(t) is not None]
    idle_missing = [t for t in cpus if cpu(t, "cpu_idle") is None]
    cpu_note = "User and system time of the terminal's processes; lower is better."
    if borrowed:
        cpu_note += " CPU seconds for terminals without a CPU run come from their heavy memory runs."
    panels(a.out, ticks(cpus), "cpu", "CPU use",
           [("Idle", "% of one core", [cpu(t, "cpu_idle") for t in cpus], lambda v: number(v, ".1f")),
            ("One colored line every 16 ms", "% of one core", [cpu(t, "cpu_lines") for t in cpus],
             lambda v: number(v, ".1f")),
            ("Printing 40 MiB", "seconds of CPU", [print_seconds(t) for t in cpus],
             lambda v: f"{v:.2f}")],
           note=cpu_note)
    hbars(a.out, ticks(rates), "throughput", "Output throughput", "MB/s (higher is better)",
          [(label, [mbps(t, key) for t in rates])
           for label, key in (("Plain ASCII", "plain"), ("256-color SGR", "sgr"),
                              ("Unicode mix", "unicode"))],
          lambda v: f"{v:.0f}", note="Time for `cat` of a 20 MiB file to finish in the terminal.")

    def streaming(t, key):
        return res[t].get("streaming", {}).get(key, [])

    def fps(t):
        gaps = streaming(t, "gaps")
        return 1000 * len(gaps) / sum(gaps) if gaps else 0.0

    hbars(a.out, ticks(keys), "latency", "Keystroke to screen latency", "ms (lower is better)",
          [("Idle terminal", [med(res[t]["latency"]) for t in keys]),
           ("While output streams", [med(streaming(t, "latency") or [0]) for t in keys])],
          lambda v: f"{v:.1f}",
          note=("Median from a Quartz key event until the end of the capture that shows the echo."
                if macos else "Median from an X key press until the echoed character's pixels change."))
    # Frame timing comes from X Damage, which macOS has no counterpart to.
    streams = [t for t in streams if streaming(t, "gaps")]
    if streams:
        panels(a.out, ticks(streams), "smoothness", "Frames while colored output streams",
               [("Frames per second", "higher is better", [fps(t) for t in streams],
                 lambda v: f"{v:.0f}"),
                ("99th percentile frame gap", "ms (lower is better)",
                 [pct(streaming(t, "gaps") or [0], 0.99) for t in streams], lambda v: f"{v:.0f}")],
               note="X Damage reports during 4 s of a flood, timed by the X server.")
    hbars(a.out, ticks(starts), "startup", "Startup: launch to a screenful of text on screen",
          "ms (lower is better)", [("Median", [med(res[t]["startup"]) for t in starts])],
          lambda v: f"{v:.0f}", note="Median of 10 launches.")

    lines = ["# Terminal benchmark", ""]
    if "scrollback" not in meta:
        setup = "The results file records no details of its run."
    elif macos:
        setup = (f"macOS {meta.get('os', '')}, scrollback {meta['scrollback']} lines, "
                 f"window {meta.get('window')}.")
        if meta.get("display_hz"):
            setup += f" The display refreshes at {meta['display_hz']:.0f} Hz."
    else:
        setup = (f"Scrollback {meta['scrollback']} lines, window {meta.get('window')}, "
                 f"vsync off: {meta.get('vsync_off')}.")
    # Older results do not record how long their run took.
    if "run_seconds" in meta:
        setup += f" The run took {duration(meta['run_seconds'])}, finishing {meta['finished']}."
    lines += [setup, ""]
    if versions:
        lines += [row(["Terminal", "Version"]), row(["---", "---"])]
        lines += [row([t, versions.get(t, "")]) for t in order] + [""]
    def rested_mib(t, phase):
        value = rested(t, phase)
        return "-" if value is None else mib(value)

    if memory:
        lines += ["## Memory", "", "![Memory](ram.png)", ""]
        lines += [("The cursor-rested figures read the same memory again 13 seconds after the "
                   "output, once a terminal that stops blinking its cursor has; what goes only "
                   "then is held all the while the cursor blinks."), ""]
    if memory and macos:
        lines += [("Physical footprint is the memory a process dirtied, compressed memory "
                   "included, the figure Activity Monitor shows as Memory; RSS also counts the "
                   "shared library pages it touches. Terminal processes only, shell excluded."),
                  ""]
        lines += [row(["Terminal", "Idle footprint", "Idle RSS", "Heavy footprint", "Heavy RSS",
                       "Idle, cursor rested", "Heavy, cursor rested"]),
                  row(["---"] + ["---:"] * 6)]
        lines += [row([t, mib(mem(t, "idle")), mib(mem(t, "idle", "rss")),
                       mib(mem(t, "heavy")), mib(mem(t, "heavy", "rss")),
                       rested_mib(t, "idle"), rested_mib(t, "heavy")])
                  for t in memory]
    elif memory:
        lines += [("PSS shares each library page among the processes that map it; USS is the "
                   "terminal's own. X server pixmaps and GPU memory are held elsewhere on the "
                   "terminal's behalf."), ""]
        lines += [row(["Terminal", "Idle PSS", "Idle USS", "Heavy PSS", "Heavy USS",
                       "Idle, cursor rested", "Heavy, cursor rested", "X server pixmaps", "GPU"]),
                  row(["---"] + ["---:"] * 8)]
    for t in [] if macos else memory:
        held = [r["xserver"] for r in res[t]["ram_idle"] if "xserver" in r]
        lines.append(row([t, mib(mem(t, "idle")), mib(mem(t, "idle", "uss")),
                          mib(mem(t, "heavy")), mib(mem(t, "heavy", "uss")),
                          rested_mib(t, "idle"), rested_mib(t, "heavy"),
                          mib(med(held)) if held else "-",
                          mib(mem(t, "idle", "vram"), 0)]))
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
    if rates:
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
    def shown(value, spec, suffix):
        return "-" if value is None else f"{number(value, spec)}{suffix}"

    if cpus:
        lines += ["", "## CPU", "", "![CPU](cpu.png)", ""]
        lines += [row(["Terminal", "Idle", "One line every 16 ms", "While 40 MiB print",
                       "CPU time for 40 MiB"]),
                  row(["---"] + ["---:"] * 4)]
        for t in cpus:
            lines.append(row([t, shown(cpu(t, "cpu_idle"), ".2f", "%"),
                              shown(cpu(t, "cpu_lines"), ".1f", "%"),
                              shown(cpu(t, "cpu_load", "percent"), ".0f", "%"),
                              shown(print_seconds(t), ".2f", " s")]))
        if borrowed:
            lines += ["", ("Terminals without a CPU run take their CPU time from their heavy "
                           "memory runs, which print the same 40 MiB; a dash is a measure not "
                           "taken.")]
    if keys or starts or summary:
        lines += ["", "## Latency and startup", ""]
    if keys:
        lines += ["![Latency](latency.png)", ""]
    timed = [t for t in keys if res[t].get("latency_capture")]
    if timed:
        lines += [("Each echo is timed at the end of the capture that first shows it, so a "
                   "reading includes up to one capture's time."), "",
                  row(["Terminal", "Echo median", "One capture"]), row(["---"] + ["---:"] * 2)]
        lines += [row([t, f"{med(res[t]['latency']):.1f} ms",
                       f"{med(res[t]['latency_capture']):.1f} ms"]) for t in timed] + [""]
    if starts:
        lines += ["![Startup](startup.png)", ""]
    if summary:
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

    def absent(measures, only, terminals):
        if terminals:
            print(f"not in the report: {measures} for {', '.join(terminals)}; "
                  f"take it with `{measure} --only {only}`", file=sys.stderr)

    absent("memory", "ram", [t for t in order if t not in memory])
    absent("idle CPU", "cpu", idle_missing + [t for t in order if t not in cpus])
    absent("throughput", "throughput", [t for t in order if t not in rates])
    absent("latency", "latency,streaming", [t for t in order if t not in keys])
    absent("startup", "startup", [t for t in order if t not in starts])


if __name__ == "__main__":
    main()
