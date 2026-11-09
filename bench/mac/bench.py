"""RAM, CPU, throughput, latency and startup of terminals on macOS.

    uv run mac/bench.py inputs                  # writes the test inputs
    uv run mac/bench.py run [--terminals waftty,iterm2,...] [--waftty PATH]
    uv run report.py mac                        # charts and RESULTS.md

The Linux harness's measures, taken through macOS's own interfaces: memory is
each process's physical footprint (Activity Monitor's figure), keys go in as
Quartz events, and pixels come from window captures. Each terminal runs on its
defaults with the same scrollback (--scrollback, 10,000 lines) and a 1000x700
window. Results go to mac/results.json unless --out names another file; the
inputs and each run's folders stay in ~/Library/Caches/waftty-bench.

The process running this script needs Accessibility (to size windows and
type) and Screen Recording (to read pixels) in System Settings, Privacy &
Security.
"""

import argparse
import ctypes
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

import psutil
import Quartz
from AppKit import NSApplicationActivateIgnoringOtherApps, NSRunningApplication
from ApplicationServices import (
    AXIsProcessTrusted,
    AXUIElementCopyAttributeValue,
    AXUIElementCreateApplication,
    AXUIElementPerformAction,
    AXUIElementSetAttributeValue,
    AXValueCreate,
    kAXPositionAttribute,
    kAXRaiseAction,
    kAXSizeAttribute,
    kAXValueCGPointType,
    kAXValueCGSizeType,
    kAXWindowsAttribute,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from timing import duration  # noqa: E402

W, H = 1000, 700
OUT = Path.home() / "Library" / "Caches" / "waftty-bench"
INPUT_BYTES = 20 * 1024 * 1024
INPUTS = ("plain", "sgr", "unicode")
SCROLLBACK = 10_000
WAFTTY = "waftty"
LABEL = "waftty"
PYTHON = sys.executable
QUICK = "-quick"
ITERM_PROFILE = "waftty bench"

# Processes that are not the terminal: its shell, the login wrapper some
# terminals start it through, and the test commands.
HELPERS = {"sh", "bash", "zsh", "login", "cat", "head", "sleep", "python3", "Python", "python"}

# Where each terminal's executable lives when it is not on the PATH.
APPS = {
    "waftty": "/Applications/waftty.app/Contents/MacOS/waftty",
    "alacritty": "/Applications/Alacritty.app/Contents/MacOS/alacritty",
    "kitty": "/Applications/kitty.app/Contents/MacOS/kitty",
    "wezterm": "/Applications/WezTerm.app/Contents/MacOS/wezterm",
    "rio": "/Applications/Rio.app/Contents/MacOS/rio",
}

# Terminals macOS starts as applications through Launch Services, found by
# bundle identifier once running.
BUNDLES = {
    "ghostty": ("/Applications/Ghostty.app", "com.mitchellh.ghostty"),
    "iterm2": ("/Applications/iTerm.app", "com.googlecode.iterm2"),
}


def executable(name):
    if name == "waftty" and WAFTTY != "waftty":
        return WAFTTY
    return shutil.which(name) or (APPS[name] if Path(APPS.get(name, "")).exists() else None)


def installed(term):
    base = term.removesuffix(QUICK)
    if base in BUNDLES:
        return Path(BUNDLES[base][0]).exists()
    return executable(base) is not None


def command(term, cmd):
    """The argv that starts `term` running `cmd`, for terminals started directly."""
    sh = ["sh", "-c", cmd]
    base = term.removesuffix(QUICK)
    exe = executable(base)
    if base == "waftty":
        return [exe, *(["--quick"] if term.endswith(QUICK) else []), "-e", *sh]
    if base == "alacritty":
        return [exe, "-o", f"scrolling.history={SCROLLBACK}", "-e", *sh]
    if base == "kitty":
        return [exe, "--config=NONE", "-o", f"scrollback_lines={SCROLLBACK}", *sh]
    if base == "wezterm":
        return [exe, "-n", "--config", f"scrollback_lines={SCROLLBACK}", "start",
                "--always-new-process", "--", *sh]
    if base == "rio":
        return [exe, "-e", *sh]
    raise ValueError(term)


def environment(term, home):
    """The environment `term` starts in: waftty keeps its settings and its
    single-instance claim under HOME, so a HOME of the run's own keeps it apart
    from any waftty already running; rio reads its configuration folder."""
    env = dict(os.environ)
    base = term.removesuffix(QUICK)
    if base == "waftty":
        env["HOME"] = home
        settings = Path(home) / "Library" / "Application Support" / "dev.gossamer.waftty"
        settings.mkdir(parents=True, exist_ok=True)
        (settings / "settings.json").write_text(json.dumps(
            {"values": {"scrollback": str(SCROLLBACK),
                        "drop_down_key": "Ctrl+Alt+Shift+F8"}, "version": 2}))
    elif base == "rio":
        env["RIO_CONFIG_HOME"] = home
        Path(home, "config.toml").write_text(
            f"scrollback-history-limit = {SCROLLBACK}\nconfirm-before-quit = false\n")
    return env


def iterm_profile():
    """A dynamic profile with the run's scrollback, which iTerm2 loads at launch."""
    folder = Path.home() / "Library" / "Application Support" / "iTerm2" / "DynamicProfiles"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "waftty-bench.json").write_text(json.dumps({"Profiles": [{
        "Name": ITERM_PROFILE, "Guid": "waftty-bench", "Scrollback Lines": SCROLLBACK,
        "Close Sessions On End": True, "Prompt Before Closing 2": 0}]}))
    return folder / "waftty-bench.json"


