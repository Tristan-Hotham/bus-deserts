"""Reddit collage for bus-deserts (r/dataisbeautiful style, light background). Run from the study root:
python3 reddit/collage.py  ->  reddit/bus_deserts_collage.png (2700 x 2100 px)."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np, pandas as pd, geopandas as gpd
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT = "#F6EED8", "#2B2119", "#6E604E"
CAT = {"desert": "#7A1F12", "token": "#C8644A", "few": "#E8B04A", "some": "#7FA7C9", "good": "#2F5F8E"}
CATL = {"desert": "No stop with a weekday bus within 800 m", "token": "1 to 3 weekday departures (token)", "few": "4 to 11 departures",
        "some": "12 to 47 departures", "good": "48 or more departures"}
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 15, "axes.facecolor": PAPER, "figure.facecolor": PAPER,
                     "axes.edgecolor": MUT, "xtick.color": MUT, "ytick.color": MUT, "axes.spines.top": False, "axes.spines.right": False})
R = jload(f"{DATA}/results.json")
S = pd.read_parquet(f"{SCR}/places.parquet")
V = S[S.cls == "village"].copy()
V["cat"] = np.where(V.d_served > R800, "desert", np.where(V.best800 < TOKEN, "token", np.where(V.best800 < 12, "few", np.where(V.best800 < 48, "some", "good"))))
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True).to_crs(27700)
rg = rg[rg.areacd.str.startswith("E12")]

fig = plt.figure(figsize=(18, 14), dpi=150)
fig.text(0.035, 0.955, "Bus deserts: England's villages and their buses", family=DISP, fontsize=40, fontweight="bold", color=INK, va="top")
fig.text(0.035, 0.905, f"Every timetabled bus departure on one Tuesday, Saturday and Sunday in 2026, at {R['feed']['bus_stops']:,} stops, checked against {R['settle']['village']['n']:,} villages",
         fontsize=18, color=MUT, va="top")
# map
ax = fig.add_axes([0.0, 0.06, 0.52, 0.82]); ax.set_facecolor(PAPER)
rg.plot(ax=ax, color="#FFFDF6", edgecolor="#BFAE88", lw=0.6)
for c in ["good", "some", "few", "token", "desert"]:
    v = V[V.cat == c]
    ax.scatter(v.x, v.y, s=5 if c in ("good", "some") else 6.5, c=CAT[c], lw=0, rasterized=True, zorder=4 if c == "desert" else 3)
ax.set_xlim(25000, 660000); ax.set_ylim(5000, 680000); ax.set_aspect("equal"); ax.axis("off")
hs = [plt.Line2D([], [], ls="", marker="o", ms=11, mfc=CAT[c], mec="none") for c in CAT]
v_ = R["settle"]["village"]
ax.legend(hs, [f"{CATL[c]}: {v_[c + '_pc']:.0f}%" for c in CAT], loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=14.5,
          title="Villages, by the busiest stop within 800 m\n(weekday departures)", title_fontsize=15, alignment="left")
# right column: big numbers
h = R["head"]
def big(y, num, txt, col):
    fig.text(0.56, y, num, family=DISP, fontsize=58, fontweight="bold", color=col, va="top")
    fig.text(0.70, y - 0.012, txt, fontsize=17, color=INK, va="top", linespacing=1.3)
big(0.86, f"{h['v_poor_pc']:.0f}%", "of villages have no stop within\n800 m with 4+ weekday buses", "#7A1F12")
big(0.79, f"{h['v_no_eve_pc']:.0f}%", "have no bus from 7pm\nwithin 800 m", "#C8644A")
big(0.72, f"{h['v_no_sun_pc']:.0f}%", "have no Sunday bus\nwithin 800 m", "#B7832A")
big(0.65, f"{R['lsoa']['pop_poor'] / 1e6:.1f}m", f"people live in small areas with\nno usable weekday bus ({R['lsoa']['poor_rural_share_pc']:.0f}% rural)", "#2F5F8E")
# last-bus curve
a2 = fig.add_axes([0.6, 0.33, 0.36, 0.18])
BH = R["by_hour"]
a2.plot(BH["hours"], BH["villages_pc"], color="#7A1F12", lw=3.5)
a2.fill_between(BH["hours"], BH["villages_pc"], color="#7A1F12", alpha=0.12)
a2.set_xticks(range(6, 25, 3)); a2.set_xticklabels([f"{x % 24:02d}:00" for x in range(6, 25, 3)], fontsize=12)
a2.set_ylim(0, 75); a2.set_yticks([0, 25, 50, 75]); a2.set_yticklabels(["0%", "25%", "50%", "75%"], fontsize=12)
a2.set_title("Villages with a weekday bus still to come, by time of day", fontsize=15.5, loc="left", color=INK)
a2.annotate(f"{BH['v19']:.0f}% at 19:00", (19, BH["v19"]), xytext=(20.2, 52), fontsize=13.5, color=INK, arrowprops=dict(arrowstyle="-", color=MUT, lw=1))
# rurality bars
a3 = fig.add_axes([0.77, 0.085, 0.19, 0.15])
rr = R["by_ruc"]; ks = list(rr)
a3.barh(range(len(ks)), [rr[k]["poor_pc"] for k in ks], color=["#7FA7C9", "#7FA7C9", "#C8644A", "#C8644A", "#7A1F12", "#7A1F12"], height=0.65)
for i, k in enumerate(ks):
    a3.text(rr[k]["poor_pc"] + 1.5, i, f"{rr[k]['poor_pc']:.0f}%", va="center", fontsize=12.5, color=INK)
a3.set_yticks(range(len(ks))); a3.set_yticklabels(ks, fontsize=12.5); a3.invert_yaxis(); a3.set_xlim(0, 85); a3.set_xticks([])
a3.spines["bottom"].set_visible(False)
fig.text(0.56, 0.255, "Residents with no usable weekday bus,\nby type of small area", fontsize=15.5, color=INK, va="top")
fig.text(0.035, 0.015, "Data: Department for Transport, Bus Open Data Service timetables (OGL v3.0); Wikidata villages (CC0); IoD 2025 and ONS Rural Urban Classification 2021 (OGL v3.0).\n"
         "Usable = a stop within 800 m (straight line) with 4+ weekday departures. Timetabled services only: dial-a-ride and community transport may be missing.\nInteractive map: maps.tristanhotham.com/bus-deserts",
         family=MONO, fontsize=11.5, color=MUT, va="bottom", linespacing=1.5)
out = os.path.join(ROOT, "reddit", "bus_deserts_collage.png")
fig.savefig(out, dpi=150, facecolor=PAPER); plt.close(fig)
from PIL import Image
print(out, Image.open(out).size)
