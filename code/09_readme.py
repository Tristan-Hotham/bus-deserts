"""Step 9: README.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); h = R["head"]; v = R["settle"]["village"]; l = R["lsoa"]; x = R["x"]
t = f"""# Bus deserts: the villages with no bus and the last bus home

How far is the nearest bus from every English village, how often does it run, and when does the last one leave? Every timetabled
departure in the Department for Transport's Bus Open Data Service was counted at {R['feed']['bus_stops']:,} bus stops on one Tuesday,
Saturday and Sunday in 2026 and related to {v['n']:,} villages from Wikidata and all {l['n']:,} small areas (LSOAs) in England.

Dr Tristan Hotham · Independent researcher · 2026

- Interactive map: {PAGE}
- Paper: {{https://doi.org/10.5281/zenodo.24116216}}
- Blog post: {{https://blog.tristanhotham.com/2026/10/31/bus-deserts/}}
- Code and data: {REPO}

## Headline results

- {v['desert']:,} villages ({v['desert_pc']:.1f}%) have no stop with a weekday bus within 800 m; {v['deep']:,} ({v['deep_pc']:.1f}%) have none within 1.6 km.
- A further {v['token']:,} ({v['token_pc']:.1f}%) have only 1 to 3 weekday departures: {v['poor']:,} villages ({v['poor_pc']:.1f}%) have no usable weekday bus.
- {v['no_eve_pc']:.1f}% of villages have no bus from 19:00 and {v['no_sun_pc']:.1f}% none on Sunday; {v['full_pc']:.1f}% have a usable weekday, evening and Sunday service.
- {l['pop_poor']:,} people ({l['pop_poor_pc']:.1f}%) live in small areas with no usable weekday bus within 800 m; {l['poor_rural_share_pc']:.0f}% of them in rural areas.
- Pre-specified logit (LSOAs, rurality class and region fixed, clustered by district): IMD score odds ratio {x['imd_or']:.2f} (95% CI {x['imd_lo']:.2f} to {x['imd_hi']:.2f}) per SD; share aged 60+ {x['old_or']:.2f} ({x['old_lo']:.2f} to {x['old_hi']:.2f}). The planned falsification test failed (Indoors living environment OR {R['H3']['falsify']['terms']['ind_z']['or']:.2f}), so these are descriptive associations.

## Files

| Path | What |
|---|---|
| `index.html`, `js/page.js` | Interactive map (MapLibre, OpenFreeMap Positron) |
| `data/stops.csv.gz` | Every stop in England in the regional files: departures by day, first and last times, hourly counts |
| `data/settlements.csv` | Villages, hamlets, towns and cities with distance to the nearest weekday bus and service within 800 m |
| `data/lsoa.csv` | Small areas with deprivation, population, rural-urban class and service measures |
| `data/regions.csv`, `data/models.csv` | Regional table; every model estimate |
| `data/results.json` | Every number quoted anywhere |
| `data/feed_checks.json` | Duplicate and coverage checks of the timetable files |
| `data/site_*.json`, `data/england.geojson` | Compact copies for the map |
| `code/` | Numbered pipeline (00 to 09), templates, `overrides.json` (hand checks) |
| `release/paper/` | Paper (LaTeX and PDF) and cover note |
| `release/blog/`, `release/zenodo/` | Blog post and figures; Zenodo files and metadata |
| `reddit/` | Collage, its code, the GIF and the post |
| `NOTES.md` | Analysis plan (written before any result) and log |

## Method

The nine regional GTFS files were reduced to stop-level departure counts for one Tuesday, Saturday and Sunday (`code/00_gtfs_reduce.py`).
Bus and coach stops (route types 3, 200 to 209, 700 to 717) are kept; stops in two files take the copy with more weekday departures.
For each Wikidata settlement and each LSOA point, the nearest stop with a weekday departure and, among stops within 800 m, the busiest
stop, the latest weekday departure and any evening, Saturday or Sunday departure are found. A place has no usable weekday bus if no
stop within 800 m has a weekday bus, or the busiest has fewer than 4 departures. All ten towns first flagged as deserts were read by
eye; corrections are in `code/overrides.json`. LSOA points are representative points of the generalised 2021 boundaries (population
weighted centroids were not available); the geometric centroid is a check.

Limits: one week's timetables; school-only, demand-responsive and community services may be missing or odd; straight-line distances;
a stop departure is a bus calling, not a useful journey.

## Sources and licences

- Department for Transport, Bus Open Data Service (data.bus-data.dft.gov.uk), regional GTFS timetables, Open Government Licence v3.0.
- Wikidata (CC0).
- English Indices of Deprivation 2025, Ministry of Housing, Communities and Local Government, Open Government Licence v3.0.
- ONS 2021 Rural Urban Classification and LSOA 2021 boundaries, via humaniverse/geographr (GitHub), Open Government Licence v3.0. ONS region and country boundaries, OGL v3.0.
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL). MapLibre GL JS (BSD 3-Clause).
- Text, figures and data CC BY 4.0; code MIT (see `LICENSE`).

## Rerun

Raw paths are in `code/common.py` (override with `BD_BUS`, `BD_SETTLE`, `BD_IOD`, `BD_GEO`, `BD_SCRATCH`). The geographr files
`data/ruc21_lsoa21.rda` and `data/boundaries_lsoa21.rda` go in the scratch folder. Then run `01_stops.py`, `01b_lsoa_points.py`, `02_places.py`, `03_analysis.py`, `04_figures.py`, `05_site_data.py`, `06_site.py`,
`07_paper.py` (set `DOI` to fill the paper's DOI), `reddit/collage.py`, `08_release.py`, `09_readme.py`. Python 3 with pandas, geopandas,
scipy, statsmodels, rdata, matplotlib; xelatex.

## Citation

Hotham, T. (2026) Bus deserts: villages without a usable bus, the last bus home and who lives beyond the network in England. Zenodo. {{https://doi.org/10.5281/zenodo.24116216}}

## AI statement

{AI}
"""
for bad in ("—", "–", "D" "SIT", "D" "CMS", "November", "pre-" "registered"):
    assert bad not in t, bad
open(f"{ROOT}/README.md", "w", encoding="utf-8").write(t)
print("README", len(t.split()), "words")
