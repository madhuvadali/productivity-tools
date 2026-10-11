# Source register (draft) — India Makerspace Map
Last updated: 2026-10-09. Every row in the database must cite one of these source IDs.

| ID | Source | Use | Status | Notes |
|----|--------|-----|--------|-------|
| S1 | FabLabs.io (Fab Foundation lab directory) — https://www.fablabs.io | Primary source for FabLabs / mini-FabLabs | APPROVED by user 2026-10-09 | Self-registered entries; each cross-checked against the lab's own site; unconfirmed = "unverified". API endpoint api.fablabs.io/0/labs.json ignores country filter; India entries must be extracted from full paginated data. |
| S2 | Atal Innovation Mission, Operational ATLs list — https://aim.gov.in/pdf/OperationalATLsInIndia.pdf | School ATLs, separate category | APPROVED by user 2026-10-09 (as separate category) | ~10,000 labs; no coordinates in the source expected; location precision to be decided. No open licence stated. |
| S3 | Institution websites (IIT/NIT/IIIT/universities) | "Higher education" makerspaces, separate category | APPROVED by user 2026-10-09 | Each entry confirmed from the institution's own page. AIM has no official higher-ed ATL list. |
| S4 | Press listicles (Inc42 2017, The Better India, Homegrown, Digit, YourStory) | Leads only | APPROVED as leads only | Never cited as the data source; entry listed only if the space's own site/social confirms it is active. |
| S5 | OpenStreetMap (ODbL) | Not used | Not approved (leads only per user choice) | |
| -- | Lok Sabha Q.760 (7 Feb 2024) — https://eparlib.nic.in/bitstream/123456789/2974638/1/AU760.pdf | Context/count only (~10,000 ATLs) | Reference | |

## Known corrections to earlier sample data
- Maker's Asylum: sources indicate Moira, Goa (not Goregaon, Mumbai). Sample row to be replaced.

---
## Update 2026-10-11 — AICTE IDEA Labs (higher-education category)

| ID | Source | Use | Status | Notes |
|----|--------|-----|--------|-------|
| S6 | `IDEA Labs Contacts.xlsx` (user-supplied, provenance unknown) | **College names only** (193 rows, years 2021-22 to 2024-25) | Used as a checklist, not as a data source | District/State columns are misaligned with names (168 of 193 states wrong); email/contact columns are also shifted. Personal names, emails and phone numbers are NOT carried into the database. |
| S7 | AICTE, "IDEA Lab Result 2020-21" (14 Jun 2021) — https://aicte.gov.in/sites/default/files/IDEALAB_RESULT.pdf | Official confirmation for the 49 first-round labs | Reference | Only official AICTE list found; later rounds' results not located. |
| S8 | Each college's own official website / own documents (contact pages, mandatory disclosures, letterheads) | Primary source for address | Used (136 rows "high") | URL recorded per row in `source_url`. |
| S9 | Semi-official records: Anna University affiliated-college records (annauniv.edu/cai), COMEDK college pages, Punjab DTE college list, WBJEE Board institute sheet, IIT Bombay Spoken Tutorial academic-centre records, college letters hosted by the college | Fallback when the college site was unreadable | Used (rated "high" or "medium") | |
| S10 | Wikipedia | Fallback | APPROVED by user 2026-10-11 as fallback | Used for ~20 rows, rated "medium"; replace with official address when found. |
| S11 | Third-party college aggregators (CollegeBatch, TargetAdmission, Careers360, TNEA 2015 sheet mirrored on myklassroom) | Last-resort fallback | APPROVED by user 2026-10-11 — keep as "low", show on map flagged as unverified | Used for 12 rows. |

### Confidence levels in `idea_labs_verified.csv`
- **high** — address read from the college's own website/document or an official university/government record.
- **medium** — from Wikipedia or a semi-official record, or the official site gave only partial address (e.g., no PIN).
- **low** — from a third-party aggregator, or only town-level location known.
- **ambiguous** — the sheet name matches more than one college (row 14, Narayana Engineering College: Nellore or Gudur).

### Other caveats
- `district` is as stated by the source where given; otherwise inferred from the town (several Andhra Pradesh districts were reorganised in 2022 — those rows are noted).
- Rows where the name matches several colleges (UIET, Don Bosco IT, JSSATE, Guru Nanak IT, Indira Gandhi IT, G.H. Raisoni CEM) were resolved using the sheet's state ordering and email-domain hints; each is noted and should be confirmed.
- None of these rows yet confirms that the IDEA Lab itself exists/is operational — only the institution's address. Several colleges have their own "AICTE IDEA Lab" pages (e.g., Sanjivani, SVERI, SGGSIET, RGMCET) that can be used for that check.
- No coordinates yet; geocoding is a separate step.

---
## Update 2026-10-11 — Coordinates (geocoding)

