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
   **ALttP Randomizer - New Seed**, **- Continue** and **- Spoiler** → Add.
4. Switch to Game Mode and play.

## Usage
- **New Seed**: generates a fresh seed and starts it. If generation fails (offline, API down), it loads your previous seed.
- **Continue**: starts the most recent seed. Use this to resume a run; launching *New Seed* starts a different game.
  Settings are baked into the seed, so Continue never needs a preset.
- **Spoiler**: browse the latest seed's spoiler on the TV with the controller. Areas are listed on the left, and
  each one stays hidden until you press A on it, so scrolling doesn't spoil anything by accident.
  *Route to beat the game* lists one item order that works.
  D-pad/stick: move · A: reveal · L/R shoulder: page · B: back (B again quits) · Start: quit.

### Picking a preset per launch
In Steam, right-click **New Seed** → Properties → **Launch Options**, and enter a preset name, e.g. `-open`.
It maps to `presets/open.json`; `open`, `-open` and `--open` all work. Leave it empty to use the config default.
An unknown name shows an error listing the available presets.
From a terminal: `./alttpr.sh new -open`.

Tip: to have both one click away, add *New Seed* to Steam twice, rename one copy to
"ALttP Randomizer - New Seed (Open)", and give that copy the `-open` launch option.

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
