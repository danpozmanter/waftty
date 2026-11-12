#!/usr/bin/env bash
# Build waftty and package it for the host platform into OUT (default dist):
#   Linux    waftty-VERSION-linux-ARCH.tar.gz, with install.sh inside
#   FreeBSD  waftty-VERSION-freebsd-ARCH.tar.gz, with install.sh inside
#   macOS    waftty-VERSION-macos-ARCH.zip: waftty.app and install.command
#   Windows  waftty-VERSION-windows-ARCH.zip, and a -portable.zip whose user
#            folder keeps the settings beside waftty.exe
# With --installers it also builds the release's installers:
#   Linux    waftty_VERSION-1_ARCH.deb, waftty-VERSION-1.ARCH.rpm and
#            waftty-VERSION-ARCH.AppImage (dpkg-deb, rpmbuild, appimagetool)
#   Windows  waftty-VERSION-ARCH-setup.exe (Inno Setup 6, ImageMagick)
# Each gets a .sha256 beside it, and its path is printed.
#
# Usage: scripts/package.sh [--installers] [OUT]
#
# Needs the Gossamer toolchain and the libraries at ../goose-libs, where
# project.toml reaches them. GOS_LLVM_MCPU overrides the portable CPU
# baseline, and MACOSX_DEPLOYMENT_TARGET the oldest macOS.
set -euo pipefail

installers=0
if [ "${1:-}" = --installers ]; then
    installers=1
    shift
fi
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
libs="$root/../goose-libs"
out="$(mkdir -p "${1:-dist}" && cd "${1:-dist}" && pwd)"

die() { echo "error: $*" >&2; exit 1; }
need() {
    local tool
    for tool in "$@"; do
        command -v "$tool" >/dev/null 2>&1 || die "packaging needs $tool on the PATH"
    done
}

name=waftty
exe=waftty
app_id=dev.gossamer.waftty
comment="A tabbed terminal emulator"
description="waftty is a tabbed terminal emulator built on SDL 3, with WezTerm's terminal core, kitty and sixel images, and a portable mode."
maintainer="waftty contributors"
homepage="https://github.com/danpozmanter/waftty"
categories="System;TerminalEmulator;"
version="$(awk -F'"' '/^version = / { print $2; exit }' "$root/project.toml")"
[ -n "$version" ] || die "no version in project.toml"

case "$(uname -s)" in
    Linux) platform=linux ;;
    FreeBSD) platform=freebsd ;;
    Darwin) platform=macos ;;
    MINGW* | MSYS* | CYGWIN*) platform=windows ;;
    *) die "unsupported OS: $(uname -s)" ;;
esac
case "$(uname -m)" in
    x86_64 | amd64) arch=x86_64 ;;
    arm64 | aarch64) arch=aarch64 ;;
    *) die "unsupported architecture: $(uname -m)" ;;
esac
base="$exe-$version-$platform-$arch"
# The oldest macOS the app runs on: the one the released toolchain's runtime
# is built for, unless MACOSX_DEPLOYMENT_TARGET names another.
macos_minimum="${MACOSX_DEPLOYMENT_TARGET:-15.0}"

# Zips FOLDER as one top-level folder; ZipFile keeps empty folders, which
# Compress-Archive drops. PowerShell 7's .NET names entries with the forward
# slashes zip readers expect, where Windows PowerShell's writes backslashes.
zip_folder() {
    need pwsh
    rm -f "$2"
    pwsh -NoProfile -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('$(cygpath -w "$1")', '$(cygpath -w "$2")', [System.IO.Compression.CompressionLevel]::Optimal, \$true)"
}

sha256() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi
}

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

# A package runs on machines other than the one that built it, so its code
# assumes a CPU every supported machine has, not the builder's own.
if [ -z "${GOS_LLVM_MCPU:-}" ]; then
    if [ "$arch" = x86_64 ]; then export GOS_LLVM_MCPU=x86-64-v2; else export GOS_LLVM_MCPU=generic; fi
