#!/usr/bin/env python3
"""Generate an ALttPR seed via alttpr.com and patch it onto a JP 1.0 base ROM.

Prints the path of the patched ROM on stdout (and nothing else) on success.
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import pyz3r

# Cosmetic options passed to create_patched_game; overridable via the preset's "cosmetics" key.
DEFAULT_COSMETICS = {
    "heartspeed": "half",
    "heartcolor": "red",
    "quickswap": True,
    "menu_speed": "normal",
    "spritename": "Link",
    "music": True,
    "msu1_resume": True,
}


async def generate(rom: Path, preset: Path, out_dir: Path) -> Path:
    preset_data = json.loads(preset.read_text())
    settings = preset_data["settings"]
    cosmetics = {**DEFAULT_COSMETICS, **preset_data.get("cosmetics", {})}

    seed = await pyz3r.ALTTPR.generate(settings=settings)

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"alttpr_{datetime.now():%Y%m%d-%H%M}_{seed.hash}"
    out_rom = out_dir / f"{stem}.sfc"

    await seed.create_patched_game(input_filename=str(rom), output_filename=str(out_rom), **cosmetics)

    meta = {
        "hash": seed.hash,
        # Seed permalink pages (with the spoiler, when enabled) live under /<lang>/h/; pyz3r's seed.url omits the language.
        "url": f"https://alttpr.com/en/h/{seed.hash}",
        "code": seed.code,
        "preset": preset.name,
        "settings": settings,
        "cosmetics": cosmetics,
        "generated": datetime.now().isoformat(timespec="seconds"),
    }
    (out_dir / f"{stem}.json").write_text(json.dumps(meta, indent=2))
    (out_dir / f"{stem}.spoiler.json").write_text(json.dumps(seed.data.get("spoiler", {}), indent=2))
    return out_rom


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="Unheadered JP 1.0 ROM")
    parser.add_argument("--preset", required=True, type=Path, help="Preset JSON file")
    parser.add_argument("--out-dir", required=True, type=Path, help="Where seeds are written")
    args = parser.parse_args()

    out_rom = asyncio.run(generate(args.rom, args.preset, args.out_dir))
    print(out_rom)
    return 0


if __name__ == "__main__":
    sys.exit(main())
