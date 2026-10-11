"""
Download the India entries from the FabLabs.io directory (Fab Foundation).

Run from VS Code (no extra packages needed):
    cd makerspace-map
    python scripts/fetch_fablabs_india.py

Output: databases/fablabs_io_india_raw.json   (exact records as returned, for audit)
        databases/fablabs_io_india.csv        (one row per India lab, for review)

FabLabs.io entries are self-registered by the labs. Each one still has to be
checked against the lab's own website before it goes on the map.
"""
import csv
import datetime
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(ROOT, "databases", "fablabs_io_india_raw.json")
OUT_CSV = os.path.join(ROOT, "databases", "fablabs_io_india.csv")
URLS = ["https://api.fablabs.io/0/labs.json", "https://api.fablabs.io/v0/labs.json"]
UA = "IndiaMakerspaceMap/0.1 (personal research project)"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def all_labs():
    last_err = None
    for base in URLS:
        try:
            data = get(base)
        except Exception as e:
            last_err = e
            print(f"  {base} failed: {e}")
            continue
        if isinstance(data, list):
            return data, base
        # paginated / wrapped responses
        labs = data.get("labs") or data.get("data") or []
        page, url = 1, base
        while isinstance(data, dict) and (data.get("next") or data.get("links", {}).get("next")):
            url = data.get("next") or data["links"]["next"]
            page += 1
            print(f"  page {page}")
            data = get(url)
            labs += data.get("labs") or data.get("data") or []
        return labs, base
    raise SystemExit(f"Could not reach FabLabs.io API: {last_err}")


def is_india(lab):
    a = lab.get("attributes", lab)  # handle JSON:API style
    cc = (a.get("country_code") or "").lower()
    return cc == "in" or (a.get("country") or "").lower() == "india"


def main():
    print("Downloading FabLabs.io directory ...")
    labs, src = all_labs()
    print(f"  {len(labs)} labs worldwide from {src}")
    india = [l for l in labs if is_india(l)]
    print(f"  {len(india)} labs with country = India")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"source": src, "downloaded": datetime.datetime.now().isoformat(timespec="seconds"),
                   "count_worldwide": len(labs), "labs": india}, f, ensure_ascii=False, indent=1)

    cols = ["name", "slug", "kind_name", "activity_status", "address_1", "address_2", "city", "county",
            "postal_code", "latitude", "longitude", "urls", "email", "fablabs_io_url", "created_at", "updated_at"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for l in india:
            a = dict(l.get("attributes", l))
            links = a.get("links") or a.get("urls") or []
            if isinstance(links, list):
                a["urls"] = " ; ".join(x.get("url", "") if isinstance(x, dict) else str(x) for x in links)
            a["fablabs_io_url"] = f"https://www.fablabs.io/labs/{a.get('slug', '')}"
            a["email"] = ""  # not carried over (contact data not needed for the map)
            w.writerow(a)
    if india:
        print("  fields available:", ", ".join(sorted(india[0].keys())))
    print("Saved:", OUT_CSV)
    print("Saved:", OUT_JSON)


if __name__ == "__main__":
    main()
