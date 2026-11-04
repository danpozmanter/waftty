"""RAM, CPU, throughput, latency and startup of terminals on a live X11 desktop.

    uv run bench.py inputs                      # writes the test inputs
    uv run bench.py run [--terminals waftty,xfce4-terminal,...] [--waftty PATH]
    uv run report.py                            # charts and RESULTS.md

Each terminal runs on its defaults from a configuration folder of its own,
with the same scrollback (--scrollback, 10,000 lines) and the same window size
(1000x700, or the nearest size its size hints allow). Results go to
results.json in the current directory unless --out names another file; the
inputs and each run's configuration folders stay in ~/.cache/waftty-bench.
"""

import argparse
import json
import os
import random
import select
import shutil
import signal
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from Xlib import X, display, error, protocol
from Xlib.ext import damage, res, xtest

W, H = 1000, 700
OUT = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "waftty-bench"
INPUT_BYTES = 20 * 1024 * 1024
INPUTS = ("plain", "sgr", "unicode")
SCROLLBACK = 10_000
WAFTTY = "waftty"
# The name waftty's results go under, so runs of two builds share a file.
LABEL = "waftty"

d = display.Display()
root = d.screen().root
A = d.intern_atom
root.change_attributes(event_mask=X.PropertyChangeMask)


def config_home(term):
    home = tempfile.mkdtemp(dir=OUT / "run", prefix=f"cfg-{term}-")
    if term == "waftty":
        os.makedirs(f"{home}/dev.gossamer.waftty")
        with open(f"{home}/dev.gossamer.waftty/settings.json", "w") as f:
            f.write('{"values":{"scrollback":"%d"},"version":2}\n' % SCROLLBACK)
    elif term == "xfce4-terminal":
        xml = f"{home}/xfce4/xfconf/xfce-perchannel-xml"
        os.makedirs(xml)
        with open(f"{xml}/xfce4-terminal.xml", "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<channel name="xfce4-terminal" version="1.0">'
                    f'<property name="scrolling-lines" type="uint" value="{SCROLLBACK}"/>'
                    "</channel>\n")
        # The bus listens in the benchmark's folder, so the services it
        # starts, which outlive it, carry that folder in their address.
        with open(f"{home}/bus.conf", "w") as f:
            f.write('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"'
                    ' "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">\n'
                    f"<busconfig><type>session</type><keep_umask/><listen>unix:dir={home}</listen>"
                    "<auth>EXTERNAL</auth><standard_session_servicedirs/>"
                    '<policy context="default"><allow send_destination="*" eavesdrop="true"/>'
                    '<allow eavesdrop="true"/><allow own="*"/></policy></busconfig>\n')
    return home


TERMS = {
    "waftty": lambda cmd, home: [WAFTTY, "-e", "sh", "-c", cmd],
    # xfconf reads the scrollback from the benchmark's folder on a bus of its own.
    "xfce4-terminal": lambda cmd, home: ["dbus-run-session", f"--config-file={home}/bus.conf", "--",
                                         "xfce4-terminal", "--disable-server",
                                         "-x", "sh", "-c", cmd],
    "alacritty": lambda cmd, home: ["alacritty", "-o", f"scrolling.history={SCROLLBACK}",
                              "-e", "sh", "-c", cmd],
    "ghostty": lambda cmd, home: ["ghostty", "--config-default-files=false",
                            "--gtk-single-instance=false",
                            f"--scrollback-limit-lines={SCROLLBACK}", "-e", "sh", "-c", cmd],
    "wezterm": lambda cmd, home: ["wezterm", "-n", "--config", f"scrollback_lines={SCROLLBACK}", "start",
                            "--always-new-process", "--", "sh", "-c", cmd],
}

# Processes that are not the terminal: its shell and commands, and the bus and
# settings daemon the xfce4-terminal run starts (a desktop already has both).
HELPERS = {"sh", "bash", "cat", "head", "sleep", "python3", "dbus-daemon", "dbus-run-sessio",
           "xfconfd", "gvfsd"}


class Died(Exception):
    pass


def family(pid):
    pids = {pid}
    try:
        for t in os.listdir(f"/proc/{pid}/task"):
            for c in open(f"/proc/{pid}/task/{t}/children").read().split():
                pids |= family(int(c))
    except FileNotFoundError:
        pass
    return pids


