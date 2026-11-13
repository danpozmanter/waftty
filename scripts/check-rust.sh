#!/bin/sh
# Formatting, Clippy and tests for the crate that reads the process tree.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
# The binding SDK is not on crates.io. Take it where the projects gos
# generates do: GOSSAMER_BINDING_PATH when set, else what `gos env` reports,
# the checkout gos was built from or its release tag (URL@TAG).
sdk=${GOSSAMER_BINDING_PATH:-$("${GOS:-gos}" env | awk '$1 == "binding_sdk" { print $2 }')}
case "$sdk" in
    https://*@*)
        set -- --config "patch.crates-io.gossamer-binding.git=\"${sdk%@*}\"" \
            --config "patch.crates-io.gossamer-binding.tag=\"${sdk##*@}\""
        ;;
    *)
        set -- --config "patch.crates-io.gossamer-binding.path=\"$sdk\""
        ;;
esac
cd "$root/rust/processes"
cargo fmt --all --check
cargo clippy "$@" --all-targets -- -D warnings
cargo test "$@" --all-targets
