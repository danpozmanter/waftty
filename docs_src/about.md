---
title: About - waftty
description: waftty is a tabbed terminal emulator written in Gossamer on the gui-gos toolkit. Apache 2.0 licensed.
---

# About

waftty is a tabbed terminal emulator written in
[Gossamer](https://github.com/gossamer-lang/gossamer), a fast-compiling language
with deterministic memory management. Gossamer compiles waftty to one native
binary per platform, and frees memory as soon as it is no longer used, with
no garbage collector to pause or bloat the process.

The name is a nod to its icon: a gust of wind in a terminal box. A terminal
should be like a breeze - there when you want it, and weightless the rest of
the time.

## Built On

- [gui-gos](https://github.com/gossamer-lang/gui-gos), the Gossamer GUI
  toolkit: windows, menus, tabs, dialogs and the terminal widget.
- [gui-engine-gos](https://github.com/gossamer-lang/gui-engine-gos) and
  [windowing-gos](https://github.com/gossamer-lang/windowing-gos), on
  [SDL3](https://www.libsdl.org/).
- [WezTerm](https://github.com/wezterm/wezterm)'s terminal core for escape
  sequence handling.

## License

Apache 2.0 - see [LICENSE](https://github.com/danpozmanter/waftty/blob/main/LICENSE).

**Fonts:** [DejaVu](https://dejavu-fonts.github.io/) and
[IBM Plex Mono](https://github.com/IBM/plex)

**Documentation:** Built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) by Martin Donath.

## Author

[Dan Pozmanter](https://github.com/danpozmanter)
