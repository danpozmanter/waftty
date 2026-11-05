---
title: waftty - a light, tabbed terminal for Linux, macOS and Windows
description: waftty is a tabbed terminal emulator for Linux, macOS and Windows. About 20 MB of memory and no CPU at idle, with find in scrollback, shell integration, links, color schemes and 36 character sets.
---

<div class="hero" markdown>

<div class="wind" aria-hidden="true">
<svg viewBox="0 0 1000 400">
  <path d="M-10 90H230A18 18 0 1 0 212 72"/>
  <path d="M-10 128H140"/>
  <path d="M720 200H900A18 18 0 1 0 882 182"/>
  <path d="M800 238H1010"/>
  <path d="M-10 300H170A18 18 0 1 1 152 318"/>
  <path d="M850 110H1010"/>
</svg>
</div>

<img src="assets/icon.svg" alt="" class="hero-icon">

# waftty

<p class="tagline">A gentle terminal emulator - consistently lightweight on Linux, macOS and Windows.</p>

<div class="button-row">
  <a href="installation/" class="primary">Get waftty</a>
  <a href="https://github.com/danpozmanter/waftty" class="secondary">View on GitHub</a>
</div>

<img src="assets/screenshot.png" alt="waftty with two tabs, the first split into two panes: git log on the left, neofetch and ls on the right" class="screenshot">

</div>

## Features

<div class="features" markdown>

<div class="feature" markdown>

### Featherweight

Extremely low memory and CPU overhead. waftty stays out of your way, leaving resources for your applications.

</div>

<div class="feature" markdown>

### Fast and Responsive

Smooth terminal output and responsive typing, even when commands produce large amounts of text.

</div>

<div class="feature" markdown>

### Image Support

Display images directly in your terminal with support for modern graphics protocols like kitty.

</div>

<div class="feature" markdown>

### Keyboard-First Navigation

Copy text with Vim-style keyboard navigation, jump directly to links and file paths, and search your scrollback without reaching for the mouse.

</div>

<div class="feature" markdown>

### Shell-Aware and Agent-Ready

Jump between command prompts, select command output, and receive notifications from background tasks and coding agents such as Claude Code and Codex.

</div>

<div class="feature" markdown>

### Modern Terminal Features

Font ligatures, the kitty keyboard protocol, clickable code paths, customizable shortcuts, and themes.

</div>

</div>

## Built With

waftty is written in [Gossamer](https://github.com/gossamer-lang/gossamer) on the
[gui-gos](https://github.com/gossamer-lang/gui-gos) toolkit, built on a core of [Rust](https://rust-lang.org/) and [SDL3](https://github.com/libsdl-org/SDL).
  
Terminal emulation comes from a lite fork of [WezTerm's](https://wezterm.org/) terminal core [wezterm-lite](https://github.com/gossamer-lang/wezterm-lite).
