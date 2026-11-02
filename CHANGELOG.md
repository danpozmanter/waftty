# Changelog

## 0.1.1 - Settings window

- Settings opens in a window of its own that can be moved and resized.
- The color scheme list scrolls, so every scheme, your own included, can be chosen again.
- Setting descriptions wrap.
- "Follow the system" is now "System theme".

## 0.1.0 - Initial release

- A tabbed terminal emulator for Linux, macOS and Windows, with find in scrollback, shell integration, links, terminal images, color schemes and character sets.
- Packages: a tar.gz, deb, rpm and AppImage for Linux, zips for both macOS architectures, and a zip, portable zip and setup program for Windows.
- Memory work: the Linux build lays out its code by how a session uses it, releases code used only at startup once the first window is shown, and stores scrollback lines at their exact size.
