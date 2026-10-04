#!/usr/bin/env bash
# One-time setup for the ALttPR launcher.
#   ./install.sh /path/to/Zelda\ no\ Densetsu\ (Japan).sfc
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$HOME/.local/share/alttpr-launcher"
CONFIG_DIR="$HOME/.config/alttpr-launcher"
APPS_DIR="$HOME/.local/share/applications"
JP10_MD5="03a63945398191337e896e5771f77173"

mkdir -p "$DATA_DIR" "$CONFIG_DIR" "$APPS_DIR"

# --- Config ---
if [[ ! -f "$CONFIG_DIR/config.env" ]]; then
  cp "$REPO_DIR/config.env.example" "$CONFIG_DIR/config.env"
  echo "Wrote $CONFIG_DIR/config.env"
fi
# shellcheck source=config.env.example
source "$CONFIG_DIR/config.env"

# --- Base ROM ---
src_rom="${1:-}"
if [[ -n "$src_rom" ]]; then
  [[ -f "$src_rom" ]] || { echo "ROM not found: $src_rom"; exit 1; }
  size=$(stat -c%s "$src_rom")
  if (( size % 1024 == 512 )); then
    echo "Stripping 512-byte copier header"
    tail -c +513 "$src_rom" >"$BASE_ROM"
  else
    cp "$src_rom" "$BASE_ROM"
  fi
fi
[[ -f "$BASE_ROM" ]] || { echo "No base ROM yet. Re-run: ./install.sh /path/to/JP-1.0-rom.sfc"; exit 1; }
md5=$(md5sum "$BASE_ROM" | cut -d' ' -f1)
if [[ "$md5" != "$JP10_MD5" ]]; then
  echo "Base ROM MD5 is $md5, expected $JP10_MD5 (Zelda no Densetsu - Kamigami no Triforce, Japan 1.0)."
  rm -f "$BASE_ROM"
  exit 1
fi
echo "Base ROM OK: $BASE_ROM"

# --- Python venv ---
if [[ ! -x "$DATA_DIR/venv/bin/python" ]]; then
  python3 -m venv "$DATA_DIR/venv"
fi
"$DATA_DIR/venv/bin/pip" install --quiet --upgrade pyz3r
echo "pyz3r installed in $DATA_DIR/venv"
# Only the Spoiler viewer needs this; don't let a failure here block seed generation.
if "$DATA_DIR/venv/bin/pip" install --quiet --upgrade pygame-ce; then
  echo "Spoiler viewer package installed"
else
  echo "WARNING: couldn't install pygame-ce; New Seed and Continue still work, Spoiler won't."
fi

# --- Emulator check ---
emu="${RETROARCH_CMD[0]}"
if ! command -v "$emu" >/dev/null; then
  echo "WARNING: emulator command '$emu' not found; edit RETROARCH_CMD in $CONFIG_DIR/config.env"
fi
for ((i = 1; i < ${#RETROARCH_CMD[@]}; i++)); do
  if [[ "${RETROARCH_CMD[i]}" == "-L" && ! -f "${RETROARCH_CMD[i + 1]}" ]]; then
    echo "WARNING: core not found: ${RETROARCH_CMD[i + 1]}"
    echo "         Install snes9x in RetroArch (Main Menu > Online Updater > Core Downloader) or edit the config."
  fi
done

# --- Desktop entries (appear in Steam's "Add a Non-Steam Game" list) ---
chmod +x "$REPO_DIR/alttpr.sh"
write_desktop() {
  local id="$1" name="$2" mode="$3"
  cat >"$APPS_DIR/$id.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$name
Exec="$REPO_DIR/alttpr.sh" $mode
Icon=applications-games
Categories=Game;
Terminal=false
EOF
  echo "Wrote $APPS_DIR/$id.desktop"
}
write_desktop alttpr-new "ALttP Randomizer - New Seed" new
write_desktop alttpr-continue "ALttP Randomizer - Continue" continue
write_desktop alttpr-spoiler "ALttP Randomizer - Spoiler" spoiler

echo
echo "Done. In Desktop Mode: Steam > Games > Add a Non-Steam Game to My Library,"
echo "tick the 'ALttP Randomizer' entries, then play from Game Mode."