def terminal_pids(pid):
    out = []
    for p in family(pid):
        try:
            if open(f"/proc/{p}/comm").read().strip() not in HELPERS:
                out.append(p)
        except FileNotFoundError:
            pass
    return out


# A child's exit wakes a wait on its descriptors through this pipe.
_child_r, _child_w = os.pipe()
os.set_blocking(_child_r, False)
os.set_blocking(_child_w, False)
signal.set_wakeup_fd(_child_w)
signal.signal(signal.SIGCHLD, lambda *_: None)


def wait_readable(p, fds):
    """The ready descriptors among `fds`; Died once the terminal exits first."""
    while True:
        if p.poll() is not None:
            raise Died(f"the terminal exited with status {p.returncode}")
        ready, _, _ = select.select([*fds, _child_r], [], [])
        if _child_r in ready:
            try:
                os.read(_child_r, 4096)
            except BlockingIOError:
                pass
        ready = [f for f in ready if f != _child_r]
        if ready:
            return ready


def next_event(p):
    while not d.pending_events():
        wait_readable(p, [d.fileno()])
    return d.next_event()


def window_of(pid):
    prop = root.get_full_property(A("_NET_CLIENT_LIST"), X.AnyPropertyType)
    pids = family(pid)
    for w in prop.value if prop else []:
        o = d.create_resource_object("window", w)
        try:
            p = o.get_full_property(A("_NET_WM_PID"), X.AnyPropertyType)
        except error.BadWindow:
            continue
        if p and p.value[0] in pids:
            return o
    return None


def wait_window(p):
    w = window_of(p.pid)
    while w is None:
        next_event(p)
        w = window_of(p.pid)
    return w


def focused(win):
    w = d.get_input_focus().focus
    while not isinstance(w, int) and w.id != root.id:
        if w.id == win.id:
            return True
        w = w.query_tree().parent
    return False


def ensure_focus(p, win):
    if focused(win):
        return
    ev = protocol.event.ClientMessage(window=win, client_type=A("_NET_ACTIVE_WINDOW"),
                                      data=(32, [2, X.CurrentTime, 0, 0, 0]))
    root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    d.sync()
    while not focused(win):
        next_event(p)


def granted(w):
    """The size nearest W x H the window's size hints allow (some resize in whole cells)."""
    hints = w.get_wm_normal_hints()
    if hints is None or not hints.flags & 64:  # PResizeInc
        return W, H
    if hints.flags & 256:  # PBaseSize
        bw, bh = hints.base_width, hints.base_height
    else:
        bw, bh = hints.min_width, hints.min_height
    iw, ih = max(hints.width_inc, 1), max(hints.height_inc, 1)
    return bw + (W - bw) // iw * iw, bh + (H - bh) // ih * ih


def resize(p, w):
    w.change_attributes(event_mask=X.StructureNotifyMask)
    want = granted(w)
    w.configure(width=want[0], height=want[1])
    d.sync()
    while (w.get_geometry().width, w.get_geometry().height) != want:
        next_event(p)


def monitor_connected():
    out = subprocess.run(["xrandr", "--listactivemonitors"], capture_output=True, text=True).stdout
    return not out.startswith("Monitors: 0")


def launch(term, cmd):
    home = config_home(term)
    env = dict(os.environ, XDG_CONFIG_HOME=home)
    # Without a monitor there is no vblank: a GL terminal synced to it would
    # pace itself at the driver's 1 Hz fallback.
    if not monitor_connected():
        env["__GL_SYNC_TO_VBLANK"] = "0"
    return subprocess.Popen(TERMS[term](cmd, home), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, env=env)