| ID | Source | Use | Status | Notes |
|----|--------|-----|--------|-------|
| S12 | OpenStreetMap Nominatim — https://nominatim.org (data © OpenStreetMap contributors, ODbL) | Converting verified addresses to map coordinates | APPROVED by user 2026-10-11 | Run locally with `scripts/geocode_idea_labs.py` (1 request/s). Credited on the map. |

### How each pin is placed (`location_precision`)
1. **campus** — Nominatim finds the institution itself (tagged as a university/college) in the expected state, and it is within 25 km of its PIN-code area. Otherwise rejected.
2. **pin_area** — centre of the college's PIN-code area, only if that area is in the expected state.
3. **town** — centre of the town/city in the expected state.
4. **not_found / skipped** — no pin; the ambiguous row (Narayana Engineering College) is skipped.

Approximate pins (pin_area, town) are drawn as faded dots, and every popup shows the confidence level, the pin precision and a link to the address source.
`databases/idea_labs_geocoded.csv` keeps the query and the OSM match for every row, so any pin can be audited.

---
## Update 2026-10-11 — Institute makerspaces, Maker Bhavan Tinkerers' Labs, community makerspaces

| ID | Source | Use | Status | Notes |
|----|--------|-----|--------|-------|
| S13 | Wikipedia lists of IITs, NITs, IIITs, IISERs | List of the 88 institutes to check (23 IITs, 31 NITs + IIEST Shibpur, 25 IIITs, IISc, 7 IISERs) | Reference (Wikipedia approved as fallback) | Institute websites/cities partly from memory; IIT Roorkee state corrected to Uttarakhand. |
| S14 | Maker Bhavan Foundation, "Our Labs" — https://makerbhavanfoundation.org/programs/tinkerers-lab/our-labs/ | Source for Tinkerers' Labs (24 listed) | APPROVED by user 2026-10-11 (include all 24) | Snapshot: `maker_bhavan_our_labs_snapshot.txt`. 7 IIT labs merged into the institute file; 16 others in `maker_bhavan_tinkerers_labs.csv`. |
| S15 | hackerspaces.in (Ansh Arora, CC BY-SA 4.0; GitHub commit 228c1d2, 8 Apr 2026) | Leads for community makerspaces | APPROVED as leads only | Raw leads kept in `hackerspaces_in_leads.csv`; a space is listed only if its own site confirms it. |
| S4 | Press articles: Better India (2016), Inc42 (2017), ThePrint (2022), Homegrown (2021) | Leads for community makerspaces | Leads only (approved earlier) | |
| S1 | FabLabs.io | FabLab category | APPROVED as primary source | Pending: run `scripts/fetch_fablabs_india.py`, then each lab is checked on its own site. |

### Institute makerspaces (`higher_ed_institutes_checked.csv`)
- Included only if an official institute page (or the Maker Bhavan list) describes a fabrication / tinkering / prototyping facility that students can use.
- 19 of 88 institutes have a facility recorded. For the other 69 the note says **"Not found in web search — absence NOT confirmed"**: my search tools index institute sites poorly, so a missing entry means "not yet found", not "does not exist".
- Excluded after checking: NIT Uttarakhand DIC (no fabrication facility stated), NIT Rourkela TIIR fabrication unit (for incubated companies, not students), IIT Roorkee (only a third-party LinkedIn page).

