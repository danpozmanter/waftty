#!/usr/bin/env bash
# Writes the link order scripts/package.sh hands the linker: first the
# functions a session keeps running once its first frame is shown (the session
# profile), hottest first; then, between the engine's startup markers, the
# ones only startup or an occasional feature (the journey profile) runs. The
# engine releases that second run once the window is up, and a feature used
# later reads its pages back.
#
# Usage: scripts/link-order.sh [OUTPUT]   (default build-data/link-order.txt)
#
# The order names functions by scripts/symbol-key.awk's keys, which hold
# across builds of the same sources, so one profile serves local and release
# builds; package.sh matches them to the names of the build it links. Rerun it
# when the code a session runs changes.
#
# The session profile is a real one: run it from an X11 desktop session with
# no waftty open, since a running waftty takes the launch. The window it opens
# talks to the desktop's portal and window manager as any session does, and
# python3-xlib drives it the way a user does.
# The journey profile is the scripted journey (--fixture), which runs
# offscreen on a bus of its own. Valgrind's slowdown moves work that starts
# asynchronously (portal replies, background jobs) to before the first frame,
# so the session then runs natively under gdb, and whatever runs there after
# the first frame joins the session part. Needs valgrind, gdb, python3-xlib
# and the Gossamer toolchain.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="${1:-$root/build-data/link-order.txt}"
die() { echo "error: $*" >&2; exit 1; }
for tool in valgrind gdb gos nm dbus-run-session dbus-send python3; do
    command -v "$tool" >/dev/null 2>&1 || die "$tool is not on the PATH"
done

[ -n "${DISPLAY:-}" ] || die "the session profile needs an X11 desktop session"
dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus \
    org.freedesktop.DBus.NameHasOwner string:dev.gossamer.waftty 2>/dev/null |
    grep -q "boolean false" || die "close waftty first (or no session bus is reachable)"

python3 -c "import Xlib.ext.xtest" 2>/dev/null || die "python3-xlib is not installed"

work="$(mktemp -d)"
# Services a profile's private session bus starts (the desktop portal) are
# adopted by the user's service manager and outlive that bus; each carries the
# profile's configuration folder in its environment.
end_work() {
    local environ
    for environ in /proc/[0-9]*/environ; do
        grep -qzF "XDG_CONFIG_HOME=$work/" "$environ" 2>/dev/null &&
            kill "$(basename "$(dirname "$environ")")" 2>/dev/null
    done
    rm -rf "$work"
}
trap end_work EXIT

# The build package.sh makes: code for a CPU every machine has (which valgrind
# also runs), in the release build environment.
. "$root/scripts/build-env.sh"
(cd "$root" && GOS_LLVM_MCPU=x86-64-v2 gos build --release . --out-dir "$work/build" >&2)
binary="$work/build/waftty"

# A user's session: the login shell's prompt, commands typed into it (colored
# listings, a long output, a link, the alternate screen), then resizing the
# window, moving the pointer through it, scrolling with the wheel, clicking
# it, moving focus to a window of the driver's own and back, a stretch of
# idle, and exit. The shell writes to a FIFO once it has run the commands, so
# the idle stretch starts after them.
cat > "$work/interact.py" <<'EOF'
import os, sys, time
from Xlib import X, XK, display, protocol
from Xlib.ext import xtest

launcher, ready = int(sys.argv[1]), sys.argv[2]
d = display.Display()
root = d.screen().root
NET_WM_PID = d.intern_atom("_NET_WM_PID")
NET_ACTIVE = d.intern_atom("_NET_ACTIVE_WINDOW")
NET_CLIENTS = d.intern_atom("_NET_CLIENT_LIST")

def family(pid):
    pids = {pid}
    try:
        for task in os.listdir(f"/proc/{pid}/task"):
            for child in open(f"/proc/{pid}/task/{task}/children").read().split():
                pids |= family(int(child))
    except FileNotFoundError:
        pass
    return pids

def clients():
    prop = root.get_full_property(NET_CLIENTS, X.AnyPropertyType)
    return [d.create_resource_object("window", w) for w in (prop.value if prop else [])]

def pid_of(w):
    prop = w.get_full_property(NET_WM_PID, X.AnyPropertyType)
    return prop.value[0] if prop else None