fi
. "$root/scripts/build-env.sh"
(cd "$root" && gos fetch >/dev/null && gos build --release . --out-dir "$stage/build" >&2)
binary="$stage/build/$exe"
[ "$platform" = windows ] && binary="$binary.exe"
[ -f "$binary" ] || die "the build did not produce $binary"
# The functions a session runs, laid out together so they fill few pages.
# build-data/link-order.txt names them by key (scripts/link-order.sh writes
# it); this build's names for those keys make the order its relink follows.
# Orders are profiled on Linux, where the engine releases startup code.
order="$root/build-data/link-order.txt"
if [ "$platform" = linux ] && [ -f "$order" ]; then
    need nm awk
    nm --defined-only "$binary" | awk '$2 ~ /^[tTwW]$/ { print $3 }' |
        awk -f "$root/scripts/symbol-key.awk" > "$stage/symbols"
    awk 'NR == FNR { names[$1] = names[$1] $2 "\n"; next }
         $1 in names { printf "%s", names[$1]; delete names[$1]; found++ }
         END { printf "link order: %d of %d functions in this build\n", found, FNR > "/dev/stderr" }' \
        "$stage/symbols" "$order" > "$stage/link-order.txt"
    grep -qx gui_engine_startup_code_end "$stage/link-order.txt" ||
        die "$order does not match this build; rerun scripts/link-order.sh"
    (cd "$root" && GOS_SYMBOL_ORDER="$stage/link-order.txt" \
        gos build --release . --out-dir "$stage/build" >&2)
fi
if { [ "$platform" = linux ] || [ "$platform" = freebsd ]; } && ldd "$binary" | grep -q "not found"; then
    die "unresolved native libraries: $(ldd "$binary" | grep "not found")"
fi

# The licenses of what the binary carries: fonts, SDL, pulldown-cmark,
# WezTerm's terminal core, and the libraries' own Apache-2.0.
notices() {
    local dir="$1"
    mkdir -p "$dir"
    for license in dejavu-fonts.txt ibm-plex-mono.txt sdl3-zlib.txt pulldown-cmark.txt wezterm.txt; do
        cp "$libs/gui-gos/licenses/$license" "$dir/$license"
    done
    cp "$libs/windowing-gos/LICENSE" "$dir/apache-2.0.txt"
    printf '%s %s\nSDL 3 is built from sdl3-src and statically linked.\nDejaVu fonts are embedded. The terminal emulation is WezTerm'"'"'s (MIT). See accompanying licenses.\n' \
        "$name" "$version" > "$dir/README.txt"
}

# The app writes its own icon when asked to.
icon="$stage/icon.png"
(cd "$stage" && GUI_EXPORT_ICON="$icon" SDL_VIDEO_DRIVER=offscreen "$binary" >/dev/null)
[ -f "$icon" ] || die "the app did not export its icon"

# Writes FILE's checksum beside it and names it on stdout.
publish() {
    (cd "$out" && sha256 "$(basename "$1")" > "$(basename "$1").sha256")
    echo "$1"
}

# The distribution packages install the Linux bundle's bin and share under /usr.
deb_package() {
    local bundle="$1" pkg="$stage/deb" deb_arch depends file
    need dpkg-deb dpkg-shlibdeps
    case "$arch" in
        x86_64) deb_arch=amd64 ;;
        aarch64) deb_arch=arm64 ;;
    esac
    mkdir -p "$pkg/DEBIAN" "$pkg/usr" "$stage/shlibs/debian"
    cp -r "$bundle/bin" "$bundle/share" "$pkg/usr/"
    # dpkg-shlibdeps reads the source package's name from debian/control.
    printf 'Source: %s\n\nPackage: %s\nArchitecture: any\n' "$exe" "$exe" > "$stage/shlibs/debian/control"
    depends="$(cd "$stage/shlibs" && dpkg-shlibdeps -O "$pkg/usr/bin/$exe" | sed -n 's/^shlibs:Depends=//p')"
    [ -n "$depends" ] || die "dpkg-shlibdeps found no libraries for $exe"
    cat > "$pkg/DEBIAN/control" <<EOF
