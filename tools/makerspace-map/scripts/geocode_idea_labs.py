"""
Geocode the verified AICTE IDEA Lab list with OpenStreetMap Nominatim.

Run from VS Code (no extra packages needed):
    cd makerspace-map
    python scripts/geocode_idea_labs.py

Input : databases/idea_labs_verified.csv
Output: databases/idea_labs_geocoded.csv  (full audit trail, one row per college)
        data/idea_labs_map.csv            (map-ready rows the web app loads)
Cache : databases/.geocode_cache.json     (so re-runs resume and do not re-query)

Usage policy: Nominatim allows at most 1 request per second and needs an
identifying User-Agent. This script waits 1.1 s between requests.
Data (c) OpenStreetMap contributors, ODbL.
"""
import csv
import difflib
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_CSV = os.path.join(ROOT, "databases", "idea_labs_verified.csv")
OUT_AUDIT = os.path.join(ROOT, "databases", "idea_labs_geocoded.csv")
OUT_MAP = os.path.join(ROOT, "data", "idea_labs_map.csv")
CACHE = os.path.join(ROOT, "databases", ".geocode_cache.json")
MANUAL = os.path.join(ROOT, "databases", "manual_coordinates.csv")


def load_manual():
    """Hand-checked coordinates: databases/manual_coordinates.csv (layer, name, latitude, longitude, ...)."""
    out = {}
    if os.path.exists(MANUAL):
        with open(MANUAL, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                try:
                    out[(r["layer"].strip(), r["name"].strip())] = (float(r["latitude"]), float(r["longitude"]), r.get("coordinates_source", ""))
                except (ValueError, KeyError):
                    print("   ! skipped bad row in manual_coordinates.csv:", r)
    return out

ENDPOINT = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "IndiaMakerspaceMap/0.1 (personal research project; geocoding ~200 college addresses)"
DELAY = 1.1
MAX_KM_FROM_PIN = 25  # a campus hit further than this from its PIN area is flagged

CAMPUS_TYPES = {"university", "college", "school", "research_institute"}


ABBREV = [(r"\bgovt\.?", "government"), (r"\bengg\.?", "engineering"), (r"\binst\.?", "institute"), (r"\btech\.?(?=\s|$)", "technology")]


def norm(s):
    s = (s or "").lower().replace("&", "and")
    for pat, rep in ABBREV:
        s = re.sub(pat, rep, s)
    return re.sub(r"[^a-z]", "", s)


def km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


class Geocoder:
    def __init__(self, fetch=None):
        self.cache = {}
        if os.path.exists(CACHE):
            with open(CACHE, encoding="utf-8") as f:
                self.cache = json.load(f)
        self.fetch = fetch or self._http
        self.last = 0.0

    def _http(self, url):
        wait = DELAY - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        finally:
            self.last = time.time()

    def search(self, **params):
        params.update({"format": "jsonv2", "addressdetails": 1, "countrycodes": "in", "limit": 5})
        url = ENDPOINT + "?" + urllib.parse.urlencode(params)
        if url not in self.cache:
            try:
                self.cache[url] = self.fetch(url)
            except Exception as e:  # network error: do not cache, report
                print(f"   ! request failed: {e}")
                return []
            with open(CACHE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
        return self.cache[url]


def state_ok(hit, state):
    s = norm((hit.get("address") or {}).get("state"))
    want = norm(state)
    return bool(s) and (s == want or want in s or s in want)


def same_name(ours, hit):
    """True if the OSM feature's name matches our institution name closely enough."""
    osm = re.sub(r"\(.*?\)", "", hit.get("name") or (hit.get("display_name") or "").split(",")[0])
    a, b = norm(clean_name(ours)), norm(osm)
    if not a or not b:
        return False
    short, long_ = sorted((a, b), key=len)
    if len(short) >= 12 and short in long_:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


def clean_name(name):
    name = re.sub(r"\(.*?\)", "", name)          # drop "(Autonomous)", "(now ...)"
    name = name.split(" / ")[0]
    return re.sub(r"\s+", " ", name).strip(" ,")


def geocode_row(g, row):
    """Return dict with lat, lon, precision, query, display_name, note."""
    state, city, pin = row["state"], row["city_town"], row["pin"]
    city = re.sub(r"\(.*?\)", "", city).split(" or ")[0].strip()
    out = {"lat": "", "lon": "", "geocode_precision": "not_found", "geocode_query": "",
           "osm_display_name": "", "geocode_note": ""}

    pin_pt = None
    if pin:
        hits = g.search(postalcode=pin, country="India")
        hits = [h for h in hits if state_ok(h, state)]  # never trust a PIN hit in another state
        if hits:
            pin_pt = (float(hits[0]["lat"]), float(hits[0]["lon"]))

    # 1) the institution itself
    name = clean_name(row["official_name_found"])
    for q in (f"{name}, {city}, {state}", f"{name}, {state}"):
        for h in g.search(q=q):
            if not state_ok(h, state):
                continue
            is_campus = h.get("category") in ("amenity", "building") and h.get("type") in CAMPUS_TYPES
            if not is_campus:
                continue
            if not same_name(name, h):
                out["geocode_note"] = f"name mismatch rejected: {(h.get('name') or '')[:60]}; "
                continue
            pt = (float(h["lat"]), float(h["lon"]))
            if pin_pt and km(pt, pin_pt) > MAX_KM_FROM_PIN:
                out["geocode_note"] = f"campus match {km(pt, pin_pt):.0f} km from PIN area - rejected; "
                continue
            out.update(lat=f"{pt[0]:.6f}", lon=f"{pt[1]:.6f}", geocode_precision="campus",
                       geocode_query=q, osm_display_name=h.get("display_name", ""))
            return out

    # 2) PIN-code area
    if pin_pt:
        out.update(lat=f"{pin_pt[0]:.6f}", lon=f"{pin_pt[1]:.6f}", geocode_precision="pin_area",
                   geocode_query=f"postalcode={pin}")
        out["geocode_note"] += "approximate: centre of PIN-code area"
        return out

    # 3) town
    for q in (f"{city}, {row['district']}, {state}", f"{city}, {state}"):
        hits = [h for h in g.search(q=q) if state_ok(h, state)]
        if hits:
            h = hits[0]
            out.update(lat=f"{float(h['lat']):.6f}", lon=f"{float(h['lon']):.6f}", geocode_precision="town",
                       geocode_query=q, osm_display_name=h.get("display_name", ""))
            out["geocode_note"] += "approximate: centre of town"
            return out

    out["geocode_note"] += "no match - add coordinates manually"
    return out


def main(fetch=None):
    with open(IN_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    g = Geocoder(fetch)
    manual = load_manual()
    audit, mapped = [], []
    for i, row in enumerate(rows, 1):
        mk = ("idea_labs", row["official_name_found"].strip())
        if mk in manual:
            lat, lon, src = manual[mk]
            res = {"lat": f"{lat:.6f}", "lon": f"{lon:.6f}", "geocode_precision": "manual", "geocode_query": "manual_coordinates.csv",
                   "osm_display_name": "", "geocode_note": f"hand-checked coordinates ({src})"}
        elif row["confidence"] == "ambiguous":
            res = {"lat": "", "lon": "", "geocode_precision": "skipped", "geocode_query": "",
                   "osm_display_name": "", "geocode_note": "ambiguous institution - resolve first"}
        else:
            res = geocode_row(g, row)
        print(f"[{i:3}/{len(rows)}] {res['geocode_precision']:9} {row['official_name_found'][:60]}")
        audit.append({**row, **res})
        if res["lat"]:
            mapped.append({
                "name": row["official_name_found"],
                "type": "IDEA Lab (AICTE, higher education)",
                "city": row["city_town"], "state": row["state"],
                "latitude": res["lat"], "longitude": res["lon"],
                "address": row["address"], "website": row["official_website"],
                "contact": "",
                "description": f"AICTE IDEA Lab, listed for {row['sheet_year']}.",
                "verified": row["confidence"],
                "location_precision": res["geocode_precision"],
                "source_url": row["source_url"],
                "notes": row["notes"],
            })

    with open(OUT_AUDIT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(audit[0].keys()))
        w.writeheader(); w.writerows(audit)
    os.makedirs(os.path.dirname(OUT_MAP), exist_ok=True)
    with open(OUT_MAP, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(mapped[0].keys()))
        w.writeheader(); w.writerows(mapped)

    from collections import Counter
    c = Counter(r["geocode_precision"] for r in audit)
    print("\nDone.", dict(c))
    print("Audit file :", OUT_AUDIT)
    print("Map file   :", OUT_MAP)
    return audit


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