def ours():
    pids = family(launcher)
    return next((w for w in clients() if pid_of(w) in pids), None)

def activate(w):
    event = protocol.event.ClientMessage(window=w, client_type=NET_ACTIVE,
                                         data=(32, [2, X.CurrentTime, 0, 0, 0]))
    root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    d.flush()

def pace():
    d.sync()
    time.sleep(0.5)

# Keys go in at a fast typist's pace, one at a time.
def key(keysym):
    code = d.keysym_to_keycode(keysym)
    shift = d.keycode_to_keysym(code, 0) != keysym
    shift_code = d.keysym_to_keycode(XK.XK_Shift_L)
    if shift:
        xtest.fake_input(d, X.KeyPress, shift_code)
    xtest.fake_input(d, X.KeyPress, code)
    xtest.fake_input(d, X.KeyRelease, code)
    if shift:
        xtest.fake_input(d, X.KeyRelease, shift_code)
    d.sync()
    time.sleep(0.01)

def focused():
    w = d.get_input_focus().focus
    # The focus is a window, or a number for PointerRoot and None.
    while not isinstance(w, int) and w.id != root.id:
        if w.id == win.id:
            return True
        w = w.query_tree().parent
    return False

# Keystrokes go to whichever window has focus, so they are sent only while
# the session's own window has it; otherwise this waits for the window
# manager to say focus moved.
def ensure_focus():
    if focused():
        return
    activate(win)
    while not focused():
        print("link-order: waiting for the waftty window to take focus", file=sys.stderr)
        d.next_event()

# Latin-1 keysyms are the characters' own code points.
def type_line(text):
    ensure_focus()
    for ch in text:
        key(ord(ch))
    key(XK.XK_Return)
    pace()

# The window list changes when the window maps.
root.change_attributes(event_mask=X.PropertyChangeMask)
win = ours()
while win is None:
    d.next_event()
    win = ours()
# The window manager can name the window active before it moves the input
# focus there, so the wait for focus hears the window's own focus changes.
win.change_attributes(event_mask=X.FocusChangeMask)
activate(win)
pace()
type_line("ls -la --color=always /usr/bin | head -200")
type_line("seq 100000")
type_line("echo https://gossamer.dev/docs")
type_line("tput smcup; ls -la --color=always /usr/bin | head -60; tput cup 5 10; tput rmcup")
type_line(f"echo > {ready}")
open(ready).read()
win.configure(width=900, height=600)
pace()
geometry = win.get_geometry()
for i in range(1, 6):
    win.warp_pointer(geometry.width * i // 6, geometry.height * i // 6)
    pace()
for button in (4, 4, 4, 5, 5, 5):
    xtest.fake_input(d, X.ButtonPress, button)
    xtest.fake_input(d, X.ButtonRelease, button)
    pace()
xtest.fake_input(d, X.ButtonPress, 1)
xtest.fake_input(d, X.ButtonRelease, 1)
pace()
root.warp_pointer(0, 0)
pace()
# Focus moves to a window of the driver's own and back, leaving the user's
# windows alone.
other = root.create_window(0, 0, 200, 100, 0, d.screen().root_depth,
                           event_mask=X.StructureNotifyMask)
other.set_wm_name("link-order focus")
other.map()
while d.next_event().type != X.MapNotify:
    pass
activate(other)
pace()
ensure_focus()
other.destroy()
pace()
# A session spends most of its time idle: the cursor blinks, and work started
# with the window lands.
time.sleep(30)
# The user closes the window, its shell idle at the prompt.
close = protocol.event.ClientMessage(window=win, client_type=d.intern_atom("WM_PROTOCOLS"),
                                     data=(32, [d.intern_atom("WM_DELETE_WINDOW"), X.CurrentTime, 0, 0, 0]))
win.send_event(close)
d.flush()
EOF

# Runs one session of the program, as COMMAND... runs it, with the user's
# input; the program exits when the user closes its window.
session() {
    local ready="$1"
    shift
    rm -f "$ready"
    mkfifo "$ready"
    "$@" &
    local program=$!
    python3 "$work/interact.py" "$program" "$ready" &
    local user=$!
    wait "$program" || true
    kill "$user" 2>/dev/null || true
    wait "$user" 2>/dev/null || true
}

# Settings as a session that has saved some keeps them: an installed font
# (one waftty does not bundle), values of its own and a color scheme of the
# user's. With "default" the folder stays empty, as on a first launch. Each
# run starts from a fresh copy.
font="$(fc-list ':spacing=mono:fontformat=TrueType' family 2>/dev/null | cut -d, -f1 |
    grep -viE 'dejavu|ibm plex' | sort -u | head -n 1 || true)"