### Community makerspaces (`community_makerspaces_checked.csv`)
- `status`: **active** (dated activity in 2024-2026 on own site), **uncertain** (site live but no date), **likely inactive** (nothing after 2019-2020 — not mapped).
- Excluded leads and reasons: `community_leads_excluded.csv` (e.g., Maker's Loft now a coaching business; Collab House domain for sale; Jaaga and The Makerspace Initiative are not makerspaces).

### Pins for these layers (`scripts/geocode_layers.py`)
Same rules as the IDEA Labs (state check, 25 km PIN check), plus: a named building is accepted only if its OSM name contains a distinctive word of the facility/institution name. Precision `site` = the makerspace's own building.

---
## Update 2026-10-11 — Government prototyping hubs, incubators with makerspaces (MSME Technology Centres excluded at user's request)

| ID | Source | Use | Status | Notes |
|----|--------|-----|--------|-------|
| S16 | Official sites of government bodies: T-Works (tworks.telangana.gov.in), STPI (stpi.in), NIF (nif.org.in), iTNT Hub (itnthub.tn.gov.in), 36Inc (36inc.in) | Primary source | Official | |
| S17 | Kerala Startup Mission official FabLab list — https://sites.google.com/startupmission.in/fablabkerala/labs | All 23 KSUM FabLabs (2 main + 21 college-hosted) | APPROVED by user: all 23 in 'Government prototyping hubs' | Listed by the operator; per-lab activity not checked → 'medium'. |
| S18 | MeitY/NeGD presentation "Maker Village Incubation Facilities" (Dec 2021) | Confirms Maker Village Kochi (own site blocks automated reading) | Government document | |
| S19 | startupgrantsindia.com "Incubators with FabLab" (75 names) | Leads for 'Incubators with makerspaces' | APPROVED as leads only | Confirmed 7 on own sites; the rest listed in `incubator_leads_not_confirmed.txt`, to be cross-checked in the FabLab pass. |

Files: `government_prototyping_hubs.csv` (27), `incubators_with_makerspaces.csv` (7). Column `geocode_name` = the place name used for geocoding.
Also added at user's request: Centre for Creative Learning, IIT Gandhinagar (community makerspaces, confirmed on ccl.iitgn.ac.in).

---
## Update 2026-10-11 — FabLabs (FabLabs.io, approved primary source)

Downloaded with `scripts/fetch_fablabs_india.py` (raw file kept: `fablabs_io_india_raw.json`). Every one of the 102 India entries has a recorded decision in `fablabs_io_decisions.csv`:
- **Excluded (29):** FabLabs.io status 'planned' (23, mostly KSUM mini-labs) or 'closed' (2); Logicbrigade (domain for sale); INIFD College Pune (domain now an unrelated site); Maker Auto (mobile, no fixed place).
- **Duplicates (21):** already in another layer (11 Kerala Startup Mission / STPI / NIF hubs, 3 incubators, 3 community spaces, 1 IIT Palakkad) or repeated entries.
- **Included (52)** in `fablabs_checked.csv`: high 5 / medium 7 (own site confirms) and **low 40 = 'unverified'** (no site, site unreadable, or site does not mention a lab) — kept per the approved rule "flag any I can't confirm as unverified".
- FabLabs.io data is self-registered and partly stale: e.g. 36Inc is 'planned' there but its own site says it opened in 2017; Vigyan Ashram is marked 'corona' but is active (2026); Sathyabama TBI (Chennai) carries a Salem PIN (removed).

### Pins for FabLabs
FabLabs.io gives coordinates for most labs. They are used as `self_reported` pins only if inside India and within 25 km of the lab's PIN-code area; otherwise the usual PIN-area / town fallback applies. Self-reported and approximate pins are drawn faded.
A named building found in OpenStreetMap is now accepted only if its own name matches the facility name (a shared town name is not enough).

---
## Update 2026-10-11 — Re-check of unverified FabLabs; decisions

**Atal Tinkering Labs: DROPPED by user decision (2026-10-11).** The AIM PDF stays in `databases/` but will not be used.

| ID | Source | Use | Status | Notes |
|----|--------|-----|--------|-------|
| S20 | Fab Academy lab lists 2022-2026 (fabacademy.org/<year>/labs/) — run by the Fab Foundation, same body as FabLabs.io | Evidence that a lab is operating in a given year | Used as activity evidence | India labs 2025-26: Kerala (Trivandrum, Kochi), Salem, Nellai, Trichy, riidl, Sanjivani, Vigyan Ashram, Nagpur. |
| S21 | Innovate TN programme page at GCE Tirunelveli (gcetly.ac.in/About/InnovateTN.php) | Confirms Tamil Nadu govt FabLabs: selected by Directorate of Technical Education, funded by TANSIM, run by Forge for 5 years from 2023-24 | Official | |
| S22 | Forge FORT site (fort.forgeforward.in) | Confirms SIPCOT FORT Hosur / FORT Chennai (Tamil Nadu Industries Dept with Forge) | Operator site | |

Results of the re-check (40 unverified at start):
- Upgraded with evidence: riidl Mumbai, FabLab Salem, Nellai, Trichy (Fab Academy / host college), FORT Hosur (operator site), NSUT Delhi IoT & Fab Lab (press, Aug 2025), IIT Kanpur 4i Lab (official page), AIC-RNTU i4 Lab (own lab page), AKGEC FabLab (college document 2023), Fab Crescent (Crescent's 2026 infrastructure book describes the fabrication labs).
- **Moved to 'Government prototyping hubs' (user decision):** the 3 Innovate TN labs, FORT Hosur, FORT Chennai and FabLab Madurai (Madurai and FORT Chennai still unconfirmed).
- **Doubtful (kept in database, NOT mapped — user decision):** hackerslab Erode (IoT/Android group, no fabrication listed), INIFD Pune Kothrud and INIFD Kondhwa (entries read as fashion-school advertising).
- Still unverified (23): only FabLabs.io lists them; their self-reported capabilities are shown in the description. No dates exist in FabLabs.io data, so the age of these listings cannot be judged.

---
## Update 2026-10-11 — Remarks (to-do) columns and manual pins

Every database file now has two extra columns that are **never shown on the map**:
- `action_needed` — what still has to be done for that entry (e.g. confirm the IDEA Lab is running, find the PIN, resolve an address conflict, contact an unverified lab).
- `action_priority` — High / Medium / Low.

`scripts/build_todo.py` combines these with map-pin issues from the latest geocoding run into **`databases/TODO.csv`** (one row per task, sorted by priority).

**Fixing a pin by hand:** add a row to `databases/manual_coordinates.csv`
(`layer,name,latitude,longitude,coordinates_source,checked_on,notes`; `name` exactly as in the database file) and rerun the geocoding script. Hand-set pins show as "Pin checked by hand" and are not faded.
