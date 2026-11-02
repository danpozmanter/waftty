#!/usr/bin/env bash
# Writes the link order scripts/package.sh hands the linker (as
# GOS_SYMBOL_ORDER): first the functions a session keeps running once its
# first frame is shown (the output profile), hottest first; then, between
# the engine's startup markers, the ones only startup or an occasional
# feature (the journey profile) runs. The engine releases that second run
# once the window is up, and a feature used later reads its pages back.
#
# Usage: scripts/link-order.sh [OUTPUT]   (default build-data/link-order.txt)
#
# Symbol names depend on the toolchain, the target and where each library
# was built from, so the order holds only for a build made the same way as
# this one; the release workflow writes it in the job that packages.
#
# Needs valgrind, Xephyr and the Gossamer toolchain. The profile is the
# scripted journey (--fixture), which runs offscreen, and a stretch of
# output on X11.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="${1:-$root/build-data/link-order.txt}"
die() { echo "error: $*" >&2; exit 1; }
for tool in valgrind Xephyr gos nm dbus-run-session; do
    command -v "$tool" >/dev/null 2>&1 || die "$tool is not on the PATH"
done

work="$(mktemp -d)"
xephyr=""
cleanup() {
    [ -z "$xephyr" ] || kill "$xephyr" 2>/dev/null || true
    rm -rf "$work"
}
trap cleanup EXIT

# valgrind runs code for a CPU every machine has.
(cd "$root" && GOS_LLVM_MCPU=x86-64-v2 gos build --release . --out-dir "$work/build" >&2)
binary="$work/build/waftty"

display=70
while [ -e "/tmp/.X$display-lock" ] || [ -e "/tmp/.X11-unix/X$display" ]; do
    display=$((display + 1))
done
Xephyr ":$display" -screen 1400x900 >/dev/null 2>&1 &
xephyr=$!
until [ -S "/tmp/.X11-unix/X$display" ]; do
    kill -0 "$xephyr" 2>/dev/null || die "Xephyr did not start"
    sleep 0.1
done

cat > "$work/output.sh" <<'EOF'
#!/bin/sh
seq 100000
ls -la /usr/bin | head -200
exit
EOF
chmod +x "$work/output.sh"

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

# A bus of its own keeps a running waftty from taking the profiled launch.
# Callgrind writes what ran before the first frame to <out>.1, and the rest
# of the session to <out> when the program exits.
profile() {
    DISPLAY=":$display" XDG_CONFIG_HOME="$work/config" SDL_VIDEO_DRIVER="$1" dbus-run-session -- \
        valgrind --tool=callgrind --dump-instr=yes --dump-line=no \
        --dump-before=gui_engine_startup_complete --dump-before="$split_at" \
        --callgrind-out-file="$2" -q \
        "$binary" "${@:3}" \
        >"$2.log" 2>&1
}
profile offscreen "$work/journey.out" --fixture
profile x11 "$work/output.out" -e "$work/output.sh"
for out in journey output; do
    [ -f "$work/$out.out.1" ] && [ -f "$work/$out.out" ] || {
        tail -n 40 "$work/$out.out.log" >&2
        die "the $out profile never reached gui_engine_startup_complete"
    }
done

mkdir -p "$(dirname "$output")"
python3 - "$base" "$work/defined" "$binary" "$work"/output.out "$work"/journey.out.1 "$work"/output.out.1 \
    "$work"/journey.out > "$output" <<'EOF'
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
echo "wrote $(wc -l < "$output") functions to $output"