seed_config() {
    local dir="$1/dev.gossamer.waftty"
    mkdir -p "$dir"
    [ "${2:-}" != default ] || return 0
    printf '{"values":{"font":"%s","font_size":"11","scheme":"user:profile","scrollback":"2000"},"version":2}\n' \
        "$font" > "$dir/settings.json"
    cat > "$dir/scheme-profile.toml" <<'EOF'
name = "Profile"
appearance = "dark"
foreground = "#d8d8d8"
background = "#202428"
cursor = "#d8d8d8"
selection = "#3d6e99"
selection_text = "#ffffff"
ansi = [
  "#000000", "#cc0000", "#4e9a06", "#c4a000", "#3465a4", "#75507b", "#06989a", "#d3d7cf",
  "#555753", "#ef2929", "#8ae234", "#fce94f", "#729fcf", "#ad7fa8", "#34e2e2", "#eeeeec",
]
EOF
}

# Each function an executed instruction lies in, by the instructions' own
# cost, hottest first. Instructions are mapped to functions here. Where
# valgrind reads the program's symbol table it files the program's code under
# its path at link-time addresses; where it cannot, under "???" at run-time
# ones, offset by where it loaded the program, which depends on the machine's
# address space. Which happens varies between machines, so each profile is
# read at the offset that puts its calls on function starts. Valgrind names
# functions by symbol or by address to match, so the profile splits at the
# engine's startup end under either name.
nm -S --defined-only "$binary" | awk '$3 ~ /^[tTwW]$/ { print $1, $2, $4 }' > "$work/defined"
address() {
    awk -v m="$1" '$3 == m { print $1; found = 1 } END { exit !found }' "$work/defined" ||
        die "the binary has no $1; the engine predates startup release"
}
address gui_engine_startup_code_begin >/dev/null
address gui_engine_startup_code_end >/dev/null
base=$(valgrind --tool=none --trace-symtab=yes --trace-symtab-patt="*/$(basename "$binary")" \
    "$binary" --version 2>&1 | awk '!found && $2 == "avma" && $6 == "foff" && $7 == "0" { print $3; found = 1 }')
[ -n "$base" ] || die "valgrind did not report where it loads $binary"
split_at=$(printf '0x%016x' $((base + 0x$(address gui_engine_startup_complete))))

# Callgrind writes what ran before the first frame to <out>.1, and the rest
# of the session to <out> when the program exits.
callgrind() {
    local out="$1"
    shift
    seed_config "$out.config"
    XDG_CONFIG_HOME="$out.config" "$@" \
        valgrind --tool=callgrind --dump-instr=yes --dump-line=no \
        --dump-before=gui_engine_startup_complete --dump-before="$split_at" \
        --callgrind-out-file="$out" -q \
        "$binary" "${profile_args[@]}" \
        >"$out.log" 2>&1
}
profile_args=(--fixture)
callgrind "$work/journey.out" env SDL_VIDEO_DRIVER=offscreen dbus-run-session --
profile_args=()
# The session types its input through XTEST, which arrives in bursts while the
# program runs slowly under valgrind or gdb; IBus's XIM server drops and
# reorders keys that come that fast, so the profiled program opens no input
# method server. Its own key handling is the same either way.
im=XMODIFIERS=@im=none
session "$work/ready" callgrind "$work/output.out" env "$im"
for out in journey output; do
    [ -f "$work/$out.out.1" ] && [ -f "$work/$out.out" ] || {
        tail -n 40 "$work/$out.out.log" >&2
        die "the $out profile never reached gui_engine_startup_complete"
    }
done