class Run:
    """A terminal running `script` once the window has its size: `go` starts
    the script, and `signal` waits for a line the script writes to its pipe."""

    def __init__(self, term, script):
        tmp = tempfile.mkdtemp(dir=OUT / "run")
        self.go, self.done = f"{tmp}/go", f"{tmp}/done"
        os.mkfifo(self.go)
        os.mkfifo(self.done)
        # Held open for reading and writing, neither end blocks the other.
        self.go_fd = os.open(self.go, os.O_RDWR)
        self.done_fd = os.open(self.done, os.O_RDWR | os.O_NONBLOCK)
        script = script.replace("$DONE", self.done)
        self.p = launch(term, f"head -n1 {self.go} >/dev/null; {script}")
        self.w = wait_window(self.p)
        resize(self.p, self.w)

    def start(self):
        os.write(self.go_fd, b"go\n")

    def signal(self):
        wait_readable(self.p, [self.done_fd])
        return os.read(self.done_fd, 4096).decode()

    def stop(self):
        for pid in family(self.p.pid):
            try:
                os.kill(pid, 15)
            except ProcessLookupError:
                pass
        self.p.wait()
        os.close(self.go_fd)
        os.close(self.done_fd)


def memory(pid):
    pss = uss = rss = 0
    for p in terminal_pids(pid):
        try:
            for line in open(f"/proc/{p}/smaps_rollup"):
                k, _, v = line.partition(":")
                if k == "Pss":
                    pss += int(v.split()[0])
                elif k in ("Private_Clean", "Private_Dirty"):
                    uss += int(v.split()[0])
                elif k == "Rss":
                    rss += int(v.split()[0])
        except (FileNotFoundError, ProcessLookupError):
            pass
    return pss / 1024, uss / 1024, rss / 1024


def cpu_seconds(pid):
    tick = os.sysconf("SC_CLK_TCK")
    total = 0
    for p in terminal_pids(pid):
        try:
            fields = open(f"/proc/{p}/stat").read().rsplit(")", 1)[1].split()
            total += int(fields[11]) + int(fields[12])
        except (FileNotFoundError, ProcessLookupError):
            pass
    return total / tick


def gpu_mib(pid):
    if not shutil.which("nvidia-smi"):
        return 0
    pids = family(pid)
    total = 0
    for line in subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout.splitlines():
        parts = line.split()
        if (len(parts) > 6 and parts[4].isdigit() and int(parts[4]) in pids
                and parts[-2].endswith("MiB")):
            total += int(parts[-2][:-3])
    return total


def xserver_mib(pid):
    """MiB of pixmaps the X server holds for the terminal's connections, which
    its own memory leaves out: GTK keeps window contents there."""
    pids = family(pid)
    ids = d.res_query_client_ids([{"client": 0, "mask": res.LocalClientPIDMask}]).ids
    total = 0
    for v in ids:
        if v.value and v.value[0] in pids:
            r = d.res_query_client_pixmap_bytes(v.spec.client)
            total += r.bytes + (r.bytes_overflow << 32)
    return total / (1024 * 1024)


def settled_memory(pid):
    """Memory once its total stops moving between readings a second apart."""
    last, same = None, 0
    while same < 3:
        time.sleep(1)
        now = memory(pid)[0]
        same = same + 1 if last is not None and abs(now - last) < 0.25 else 0
        last = now
    return memory(pid)


def ram(term, files):
    """Memory after `files` print (none: idle), and the CPU time printing them took."""
    load = f"cat {' '.join(str(OUT / f'{n}.txt') for n in files)}; " if files else ""
    run = Run(term, f"{load}echo > $DONE; exec sleep 100000")
    before = cpu_seconds(run.p.pid)
    run.start()
    run.signal()
    cpu = cpu_seconds(run.p.pid) - before
    pss, uss, rss = settled_memory(run.p.pid)
    vram = gpu_mib(run.p.pid)
    xserver = xserver_mib(run.p.pid)
    run.stop()
    return {"pss": pss, "uss": uss, "rss": rss, "vram": vram, "xserver": xserver, "cpu": cpu}


def idle_cpu(term, seconds=10):
    """Share of one core the terminal uses while idle with a blinking cursor."""
    run = Run(term, "echo > $DONE; exec sleep 100000")
    run.start()
    run.signal()
    time.sleep(3)  # startup work that lands after the window shows
    before = cpu_seconds(run.p.pid)
    time.sleep(seconds)
    used = cpu_seconds(run.p.pid) - before
    run.stop()
    return 100 * used / seconds


