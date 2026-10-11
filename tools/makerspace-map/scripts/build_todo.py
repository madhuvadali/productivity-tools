"""
Build one combined to-do list from all databases.

Run from VS Code (after the geocoding scripts, so pin items are current):
    cd makerspace-map
    python scripts/build_todo.py

Reads   databases/<file>.csv            -> columns action_needed / action_priority (data checks)
        databases/<layer>_geocoded.csv  -> pin precision (map-pin improvements)
Writes  databases/TODO.csv   (never loaded by the map)

To fix an approximate pin, add a row to databases/manual_coordinates.csv:
    layer,name,latitude,longitude,coordinates_source,checked_on,notes
(layer = idea_labs, higher_ed_institute_makerspaces, maker_bhavan_tinkerers_labs,
 community_makerspaces_checked, government_prototyping_hubs, incubators_with_makerspaces,
 fablabs_checked; name = exactly as in the database) and rerun the geocoding script.
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "databases")

# (category label, source file, name column, layer key for pins or None)
FILES = [
    ("IDEA Labs (AICTE)", "idea_labs_verified.csv", "official_name_found", "idea_labs"),
    ("Institutes checked (IIT/NIT/IIIT/IISc/IISER)", "higher_ed_institutes_checked.csv", "institute", None),
    ("Institute makerspaces", "higher_ed_institute_makerspaces.csv", "name", "higher_ed_institute_makerspaces"),
    ("Tinkerers' Labs (Maker Bhavan)", "maker_bhavan_tinkerers_labs.csv", "name", "maker_bhavan_tinkerers_labs"),
    ("Community makerspaces", "community_makerspaces_checked.csv", "name", "community_makerspaces_checked"),
    ("Community leads excluded", "community_leads_excluded.csv", "name", None),
    ("Government prototyping hubs", "government_prototyping_hubs.csv", "name", "government_prototyping_hubs"),
    ("Incubators with makerspaces", "incubators_with_makerspaces.csv", "name", "incubators_with_makerspaces"),
    ("FabLabs", "fablabs_checked.csv", "name", "fablabs_checked"),
]
GEOCODED = {"idea_labs": "idea_labs_geocoded.csv"}
PIN_ACTION = {
    "not_found": ("High", "No map pin: add coordinates to manual_coordinates.csv"),
    "town": ("Medium", "Map pin is only the town centre: add exact coordinates to manual_coordinates.csv"),
    "pin_area": ("Low", "Map pin is the PIN-code area centre: add exact coordinates to manual_coordinates.csv"),
    "self_reported": ("Low", "Pin uses FabLabs.io's self-reported coordinates: check it on a map; if wrong, add to manual_coordinates.csv"),
}
ORDER = {"High": 0, "Medium": 1, "Low": 2}
NO_ACTION = ("No action", "None - re-check yearly")


def read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    todo = []
    for cat, fn, ncol, layer in FILES:
        rows = read(os.path.join(DB, fn))
        if not rows:
            print("missing", fn)
            continue
        for r in rows:
            act = r.get("action_needed", "")
            if act and not act.startswith(NO_ACTION):
                todo.append({"priority": r.get("action_priority", "Medium"), "category": cat, "name": r.get(ncol, ""),
                             "city": r.get("city", r.get("city_town", "")), "state": r.get("state", ""),
                             "kind": "data check", "action": act, "file": fn})
        if layer:
            geo = read(os.path.join(DB, GEOCODED.get(layer, f"{layer}_geocoded.csv")))
            for g in geo:
                prec = g.get("location_precision") or g.get("geocode_precision")
                if prec in PIN_ACTION:
                    p, a = PIN_ACTION[prec]
                    todo.append({"priority": p, "category": cat, "name": g.get(ncol, g.get("name", "")),
                                 "city": g.get("city", g.get("city_town", "")), "state": g.get("state", ""),
                                 "kind": "map pin", "action": a, "file": GEOCODED.get(layer, f"{layer}_geocoded.csv")})
    todo.sort(key=lambda t: (ORDER.get(t["priority"], 3), t["category"], t["kind"], t["name"]))
    out = os.path.join(DB, "TODO.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["priority", "category", "name", "city", "state", "kind", "action", "file"])
        w.writeheader()
        w.writerows(todo)
    from collections import Counter
    print(f"{len(todo)} items -> {out}")
    print("  by priority:", dict(Counter(t["priority"] for t in todo)))
    print("  by kind    :", dict(Counter(t["kind"] for t in todo)))


if __name__ == "__main__":
    main()
