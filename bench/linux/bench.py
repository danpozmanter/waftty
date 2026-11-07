"""RAM, CPU, throughput, latency and startup of terminals on a live X11 desktop.

    uv run linux/bench.py inputs                # writes the test inputs
    uv run linux/bench.py run [--terminals waftty,waftty-quick,guake,...] [--waftty PATH]
    uv run report.py linux                      # charts and RESULTS.md

Each terminal runs on its defaults from a configuration folder of its own,
with the same scrollback (--scrollback, 10,000 lines) and the same window size
(1000x700, or the nearest size its size hints allow). Results go to
linux/results.json unless --out names another file; the
inputs and each run's configuration folders stay in ~/.cache/waftty-bench.
"""

import argparse
import ctypes
import errno
import itertools
import json
import os
import random
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from Xlib import X, display, error, protocol
from Xlib.ext import damage, res, xtest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from timing import duration  # noqa: E402

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


# The drop-down form of a terminal, which hangs from the top of the screen
# and stays above other windows, as Guake always does.
QUICK = "-quick"


def program(term):
    """The executable a benchmark entry runs."""
    base = term.removesuffix(QUICK)
    return WAFTTY if base == "waftty" else base


def drop_down(term):
    return term.endswith(QUICK) or term == "guake"


def work_area():
    v = root.get_full_property(A("_NET_WORKAREA"), X.AnyPropertyType).value
    return v[2], v[3]


def share_of_work_area():
    """The window size as whole percentages of the work area, the unit
    drop-down terminals size themselves in."""
    aw, ah = work_area()
    return round(100 * W / aw), round(100 * H / ah)


def docked_size():
    """The size a drop-down terminal gives itself from share_of_work_area."""
    (aw, ah), (wide, tall) = work_area(), share_of_work_area()
    return aw * wide / 100, ah * tall / 100


def config_home(term):
    home = tempfile.mkdtemp(dir=OUT / "run", prefix=f"cfg-{term}-")
    base, quick = term.removesuffix(QUICK), term.endswith(QUICK)
    if base == "waftty":
        values = {"scrollback": str(SCROLLBACK)}
        if quick:
            wide, tall = share_of_work_area()
            # A chord nothing else holds, so the run takes its shortcut quietly.
            values.update(drop_down_key="Ctrl+Alt+Shift+F8", drop_down_width=str(wide),
                          drop_down_height=str(tall))
            # The quick terminal is a single instance named on the session bus; a
            # bus of its own keeps the run from handing off to one already open,
            # and starts the desktop portal it reads its scheme and font from.
            private_bus(home, services=True)
        os.makedirs(f"{home}/dev.gossamer.waftty")
        with open(f"{home}/dev.gossamer.waftty/settings.json", "w") as f:
            json.dump({"values": values, "version": 2}, f)
    elif base == "xfce4-terminal":
        xml = f"{home}/xfce4/xfconf/xfce-perchannel-xml"
        os.makedirs(xml)
        with open(f"{xml}/xfce4-terminal.xml", "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<channel name="xfce4-terminal" version="1.0">'
                    f'<property name="scrolling-lines" type="uint" value="{SCROLLBACK}"/>'
                    "</channel>\n")
        private_bus(home, services=True)
    elif base == "rio":
        # Rio asks before closing a window with a program running, which would
        # hold every run's end.
        os.makedirs(f"{home}/rio")
        with open(f"{home}/rio/config.toml", "w") as f:
            f.write(f"scrollback-history-limit = {SCROLLBACK}\nconfirm-before-quit = false\n")
    elif term == "guake":
        # Guake reads GSettings, here from a key file in the run's folder; its
        # show-hide key is left unbound, so it takes no global shortcut.
        wide, tall = share_of_work_area()
        os.makedirs(f"{home}/glib-2.0/settings")
        with open(f"{home}/glib-2.0/settings/keyfile", "w") as f:
            f.write("[org/guake/general]\n"
                    f"history-size={SCROLLBACK}\ninfinite-history=false\n"
                    "use-popup=false\nuse-trayicon=false\nprompt-on-quit=false\n"
                    "default-shell='/bin/sh'\nuse-login-shell=false\n"
                    "restore-tabs-startup=false\nload-guake-yml=false\n"
                    f"window-width={wide}\nwindow-height={tall}\n"
                    "[org/guake/keybindings/global]\nshow-hide=''\n")
        # Nothing on its bus starts desktop services, which Guake would wait
        # for at startup.
        private_bus(home, services=False)
    return home


