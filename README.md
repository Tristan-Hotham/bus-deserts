# Bus deserts: the villages with no bus and the last bus home

How far is the nearest bus from every English village, how often does it run, and when does the last one leave? Every timetabled
departure in the Department for Transport's Bus Open Data Service was counted at 251,790 bus stops on one Tuesday,
Saturday and Sunday in 2026 and related to 15,012 villages from Wikidata and all 33,755 small areas (LSOAs) in England.

Dr Tristan Hotham · Independent researcher · 2026

- Interactive map: https://maps.tristanhotham.com/bus-deserts/
- Paper: https://doi.org/10.5281/zenodo.24116216
- Blog post: https://blog.tristanhotham.com/2026/10/31/bus-deserts/
- Code and data: https://github.com/Tristan-Hotham/bus-deserts

## Headline results

- 4,891 villages (32.6%) have no stop with a weekday bus within 800 m; 2,966 (19.8%) have none within 1.6 km.
- A further 1,318 (8.8%) have only 1 to 3 weekday departures: 6,209 villages (41.4%) have no usable weekday bus.
- 61.5% of villages have no bus from 19:00 and 67.8% none on Sunday; 29.8% have a usable weekday, evening and Sunday service.
- 5,973,411 people (10.5%) live in small areas with no usable weekday bus within 800 m; 72% of them in rural areas.
- Pre-specified logit (LSOAs, rurality class and region fixed, clustered by district): IMD score odds ratio 0.68 (95% CI 0.60 to 0.78) per SD; share aged 60+ 1.28 (1.19 to 1.38). The planned falsification test failed (Indoors living environment OR 1.23), so these are descriptive associations.

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

Hotham, T. (2026) Bus deserts: villages without a usable bus, the last bus home and who lives beyond the network in England. Zenodo. https://doi.org/10.5281/zenodo.24116216

## AI statement

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
