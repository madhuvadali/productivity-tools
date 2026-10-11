# India Makerspace Map

## Purpose

An interactive map of makerspaces, tinkering labs, FabLabs and prototyping
centres across India: AICTE IDEA Labs, IIT/NIT/IIIT/IISc/IISER institute
makerspaces, Maker Bhavan Tinkerers' Labs, community makerspaces, government
prototyping hubs, incubators with makerspaces, and FabLabs. Every entry is
checked against a source and tagged with a verification level and pin
precision; the full source register is in `databases/SOURCES.md`.

## Usage

Static site — no build step and no server-side code.

1. Open this folder in VS Code.
2. Right-click `index.html` → **Open with Live Server** (or run
   `python -m http.server 8000` from a terminal here and open
   `http://localhost:8000`).
3. Opening `index.html` directly by double-click will NOT work — the map
   loads its data over `fetch()`, which needs a real local server.

To refresh the underlying data, run the scripts in `scripts/` (see each
script's own docstring for usage and its Nominatim usage policy), then
`scripts/build_todo.py` to rebuild the combined to-do list.

## Dependencies

None to install — it's plain HTML/CSS/JS loading MapLibre GL and an
OpenFreeMap tile style from a CDN. The data-refresh scripts need Python 3
(standard library only).

## Status

`active`
