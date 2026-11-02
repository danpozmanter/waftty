#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
prefix=${PREFIX:-$HOME/.local}
exe=waftty
app_id=dev.gossamer.waftty
install -Dm755 "$here/bin/$exe" "$prefix/bin/$exe"
mkdir -p "$prefix/share/applications"
escaped=$(printf '%s' "$prefix/bin/$exe" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\$/\\$/g; s/`/\\`/g; s/%/%%/g')
while IFS= read -r line; do
    case "$line" in Exec=*) printf 'Exec="%s"\n' "$escaped" ;; *) printf '%s\n' "$line" ;; esac
done < "$here/share/applications/$app_id.desktop" > "$prefix/share/applications/$app_id.desktop"
chmod 644 "$prefix/share/applications/$app_id.desktop"
if [ -d "$here/share/icons" ]; then
    cp -R "$here/share/icons" "$prefix/share/"
    hicolor="$prefix/share/icons/hicolor"
    # Icon lookups (KDE's in particular) only search a hicolor root that
    # describes its directories.
    if [ ! -f "$hicolor/index.theme" ]; then
        {
            printf '[Icon Theme]\nName=Hicolor\nComment=Fallback icon theme\nDirectories='
            first=1
            for size in 16 22 24 32 48 64 128 256 512; do
                if [ "$first" = 1 ]; then first=0; else printf ','; fi
                printf '%sx%s/apps' "$size" "$size"
            done
            printf '\n'
            for size in 16 22 24 32 48 64 128 256 512; do
                printf '\n[%sx%s/apps]\nSize=%s\nType=Fixed\nContext=Applications\n' "$size" "$size" "$size"
            done
        } > "$hicolor/index.theme"
    fi
    touch "$hicolor"/*/apps/"$app_id".png
    # A stale cache hides the new icon; GTK scans the directories without one.
    rm -f "$hicolor/icon-theme.cache"
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then gtk-update-icon-cache -q -f -t "$hicolor" || true; fi
fi
mkdir -p "$prefix/share/doc/$exe"
cp -R "$here/share/doc/$exe/." "$prefix/share/doc/$exe/"
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database -q "$prefix/share/applications"; fi
# KDE Plasma lists applications and icons from its own caches.
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 >/dev/null 2>&1 || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 >/dev/null 2>&1 || true
fi
rm -f "${XDG_CACHE_HOME:-$HOME/.cache}/icon-cache.kcache"
printf 'installed %s in %s/bin\n' "$exe" "$prefix"