Package: $exe
Version: $version-1
Architecture: $deb_arch
Maintainer: $maintainer
Installed-Size: $(du -sk "$pkg/usr" | cut -f1)
Depends: $depends
Section: x11
Priority: optional
Homepage: $homepage
Description: $comment
 $description
EOF
    file="$out/${exe}_$version-1_$deb_arch.deb"
    dpkg-deb --build --root-owner-group "$pkg" "$file" >/dev/null
    publish "$file"
}

rpm_package() {
    local bundle="$1" top="$stage/rpm" file="$out/$exe-$version-1.$arch.rpm"
    need rpmbuild
    mkdir -p "$top/SPECS"
    # The binary ships as built: rpmbuild's stripping and debug packages would
    # rewrite it after its symbols were laid out.
    cat > "$top/SPECS/$exe.spec" <<EOF
%global debug_package %{nil}
%global __os_install_post %{nil}
%global _build_id_links none

Name: $exe
Version: $version
Release: 1
Summary: $comment
License: Apache-2.0
URL: $homepage

%description
$description

%install
mkdir -p %{buildroot}/usr
cp -r $bundle/bin $bundle/share %{buildroot}/usr/

%files
/usr/bin/$exe
/usr/share/applications/$app_id.desktop
/usr/share/icons/hicolor/*/apps/$app_id.png
/usr/share/doc/$exe
EOF
    rpmbuild -bb --quiet --define "_topdir $top" --target "$arch" "$top/SPECS/$exe.spec" >&2
    mv "$top/RPMS/$arch/$(basename "$file")" "$file"
    publish "$file"
}

appimage() {
    local bundle="$1" dir="$stage/$exe.AppDir" file="$out/$exe-$version-$arch.AppImage"
    need appimagetool
    mkdir -p "$dir/usr"
    cp -r "$bundle/bin" "$bundle/share" "$dir/usr/"
    cp "$bundle/share/applications/$app_id.desktop" "$dir/"
    cp "$icon" "$dir/$app_id.png"
    cp "$icon" "$dir/.DirIcon"
    # The AppImage runtime's own variables would otherwise reach every shell
    # waftty opens, and tell programs there that they run from this AppImage.
    cat > "$dir/AppRun" <<EOF
#!/bin/sh
here="\$(dirname "\$(readlink -f "\$0")")"
exec env -u APPDIR -u APPIMAGE -u ARGV0 -u OWD "\$here/usr/bin/$exe" "\$@"
EOF
    chmod 755 "$dir/AppRun"
    ARCH="$arch" APPIMAGE_EXTRACT_AND_RUN=1 appimagetool --no-appstream \
        ${APPIMAGE_RUNTIME:+--runtime-file "$APPIMAGE_RUNTIME"} "$dir" "$file" >&2
    publish "$file"
}

windows_installer() {
    local bundle="$1" iscc ico="$stage/$exe.ico" name="$exe-$version-$arch-setup"
    need magick
    iscc="$(command -v iscc || command -v ISCC || true)"
    for candidate in "/c/Program Files (x86)/Inno Setup 6/ISCC.exe" "/c/Program Files/Inno Setup 6/ISCC.exe"; do
        [ -n "$iscc" ] || { [ -f "$candidate" ] && iscc="$candidate"; }
    done
    [ -n "$iscc" ] || die "--installers needs Inno Setup 6 (ISCC.exe)"
    magick "$icon" -define icon:auto-resize=16,32,48,64,128,256 "$ico"
    "$iscc" -Q \
        "-DAppVersion=$version" \
        "-DPayload=$(cygpath -w "$bundle")" \
        "-DIconFile=$(cygpath -w "$ico")" \
        "-DLicenseFile=$(cygpath -w "$root/LICENSE")" \
        "-O$(cygpath -w "$out")" \
        "-F$name" \
        "$(cygpath -w "$root/scripts/waftty.iss")" >&2
    publish "$out/$name.exe"
}

case "$platform" in
    linux | freebsd)
        bundle="$stage/$base"
        size="$(od -An -tu1 -j16 -N4 "$icon" | awk '{ print $1 * 16777216 + $2 * 65536 + $3 * 256 + $4 }')"
        mkdir -p "$bundle/bin" "$bundle/share/icons/hicolor/${size}x${size}/apps" "$bundle/share/applications"
        install -m755 "$binary" "$bundle/bin/$exe"
        install -m644 "$icon" "$bundle/share/icons/hicolor/${size}x${size}/apps/$app_id.png"
        notices "$bundle/share/doc/$exe"
        {
            echo "[Desktop Entry]"
            echo "Type=Application"
            echo "Name=$name"
            echo "Exec=$exe"
            echo "Icon=$app_id"
            echo "Terminal=false"
            echo "StartupWMClass=$app_id"
            echo "Comment=$comment"
            echo "Categories=$categories"
        } > "$bundle/share/applications/$app_id.desktop"
        if command -v desktop-file-validate >/dev/null 2>&1; then
            desktop-file-validate "$bundle/share/applications/$app_id.desktop"
        fi
        install -m755 "$root/scripts/install-xdg.sh" "$bundle/install.sh"
        tar -czf "$out/$base.tar.gz" -C "$stage" "$base"
        publish "$out/$base.tar.gz"
        if [ "$platform" = linux ] && [ "$installers" -eq 1 ]; then
            deb_package "$bundle"
            rpm_package "$bundle"
            appimage "$bundle"
        fi
        ;;
    macos)
        app="$stage/shipped/$name.app"
        mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
        install -m755 "$binary" "$app/Contents/MacOS/$exe"
        notices "$app/Contents/Resources/notices"
        iconset="$stage/AppIcon.iconset"
        mkdir -p "$iconset"
        for size in 16 32 128 256 512; do
            sips -z "$size" "$size" "$icon" --out "$iconset/icon_${size}x${size}.png" >/dev/null
            sips -z "$((size * 2))" "$((size * 2))" "$icon" --out "$iconset/icon_${size}x${size}@2x.png" >/dev/null
        done
        iconutil -c icns "$iconset" -o "$app/Contents/Resources/AppIcon.icns"
        cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDisplayName</key>
	<string>$name</string>
	<key>CFBundleExecutable</key>
	<string>$exe</string>
	<key>CFBundleIconFile</key>
	<string>AppIcon</string>
	<key>CFBundleIdentifier</key>
	<string>$app_id</string>
	<key>CFBundleName</key>
	<string>$name</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>$version</string>
	<key>CFBundleVersion</key>
	<string>$version</string>
	<key>LSMinimumSystemVersion</key>
	<string>$macos_minimum</string>
	<key>NSHighResolutionCapable</key>
	<true/>
</dict>
</plist>
EOF
        plutil -lint "$app/Contents/Info.plist" >/dev/null
        codesign --force --sign - "$app"
        codesign --verify --deep --strict "$app"
        install -m755 "$root/scripts/install.command" "$stage/shipped/install.command"
        rm -f "$out/$base.zip"
        (cd "$stage/shipped" && ditto -c -k . "$out/$base.zip")
        publish "$out/$base.zip"
        ;;
    windows)
        bundle="$stage/$base"
        mkdir -p "$bundle"
        cp "$binary" "$bundle/$exe.exe"
        notices "$bundle/notices"
        zip_folder "$bundle" "$out/$base.zip"
        publish "$out/$base.zip"
        # A user folder beside waftty.exe keeps every setting inside the
        # unpacked folder, so it runs from anywhere and leaves no trace.
        portable="$stage/$base-portable"
        cp -r "$bundle" "$portable"
        mkdir -p "$portable/user"
        zip_folder "$portable" "$out/$base-portable.zip"
        publish "$out/$base-portable.zip"
        [ "$installers" -eq 0 ] || windows_installer "$bundle"
        ;;
esac
