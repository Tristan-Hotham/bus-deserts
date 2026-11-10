"""Step 2: service at settlements and LSOAs. For each Wikidata settlement in England and each English LSOA 2021 point:
distance to the nearest served bus stop, and (within 400, 800 and 1,200 m) the best stop's weekday departures, latest
weekday departure, any departure from 19:00, any Saturday and Sunday departure. Also the planned sensitivity variants
(all modes, summed duplicates). Writes SCR/places.parquet, SCR/lsoa.parquet, data/settlements.csv, data/lsoa.csv."""
import warnings, pandas as pd, numpy as np, geopandas as gpd
from scipy.spatial import cKDTree
from common import *
warnings.simplefilter("ignore")

D = pd.read_parquet(f"{SCR}/stops.parquet")
ov = jload(os.path.join(ROOT, "code", "overrides.json")) if os.path.exists(os.path.join(ROOT, "code", "overrides.json")) else {}


def service(px, py, S, radii=(400, 800, 1200), tag=""):
    """S: stops frame with x, y and counts (only stops of the chosen mode set). Returns dict of arrays."""
    out = {}
    served = S[S.wk_n > 0]
    T = cKDTree(np.c_[served.x, served.y])
    d, _ = T.query(np.c_[px, py])
    out[f"d_served{tag}"] = np.round(d)
    TA = cKDTree(np.c_[S.x, S.y])
    wk, last, a19, sat, sun, wks = (S[c].values for c in ["wk_n", "wk_last", "wk_after19", "sat_n", "sun_n", "wk_n_sum"])
    for r in radii:
        nb = TA.query_ball_point(np.c_[px, py], r)
        best = np.zeros(len(px)); lastv = np.full(len(px), np.nan); e = np.zeros(len(px), bool)
        sa = np.zeros(len(px), bool); su = np.zeros(len(px), bool); bsum = np.zeros(len(px)); nstop = np.zeros(len(px), int)
        for i, ids in enumerate(nb):
            if not ids:
                continue
            ids = np.asarray(ids)
            best[i] = wk[ids].max(); bsum[i] = wks[ids].max(); nstop[i] = len(ids)
            lv = last[ids]
            if np.isfinite(lv).any():
                lastv[i] = np.nanmax(lv)
            e[i] = (a19[ids] > 0).any(); sa[i] = (sat[ids] > 0).any(); su[i] = (sun[ids] > 0).any()
        out[f"best{r}{tag}"] = best; out[f"last{r}{tag}"] = lastv; out[f"eve{r}{tag}"] = e
        out[f"sat{r}{tag}"] = sa; out[f"sun{r}{tag}"] = su; out[f"stops{r}{tag}"] = nstop
        if tag == "":
            out[f"bestsum{r}"] = bsum
    return out


B = D[D.bus]                      # main: bus and coach stops
M = D                             # sensitivity: all modes

# ---------- settlements ----------
s = pd.read_csv(SETTLE, sep="\t")
s.columns = ["qid", "name", "coord", "pop", "type"]
s["qid"] = s.qid.str.extract(r"(Q\d+)")
s["name"] = s.name.str.replace(r'^"|"?@en$', "", regex=True)
s["type"] = s.type.str.replace(r'^"|"?@en$', "", regex=True)
s["rank"] = s.type.map(KEEP_TYPES)
s = s[s["rank"].notna()].copy()
xy = s.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)").astype(float)
s["lon"], s["lat"] = xy[0], xy[1]
s = s.dropna(subset=["lon", "lat"])
s = s.sort_values(["qid", "rank"], ascending=[True, False])
s["pop"] = s.groupby("qid")["pop"].transform("max")
s = s.drop_duplicates("qid").copy()
s["cls"] = s["rank"].astype(int).map(CLASS_NAME)
for q, o in ov.get("settlements", {}).items():
    if q in set(s.qid):
        if o.get("drop"):
            s = s[s.qid != q]
        else:
            for k in ("lon", "lat"):
                if k in o:
                    s.loc[s.qid == q, k] = o[k]
