"""Turn an ALttPR spoiler (the JSON saved by generate_seed.py) into readable sections of (left, right) rows."""
import re

DUNGEONS = {
    "H1": "Hyrule Castle", "H2": "Hyrule Castle", "P1": "Eastern Palace", "P2": "Desert Palace",
    "P3": "Tower of Hera", "A1": "Castle Tower", "D1": "Palace of Darkness", "D2": "Swamp Palace",
    "D3": "Skull Woods", "D4": "Thieves' Town", "D5": "Ice Palace", "D6": "Misery Mire",
    "D7": "Turtle Rock", "A2": "Ganon's Tower",
}
DUNGEON_ITEM = re.compile(r"^(Key|BigKey|Map|Compass)(H1|H2|P1|P2|P3|A1|A2|D[1-7])$")
RENAMES = {"OcarinaInactive": "Flute", "OcarinaActive": "Flute (activated)", "BossHeartContainer": "Heart Container"}


def item_name(raw: str) -> str:
    name = raw.split(":")[0]
    if m := DUNGEON_ITEM.match(name):
        kind = {"Key": "Small Key", "BigKey": "Big Key"}.get(m[1], m[1])
        return f"{kind} ({DUNGEONS[m[2]]})"
    name = RENAMES.get(name, name)
    return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=[0-9])", " ", name)


def location_name(raw: str) -> str:
    return raw.rsplit(":", 1)[0]


def sections(spoiler: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    """Return [(title, rows)]. A row with an empty right side is a sub-heading."""
    out = []

    playthrough = spoiler.get("playthrough", {})
    route = []
    for step in sorted((k for k in playthrough if k.isdigit()), key=int):
        route.append((f"Step {step}", ""))
        route += [(location_name(loc), item_name(item))
                  for region in playthrough[step].values() for loc, item in region.items()]
    if route:
        out.append(("Route to beat the game", route))

    skip = {"playthrough", "meta", "Shops", "Bosses", "Equipped"}
    for region, locations in spoiler.items():
        if region not in skip and isinstance(locations, dict):
            out.append((region, [(location_name(loc), item_name(item)) for loc, item in locations.items()]))

    if bosses := spoiler.get("Bosses"):
        out.append(("Bosses", list(bosses.items())))

    shops = []
    for shop in spoiler.get("Shops", []):
        for key, val in shop.items():
            if key.startswith("item_") and isinstance(val, dict):
                shops.append((shop.get("location", "Shop"), f"{item_name(val['item'])} ({val.get('price', '?')}r)"))
    if shops:
        out.append(("Shops", shops))

    return out
