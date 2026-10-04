#!/usr/bin/env bash
# ALttPR launcher.
#   alttpr.sh new       generate a fresh seed, then play it
#   alttpr.sh continue  play the most recently generated seed
set -uo pipefail

REPO_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
DATA_DIR="$HOME/.local/share/alttpr-launcher"
CONFIG="$HOME/.config/alttpr-launcher/config.env"
LOG="$DATA_DIR/launcher.log"

mkdir -p "$DATA_DIR"
exec >>"$LOG" 2>&1
echo "=== $(date '+%F %T') alttpr.sh $*"

die() {
  echo "ERROR: $*"
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
[[ "$PRESET" = /* ]] || PRESET="$REPO_DIR/$PRESET"
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
  *)
    die "Usage: alttpr.sh new|continue"
    ;;
esac