def load_cpu(term):
    """CPU the terminal uses while 20 MiB of plain and 20 MiB of colored text
    print: as a share of one core (above 100 when it keeps several busy), and
    in seconds, which a faster terminal spends in less wall time."""
    files = " ".join(str(OUT / f"{n}.txt") for n in ("plain", "sgr"))
    run = Run(term, f"cat {files}; echo > $DONE; exec sleep 100000")
    before = cpu_seconds(run.p.pid)
    t0 = time.perf_counter()
    run.start()
    run.signal()
    used = cpu_seconds(run.p.pid) - before
    seconds = time.perf_counter() - t0
    run.stop()
    return {"percent": 100 * used / seconds, "seconds": used}


def throughput(term, name):
    """Milliseconds for `cat` of an input to finish inside the terminal."""
    run = Run(term, f's=$(date +%s%N); cat {OUT / f"{name}.txt"}; e=$(date +%s%N); '
                    'echo $((e-s)) > $DONE; exec sleep 100000')
    run.start()
    ns = int(run.signal())
    run.stop()
    return ns / 1e6


def region(w, x, y, cw, ch):
    return w.get_image(x, y, cw, ch, X.ZPixmap, 0xFFFFFFFF).data


def latency(term, samples=65):
    """Milliseconds from a key press until the echoed character's pixels change.
    Each damage report on the window is checked against the pixels before the key."""
    echo = ("import os,tty; tty.setraw(0); os.write(1, b'\\x1b[?25l\\x1b[2J\\x1b[H'); "
            "[os.write(1, b'\\r' + c) for c in iter(lambda: os.read(0, 1), b'q')]")
    run = Run(term, f"exec python3 -c \"{echo}\"")
    run.start()
    w = run.w
    ensure_focus(run.p, w)
    d.damage_query_version()
    report = w.damage_create(damage.DamageReportNonEmpty)
    box = (0, 0, 160, 80)
    keys = [d.keysym_to_keycode(ord(c)) for c in "ab"]
    lat = []
    for i in range(samples):
        time.sleep(0.05 + random.random() * 0.1)
        ensure_focus(run.p, w)
        before = region(w, *box)
        d.damage_subtract(report)
        d.sync()
        while d.pending_events():
            d.next_event()
        t0 = time.perf_counter()
        xtest.fake_input(d, X.KeyPress, keys[i % 2])
        xtest.fake_input(d, X.KeyRelease, keys[i % 2])
        d.flush()
        while True:
            e = next_event(run.p)
            if e.type != d.extension_event.DamageNotify:
                continue
            t1 = time.perf_counter()
            d.damage_subtract(report)
            if region(w, *box) != before:
                lat.append((t1 - t0) * 1000)
                break
    run.stop()
    # The first samples cover the echo program starting up.
    return lat[5:]


# Floods colored lines below five fixed rows, the first of which shows the
# last key typed: the same program in every terminal, so frames and echoes
# compare. Five rows put the scrolling ones below any window's measured box.
# Every line is numbered, so no two moments of the stream look the same: a
# terminal that sends nothing for a frame identical to the last one would
# otherwise show a gap where nothing on screen changed.
STREAM = r'''
import os, select, tty
tty.setraw(0)
rows = os.get_terminal_size(1).lines
colors = [f"\x1b[38;5;{16 + 7 * i}m" for i in range(30)]
lines = [("".join(f"{colors[(i + j) % 30]}word{j:02d} " for j in range(12)) + "\x1b[0m\r\n").encode()
    for i in range(64)]
os.write(1, f"\x1b[?25l\x1b[2J\x1b[6;{rows}r\x1b[{rows};1H".encode())
def put(data):
    view = memoryview(data)
    while view:
        view = view[os.write(1, view):]
start = 0
while True:
    put(b"".join(b"%09d " % (start + i) + line for i, line in enumerate(lines)))
    start += len(lines)
    if select.select([0], [], [], 0)[0]:
        key = os.read(0, 1)
        if key == b"q":
            break
        put(b"\x1b7\x1b[1;1H" + key * 8 + b"\x1b8")
'''


# Shorter than any frame interval here: every terminal paints 60 frames a
# second or fewer.
FRAME_SPREAD_MS = 4


