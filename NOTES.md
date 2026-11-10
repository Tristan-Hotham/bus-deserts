# bus-deserts: working notes and analysis plan

"Bus deserts: the villages with no bus and the last bus home". Author Dr Tristan Hotham, Independent researcher.

## Status

- Phase 1 (this section, 2026): plan written after reading only the file headers and the reducer code, before any service
  count, distance or share was computed. The plan below is pre-specified in a written plan. Anything added after the first
  results is labelled exploratory here and in the paper.
- Phase 2: pipeline, results, paper and release (log at the end).

## Data

- Stops: `/home/claude/newdata/raw_new14/bus/<region>_stops.csv`, nine English regional GTFS feeds from the Bus Open Data
  Service (BODS) "ITM" regional timetable files, downloaded by the lead in 2026 and reduced with
  `tools/gtfs_reduce.py` (copied to `code/00_gtfs_reduce.py`). One row per stop: departures on Tuesday 17 November 2026
  (`wk_n`, first/last, after 19:00, hourly 0 to 29), Saturday 21 and Sunday 22 November 2026 (`sat_n`, `sun_n`, last).
  Open Government Licence v3.0. Cite: Department for Transport, Bus Open Data Service, data.bus-data.dft.gov.uk.
- Settlements: Wikidata UK settlements (`raw_new8/uk_settlements.tsv`, CC0). Kept: types village, hamlet, town, market
  town, city (others such as forts, suburbs, areas of London, deserted villages are dropped; suburbs and areas of London
  are inside towns and are not the question). One row per Wikidata item (an item with several types takes the highest of
  city > town/market town > village > hamlet). England only, by point in the ONS country polygon (`uk_topo.json`), and
  region by the ONS region polygon.
- LSOAs: England 2021 LSOAs from IoD 2025 File 7 (`raw_new14/deprivation`): IMD score and decile, income score, total
  population mid 2022, population 60 and over. Rural-urban classification 2021 (RUC21, ONS, OGL) at LSOA from the
  humaniverse/geographr R package on GitHub (`data/ruc21_lsoa21.rda`, MIT; data ONS OGL). LSOA location: ONS 2021
  population-weighted centroids could not be found on GitHub (only the .shp.xml metadata of copies). Fallback, decided
  now: the representative point (a point guaranteed inside the polygon, shapely `representative_point`) of the generalised
  LSOA 2021 boundary from geographr (`data/boundaries_lsoa21.rda`, ONS OGL). Sensitivity: the geometric centroid. In
  large rural LSOAs neither is where people live, so LSOA distances are noisier than settlement distances; the settlement
  analysis is the main one for distance, the LSOA analysis is the main one for "who lives there".

## Measurement decisions (fixed now)

- **Modes.** A stop counts as a bus stop if its `route_types` include a bus or coach type: 3, 200 to 209 (coach), 700 to
  717 (extended bus types, including 715 demand-responsive if timetabled). Stops served only by tram/light rail (0, 900s),
  metro (1, 400s), rail (2, 100s) or ferry (4, 1000s) are excluded from the main measure; including them is a sensitivity
  check. Mixed stops (bus and tram at one stop id) are kept with all their departures, since the reduced file cannot split
  them; their number is reported.
- **Cross-feed duplicates.** Stops in more than one regional feed are deduplicated by `stop_id`, taking for each count
  the value from the feed with the most weekday departures (max). Before that, check whether duplicated stops have equal
  counts in both feeds (same trips) or different counts (different trips); report the shares. Sensitivity: sum across
  feeds.
- **Served stop.** A bus stop with at least one weekday (Tuesday) departure.
- **Settlement service.** For each settlement point: distance to the nearest served stop (great-circle, metres); within
  800 m, the best stop's weekday departures (max `wk_n` over stops within 800 m; not a sum, which would count the same
  bus at every stop it passes), the latest weekday departure over those stops, any departure from 19:00, any Saturday and
  any Sunday departure.
- **Categories.** Bus desert: nearest served stop more than 800 m away (deep desert: more than 1.6 km). Token service:
  a served stop within 800 m but the best stop has 1 to 3 weekday departures (roughly no usable return trip). Then 4 to 11,
  12 to 47 (up to about hourly over a 12 hour day... "less than hourly" is 4 to 11), 48 or more.
- **Last bus home.** Latest weekday departure from stops within 800 m (minutes after midnight; over 1440 is after
  midnight). "No evening bus" = no departure at or after 19:00 from any stop within 800 m.

## Questions and hypotheses

- **Q1 (descriptive).** Counts and shares of English villages, hamlets and towns that are bus deserts (800 m, 1.6 km) or have
  token service; same for LSOAs and population. No hypothesis; the expectation is that most villages have some stop, and the
  main problem is frequency and time of day rather than distance.
- **Q2 (descriptive).** Distribution of the last weekday bus for villages with a stop; share of villages (all, and those with a
  weekday service) with no bus after 19:00, none on Saturday, none on Sunday.
