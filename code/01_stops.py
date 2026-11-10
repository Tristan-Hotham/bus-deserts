"""Step 1: stops. Reads the nine reduced regional BODS feeds, flags bus stops, checks and removes cross-feed duplicates,
assigns each stop to an ONS region (England only) and writes SCR/stops.parquet and data/stops.csv.gz.
Also writes data/feed_checks.json (duplicates, zero-service shares, mode counts)."""
import glob, pandas as pd, numpy as np, geopandas as gpd
from common import *

rows = []
for reg in REGIONS:
    d = pd.read_csv(f"{BUS}/{reg}_stops.csv", dtype={"stop_id": str, "route_types": str, "wk_hours": str})
    d["feed"] = reg
    rows.append(d)
A = pd.concat(rows, ignore_index=True)
A["route_types"] = A.route_types.fillna("")
A["bus"] = A.route_types.map(is_bus)
types = A.route_types.str.split("|").explode()
chk = {"rows_all_feeds": len(A), "route_type_counts": types[types != ""].value_counts().to_dict(),
       "rows_no_route": int((A.route_types == "").sum())}

# cross-feed duplicates
dup = A[A.duplicated("stop_id", keep=False)]
g = dup.groupby("stop_id")
same = g.wk_n.nunique().eq(1)
both_served = g.wk_n.apply(lambda s: (s > 0).sum() >= 2)
chk["dup_stop_ids"] = int(g.ngroups)
chk["dup_same_wk_n"] = int(same.sum())
chk["dup_both_served"] = int(both_served.sum())
chk["dup_both_served_same"] = int((same & both_served).sum())
# sum alternative (sensitivity)
num = ["wk_n", "wk_after19", "sat_n", "sun_n", "n_routes"]
S_sum = A.groupby("stop_id")[num].sum()
A = A.sort_values(["stop_id", "wk_n", "sat_n", "sun_n"], ascending=[True, False, False, False])
feeds = A.groupby("stop_id").feed.apply(lambda s: "|".join(sorted(set(s))))
# for "max" take the feed row with most weekday departures, but latest times and any-day counts as max over feeds
D = A.drop_duplicates("stop_id").set_index("stop_id")
for c in ["wk_last", "sat_last", "sun_last", "sat_n", "sun_n", "wk_after19"]:
    D[c] = A.groupby("stop_id")[c].max()
D["wk_first"] = A.groupby("stop_id").wk_first.min()
D["bus"] = A.groupby("stop_id").bus.max()
D["route_types"] = A.groupby("stop_id").route_types.apply(lambda s: "|".join(sorted({x for v in s for x in v.split("|") if x})))
D["feeds"] = feeds
D["wk_n_sum"] = S_sum.wk_n
D["wk_after19_sum"] = S_sum.wk_after19
D["sun_n_sum"] = S_sum.sun_n
D = D.reset_index()
chk["unique_stops"] = len(D)
D = D[D.lat.between(49, 56.5) & D.lon.between(-7, 2.5)].copy()

# region, England only
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True).to_crs(27700)
rg = rg[rg.areacd.str.startswith("E12")][["areacd", "geometry"]]
x, y = bng(D.lon.values, D.lat.values)
P = gpd.GeoDataFrame(D[["stop_id"]].copy(), geometry=gpd.points_from_xy(x, y), crs=27700)
J = gpd.sjoin(P, rg, how="left", predicate="within").drop_duplicates("stop_id")
miss = J.areacd.isna()
if miss.any():   # coastal points just outside the generalised polygons: nearest region within 2 km
    N = gpd.sjoin_nearest(P[miss.values], rg, how="left", max_distance=2000, distance_col="dd").drop_duplicates("stop_id")
    J.loc[miss, "areacd"] = N.set_index("stop_id").areacd.reindex(J.loc[miss, "stop_id"]).values
D["rgn"] = J.areacd.values
D["x"], D["y"] = np.round(x), np.round(y)
chk["outside_england"] = int(D.rgn.isna().sum())
D = D[D.rgn.notna()].copy()
chk["england_stops"] = len(D)
chk["england_bus_stops"] = int(D.bus.sum())
chk["mixed_bus_other"] = int((D.bus & D.route_types.str.contains(r"(?:^|\|)(?:0|1|2|4|6)(?:\||$)")).sum())
B = D[D.bus]
chk["bus_zero_tuesday_share_by_region"] = {RGN_SHORT[k]: round(float((v.wk_n == 0).mean()), 4) for k, v in B.groupby("rgn")}
chk["bus_stops_by_region"] = {RGN_SHORT[k]: int(len(v)) for k, v in B.groupby("rgn")}
chk["served_bus_stops"] = int((B.wk_n > 0).sum())
chk["late_after_29h"] = int((D.wk_last >= 29 * 60).sum())
D.to_parquet(f"{SCR}/stops.parquet")
cols = ["stop_id", "stop_name", "lat", "lon", "rgn", "feeds", "route_types", "bus", "n_routes", "wk_n", "wk_first", "wk_last",
        "wk_after19", "wk_hours", "sat_n", "sat_last", "sun_n", "sun_last"]
D[cols].to_csv(f"{DATA}/stops.csv.gz", index=False, compression="gzip")
jsave(chk, f"{DATA}/feed_checks.json", indent=1)
print(json.dumps(chk, indent=1))
