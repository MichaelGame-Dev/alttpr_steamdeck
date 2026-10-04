# ALttP Randomizer launcher (Bazzite / Steam Game Mode)

Generates an [ALttPR](https://alttpr.com) seed with the official alttpr.com API (via
[pyz3r](https://github.com/tcprescott/pyz3r)), patches your ROM, and launches it in RetroArch,
all from a Steam shortcut.

## Requirements
- The **Japan 1.0** ROM (*Zelda no Densetsu - Kamigami no Triforce*), MD5 `03a63945398191337e896e5771f77173`.
  A headered `.smc` is fine because `install.sh` strips the header.
- RetroArch flatpak (EmuDeck installs it) with the **snes9x** core.
- Internet access when generating a new seed.

## Setup (on the HTPC, once)
1. Copy this folder to its permanent home, e.g. `~/Games/alttp_randomizer`. The Steam shortcuts
   point at this path, so re-run `install.sh` if you move it.
2. In Desktop Mode, open a terminal and run:
   ```bash
   cd ~/Games/alttp_randomizer
   ./install.sh "/path/to/Zelda no Densetsu (Japan).sfc"
   ```
   If it warns that the core is missing, open RetroArch → Online Updater → Core Downloader → *Nintendo - SNES / SFC (Snes9x - Current)*.
3. Steam → Games → **Add a Non-Steam Game to My Library…** → tick
   **ALttP Randomizer - New Seed** and **ALttP Randomizer - Continue** → Add.
4. Switch to Game Mode and play.

## Usage
- **New Seed**: generates a fresh seed and starts it. If generation fails (offline, API down), it loads your previous seed.
- **Continue**: starts the most recent seed. Use this to resume a run; launching *New Seed* starts a different game.

Seeds are stored in `~/Emulation/roms/snes/alttpr/` (or `~/.local/share/alttpr-launcher/seeds/` without
EmuDeck). Each seed comes with:
- `<seed>.json`: the alttpr.com permalink, the file-select hash code and the settings used
- `<seed>.spoiler.json`: the full item locations. Don't open it unless you're stuck!

Saves are RetroArch `.srm` files named after the seed ROM, so older runs keep their saves.

Log: `~/.local/share/alttpr-launcher/launcher.log`.

## Settings
Config lives in `~/.config/alttpr-launcher/config.env`:
- `PRESET`: which file in `presets/` to use. The default is `beginner.json`, which matches alttpr.com's Beginner preset:
  Standard start, basic item placement, every location reachable, sword guaranteed from your uncle.
  `open.json` is the more typical "Open" setup for later.
- `RETROARCH_CMD`: the emulator command.
- `SEED_DIR`: where seeds go.

To make your own preset, copy one in `presets/` and edit it. Valid values are listed at
<https://alttpr.com/randomizer/settings>. `cosmetics` controls heart beep speed, heart color, sprite and music.
