"""Step 1b: representative points and geometric centroids of the generalised LSOA 2021 boundaries (geographr
data/boundaries_lsoa21.rda, ONS OGL) -> SCR/lsoa21_points.csv. Population-weighted centroids were not available."""
import warnings, pandas as pd, rdata
from shapely.geometry import Polygon, MultiPolygon
from common import *
warnings.simplefilter("ignore")
d = rdata.conversion.convert(rdata.parser.parse_file(f"{SCR}/boundaries_lsoa21.rda"))["boundaries_lsoa21"]
rows = []
for code, name, g in zip(d.lsoa21_code, d.lsoa21_name, d.geometry):
    polys = [Polygon(p[0], p[1:]) for p in g]
    mp = MultiPolygon(polys) if len(polys) > 1 else polys[0]
    if not mp.is_valid:
        mp = mp.buffer(0)
    pt, ce = mp.representative_point(), mp.centroid
    rows.append((code, name, round(pt.x, 6), round(pt.y, 6), round(ce.x, 6), round(ce.y, 6)))
pd.DataFrame(rows, columns=["lsoa21cd", "name", "rp_lon", "rp_lat", "c_lon", "c_lat"]).to_csv(f"{SCR}/lsoa21_points.csv", index=False)
print(len(rows))