def private_bus(home, services):
    """A session bus config for a terminal that runs as a single instance, so
    the run starts its own rather than handing off to one already running;
    with `services`, the bus starts the desktop's session services on demand."""
    # The bus listens in the benchmark's folder, so the services it
    # starts, which outlive it, carry that folder in their address.
    with open(f"{home}/bus.conf", "w") as f:
        f.write('<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"'
                ' "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">\n'
                f"<busconfig><type>session</type><keep_umask/><listen>unix:dir={home}</listen>"
                "<auth>EXTERNAL</auth>"
                f"{'<standard_session_servicedirs/>' if services else ''}"
                '<policy context="default"><allow send_destination="*" eavesdrop="true"/>'
                '<allow eavesdrop="true"/><allow own="*"/></policy></busconfig>\n')


TERMS = {
    "waftty": lambda cmd, home: [WAFTTY, "-e", "sh", "-c", cmd],
    "waftty-quick": lambda cmd, home: [WAFTTY, "--quick", "-e", "sh", "-c", cmd],
    # xfconf reads the scrollback from the benchmark's folder on a bus of its own.
    "xfce4-terminal": lambda cmd, home: ["xfce4-terminal", "--disable-server",
                                         "-x", "sh", "-c", cmd],
    # Guake types the command into its shell, which runs it.
    "guake": lambda cmd, home: ["guake", "--show", "-e", cmd],
    "alacritty": lambda cmd, home: ["alacritty", "-o", f"scrolling.history={SCROLLBACK}",
                              "-e", "sh", "-c", cmd],
    "ghostty": lambda cmd, home: ["ghostty", "--config-default-files=false",
                            "--gtk-single-instance=false",
                            f"--scrollback-limit-lines={SCROLLBACK}", "-e", "sh", "-c", cmd],
    # kitty paces frames by its own sync_to_monitor rather than the driver's
    # vblank setting, so without a monitor it is turned off the same way.
    "kitty": lambda cmd, home: ["kitty", "--config=NONE", "-o", f"scrollback_lines={SCROLLBACK}",
                                *([] if monitor_connected() else ["-o", "sync_to_monitor=no"]),
                                "sh", "-c", cmd],
    "rio": lambda cmd, home: ["rio", "-e", "sh", "-c", cmd],
    "wezterm": lambda cmd, home: ["wezterm", "-n", "--config", f"scrollback_lines={SCROLLBACK}", "start",
                            "--always-new-process", "--", "sh", "-c", cmd],
}

# Terminals that present through Vulkan's FIFO mode with no way to turn it off:
# with no monitor connected the driver paces them at about two frames a second.
VBLANK_BOUND = {"rio"}

# Processes that are not the terminal: its shell and commands.
HELPERS = {"sh", "bash", "cat", "head", "sleep", "python3"}

# The desktop services a terminal on a bus of its own reads at startup, called
# once before it launches: a desktop already runs them.
WARM = {
    "waftty-quick": [["gdbus", "call", "--session", "--dest", "org.freedesktop.portal.Desktop",
                      "--object-path", "/org/freedesktop/portal/desktop",
                      "--method", "org.freedesktop.portal.Settings.ReadAll", "[]"]],
    "xfce4-terminal": [["xfconf-query", "--channel", "xfce4-terminal", "--list"],
                       ["gdbus", "call", "--session", "--dest", "org.gtk.vfs.Daemon",
                        "--object-path", "/org/gtk/vfs/Daemon",
                        "--method", "org.freedesktop.DBus.Peer.Ping"],
                       ["gdbus", "call", "--session", "--dest", "org.a11y.Bus",
                        "--object-path", "/org/a11y/bus", "--method", "org.a11y.Bus.GetAddress"]],
}


_libc = ctypes.CDLL(None, use_errno=True)
SYS_PIDFD_OPEN = 434


