"""
Geocode the other verified layers (institute makerspaces, Maker Bhavan
Tinkerers' Labs, community makerspaces) with OpenStreetMap Nominatim.

Run from VS Code (after geocode_idea_labs.py, which shares the cache):
    cd makerspace-map
    python scripts/geocode_layers.py

For each databases/<layer>.csv it writes:
    databases/<layer>_geocoded.csv   (audit trail: query used, OSM match, precision)
    data/<layer>_map.csv             (rows the web app loads)
Rows with status 'likely inactive' or 'doubtful' are kept in the audit file but not mapped.
Data (c) OpenStreetMap contributors, ODbL.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geocode_idea_labs import Geocoder, state_ok, km, norm, same_name, load_manual, MAX_KM_FROM_PIN, CAMPUS_TYPES, ROOT  # noqa: E402

LAYERS = ["higher_ed_institute_makerspaces", "maker_bhavan_tinkerers_labs", "community_makerspaces_checked",
          "government_prototyping_hubs", "incubators_with_makerspaces", "fablabs_checked"]
SKIP_STATUS = {"likely inactive", "doubtful"}
PLACE_CATS = {"amenity", "building", "leisure", "office", "craft", "shop", "tourism"}


def name_tokens(name):
    words = re.findall(r"[A-Za-z]{4,}", name)
    stop = {"institute", "technology", "college", "engineering", "university", "indian", "national",
            "science", "research", "education", "makerspace", "tinkerers", "tinkering", "community", "centre", "center",
            "fablab", "fablabs", "labs", "maker", "makers", "space", "foundation", "india", "mini", "kerala"}
    return [w.lower() for w in words if w.lower() not in stop]


def geocode(g, row):
    state, city, pin = row["state"], re.sub(r"\(.*?\)", "", row["city"]).strip(), row.get("pin", "")
    out = {"lat": "", "lon": "", "location_precision": "not_found", "geocode_query": "", "osm_display_name": "", "geocode_note": ""}

    pin_pt = None
    if pin:
        hits = [h for h in g.search(postalcode=pin, country="India") if state_ok(h, state)]
        if hits:
            pin_pt = (float(hits[0]["lat"]), float(hits[0]["lon"]))

    target = row.get("geocode_name") or row["institution"] or row["name"].split(" — ")[0]
    toks = [t for t in name_tokens(target) if t not in norm(city) and t not in norm(state)]  # a city name is not evidence
    queries = [f"{target}, {city}, {state}", f"{target}, {state}"]
    addr = row.get("address", "")
    if re.search(r"\d", addr) and "(" not in addr:  # only real street addresses
        queries.insert(0, addr)
    for q in queries:
        for h in g.search(q=q):
            if not state_ok(h, state) or h.get("category") not in PLACE_CATS:
                continue
            disp = (h.get("display_name") or "").lower()
            is_campus = h.get("type") in CAMPUS_TYPES
            if not is_campus and not (toks and any(t in disp for t in toks) and same_name(target, h)):
                continue  # a building whose own name does not match ours
            if is_campus and not same_name(target, h):
                out["geocode_note"] += f"name mismatch rejected: {(h.get('name') or '')[:60]}; "
                continue
            pt = (float(h["lat"]), float(h["lon"]))
            if pin_pt and km(pt, pin_pt) > MAX_KM_FROM_PIN:
                out["geocode_note"] += f"match {km(pt, pin_pt):.0f} km from PIN area rejected; "
                continue
            out.update(lat=f"{pt[0]:.6f}", lon=f"{pt[1]:.6f}", location_precision="campus" if row["institution"] else "site",
                       geocode_query=q, osm_display_name=h.get("display_name", ""))
            return out

    # coordinates reported by the source itself (e.g. FabLabs.io), accepted only if they sit
    # inside India and, when a PIN is known, within 25 km of that PIN area
    try:
        slat, slon = float(row.get("src_lat") or "x"), float(row.get("src_lon") or "x")
    except ValueError:
        slat = slon = None
    if slat is not None and 6 <= slat <= 37.5 and 68 <= slon <= 97.5:
        if not pin_pt or km((slat, slon), pin_pt) <= MAX_KM_FROM_PIN:
            out.update(lat=f"{slat:.6f}", lon=f"{slon:.6f}", location_precision="self_reported", geocode_query="source coordinates")
            out["geocode_note"] += "coordinates as reported on the source (FabLabs.io), checked against PIN area"
            return out
        out["geocode_note"] += f"source coordinates {km((slat, slon), pin_pt):.0f} km from PIN area rejected; "

    if pin_pt:
        out.update(lat=f"{pin_pt[0]:.6f}", lon=f"{pin_pt[1]:.6f}", location_precision="pin_area", geocode_query=f"postalcode={pin}")
        out["geocode_note"] += "approximate: centre of PIN-code area"
        return out
    for q in (f"{city}, {state}",):
        hits = [h for h in g.search(q=q) if state_ok(h, state)]
        if hits:
            h = hits[0]
            out.update(lat=f"{float(h['lat']):.6f}", lon=f"{float(h['lon']):.6f}", location_precision="town",
                       geocode_query=q, osm_display_name=h.get("display_name", ""))
            out["geocode_note"] += "approximate: centre of town"
            return out
    out["geocode_note"] += "no match - add coordinates manually"
    return out


def main(fetch=None):
    g = Geocoder(fetch)
    manual = load_manual()
    for layer in LAYERS:
        src = os.path.join(ROOT, "databases", f"{layer}.csv")
        if not os.path.exists(src):
            print("missing", src); continue
        with open(src, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        audit, mapped = [], []
        print(f"\n== {layer} ({len(rows)} rows)")
        for i, row in enumerate(rows, 1):
            mk = (layer, row["name"].strip())
            if row.get("status") in SKIP_STATUS:
                res = {"lat": "", "lon": "", "location_precision": "skipped", "geocode_query": "", "osm_display_name": "",
                       "geocode_note": f"status '{row.get('status')}' - not mapped"}
            elif mk in manual:
                lat, lon, src = manual[mk]
                res = {"lat": f"{lat:.6f}", "lon": f"{lon:.6f}", "location_precision": "manual", "geocode_query": "manual_coordinates.csv",
                       "osm_display_name": "", "geocode_note": f"hand-checked coordinates ({src})"}
            else:
                res = geocode(g, row)
            print(f"[{i:3}/{len(rows)}] {res['location_precision']:9} {row['name'][:60]}")
            audit.append({**row, **res})
            if res["lat"]:
                m = {k: row[k] for k in ("name", "type", "institution", "city", "state", "address", "website", "description",
                                         "verified", "status", "source_url", "notes")}
                m.update(latitude=res["lat"], longitude=res["lon"], location_precision=res["location_precision"], contact="")
                mapped.append(m)
        with open(os.path.join(ROOT, "databases", f"{layer}_geocoded.csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(audit[0])); w.writeheader(); w.writerows(audit)
        os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
        with open(os.path.join(ROOT, "data", f"{layer}_map.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(mapped[0])); w.writeheader(); w.writerows(mapped)
        from collections import Counter
        print("  ", dict(Counter(r["location_precision"] for r in audit)))
    return True


if __name__ == "__main__":
    main()
