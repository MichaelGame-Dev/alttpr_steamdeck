#!/usr/bin/env bash
# ALttPR launcher.
#   alttpr.sh new [preset]  generate a fresh seed (default preset from config, or e.g. -open), then play it
#   alttpr.sh continue      play the most recently generated seed (settings are baked into it; extra args ignored)
#   alttpr.sh spoiler       browse the latest seed's spoiler on the TV with the controller
set -uo pipefail

REPO_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
DATA_DIR="$HOME/.local/share/alttpr-launcher"
CONFIG="$HOME/.config/alttpr-launcher/config.env"
LOG="$DATA_DIR/launcher.log"
export PYGAME_HIDE_SUPPORT_PROMPT=1

mkdir -p "$DATA_DIR"
exec >>"$LOG" 2>&1
echo "=== $(date '+%F %T') alttpr.sh $*"

die() {
  printf 'ERROR: %b\n' "$*"
  command -v zenity >/dev/null && zenity --error --title="ALttP Randomizer" --text="$*\n\nLog: $LOG" --width=400
  exit 1
}

[[ -f "$CONFIG" ]] || die "Missing config $CONFIG. Run install.sh first."
# shellcheck source=config.env.example
source "$CONFIG"

if [[ -z "${SEED_DIR:-}" ]]; then
  if [[ -d "$HOME/Emulation/roms/snes" ]]; then
    SEED_DIR="$HOME/Emulation/roms/snes/alttpr"
  else
    SEED_DIR="$DATA_DIR/seeds"
  fi
fi
LATEST="$SEED_DIR/latest.txt"

latest_rom() {
  [[ -f "$LATEST" ]] && cat "$LATEST"
}

launch() {
  local rom="$1"
  [[ -f "$rom" ]] || die "Seed ROM not found: $rom"
  echo "Launching $rom"
  exec "${RETROARCH_CMD[@]}" "$rom"
}

case "${1:-continue}" in
  new)
    [[ -f "$BASE_ROM" ]] || die "Base ROM not found: $BASE_ROM. Run install.sh."
    # Optional preset name overrides the config, e.g. "open", "-open" or "--open" -> presets/open.json.
    if [[ -n "${2:-}" ]]; then
      name="${2#"${2%%[!-]*}"}"
      PRESET="presets/${name%.json}.json"
      [[ -f "$REPO_DIR/$PRESET" ]] || die "Unknown preset '$2'. Available: $(cd "$REPO_DIR/presets" && ls *.json | sed 's/\.json$//' | tr '\n' ' ')"
    fi
    [[ "$PRESET" = /* ]] || PRESET="$REPO_DIR/$PRESET"
    echo "Generating seed with preset $PRESET"
    if rom="$("$DATA_DIR/venv/bin/python" "$REPO_DIR/generate_seed.py" \
        --rom "$BASE_ROM" --preset "$PRESET" --out-dir "$SEED_DIR")" && [[ -f "$rom" ]]; then
      echo "$rom" >"$LATEST"
      launch "$rom"
    fi
    prev="$(latest_rom)"
    [[ -n "$prev" ]] || die "Seed generation failed and there is no previous seed to fall back to."
    command -v zenity >/dev/null && zenity --warning --title="ALttP Randomizer" --timeout=8 --width=400 \
      --text="Couldn't generate a new seed (offline?).\nLoading your previous seed instead."
    launch "$prev"
    ;;
  continue)
    prev="$(latest_rom)"
    [[ -n "$prev" ]] || die "No seed generated yet. Use 'New Seed' first."
    launch "$prev"
    ;;
  spoiler)
    prev="$(latest_rom)"
    [[ -n "$prev" ]] || die "No seed generated yet. Use 'New Seed' first."
    meta="${prev%.sfc}.json"
    [[ -f "$meta" ]] || die "Seed info not found: $meta"
    "$DATA_DIR/venv/bin/python" -c 'import pygame' 2>/dev/null \
      || die "The spoiler viewer's Python package (pygame-ce) is missing. Re-run install.sh."
    exec "$DATA_DIR/venv/bin/python" "$REPO_DIR/show_spoiler.py" "$meta"
    ;;
  *)
    die "Usage: alttpr.sh new [preset]|continue|spoiler"
    ;;
esac
