# The environment release builds are made in, which build-data/link-order.txt
# is profiled from; scripts/package.sh and scripts/link-order.sh source it
# after setting root.

# The pinned Rust toolchain: another compiler inlines and names functions
# differently.
export RUSTUP_TOOLCHAIN="${RUSTUP_TOOLCHAIN:-$(awk -F'"' '/^channel/ { print $2 }' "$root/rust-toolchain.toml")}"
# v0 symbol names spell out each generic instance, so the order's keys tell
# instances apart without the per-build hashes legacy names carry.
export RUSTFLAGS="${RUSTFLAGS:+$RUSTFLAGS }-C symbol-mangling-version=v0"