- **Q3 (who lives in bus deserts).** Unit: LSOA (England, N about 33,700). Outcome: poorly served = no served stop within
  800 m of the LSOA point, or best stop within 800 m has fewer than 4 weekday departures. Main model: logit with RUC21
  class (6 categories, urban nearer a major town as reference), IMD 2025 score (standardised), share of residents aged 60 and
  over (standardised) and region fixed effects; standard errors clustered by local authority district (2024). Report odds
  ratios and average marginal effects with 95% CIs and N. Also population-weighted descriptive shares by RUC21 class and IMD
  decile.
  - H3a: rural LSOAs (each rural class) are far more likely to be poorly served than urban ones. Against: odds ratios at or
    below 1.
  - H3b: holding rurality and region fixed, more deprived LSOAs are less likely to be poorly served (buses follow demand,
    and deprived areas have lower car ownership). Against: an odds ratio for IMD at or above 1.
  - H3c: holding rurality fixed, LSOAs with older populations are more likely to be poorly served. Against: odds ratio at or
    below 1.
- **Q4 (regions, descriptive).** Weekday bus departures (stop calls: a bus counts once at every stop it serves) per 1,000
  residents by region; share of the region's population in poorly served LSOAs; share of villages that are deserts.

## Robustness (planned)

1. Radius 400 m and 1,200 m instead of 800 m. 2. Token threshold 2 and 6 departures instead of 4. 3. Include tram, metro,
rail and ferry stops. 4. Cross-feed duplicates summed instead of max. 5. LSOA geometric centroid instead of representative
point. 6. Income deprivation score instead of the IMD score (the IMD includes a geographical barriers sub-domain that
measures road distance to services, which overlaps rurality). 7. Linear probability model instead of logit. 8. Leave one region
out (H3). 9. London excluded (H3), since London's network and RUC profile are unlike the rest. 10. Outcome split: no stop
within 800 m alone, and token service alone. Falsification: the outcome should not be associated with the IoD "Indoors"
living environment sub-domain (housing condition, no plausible link to buses) once rurality and region are held fixed; a
clear association would suggest the deprivation coefficient reflects something general about the area rather than demand.

## Checks before writing text

- Read every town or city (Wikidata type town, market town or city) flagged as a bus desert by eye: likely coordinate errors
  or feed gaps. Keep documented overrides in `code/overrides.json` and report the share corrected.
- Check the busiest stops and the stops with departures after 29:00 or before 04:00 for oddities.
- Check the share of stops with zero departures on the Tuesday in each region (a feed gap would show as a region with many
  zero stops).

## Caveats to state

A single timetable snapshot (one Tuesday, Saturday and Sunday in November 2026). School-day-only services, demand-responsive
services and community transport may be missing or appear with odd times. Distances are straight lines, not walking routes.
Wikidata coverage of hamlets is uneven. Stop departures count calls at a stop, not seats or useful destinations. Associations
only; nothing here identifies why services are where they are.

## Log

- 2026, phase 1 to 2: London feed arrived complete (24,759 rows) before any result was computed. RUC21 and generalised LSOA
  boundaries from humaniverse/geographr (GitHub). ONS population-weighted centroids not found on GitHub: representative
  point used as planned.
- Feed checks (`data/feed_checks.json`): 24,152 stop ids appear in two or three regional feeds; for 22,637 both copies have
  Tuesday departures, and only a third of those have equal counts, so the feeds overlap partly (shared cross-border trips
  plus feed-specific ones). The planned max rule is kept; the summed variant is the planned sensitivity check. 5,432 bus
  stops (2.2%) are listed with routes but have no Tuesday departure; 1,367 of them have a Saturday or Sunday departure.
- Data check of settlements: all 10 towns first flagged as deserts read by eye (`code/overrides.json`): 3 not real towns
  (dropped), 5 Wikidata points off the town (moved), Hawes kept (stops listed but Sunday-only in the feed: a likely gap),
  Woburn kept (point correct). 8 of 1,161 towns corrected (0.7%). Villages: the 40 largest desert villages read by eye.
  Several are civil parishes whose population covers suburbs (Hampreston, Winkfield) or whose point is rounded (Edwinstowe):
  settlement population is therefore not used for totals, only LSOA population. Coordinate precision sensitivity: villages
  with points given to 3+ decimals have a desert share within a few points of the rest (see `settle_sens`).
- Results against the plan: H3a supported (every rural class far more often poorly served). H3b supported in direction
  (OR for IMD per SD below 1 in every check), but the gradient is a hump within rural areas, and it comes from distance
  (deserts), not from frequency: among LSOAs with a stop, deprivation is not associated with token service (CI includes 1).
  H3c supported. **The falsification test failed**: the Indoors living environment sub-domain is positively associated with
  poor service (OR about 1.2) with rurality and region held fixed, so the six-class RUC leaves residual rurality; the IMD and
  older-share coefficients must be read with that caveat. With IMD and Indoors together the IMD odds ratio stays below 1.
- Exploratory (not in the plan): the hourly curves of villages and stops with a bus still to come; the Hawes-type feed gap
  count; regional bars of villages poorly served.