mkdir -p "$(dirname "$output")"
python3 - "$base" "$work/defined" "$binary" "$work"/output.out "$work"/journey.out.1 "$work"/output.out.1 \
    "$work"/journey.out > "$work/names" <<'EOF'
import bisect, os, re, sys
LOAD_BASE = int(sys.argv[1], 16)
symbols = []
for line in open(sys.argv[2]):
    address, size, name = line.split()
    symbols.append((int(address, 16), int(size, 16), name))
symbols.sort()
starts = [a for a, _, _ in symbols]
binary = os.path.realpath(sys.argv[3])
session_part, startup_parts, feature_part = sys.argv[4], sys.argv[5:7], sys.argv[7]

def symbol(address):
    i = bisect.bisect_right(starts, address) - 1
    if i >= 0 and symbols[i][0] <= address < symbols[i][0] + symbols[i][1]:
        return symbols[i][2]
    return None

function_starts = set(starts)

# A compressed name line: "ob=(3) name" names id 3, a later "ob=(3)" reuses it.
def named(line, names):
    m = re.match(r"\w+=\((\d+)\)\s*(.*)", line)
    if not m:
        return line.split("=", 1)[1].strip()
    if m.group(2):
        names[m.group(1)] = m.group(2).strip()
    return names.get(m.group(1), "")

# The parts callgrind dumped before `path` in the same run: out.1, out.2 ...
# come before out, and before out.N come out.1 to out.N-1. A run names each
# object once, in the part where it first appears.
def earlier(path):
    m = re.fullmatch(r"(.*)\.(\d+)", path)
    base, last = (m.group(1), int(m.group(2))) if m else (path, None)
    n = 1
    while (last is None or n < last) and os.path.exists(f"{base}.{n}"):
        yield f"{base}.{n}"
        n += 1

# Code valgrind has no symbols for sits under "???", the program's included
# when its symbol table is unreadable.
UNKNOWN = "???"

def object_name(line, objects):
    name = named(line, objects)
    return name if name == UNKNOWN else os.path.realpath(name)

# Each line of a profile with the object it lies in: a cost line's own, a
# call line's callee's, which "cob=" names when it differs.
def lines(path):
    objects = {}
    for part in earlier(path):
        for line in open(part):
            if line.startswith(("ob=", "cob=")):
                named(line, objects)
    current = callee = ""
    for line in open(path):
        if line.startswith("ob="):
            current = callee = object_name(line, objects)
        elif line.startswith("cob="):
            callee = object_name(line, objects)
        if line.startswith("calls="):
            yield line, callee
            callee = current
        else:
            yield line, current

# The offset of each object's addresses from the program's link addresses,
# for the objects that hold the program: the offset that puts most of their
# calls on function starts, where that is most of them.
def offsets(path):
    targets = {binary: [], UNKNOWN: []}
    for line, obj in lines(path):
        m = re.match(r"calls=\d+\s+(0x[0-9a-f]+)", line)
        if m and obj in targets:
            targets[obj].append(int(m.group(1), 16))
    found = {}
    for obj, calls in targets.items():
        hits = {b: sum(1 for t in calls if t - b in function_starts) for b in (0, LOAD_BASE)}
        best = max(hits, key=hits.get)
        if calls and hits[best] * 2 >= len(calls):
            found[obj] = best
    if not found:
        sys.exit(f"{path}: no calls reach the program's function starts")
    return found

def costs(paths):
    cost = {}
    for path in paths:
        read(path, cost)
    return cost

def read(path, cost):
    biases = offsets(path)
    at = 0
    after_call = False
    for line, obj in lines(path):
        if line.startswith("calls="):
            after_call = True
            continue
        m = re.match(r"(0x[0-9a-f]+|[+-]\d+|\*)\s+(\d+)", line)
        if not m:
            continue
        position, amount = m.groups()
        if position.startswith("0x"):
            at = int(position, 16)
        elif position != "*":
            at += int(position)
        name = symbol(at - biases[obj]) if obj in biases else None
        if name:
            # A call line's cost is the callee's; the call itself still ran.
            cost[name] = cost.get(name, 0) + (0 if after_call else int(amount))
        after_call = False