def ghostty_scrollback():
    """The scrollback flag, where this Ghostty counts it in lines; released
    versions count bytes and keep their default."""
    exe = Path(BUNDLES["ghostty"][0]) / "Contents" / "MacOS" / "ghostty"
    defaults = subprocess.run([str(exe), "+show-config", "--default"], capture_output=True,
                              text=True, check=False).stdout
    return [f"--scrollback-limit-lines={SCROLLBACK}"] if "scrollback-limit-lines" in defaults else []


def running(bundle):
    return {a.processIdentifier() for a in
            NSRunningApplication.runningApplicationsWithBundleIdentifier_(bundle)}


# The launches not yet ended, which the run ends however it stops.
LIVE = set()


class Launch:
    """A terminal started for one measurement, and the processes it owns."""

    def __init__(self, term, cmd):
        self.term = term
        self.owner = None
        self.home = tempfile.mkdtemp(dir=OUT / "run", prefix=f"cfg-{term}-")
        base = term.removesuffix(QUICK)
        self.started = time.perf_counter()
        if base in BUNDLES:
            app, bundle = BUNDLES[base]
            # The command reaches the application as a script file, so no
            # quoting passes through AppleScript or Launch Services.
            script = Path(self.home, "run.sh")
            script.write_text(cmd + "\n")
            before = running(bundle)
            if base == "iterm2":
                # iTerm2 may open a window of its own as it starts; the run keeps
                # only the one it asks for.
                subprocess.run(["osascript", "-e", f'''tell application id "{bundle}"
                    set made to (create window with profile "{ITERM_PROFILE}" command "sh {script}")
                    set keep to id of made
                    repeat with other in (windows whose id is not keep)
                        close other
                    end repeat
                end tell'''], check=True, capture_output=True)
            else:
                subprocess.run(["open", "-na", app, "--args", "--config-default-files=false",
                                *ghostty_scrollback(), "-e", "sh", str(script)], check=True)
            self.pid = self._new_pid(bundle, before)
            self.popen = None
        else:
            self.popen = subprocess.Popen(command(term, cmd), env=environment(term, self.home),
                                          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL, start_new_session=True)
            self.pid = self.popen.pid
        LIVE.add(self)

    @staticmethod
    def _new_pid(bundle, before, timeout=20):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            new = running(bundle) - before
            if new:
                return new.pop()
            time.sleep(0.05)
        raise SystemExit(f"{bundle} did not start")

    def alive(self):
        return psutil.pid_exists(self.pid)

    def family(self):
        """The started process and every process under it."""
        try:
            root = psutil.Process(self.pid)
            return [root, *root.children(recursive=True)]
        except psutil.NoSuchProcess:
            return []

    def processes(self):
        """The terminal's own processes: the one started and its descendants,
        leaving out its shell and the test commands."""
        found = []
        for p in self.family():
            try:
                if p.name() not in HELPERS:
                    found.append(p)
            except psutil.NoSuchProcess:
                pass
        return found

    def end(self):
        LIVE.discard(self)
        for p in reversed(self.processes()):
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        try:
            psutil.Process(self.pid).wait(5)
        except psutil.TimeoutExpired:
            os.kill(self.pid, signal.SIGKILL)
        except psutil.NoSuchProcess:
            pass
        shutil.rmtree(self.home, ignore_errors=True)


