# Prints "KEY NAME" for each symbol NAME read one a line: KEY is NAME without
# the parts that differ between builds of the same sources (Rust's crate and
# instance hashes, LLVM's local-clone suffixes), so a link order profiled from
# one build names the same functions in another. Several names can share a
# key; a link order lays them out together.
{
    key = $1
    sub(/\.llvm\.[0-9]+$/, "", key)
    sub(/\.[0-9]+$/, "", key)
    sub(/17h[0-9a-f]+E$/, "E", key)
    if (key ~ /^_R/) {
        gsub(/Cs[0-9A-Za-z]+_/, "C_", key)
    }
    print key, $1
}