session = costs([session_part])
startup = costs(startup_parts)
features = costs([feature_part])
hottest = lambda cost: [n for n, _ in sorted(cost.items(), key=lambda item: -item[1])]
for name in hottest(session):
    print(name)
print("gui_engine_startup_code_begin")
for name in hottest(startup):
    if name not in session:
        print(name)
for name in hottest(features):
    if name not in session and name not in startup:
        print(name)
print("gui_engine_startup_code_end")
EOF
# The session natively. Breakpoints slow what they watch, so the late runs
# arm them only once the first frame is shown, leaving startup at native
# speed: every function outside the session part that runs after it is
# recorded. Which work lands after the first frame depends on the settings (a
# saved font is looked up while the first frame is laid out), so they run with
# saved settings and with none. The unseen run watches from the start for
# functions no profile saw at all.
cat > "$work/native.py" <<'EOF'
import gdb, subprocess
binary, out_file, start, exclude_files = NATIVE_ARGS
exclude = {line.strip() for path in exclude_files for line in open(path)}
names = {}
for line in subprocess.check_output(["nm", "--defined-only", binary], text=True).splitlines():
    parts = line.split()
    if len(parts) == 3 and parts[1] in "tTwW":
        names.setdefault(int(parts[0], 16), []).append(parts[2])
watched = [a for a, ns in names.items()
           if not any(n in exclude or n.startswith("gui_engine_startup_code_") for n in ns)]
marker = next(a for a, ns in names.items() if "gui_engine_startup_code_begin" in ns)
hits = []

class Call(gdb.Breakpoint):
    def stop(self):
        hits.extend(names[self.at])
        self.enabled = False
        return False

class Arm(gdb.Breakpoint):
    def stop(self):
        base = int(gdb.parse_and_eval("(long)&gui_engine_startup_code_begin")) - marker
        for a in watched:
            Call(f"*{a + base:#x}", internal=True).at = a
        self.enabled = False
        return False

Arm(start, internal=True)

def report(_event):
    with open(out_file, "w") as out:
        out.writelines(f"{n}\n" for n in hits)

gdb.events.exited.connect(report)
EOF
native() {
    local out="$1" start="$2" settings="$3"
    shift 3
    local excludes
    excludes=$(printf "'%s'," "$@")
    seed_config "$out.config" "$settings"
    session "$work/ready" env XDG_CONFIG_HOME="$out.config" "$im" gdb -q -batch -ex "set pagination off" \
        -ex "python NATIVE_ARGS = ('$binary', '$out', '$start', [$excludes])" \
        -ex "source $work/native.py" -ex run --args "$binary" \
        >"$out.log" 2>&1
    [ -f "$out" ] || { tail -n 40 "$out.log" >&2; die "the native session did not finish"; }
}
awk '/^gui_engine_startup_code_begin$/ { exit } { print }' "$work/names" > "$work/session"
native "$work/late.saved" gui_engine_startup_complete saved "$work/session"
native "$work/late.default" gui_engine_startup_complete default "$work/session"
cat "$work/late.saved" "$work/late.default" > "$work/late"
awk '/^gui_engine_startup_code_/ { next } { print }' "$work/names" > "$work/profiled"
native "$work/unseen" main saved "$work/profiled" "$work/late"

# Functions called after the first frame join the session part; the startup
# part keeps the rest, with those only the native run saw.
python3 - "$work/names" "$work/late" "$work/unseen" > "$work/ordered" <<'EOF'
import sys
names = [l.strip() for l in open(sys.argv[1])]
cut = names.index("gui_engine_startup_code_begin")
session, startup = names[:cut], names[cut + 1:-1]
late = [l.strip() for l in open(sys.argv[2])]
unseen = [l.strip() for l in open(sys.argv[3])]
moved = set(late)
seen = set()
for name in session + late + ["gui_engine_startup_code_begin"] + \
        [n for n in startup if n not in moved] + unseen + ["gui_engine_startup_code_end"]:
    if name not in seen:
        seen.add(name)
        print(name)
EOF
awk -f "$root/scripts/symbol-key.awk" "$work/ordered" | awk '!seen[$1]++ { print $1 }' > "$output"
echo "wrote $(wc -l < "$output") functions to $output"