# Application windows sit below the menu bar's level: normal ones at 0, and
# floating ones, such as a drop-down terminal kept above the others, higher.
MENU_LAYER = Quartz.CGWindowLevelForKey(Quartz.kCGMainMenuWindowLevelKey)


def app_layer(w):
    return 0 <= w["kCGWindowLayer"] < MENU_LAYER


def windows(pid):
    info = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID)
    return [w for w in info if w["kCGWindowOwnerPID"] == pid and app_layer(w)]


def shown_window(launch, timeout=30):
    """The terminal's largest on-screen window, once it has one; the process
    that owns it, which can be a child of the one started, becomes
    `launch.owner`."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if not launch.alive():
            raise SystemExit(f"{launch.term} exited before showing a window")
        shown = [w for p in launch.family() for w in windows(p.pid)]
        if shown:
            w = max(shown, key=lambda w: w["kCGWindowBounds"]["Width"] * w["kCGWindowBounds"]["Height"])
            launch.owner = w["kCGWindowOwnerPID"]
            return w
        time.sleep(0.02)
    raise SystemExit(f"{launch.term} showed no window")


def window_of(launch):
    return shown_window(launch)["kCGWindowNumber"]


def located(launch, wid):
    """The number and frame of the terminal's window: `wid` while it is on
    screen, otherwise the one the terminal shows now, since a terminal can
    change windows as it starts (iTerm2 closes the one it opens at launch)."""
    w = next((w for w in windows(launch.owner) if w["kCGWindowNumber"] == wid), None)
    w = w or shown_window(launch)
    b = w["kCGWindowBounds"]
    return w["kCGWindowNumber"], (b["X"], b["Y"], b["Width"], b["Height"])


def ax_window(pid):
    app = AXUIElementCreateApplication(pid)
    err, wins = AXUIElementCopyAttributeValue(app, kAXWindowsAttribute, None)
    if err or not wins:
        return None
    return wins[0]


def place(launch, wid):
    """Moves the window to the top left of the main display at the run's size,
    a drop-down terminal keeping the place it docks itself to, and answers the
    number of the window it placed."""
    win = None
    end = time.monotonic() + 10
    while win is None and time.monotonic() < end:
        win = ax_window(launch.owner)
        time.sleep(0.05)
    if win is None:
        raise SystemExit(f"{launch.term}: its window is not reachable through Accessibility")
    if not launch.term.endswith(QUICK):
        for _ in range(20):
            win = ax_window(launch.owner) or win
            AXUIElementSetAttributeValue(win, kAXPositionAttribute,
                                         AXValueCreate(kAXValueCGPointType, Quartz.CGPoint(40, 60)))
            AXUIElementSetAttributeValue(win, kAXSizeAttribute,
                                         AXValueCreate(kAXValueCGSizeType, Quartz.CGSize(W, H)))
            time.sleep(0.1)
            wid, frame = located(launch, wid)
            if frame[2:] == (W, H):
                break
    focus(launch)
    return wid


def in_front(owner):
    """Whether `owner`'s window is the foremost of its level. The Dock and other
    applications' floating windows sit at higher levels and stay above it however
    it is raised."""
    listed = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID)
    own = next((w for w in listed if w["kCGWindowOwnerPID"] == owner and app_layer(w)), None)
    if own is None:
        return False
    top = next(w for w in listed if w["kCGWindowLayer"] == own["kCGWindowLayer"])
    return top["kCGWindowOwnerPID"] == owner


def focus(launch):
    app = NSRunningApplication.runningApplicationWithProcessIdentifier_(launch.owner)
    if app is not None:
        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    win = ax_window(launch.owner)
    if win is not None:
        AXUIElementPerformAction(win, kAXRaiseAction)
    end = time.monotonic() + 5
    while time.monotonic() < end:
        if in_front(launch.owner):
            return
        time.sleep(0.02)
    raise SystemExit(f"{launch.term}: its window did not come to the front")


def capture(wid, rect):
    """The pixels of `rect` (window points) of window `wid`, as bytes."""
    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectMake(*rect), Quartz.kCGWindowListOptionIncludingWindow, wid,
        Quartz.kCGWindowImageBoundsIgnoreFraming | Quartz.kCGWindowImageNominalResolution)
    if image is None:
        raise SystemExit("window capture failed: grant Screen Recording to this terminal")
    return bytes(Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image)))


# The ANSI key codes of the two letters typed in turn.
KEYS = (0, 11)


def press(code):
    for down in (True, False):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap,
                           Quartz.CGEventCreateKeyboardEvent(None, code, down))


class Run:
    """A terminal running `script` once its window is placed: `start` lets the
    script go, and `signal` waits for the line it writes to its pipe."""

    def __init__(self, term, script):
        tmp = tempfile.mkdtemp(dir=OUT / "run")
        self.go, self.done = f"{tmp}/go", f"{tmp}/done"
        os.mkfifo(self.go)
        os.mkfifo(self.done)
        self.go_fd = os.open(self.go, os.O_RDWR)
        self.done_fd = os.open(self.done, os.O_RDWR | os.O_NONBLOCK)
        script = script.replace("$DONE", self.done)
        self.launch = Launch(term, f"head -n1 {self.go} >/dev/null; {script}")
        self.wid = place(self.launch, window_of(self.launch))

    def start(self):
        os.write(self.go_fd, b"go\n")

    def signal(self, timeout=600):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if not self.launch.alive():
                raise SystemExit(f"{self.launch.term} exited during the run")
            ready, _, _ = select.select([self.done_fd], [], [], 0.5)
            if ready:
                return os.read(self.done_fd, 4096).decode()
        raise SystemExit(f"{self.launch.term}: the script did not finish")

    def stop(self):
        self.launch.end()
        os.close(self.go_fd)
        os.close(self.done_fd)


class RusageInfoV2(ctypes.Structure):
    _fields_ = [("uuid", ctypes.c_uint8 * 16), ("user_time", ctypes.c_uint64),
                ("system_time", ctypes.c_uint64), ("pkg_idle_wkups", ctypes.c_uint64),
                ("interrupt_wkups", ctypes.c_uint64), ("pageins", ctypes.c_uint64),
                ("wired_size", ctypes.c_uint64), ("resident_size", ctypes.c_uint64),
                ("phys_footprint", ctypes.c_uint64), ("proc_start_abstime", ctypes.c_uint64),
                ("proc_exit_abstime", ctypes.c_uint64), ("child_user_time", ctypes.c_uint64),
                ("child_system_time", ctypes.c_uint64), ("child_pkg_idle_wkups", ctypes.c_uint64),
                ("child_interrupt_wkups", ctypes.c_uint64), ("child_pageins", ctypes.c_uint64),
                ("child_elapsed_abstime", ctypes.c_uint64), ("diskio_bytesread", ctypes.c_uint64),
                ("diskio_byteswritten", ctypes.c_uint64)]


_libproc = ctypes.CDLL("/usr/lib/libproc.dylib")
RUSAGE_INFO_V2 = 2


def footprint_mib(pid):
    """The physical footprint of process `pid`: its own dirty and compressed
    memory, the figure Activity Monitor shows as Memory."""
    info = RusageInfoV2()
    if _libproc.proc_pid_rusage(pid, RUSAGE_INFO_V2, ctypes.byref(info)) != 0:
        return 0.0
    return info.phys_footprint / 2**20


def memory(launch):
    footprint = rss = 0.0
    processes = {}
    for p in launch.processes():
        try:
            mib = footprint_mib(p.pid)
            footprint += mib
            rss += p.memory_info().rss / 2**20
            processes[p.name()] = processes.get(p.name(), 0.0) + mib
        except psutil.NoSuchProcess:
            pass
    return footprint, rss, processes


def cpu_seconds(launch):
    total = 0.0
    for p in launch.processes():
        try:
            t = p.cpu_times()
            total += t.user + t.system
        except psutil.NoSuchProcess:
            pass
    return total


def settled_memory(launch):
    """Memory once it stops moving: two readings a second apart within 1%."""
    last = memory(launch)
    for _ in range(30):
        time.sleep(1)
        now = memory(launch)
        if abs(now[0] - last[0]) <= 0.01 * max(now[0], 1):
            return now
        last = now
    return last


def ram(term, files):
    """Memory after `files` print (none: idle), and the CPU time printing them took."""
    load = f"cat {' '.join(str(OUT / f'{n}.txt') for n in files)}; " if files else ""
    run = Run(term, f"{load}echo > $DONE; exec sleep 100000")
    before = cpu_seconds(run.launch)
    run.start()
    run.signal()
    cpu = cpu_seconds(run.launch) - before
    footprint, rss, processes = settled_memory(run.launch)
    run.stop()
    return {"footprint": footprint, "rss": rss, "cpu": cpu, "processes": processes}


def idle_cpu(term, seconds=10):
    """Share of one core the terminal uses while idle with a blinking cursor."""
    run = Run(term, "echo > $DONE; exec sleep 100000")
    run.start()
    run.signal()
    time.sleep(3)
    before = cpu_seconds(run.launch)
    time.sleep(seconds)
    used = cpu_seconds(run.launch) - before
    run.stop()
    return 100 * used / seconds


def load_cpu(term):
    """CPU the terminal uses while 20 MiB of plain and 20 MiB of colored text print."""
    files = " ".join(str(OUT / f"{n}.txt") for n in ("plain", "sgr"))
    run = Run(term, f"cat {files}; echo > $DONE; exec sleep 100000")
    before = cpu_seconds(run.launch)
    t0 = time.perf_counter()
    run.start()
    run.signal()
    used = cpu_seconds(run.launch) - before
    seconds = time.perf_counter() - t0
    run.stop()
    return {"percent": 100 * used / seconds, "seconds": used}


# Times `cat` of a file from inside the terminal, writing the nanoseconds to
# the run's pipe; macOS's date has no sub-second format.
TIMED_CAT = ("import subprocess, sys, time; t = time.perf_counter_ns(); "
             "subprocess.run(['cat', sys.argv[1]]); "
             "open(sys.argv[2], 'w').write(f'{time.perf_counter_ns() - t}\\n')")


def throughput(term, name):
    """Milliseconds for `cat` of an input to finish inside the terminal."""
    timer = OUT / "timed_cat.py"
    timer.write_text(TIMED_CAT)
    run = Run(term, f'{PYTHON} {timer} {OUT / f"{name}.txt"} $DONE; exec sleep 100000')
    run.start()
    ns = int(run.signal().strip())
    run.stop()
    return ns / 1e6


ECHO = ("import os,tty; tty.setraw(0); os.write(1, b'\\x1b[?25l\\x1b[2J\\x1b[H'); "
        "[os.write(1, b'\\r' + c) for c in iter(lambda: os.read(0, 1), b'q')]")


def wait_change(wid, rect, before, timeout=5):
    """Seconds until `rect` of window `wid` differs from `before`, and how long
    one capture took, which bounds the reading's precision."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        c0 = time.perf_counter()
        now = capture(wid, rect)
        if now != before:
            return c0, time.perf_counter() - c0
    raise SystemExit("the echoed key never showed")


