**Title:** [OC] 41% of English villages have no bus stop with four or more weekday buses within 800 m, and 68% have no Sunday bus within that distance

**Body:**

I counted every timetabled bus departure in England (Department for Transport's Bus Open Data Service) at 251,790 stops on one Tuesday, Saturday and Sunday in 2026, then checked 15,012 villages from Wikidata.

- 33% of villages have no stop with a single weekday bus within 800 m; 20% have none within 1.6 km.
- Another 9% get only 1 to 3 buses a day. Together, 41% have no usable weekday bus.
- 62% have no bus from 7pm. Only 30% have a usable weekday service, an evening bus and a Sunday bus.
- 6.0 million people (10.5%) live in small areas with no usable weekday bus; 72% of them are rural.
- Holding rurality fixed, more deprived areas are better served and areas with more over-60s are worse served (a pre-specified model; one planned check failed, so read these as patterns, not causes).

Caveats: one week's timetables; dial-a-ride and community transport may be missing; straight-line distances.

Interactive map, with a clock you can drag to watch the network shut down for the night: https://maps.tristanhotham.com/bus-deserts/

**Source comment:**

Data: Department for Transport, Bus Open Data Service regional GTFS timetables (Open Government Licence v3.0); Wikidata villages (CC0); English Indices of Deprivation 2025 and ONS Rural Urban Classification 2021 (OGL v3.0). Method: departures counted per stop per day; for each village, the busiest stop within 800 m; logit model for small areas with region fixed effects, plan written before any results. Tools: Python (pandas, geopandas, scipy, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/bus-deserts