x, y = bng(s.lon.values, s.lat.values)
s["x"], s["y"] = x, y
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True).to_crs(27700)
rg = rg[rg.areacd.str.startswith("E12")][["areacd", "geometry"]]
P = gpd.GeoDataFrame(s[["qid"]].copy(), geometry=gpd.points_from_xy(x, y), crs=27700)
J = gpd.sjoin(P, rg, how="left", predicate="within").drop_duplicates("qid")
s["rgn"] = J.areacd.values
s = s[s.rgn.notna()].copy()
o = service(s.x.values, s.y.values, B)
for k, v in o.items():
    s[k] = v
o = service(s.x.values, s.y.values, M, radii=(800,), tag="_all")
for k, v in o.items():
    s[k] = v
s.to_parquet(f"{SCR}/places.parquet")
out = s[["qid", "name", "cls", "type", "pop", "lat", "lon", "rgn", "d_served", "best800", "last800", "eve800", "sat800", "sun800", "stops800"]].copy()
out["rgn"] = out.rgn.map(RGN_NAME)
out["d_served"] = out.d_served.astype(int)
out["best800"] = out.best800.astype(int)
out.to_csv(f"{DATA}/settlements.csv", index=False)
print("settlements", len(s), s.cls.value_counts().to_dict())

# ---------- LSOAs ----------
import rdata
c = rdata.conversion.convert(rdata.parser.parse_file(f"{SCR}/ruc21_lsoa21.rda"))["ruc21_lsoa21"]
ruc = pd.DataFrame({"lsoa": c.lsoa21_code.astype(str), "ruc": c.classification.astype(str)})
pts = pd.read_csv(f"{SCR}/lsoa21_points.csv")       # from 01b_lsoa_points.py
I = pd.read_csv(IOD)
I = I.rename(columns={I.columns[0]: "lsoa", I.columns[2]: "lad", I.columns[3]: "lad_name", I.columns[4]: "imd",
                      I.columns[6]: "imd_dec", I.columns[7]: "income"})
I["pop"] = I["Total population: mid 2022"]; I["pop60"] = I["Older population aged 60 and over: mid 2022"]
I["indoors"] = I["Indoors Sub-domain Score"]
L = I[["lsoa", "lad", "lad_name", "imd", "imd_dec", "income", "pop", "pop60", "indoors"]].merge(ruc, on="lsoa", how="left").merge(
    pts.rename(columns={"lsoa21cd": "lsoa"}), on="lsoa", how="left")
L["old"] = L.pop60 / L["pop"]
x, y = bng(L.rp_lon.values, L.rp_lat.values)
L["x"], L["y"] = x, y
P = gpd.GeoDataFrame(L[["lsoa"]].copy(), geometry=gpd.points_from_xy(x, y), crs=27700)
J = gpd.sjoin(P, rg, how="left", predicate="within").drop_duplicates("lsoa")
miss = J.areacd.isna()
if miss.any():
    N = gpd.sjoin_nearest(P[miss.values], rg, how="left", max_distance=3000).drop_duplicates("lsoa")
    J.loc[miss, "areacd"] = N.set_index("lsoa").areacd.reindex(J.loc[miss, "lsoa"]).values
L["rgn"] = J.areacd.values
for k, v in service(L.x.values, L.y.values, B).items():
    L[k] = v
for k, v in service(L.x.values, L.y.values, M, radii=(800,), tag="_all").items():
    L[k] = v
cx, cy = bng(L.c_lon.values, L.c_lat.values)
for k, v in service(cx, cy, B, radii=(800,), tag="_cent").items():
    L[k] = v
L.to_parquet(f"{SCR}/lsoa.parquet")
o = L[["lsoa", "lad", "lad_name", "rgn", "ruc", "imd", "imd_dec", "pop", "pop60", "rp_lon", "rp_lat", "d_served", "best800", "last800", "eve800", "sun800"]].copy()
o["rgn"] = o.rgn.map(RGN_NAME); o["d_served"] = o.d_served.astype(int); o["best800"] = o.best800.astype(int)
o.to_csv(f"{DATA}/lsoa.csv", index=False)
print("lsoa", len(L), L.ruc.isna().sum(), L.rgn.isna().sum())