def pidfd_open(pid):
    """A descriptor that turns readable when process `pid` exits."""
    fd = _libc.syscall(SYS_PIDFD_OPEN, pid, 0)
    if fd < 0:
        err = ctypes.get_errno()
        if err == errno.ESRCH:
            raise ProcessLookupError(pid)
        raise OSError(err, os.strerror(err))
    return fd


class Died(Exception):
    pass


def family(pid):
    pids = {pid}
    try:
        for t in os.listdir(f"/proc/{pid}/task"):
            for c in Path(f"/proc/{pid}/task/{t}/children").read_text().split():
                pids |= family(int(c))
    except FileNotFoundError:
        pass
    return pids


def terminal_pids(pid):
    out = []
    for p in family(pid):
        try:
            if Path(f"/proc/{p}/comm").read_text().strip() not in HELPERS:
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
            how = (f"was killed by {signal.Signals(-p.returncode).name}" if p.returncode < 0
                   else f"exited with status {p.returncode}")
            raise Died(f"the terminal {how}")
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


def rect(w):
    g = w.get_geometry()
    at = root.translate_coords(w, 0, 0)
    return at.x, at.y, g.width, g.height


def check_uncovered(w):
    """Stops the run when another window lies over `w`: without a compositor
    its pixels read as the covering window's, and some terminals stop drawing
    while hidden, so nothing measured then is the terminal's."""
    stack = root.get_full_property(A("_NET_CLIENT_LIST_STACKING"), X.AnyPropertyType).value
    x, y, wide, tall = rect(w)
    for above in list(stack)[list(stack).index(w.id) + 1:]:
        o = d.create_resource_object("window", above)
        try:
            if o.get_attributes().map_state != X.IsViewable:
                continue
            ox, oy, ow, oh = rect(o)
        except error.BadWindow:
            continue
        if ox < x + wide and x < ox + ow and oy < y + tall and y < oy + oh:
            name = o.get_wm_name() or hex(above)
            raise SystemExit(f"the window under test is covered by {name!r}: the benchmark "
                             "needs the desktop to itself while it runs")


def ensure_focus(p, win):
    if focused(win):
        check_uncovered(win)
        return
    ev = protocol.event.ClientMessage(window=win, client_type=A("_NET_ACTIVE_WINDOW"),
                                      data=(32, [2, X.CurrentTime, 0, 0, 0]))
    root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    d.sync()
    while not focused(win):
        next_event(p)
    check_uncovered(win)


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


def ask_size(w, want):
    # Asked of the window manager as a tool would (EWMH source 2), which it
    # honours for drop-down windows that ignore a client's configure request.
    flags = (2 << 12) | (1 << 10) | (1 << 11)
    ev = protocol.event.ClientMessage(window=w, client_type=A("_NET_MOVERESIZE_WINDOW"),
                                      data=(32, [flags, 0, 0, want[0], want[1]]))
    root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    d.sync()


def resize(p, term, w):
    w.change_attributes(event_mask=X.StructureNotifyMask)
    if drop_down(term):
        # A drop-down terminal sizes itself once its window is up; asking only
        # after that size is in keeps its request from landing after this one.
        dw, dh = docked_size()
        while abs(w.get_geometry().width - dw) > 1 or abs(w.get_geometry().height - dh) > 1:
            next_event(p)
    want = granted(w)
    ask_size(w, want)
    while True:
        # The window has its size once it reads right and every configure
        # the server sent before that read has been seen.
        if (w.get_geometry().width, w.get_geometry().height) == want:
            d.sync()
            if not d.pending_events():
                return
        e = next_event(p)
        if e.type == X.ConfigureNotify and e.window == w and (e.width, e.height) != want:
            ask_size(w, want)


def monitor_connected():
    out = subprocess.run(["xrandr", "--listactivemonitors"], capture_output=True, text=True, check=False).stdout
    return not out.startswith("Monitors: 0")