def streaming(term, seconds=4, samples=25):
    """While a program floods colored output: the milliseconds between the
    frames that reach the window, and from a key press until its echo in the
    fixed top row is on screen."""
    program = OUT / "stream.py"
    program.write_text(STREAM)
    run = Run(term, f"exec python3 {program}")
    run.start()
    w = run.w
    ensure_focus(run.p, w)
    d.damage_query_version()
    report = w.damage_create(damage.DamageReportNonEmpty)

    # Damage reports that arrive together belong to one frame.
    def next_frame():
        while next_event(run.p).type != d.extension_event.DamageNotify:
            pass
        while d.pending_events():
            d.next_event()
        d.damage_subtract(report)
        return time.perf_counter()

    # Every damaged rectangle reports itself with the server's time in
    # milliseconds, so frames are told apart however late they are read. A
    # frame drawn as several images spreads its rectangles over a few
    # milliseconds; rectangles closer than FRAME_SPREAD_MS are one frame.
    raw = w.damage_create(damage.DamageReportRawRectangles)
    stamps = []
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < 1 + seconds:
        e = next_event(run.p)
        if e.type == d.extension_event.DamageNotify and e.damage == raw:
            if time.perf_counter() - t0 >= 1:
                stamps.append(e.timestamp)
    d.damage_destroy(raw)
    frames = []
    for k, t in enumerate(stamps):
        if k == 0 or t - stamps[k - 1] > FRAME_SPREAD_MS:
            frames.append(t)
    gaps = [b - a for a, b in zip(frames, frames[1:])]
    box = (0, 0, 160, 80)
    keys = [d.keysym_to_keycode(ord(c)) for c in "ab"]
    lat = []
    for i in range(samples):
        time.sleep(0.05 + random.random() * 0.1)
        ensure_focus(run.p, w)
        while d.pending_events():
            d.next_event()
        d.damage_subtract(report)
        before = region(w, *box)
        t0 = time.perf_counter()
        xtest.fake_input(d, X.KeyPress, keys[i % 2])
        xtest.fake_input(d, X.KeyRelease, keys[i % 2])
        d.flush()
        while True:
            t1 = next_frame()
            if region(w, *box) != before:
                lat.append((t1 - t0) * 1000)
                break
    run.stop()
    return {"gaps": gaps, "latency": lat}


def painted_text(w):
    try:
        data = region(w, 0, 0, 200, 60)
    except error.XError:
        return False
    return len({data[i:i + 4] for i in range(0, len(data), 4)}) > 2


def startup(term):
    """Milliseconds from launch until the first line of output is on screen."""
    t0 = time.perf_counter()
    p = launch(term, "echo READY; exec sleep 100000")
    w = wait_window(p)
    while w.get_attributes().map_state != X.IsViewable:
        next_event(p)
    d.damage_query_version()
    report = w.damage_create(damage.DamageReportNonEmpty)
    while not painted_text(w):
        while next_event(p).type != d.extension_event.DamageNotify:
            pass
        d.damage_subtract(report)
    ms = (time.perf_counter() - t0) * 1000
    for pid in family(p.pid):
        try:
            os.kill(pid, 15)
        except ProcessLookupError:
            pass
    p.wait()
    return ms


def leftovers():
    """Processes still running from a launch: each has the benchmark's
    configuration folder in its environment, or its bus there."""
    marks = (f"XDG_CONFIG_HOME={OUT / 'run'}/cfg-".encode(),
             f"DBUS_SESSION_BUS_ADDRESS=unix:path={OUT / 'run'}/cfg-".encode())
    found = []
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            environ = open(f"/proc/{pid}/environ", "rb").read()
            if any(mark in environ for mark in marks):
                found.append(int(pid))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return found


def write_inputs():
    """20 MiB each of plain ASCII lines, 256-color SGR runs, and mixed scripts."""
    OUT.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(1)
    line = " the quick brown fox jumps over the lazy dog 0123456789 abcdefghijklmnopqrstuvwxyz\n"
    plain = bytearray()
    n = 0
    while len(plain) < INPUT_BYTES:
        plain += f"{n:08d}{line}".encode()
        n += 1
    sgr = bytearray()
    while len(sgr) < INPUT_BYTES:
        for _ in range(30):
            sgr += (f"\x1b[38;5;{rnd.randrange(256)}m\x1b[48;5;{rnd.randrange(256)}m"
                    + rnd.choice("abcdefghijklmnopqrstuvwxyz") * rnd.randint(1, 4)).encode()
        sgr += b"\x1b[0m\n"
    words = ["Ελληνικά", "日本語", "héllo", "текст", "wörld", "ascii", "emoji😀"]
    uni = bytearray()
    while len(uni) < INPUT_BYTES:
        uni += (" ".join(rnd.choice(words) for _ in range(9)) + "\n").encode()
    for name, data in (("plain", plain), ("sgr", sgr), ("unicode", uni)):
        (OUT / f"{name}.txt").write_bytes(bytes(data[:INPUT_BYTES]))


