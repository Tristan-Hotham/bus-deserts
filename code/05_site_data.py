"""Step 5: compact data for the map page. data/site_stops.json (bus stops, columnar), data/site_names.json (stop names,
loaded later for popups), data/site_places.json (villages, hamlets, towns), data/england.geojson (outline)."""
import numpy as np, pandas as pd, geopandas as gpd
from common import *

D = pd.read_parquet(f"{SCR}/stops.parquet")
B = D[D.bus].sort_values(["wk_n"]).reset_index(drop=True)      # busiest drawn last
nz = lambda s: s.fillna(-1).astype(int).tolist()
st = {"lon": np.round(B.lon * 1e4).astype(int).tolist(), "lat": np.round(B.lat * 1e4).astype(int).tolist(),
      "wk": B.wk_n.astype(int).tolist(), "last": nz(B.wk_last), "sat": B.sat_n.astype(int).tolist(), "sun": B.sun_n.astype(int).tolist(),
      "first": nz(B.wk_first), "e19": B.wk_after19.astype(int).tolist()}
jsave(st, f"{DATA}/site_stops.json")
jsave(B.stop_name.fillna("").str.slice(0, 40).tolist(), f"{DATA}/site_names.json")
S = pd.read_parquet(f"{SCR}/places.parquet")
S = S[S.cls.isin(["village", "hamlet", "town", "city"])]
S["cat"] = np.where(S.d_served > R800, 0, np.where(S.best800 < TOKEN, 1, np.where(S.best800 < 12, 2, np.where(S.best800 < 48, 3, 4))))
pl = [[r.name, round(r.lon, 4), round(r.lat, 4), {"hamlet": 1, "village": 2, "town": 3, "city": 4}[r.cls], int(r.d_served), int(r.best800),
       -1 if r.last800 != r.last800 else int(r.last800), int(r.eve800), int(r.sat800), int(r.sun800), int(r.cat), r.qid]
      for r in S.itertuples()]
jsave(pl, f"{DATA}/site_places.json")
ct = gpd.read_file(f"{GEO}/uk_topo.json", layer="ctry").set_crs(4326, allow_override=True)
e = ct[ct.areacd == "E92000001"].to_crs(27700).simplify(300).to_crs(4326)
gpd.GeoDataFrame(geometry=e).to_file(f"{DATA}/england.geojson", driver="GeoJSON", COORDINATE_PRECISION=4)
for f in ("site_stops.json", "site_names.json", "site_places.json", "england.geojson"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