def launch(term, cmd):
    home = config_home(term)
    env = dict(os.environ, XDG_CONFIG_HOME=home)
    if term == "guake":
        env["GSETTINGS_BACKEND"] = "keyfile"
    # Without a monitor there is no vblank: a GL terminal synced to it would
    # pace itself at the driver's 1 Hz fallback.
    if not monitor_connected():
        env["__GL_SYNC_TO_VBLANK"] = "0"
    bus = None
    if os.path.exists(f"{home}/bus.conf"):
        bus = subprocess.Popen(["dbus-daemon", f"--config-file={home}/bus.conf", "--nofork",
                                "--print-address=1"], stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, env=env, text=True)
        env["DBUS_SESSION_BUS_ADDRESS"] = bus.stdout.readline().strip()
        for call in WARM.get(term, []):
            subprocess.run(call, stdout=subprocess.DEVNULL, env=env, check=True)
    started = time.perf_counter()
    p = subprocess.Popen(TERMS[term](cmd, home), stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, env=env)
    p.home, p.bus, p.started = home, bus, started
    return p


def end(p):
    """Ends launch `p`: its processes, and the services its session bus
    started, which the user's service manager adopts rather than it."""
    # Each process signalled is waited for: an interactive shell ignores
    # SIGTERM and leaves only once its terminal closes the pty.
    exits = []
    for pid in family(p.pid) | set(started_from(p.home)):
        try:
            exits.append(pidfd_open(pid))
            os.kill(pid, 15)
        except ProcessLookupError:
            pass
    p.wait()
    for fd in exits:
        select.select([fd], [], [])
        os.close(fd)
    if p.bus:
        p.bus.terminate()
        p.bus.wait()
        p.bus.stdout.close()


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
        resize(self.p, term, self.w)
        ensure_focus(self.p, self.w)

    def start(self):
        check_uncovered(self.w)
        os.write(self.go_fd, b"go\n")

    def signal(self):
        wait_readable(self.p, [self.done_fd])
        return os.read(self.done_fd, 4096).decode()

    def stop(self):
        check_uncovered(self.w)
        end(self.p)
        os.close(self.go_fd)
        os.close(self.done_fd)


def memory(pid):
    pss = uss = rss = 0
    for p in terminal_pids(pid):
        try:
            for line in Path(f"/proc/{p}/smaps_rollup").read_text().splitlines():
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


def process_name(pid):
    """A process as people know it: its program, or the script an interpreter runs."""
    argv = [os.path.basename(a.decode(errors="replace"))
            for a in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if a]
    if not argv:
        return Path(f"/proc/{pid}/comm").read_text().strip()
    if argv[0].startswith("python") and len(argv) > 1:
        return argv[1]
    return argv[0]


def memory_sources(pid):
    """Where the memory figure comes from: PSS per process counted and per
    process left out, by name, and the counted PSS split into private data
    (heap, scrollback), code and libraries mapped from files, and shared memory."""
    counted, left_out = {}, {}
    kinds = {"anon": 0.0, "file": 0.0, "shmem": 0.0}
    for p in sorted(family(pid)):
        try:
            comm = Path(f"/proc/{p}/comm").read_text().strip()
            name = process_name(p)
            fields = {}
            for line in Path(f"/proc/{p}/smaps_rollup").read_text().splitlines():
                k, _, v = line.partition(":")
                if v.strip().endswith("kB"):
                    fields[k] = int(v.split()[0]) / 1024
        except (FileNotFoundError, ProcessLookupError):
            continue
        into = left_out if comm in HELPERS else counted
        into[name] = into.get(name, 0.0) + fields.get("Pss", 0.0)
        if comm not in HELPERS:
            kinds["anon"] += fields.get("Pss_Anon", 0.0)
            kinds["file"] += fields.get("Pss_File", 0.0)
            kinds["shmem"] += fields.get("Pss_Shmem", 0.0)
    return {"processes": counted, "left_out": left_out, "kinds": kinds}


def cpu_seconds(pid):
    tick = os.sysconf("SC_CLK_TCK")
    total = 0
    for p in terminal_pids(pid):
        try:
            fields = Path(f"/proc/{p}/stat").read_text().rsplit(")", 1)[1].split()
            total += int(fields[11]) + int(fields[12])
        except (FileNotFoundError, ProcessLookupError):
            pass
    return total / tick