def latency(term, samples=65):
    """Milliseconds from a key event until the echoed character's pixels change."""
    run = Run(term, f'exec {PYTHON} -c "{ECHO}"')
    run.start()
    run.wid, (x, y, w, h) = located(run.launch, run.wid)
    rect = (x, y, 160, h // 4)
    lat = []
    for i in range(samples):
        time.sleep(0.05 + random.random() * 0.1)
        focus(run.launch)
        before = capture(run.wid, rect)
        t0 = time.perf_counter()
        press(KEYS[i % 2])
        seen, _ = wait_change(run.wid, rect, before)
        lat.append((seen - t0) * 1000)
    run.stop()
    return lat[5:]


STREAM_SOURCE = Path(__file__).resolve().parent.parent / "linux" / "bench.py"


def stream_program():
    """The flood the Linux harness streams: the same program on both systems."""
    text = STREAM_SOURCE.read_text()
    start = text.index("STREAM = r'''") + len("STREAM = r'''")
    return text[start:text.index("'''", start)]


def streaming(term, samples=25):
    """From a key press until its echo shows in the fixed top row while a
    program floods colored output below it."""
    program = OUT / "stream.py"
    program.write_text(stream_program())
    run = Run(term, f"exec {PYTHON} {program}")
    run.start()
    time.sleep(1)
    run.wid, (x, y, w, h) = located(run.launch, run.wid)
    strip = (x, y, 160, h)
    before = capture(run.wid, strip)
    after = before
    while after == before:
        after = capture(run.wid, strip)
    row = len(before) // h
    top = next(r for r in range(h) if before[r * row:(r + 1) * row] != after[r * row:(r + 1) * row])
    rect = (x, y, 160, max(top, 1))
    lat = []
    for i in range(samples):
        time.sleep(0.05 + random.random() * 0.1)
        focus(run.launch)
        before = capture(run.wid, rect)
        t0 = time.perf_counter()
        press(KEYS[i % 2])
        seen, _ = wait_change(run.wid, rect, before)
        lat.append((seen - t0) * 1000)
    run.stop()
    return {"latency": lat}


def startup(term):
    """Milliseconds from launch until a screenful of output is on screen."""
    launch = Launch(term, "seq 200 | sed 's/.*/READY/'; exec sleep 100000")
    wid, (x, y, w, h) = located(launch, window_of(launch))
    rect = (x, y + h // 2 - 30, 200, 60)
    while True:
        data = capture(wid, rect)
        if len({data[i:i + 4] for i in range(0, len(data), 4)}) > 2:
            break
        if time.perf_counter() - launch.started > 30:
            raise SystemExit(f"{term} showed no text")
    ms = (time.perf_counter() - launch.started) * 1000
    launch.end()
    return ms


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


def label_of(term):
    base = term.removesuffix(QUICK)
    name = LABEL if base == "waftty" else base
    return f"{name} quick" if term.endswith(QUICK) else name


def versions(terms):
    out = {}
    for term in terms:
        base = term.removesuffix(QUICK)
        if base in BUNDLES:
            plist = Path(BUNDLES[base][0]) / "Contents" / "Info.plist"
            v = subprocess.run(["defaults", "read", str(plist), "CFBundleShortVersionString"],
                               capture_output=True, text=True, check=False).stdout.strip()
            out[term] = f"{base} {v}" if v else ""
            continue
        try:
            v = subprocess.run([executable(base), "--version"], capture_output=True, text=True,
                               check=False).stdout.strip()
            out[term] = v.splitlines()[0] if v else ""
        except OSError:
            out[term] = ""
    return out


def measure(terms, runs, out, only):
    started = time.monotonic()
    # A display that sleeps or locks during an unattended run takes the
    # terminals' windows off screen; caffeinate ends with this process.
    subprocess.Popen(["caffeinate", "-d", "-i", "-w", str(os.getpid())])

    def wanted(kind):
        return not only or kind in only

    results = json.loads(out.read_text()) if out.exists() else {}
    taken = set()

    # On disk from the start, so the report can read a run that stops early;
    # only a run that finishes says when it finished.
    meta = results.setdefault("_meta", {})
    meta.pop("run_seconds", None)
    meta.pop("finished", None)
    meta.update({"platform": "macos", "scrollback": SCROLLBACK, "window": [W, H],
                 "os": subprocess.run(["sw_vers", "-productVersion"], capture_output=True,
                                      text=True, check=False).stdout.strip()})
    out.write_text(json.dumps(results, indent=1))

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
    # Saved as each is taken, so a run that stops early keeps what it measured.
    def keep(term, key, value):
        results.setdefault(label_of(term), {})[key] = value
        out.write_text(json.dumps(results, indent=1))

    for term in terms:
        if wanted("latency"):
            keep(term, "latency", latency(term))
        if wanted("streaming"):
            keep(term, "streaming", streaming(term))
        if wanted("startup"):
            keep(term, "startup", [startup(term) for _ in range(10)])
    meta = results["_meta"]
    took = round(time.monotonic() - started)
    meta.update({"run_seconds": took, "finished": time.strftime("%Y-%m-%d %H:%M %Z")})
    meta.setdefault("versions", {}).update({label_of(t): v for t, v in versions(terms).items()})
    results["_meta"] = meta
    out.write_text(json.dumps(results, indent=1))
    print(f"done in {duration(took)}")


def main():
    global SCROLLBACK, WAFTTY, LABEL
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["inputs", "run"])
    ap.add_argument("--terminals", default="waftty,waftty-quick,iterm2,alacritty,kitty,ghostty,"
                    "wezterm,rio")
    ap.add_argument("--waftty", default="waftty", help="waftty executable to measure")
    ap.add_argument("--label", default="waftty", help="the name waftty's results go under")
    ap.add_argument("--runs", type=int, default=3, help="repetitions of RAM and throughput")
    ap.add_argument("--scrollback", type=int, default=SCROLLBACK)
    ap.add_argument("--only", default="", help="comma-separated: ram, throughput, cpu, latency, streaming, startup")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results.json",
                    help="results file (default: mac/results.json)")
    a = ap.parse_args()
    if a.command == "inputs":
        write_inputs()
        print(f"inputs written to {OUT}")
        return
    SCROLLBACK, WAFTTY, LABEL = a.scrollback, a.waftty, a.label
    if not AXIsProcessTrusted():
        raise SystemExit("grant Accessibility to this terminal in System Settings, "
                         "Privacy & Security, then run again")
    if not all((OUT / f"{n}.txt").exists() for n in INPUTS):
        write_inputs()
    (OUT / "run").mkdir(parents=True, exist_ok=True)
    terms = [t for t in a.terminals.split(",") if t]
    known = {"waftty", "waftty-quick", "iterm2", "alacritty", "kitty", "ghostty", "wezterm", "rio"}
    unknown = [t for t in terms if t not in known]
    if unknown:
        raise SystemExit(f"unknown terminals: {', '.join(unknown)}; choose from {', '.join(sorted(known))}")
    missing = [t for t in terms if not installed(t)]
    if missing:
        raise SystemExit(f"not installed: {', '.join(missing)}")
    # iTerm2 runs every window in one process: one already open would take the
    # run's windows and its memory would count.
    if "iterm2" in terms and running(BUNDLES["iterm2"][1]):
        raise SystemExit("quit iTerm2 before measuring it")
    profile = iterm_profile() if "iterm2" in terms else None
    try:
        measure(terms, a.runs, a.out, {k for k in a.only.split(",") if k})
    finally:
        # A run that stops early leaves no terminal behind waiting on its pipe.
        for launch in list(LIVE):
            launch.end()
        if profile is not None:
            profile.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
