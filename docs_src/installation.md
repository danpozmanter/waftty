---
title: Installation - waftty
description: Install waftty on Linux, macOS or Windows from a release package, or build it from source with the Gossamer toolchain.
---

# Installation

## Release Packages

Download the package for your platform from the
[releases page](https://github.com/danpozmanter/waftty/releases).

| Platform | Package | Requirements |
|---|---|---|
| Debian, Ubuntu | `waftty_VERSION-1_amd64.deb` | Ubuntu 24.04, Debian 13 or newer |
| Fedora, openSUSE, RHEL | `waftty-VERSION-1.x86_64.rpm` | glibc 2.39 or newer (Fedora 40 and later) |
| Any Linux x86_64 | `waftty-VERSION-x86_64.AppImage` | glibc 2.39 or newer; nothing to install |
| Any Linux x86_64 | `waftty-VERSION-linux-x86_64.tar.gz` | glibc 2.39 or newer (Ubuntu 24.04 and later) |
| macOS, Apple Silicon | `waftty-VERSION-macos-aarch64.zip` | macOS 15 or newer on an M-series Mac |
| macOS, Intel | `waftty-VERSION-macos-x86_64.zip` | macOS 15 or newer on an Intel Mac |
| Windows x86_64 | `waftty-VERSION-x86_64-setup.exe` | Windows 10 or newer |
| Windows x86_64 | `waftty-VERSION-windows-x86_64.zip` | Nothing to install: unzip and run |
| Windows x86_64, portable | `waftty-VERSION-windows-x86_64-portable.zip` | Nothing to install; settings stay in the folder |

Not sure which Mac you have? Open the Apple menu and choose About This Mac:
"Chip" means Apple Silicon, "Processor" means Intel.

=== "Linux"

    On Debian and Ubuntu, or on Fedora and other RPM distributions:

    ```sh
    sudo apt install ./waftty_*_amd64.deb
    sudo dnf install ./waftty-*.x86_64.rpm
    ```

    The AppImage runs as it is:

    ```sh
    chmod +x waftty-*-x86_64.AppImage
    ./waftty-*-x86_64.AppImage
    ```

    Or unpack the tarball and run its installer:

    ```sh
    tar -xzf waftty-*-linux-x86_64.tar.gz
    cd waftty-*-linux-x86_64
    ./install.sh                          # installs to ~/.local
    sudo env PREFIX=/usr/local ./install.sh   # or system-wide
    ```

    The installer places the binary in `PREFIX/bin`, a desktop entry in
    `PREFIX/share/applications`, and the icon in the hicolor theme, so waftty
    shows up in your application launcher.

=== "macOS"

    With [Homebrew](https://brew.sh):

    ```sh
    brew install --cask danpozmanter/tap/waftty
    ```

    This installs `waftty.app` into `/Applications`, links the `waftty`
    command, and clears the download quarantine. `brew upgrade` moves it to
    each new release.

    Or unzip the package and double-click `install.command`. macOS checks
    the downloaded script first: the first time, open **System Settings >
    Privacy & Security** and choose **Open Anyway**. Running it in Terminal
    skips that check:

    ```sh
    bash install.command
    ```

    This copies `waftty.app` to `/Applications`, clears the download
    quarantine, and links a `waftty` command into `/usr/local/bin` (and
    `/opt/homebrew/bin` where it exists).

=== "Windows"

    Run the setup program. It installs waftty for you or for everyone on
    the computer, adds it to the Start menu, and can add it to the PATH or
    put a shortcut on the desktop. Its portable option only extracts waftty
    into a folder, with a `user` folder beside it.

    Or unzip a package anywhere and run `waftty.exe`. Settings are kept in
    `%APPDATA%\dev.gossamer.waftty`, or inside the folder with the portable
    package.

## Portable Mode

When a folder named `user` sits beside waftty, waftty keeps its settings,
color schemes and shortcuts in that folder and writes nothing to your
profile. Move the folder, or put it on a USB stick, and the settings go with
it. Delete it, and nothing is left behind.

The Windows portable package, and the setup program's portable option,
already have the `user` folder. For the other
packages, make the folder yourself:

| Package | Where the `user` folder goes |
|---|---|
| Windows | beside `waftty.exe` |
| Linux | beside the `waftty` program, in `bin/` of the unpacked package |
| macOS | beside `waftty.app` |

## Building from Source

waftty needs [Gossamer](https://github.com/gossamer-lang/gossamer) 0.75.13 or
newer, a Rust toolchain, and LLVM for native builds. The GUI libraries are
expected beside the checkout at `../goose-libs`.

```sh
git clone https://github.com/danpozmanter/waftty
mkdir goose-libs && cd goose-libs
git clone https://github.com/gossamer-lang/windowing-gos
git clone https://github.com/gossamer-lang/gui-engine-gos
git clone https://github.com/gossamer-lang/gui-gos
sh gui-gos/tools/fetch.sh
cd ../waftty
gos fetch
```

Then run or build it:

```sh
gos run .                  # your shell
gos run . -e htop          # a program in the first tab
gos build --release        # a native binary in target/release
./install.sh               # build and install: ~/.local, or /Applications on macOS
./install.sh --system      # Linux: build and install to /usr/local
```

On Linux, building SDL needs its usual development packages. On Ubuntu:

```sh
sudo apt-get install cmake ninja-build pkg-config llvm-18 \
  libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxi-dev \
  libxss-dev libxfixes-dev libxtst-dev libxkbcommon-dev libwayland-dev \
  wayland-protocols libegl-dev libgl-dev libdecor-0-dev
```

## Command Line

```text
waftty [--version] [--help] [-e program [args...]]
```

`-e` runs a program in the first tab instead of your shell. Every argument
after it belongs to the program, so `waftty -e git --version` runs
`git --version`.