def gpu_mib(pid):
    if not shutil.which("nvidia-smi"):
        return 0
    pids = family(pid)
    total = 0
    for line in subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=False).stdout.splitlines():
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
    sources = memory_sources(run.p.pid)
    vram = gpu_mib(run.p.pid)
    xserver = xserver_mib(run.p.pid)
    run.stop()
    return {"pss": pss, "uss": uss, "rss": rss, "vram": vram, "xserver": xserver, "cpu": cpu,
            **sources}


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
    # Only the first row changes, and the top quarter holds it below any tab
    # bar or padding.
    box = (0, 0, 160, w.get_geometry().height // 4)
    keys = [d.keysym_to_keycode(ord(c)) for c in "ab"]
    lat = []
    for i in range(samples):
        time.sleep(0.05 + random.random() * 0.1)
        ensure_focus(run.p, w)
        # Events already queued are dropped before `report` is emptied: one
        # that comes after it stays for the loop below, which empties it again.
        d.sync()
        while d.pending_events():
            d.next_event()
        d.damage_subtract(report)
        before = region(w, *box)
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
# compare.
# Every line is numbered, so no two moments of the stream look the same: a
# terminal that sends nothing for a frame identical to the last one would
# otherwise show a gap where nothing on screen changed.
STREAM = r'''
import os, select, signal, tty
tty.setraw(0)
# A resize resets the scroll region, so the layout is set again after each.
resized = True
def on_resize(*_):
    global resized
    resized = True
signal.signal(signal.SIGWINCH, on_resize)
colors = [f"\x1b[38;5;{16 + 7 * i}m" for i in range(30)]
lines = [("".join(f"{colors[(i + j) % 30]}word{j:02d} " for j in range(12)) + "\x1b[0m\r\n").encode()
    for i in range(64)]
def put(data):
    view = memoryview(data)
    while view:
        view = view[os.write(1, view):]
start = 0
while True:
    if resized:
        resized = False
        rows = os.get_terminal_size(1).lines
        put(f"\x1b[?25l\x1b[2J\x1b[6;{rows}r\x1b[{rows};1H".encode())
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
        while True:
            e = next_event(run.p)
            if e.type == d.extension_event.DamageNotify and e.damage == report:
                break
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
        if (e.type == d.extension_event.DamageNotify and e.damage == raw
                and time.perf_counter() - t0 >= 1):
            stamps.append(e.timestamp)
    d.damage_destroy(raw)
    # `report` notifies only once its damage is emptied, and the frames above
    # left it damaged.
    d.damage_subtract(report)
    frames = []
    for k, t in enumerate(stamps):
        if k == 0 or t - stamps[k - 1] > FRAME_SPREAD_MS:
            frames.append(t)
    gaps = [b - a for a, b in itertools.pairwise(frames)]
    # The first pixel row a new frame of scrolling output changes: everything
    # above it is the fixed rows, wherever the terminal's chrome puts them.
    height, row = w.get_geometry().height, 160 * 4
    before = region(w, 0, 0, 160, height)
    after = before
    while after == before:
        next_frame()
        after = region(w, 0, 0, 160, height)
    top = next(y for y in range(height) if before[y * row:(y + 1) * row] != after[y * row:(y + 1) * row])
    box = (0, 0, 160, top)
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


def screen_image():
    g = root.get_geometry()
    return root.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xFFFFFFFF).data, g.width


def painted_text(w, before):
    """Whether the middle of `w` shows text the terminal drew: more than two
    colors, unlike what screen image `before` held there, which a window that
    has not drawn yet shows without a compositor."""
    # The middle of the window is text area in every terminal, below any tab
    # bar or padding, and a screenful of output reaches it.
    g = w.get_geometry()
    top = g.height // 2 - 30
    try:
        data = region(w, 0, top, 200, 60)
        x, y, _, _ = rect(w)
    except error.XError:
        return False
    if len({data[i:i + 4] for i in range(0, len(data), 4)}) <= 2:
        return False
    screen, sw = before
    under = b"".join(screen[((y + top + r) * sw + x) * 4:((y + top + r) * sw + x + 200) * 4]
                     for r in range(60))
    return data != under


def startup(term):
    """Milliseconds from launch until a screenful of output is on screen."""
    before = screen_image()
    p = launch(term, "seq 200 | sed 's/.*/READY/'; exec sleep 100000")
    w = wait_window(p)
    while w.get_attributes().map_state != X.IsViewable:
        next_event(p)
    d.damage_query_version()
    report = w.damage_create(damage.DamageReportNonEmpty)
    while not painted_text(w, before):
        while next_event(p).type != d.extension_event.DamageNotify:
            pass
        d.damage_subtract(report)
    ms = (time.perf_counter() - p.started) * 1000
    check_uncovered(w)
    end(p)
    return ms


def started_from(home):
    """Processes a launch from configuration folder `home` started, wherever
    they were reparented: each has the folder in its environment, or its bus
    there."""
    return with_environ(f"XDG_CONFIG_HOME={home}\0".encode(),
                        f"DBUS_SESSION_BUS_ADDRESS=unix:path={home}/".encode())


def leftovers():
    """Processes still running from any launch."""
    return with_environ(f"XDG_CONFIG_HOME={OUT / 'run'}/cfg-".encode(),
                        f"DBUS_SESSION_BUS_ADDRESS=unix:path={OUT / 'run'}/cfg-".encode())


def with_environ(*marks):
    found = []
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            environ = Path(f"/proc/{pid}/environ").read_bytes()
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
    started = time.monotonic()

    def wanted(kind):
        return not only or kind in only

    results = json.loads(out.read_text()) if out.exists() else {}

    def label_of(term):
        base = term.removesuffix(QUICK)
        name = LABEL if base == "waftty" else base
        return f"{name} quick" if term.endswith(QUICK) else name

    # A measure this run takes replaces that terminal's earlier samples of it;
    # the ones it does not take (--only, --terminals) are kept.
    taken = set()

    def put(term, key, value):
        samples = results.setdefault(label_of(term), {})
        if (label_of(term), key) not in taken:
            taken.add((label_of(term), key))
            samples[key] = []
        samples[key].append(value)
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
                each(f"tp_{name}", lambda t, name=name: throughput(t, name))
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
    took = round(time.monotonic() - started)
    meta.update({"scrollback": SCROLLBACK, "window": [W, H], "vsync_off": not monitor_connected(),
                 "run_seconds": took, "finished": time.strftime("%Y-%m-%d %H:%M %Z")})
    meta.setdefault("versions", {}).update({label_of(t): v for t, v in versions(terms).items()})
    results["_meta"] = meta
    out.write_text(json.dumps(results, indent=1))
    print(f"done in {duration(took)}")



def versions(terms):
    out = {}
    for term in terms:
        exe = program(term)
        try:
            v = subprocess.run([exe, "--version"], capture_output=True, text=True, check=False).stdout
            out[term] = v.strip().splitlines()[0] if v.strip() else ""
        except OSError:
            out[term] = ""
    return out


def main():
    global SCROLLBACK, WAFTTY, LABEL
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["inputs", "run"])
    ap.add_argument("--terminals", default="waftty,waftty-quick,xfce4-terminal,guake,alacritty,"
                    "kitty,ghostty,wezterm,rio")
    ap.add_argument("--waftty", default="waftty", help="waftty executable to measure")
    ap.add_argument("--label", default="waftty", help="the name waftty's results go under")
    ap.add_argument("--runs", type=int, default=3, help="repetitions of RAM and throughput")
    ap.add_argument("--scrollback", type=int, default=SCROLLBACK)
    ap.add_argument("--only", default="", help="comma-separated: ram, throughput, cpu, latency, streaming, startup")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results.json",
                    help="results file (default: linux/results.json)")
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
    unknown = [t for t in terms if t not in TERMS]
    if unknown:
        raise SystemExit(f"unknown terminals: {', '.join(unknown)}; choose from {', '.join(TERMS)}")
    missing = [t for t in terms if not shutil.which(program(t))]
    if missing:
        raise SystemExit(f"not installed: {', '.join(missing)}")
    bound = [t for t in terms if t in VBLANK_BOUND]
    if bound and not monitor_connected():
        raise SystemExit(f"{', '.join(bound)} paces itself by a monitor's vblank: connect or wake "
                         "a monitor to measure it")
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