def measure(terms, runs, out, only):
    def wanted(kind):
        return not only or kind in only

    results = json.loads(out.read_text()) if out.exists() else {}

    def label_of(term):
        return LABEL if term == "waftty" else term

    def put(term, key, value):
        results.setdefault(label_of(term), {}).setdefault(key, []).append(value)
        out.write_text(json.dumps(results, indent=1))

    def each(key, fn):
        for term in terms:
            put(term, key, fn(term))
            left = leftovers()
            if left:
                raise SystemExit(f"{term} {key}: processes left running: {left}")
        print(key, flush=True)

    for _ in range(runs):
        if wanted("ram"):
            each("ram_idle", lambda t: ram(t, []))
            each("ram_heavy", lambda t: ram(t, ["plain", "sgr"]))
        if wanted("throughput"):
            for name in INPUTS:
                each(f"tp_{name}", lambda t: throughput(t, name))
    if wanted("cpu"):
        each("cpu_idle", idle_cpu)
        for _ in range(runs):
            each("cpu_load", load_cpu)
    for term in terms:
        results.setdefault(label_of(term), {})
        if wanted("latency"):
            results[label_of(term)]["latency"] = latency(term)
        if wanted("streaming"):
            results[label_of(term)]["streaming"] = streaming(term)
        if wanted("startup"):
            results[label_of(term)]["startup"] = [startup(term) for _ in range(10)]
    meta = results.get("_meta", {})
    meta.update({"scrollback": SCROLLBACK, "window": [W, H], "vsync_off": not monitor_connected()})
    meta.setdefault("versions", {}).update({label_of(t): v for t, v in versions(terms).items()})
    results["_meta"] = meta
    out.write_text(json.dumps(results, indent=1))
    print("done")


def versions(terms):
    out = {}
    for term in terms:
        exe = WAFTTY if term == "waftty" else term
        try:
            v = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout
            out[term] = v.strip().splitlines()[0] if v.strip() else ""
        except OSError:
            out[term] = ""
    return out


def main():
    global SCROLLBACK, WAFTTY, LABEL
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["inputs", "run"])
    ap.add_argument("--terminals", default="waftty,xfce4-terminal,alacritty,ghostty,wezterm")
    ap.add_argument("--waftty", default="waftty", help="waftty executable to measure")
    ap.add_argument("--label", default="waftty", help="the name waftty's results go under")
    ap.add_argument("--runs", type=int, default=3, help="repetitions of RAM and throughput")
    ap.add_argument("--scrollback", type=int, default=SCROLLBACK)
    ap.add_argument("--only", default="", help="comma-separated: ram, throughput, cpu, latency, streaming, startup")
    ap.add_argument("--out", type=Path, default=Path("results.json"),
                    help="results file (default: results.json in the current directory)")
    a = ap.parse_args()
    if a.command == "inputs":
        write_inputs()
        print(f"inputs written to {OUT}")
        return
    SCROLLBACK, WAFTTY, LABEL = a.scrollback, a.waftty, a.label
    if not all((OUT / f"{n}.txt").exists() for n in INPUTS):
        write_inputs()
    (OUT / "run").mkdir(parents=True, exist_ok=True)
    terms = [t for t in a.terminals.split(",") if t]
    missing = [t for t in terms if not shutil.which(WAFTTY if t == "waftty" else t)]
    if missing:
        raise SystemExit(f"not installed: {', '.join(missing)}")
    # A terminal left from an interrupted run would take this run's windows:
    # waftty and others hand a new launch to the instance already running.
    end_leftovers()
    try:
        measure(terms, a.runs, a.out, {k for k in a.only.split(",") if k})
    finally:
        end_leftovers()


def end_leftovers():
    for pid in leftovers():
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


if __name__ == "__main__":
    main()
