"""Step 4: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf)
and header.png (1200 x 630). Light paper; service classes run from deep red (no bus) to blue (frequent)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
import numpy as np, pandas as pd, geopandas as gpd
from PIL import Image
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
CAT = {"desert": "#7A1F12", "token": "#C8644A", "few": "#E8B04A", "some": "#7FA7C9", "good": "#2F5F8E"}
CATL = {"desert": "No bus stop with a weekday bus within 800 m", "token": "1 to 3 weekday departures", "few": "4 to 11",
        "some": "12 to 47", "good": "48 or more"}
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
SRC = ("Data: Bus Open Data Service timetables, Department for Transport (OGL v3.0), weekday = a Tuesday in 2026; Wikidata (CC0);\n"
       "IoD 2025 and ONS Rural Urban Classification 2021 (OGL v3.0) · maps.tristanhotham.com/bus-deserts")


def out(fig, name, page=True, blog=True, paper=True):
    if paper: fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor()); plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.4 / fig.get_figheight(), sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8, family=MONO, color=MUT, va="bottom", linespacing=1.4)


S = pd.read_parquet(f"{SCR}/places.parquet")
S["cat"] = np.where(S.d_served > R800, "desert", np.where(S.best800 < TOKEN, "token", np.where(S.best800 < 12, "few", np.where(S.best800 < 48, "some", "good"))))
rg = gpd.read_file(f"{GEO}/uk_topo.json", layer="rgn").set_crs(4326, allow_override=True).to_crs(27700)
rg = rg[rg.areacd.str.startswith("E12")]
ct = gpd.read_file(f"{GEO}/uk_topo.json", layer="ctry").set_crs(4326, allow_override=True).to_crs(27700)

# ---------------------------------------------------------------- 1. map of villages
V = S[S.cls.isin(["village"])]
fig = plt.figure(figsize=(8.2, 10))
ax = fig.add_axes([0.0, 0.06, 1.0, 0.82]); ax.set_facecolor(PAPER)
rg.plot(ax=ax, color="#FFFDF6", edgecolor="#BFAE88", lw=0.5)
for c in ["good", "some", "few", "token", "desert"]:
    v = V[V.cat == c]
    ax.scatter(v.x, v.y, s=2.2 if c in ("good", "some") else 3.0, c=CAT[c], lw=0, rasterized=True, zorder=3 if c != "desert" else 4)
ax.set_xlim(80000, 660000); ax.set_ylim(5000, 680000); ax.set_aspect("equal"); ax.axis("off")
title(fig, "Villages and their buses", f"{R['settle']['village']['n']:,} English villages, by the busiest stop within 800 m on a weekday")
hs = [plt.Line2D([], [], ls="", marker="o", ms=7, mfc=CAT[c], mec="none") for c in CAT]
labs = [f"{CATL[c]} ({R['settle']['village'][c + '_pc']:.0f}%)".replace("weekday bus within 800 m", "weekday bus\nwithin 800 m") for c in CAT]
ax.legend(hs, labs, loc="upper left", bbox_to_anchor=(0.0, 0.99), frameon=False, fontsize=10.5, title="Weekday departures", title_fontsize=11, alignment="left")
foot(fig); out(fig, "map")

# ---------------------------------------------------------------- 2. categories by settlement class
fig, ax = plt.subplots(figsize=(10, 4.6)); fig.subplots_adjust(left=0.13, right=0.97, top=0.7, bottom=0.25)
cls = ["hamlet", "village", "town", "city"]
left = np.zeros(len(cls))
for c in CAT:
    vals = np.array([R["settle"][k][c + "_pc"] for k in cls])
    ax.barh(range(len(cls)), vals, left=left, color=CAT[c], height=0.62, label=CATL[c])
    for i, (l_, v_) in enumerate(zip(left, vals)):
        if v_ >= 6:
            ax.text(l_ + v_ / 2, i, f"{v_:.0f}%", ha="center", va="center", fontsize=10, color="white" if c in ("desert", "good", "token") else INK)
    left += vals
ax.set_yticks(range(len(cls))); ax.set_yticklabels([f"{ {'city': 'Cities'}.get(k, k.capitalize() + 's')}\n({R['settle'][k]['n']:,})" for k in cls])
ax.set_xlim(0, 100); ax.set_xlabel("% of places"); ax.invert_yaxis()
ax.legend(ncol=3, loc="lower left", bbox_to_anchor=(-0.12, 1.02), frameon=False, fontsize=9.5)
title(fig, "Most hamlets and two in five villages have little or no bus", "Busiest stop with a weekday bus within 800 m: departures on a Tuesday", y=0.985)
foot(fig); out(fig, "classes")

# ---------------------------------------------------------------- 3. last bus home
H = R["last_hist"]; BH = R["by_hour"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [1.15, 1]}); fig.subplots_adjust(left=0.07, right=0.98, top=0.76, bottom=0.2, wspace=0.3)
cols = ["#7A1F12", "#A63A22", "#C8644A", "#E8B04A", "#A9C4DC", "#7FA7C9", "#2F5F8E"]
a1.bar(range(len(H["labels"])), H["n"], color=cols)
a1.set_xticks(range(len(H["labels"]))); a1.set_xticklabels([l.replace(" to ", "\nto ").replace(" or later", "\nor later") for l in H["labels"]], fontsize=8.5)
a1.set_ylabel("Villages"); a1.set_title("Time of the last weekday bus", fontsize=12, loc="left", color=INK)
a2.plot(BH["hours"], BH["villages_pc"], color="#7A1F12", lw=2.4, label="Villages with a bus still to come")
a2.plot(BH["hours"], BH["stops_pc"], color="#2F5F8E", lw=2.4, ls="--", label="Stops with a bus still to come")
a2.set_xticks(range(6, 25, 3)); a2.set_xticklabels([f"{h % 24:02d}:00" for h in range(6, 25, 3)], fontsize=9)
a2.set_ylim(0, 102); a2.set_ylabel("%"); a2.set_title("Still a bus to come after...", fontsize=12, loc="left", color=INK)
a2.axvline(19, color=MUT, lw=0.8, ls=":"); a2.legend(frameon=False, fontsize=9, loc="lower left")
title(fig, "The last bus home", f"Villages with any weekday bus within 800 m ({H['N']:,}); share of all villages and all served stops by hour", y=0.985)
foot(fig); out(fig, "lastbus")

# ---------------------------------------------------------------- 4. rurality
rr = R["by_ruc"]; ks = list(rr)
fig, ax = plt.subplots(figsize=(10, 5)); fig.subplots_adjust(left=0.25, right=0.97, top=0.74, bottom=0.22)
y = np.arange(len(ks)); w = 0.26
for j, (k, lab, col) in enumerate((("poor_pc", "No usable weekday bus (no stop, or under 4 departures)", "#7A1F12"),
                                    ("no_eve_pc", "No bus from 19:00", "#E8B04A"), ("no_sun_pc", "No Sunday bus", "#7FA7C9"))):
    vals = [rr[x][k] for x in ks]
    ax.barh(y + (j - 1) * w, vals, height=w, color=col, label=lab)
    for i, v_ in enumerate(vals):
        ax.text(v_ + 0.8, y[i] + (j - 1) * w, f"{v_:.0f}%", va="center", fontsize=8.5, color=INK)
ax.set_yticks(y); ax.set_yticklabels([f"{k}\n{rr[k]['pop'] / 1e6:.1f}m people" for k in ks], fontsize=10); ax.invert_yaxis()
ax.set_xlim(0, 100); ax.set_xlabel("% of residents (small areas, by the stops within 800 m of the area's point)")
ax.legend(frameon=False, fontsize=9.5, loc="lower left", bbox_to_anchor=(-0.3, 1.0), ncol=3)
title(fig, "Rural areas carry most of the gap", "Share of residents of England's small areas (LSOAs), by the 2021 rural-urban classification", y=0.985)
foot(fig); out(fig, "rural")

# ---------------------------------------------------------------- 5. deprivation
bi = R["by_imd"]; d = sorted(bi, key=int)
fig, ax = plt.subplots(figsize=(10, 4.8)); fig.subplots_adjust(left=0.1, right=0.97, top=0.76, bottom=0.27)
ax.plot([int(k) for k in d], [bi[k]["poor_pc_rural"] for k in d], "o-", color="#7A1F12", lw=2.2, label="Rural small areas")
ax.plot([int(k) for k in d], [bi[k]["poor_pc_urban"] for k in d], "o-", color="#2F5F8E", lw=2.2, label="Urban small areas")
ax.set_xticks(range(1, 11)); ax.set_xticklabels(["1\nmost\ndeprived"] + [str(i) for i in range(2, 10)] + ["10\nleast\ndeprived"], fontsize=9)
ax.set_ylabel("% of residents with\nno usable weekday bus"); ax.set_ylim(0, 62); ax.legend(frameon=False)
title(fig, "In the countryside, a hump rather than a slope", "Index of Multiple Deprivation 2025 decile of the small area", y=0.985)
foot(fig); out(fig, "deprivation")

# ---------------------------------------------------------------- 6. regions
RG = pd.read_csv(f"{DATA}/regions.csv").sort_values("dep_per_1000")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.9), sharey=True); fig.subplots_adjust(left=0.15, right=0.97, top=0.76, bottom=0.17, wspace=0.12)
yy = np.arange(len(RG))
a1.barh(yy, RG.dep_per_1000, color="#2F5F8E", height=0.6)
for i, v_ in enumerate(RG.dep_per_1000): a1.text(v_ + 5, i, f"{v_:.0f}", va="center", fontsize=9)
a1.set_yticks(yy); a1.set_yticklabels(RG.region); a1.set_title("Weekday stop departures per 1,000 residents", fontsize=11.5, loc="left", color=INK)
a1.set_xlim(0, RG.dep_per_1000.max() * 1.15)
a2.barh(yy, np.where(RG.villages < 100, 0, RG.v_poor_pc.fillna(0)), color="#7A1F12", height=0.6)
for i, v_ in enumerate(RG.v_poor_pc):
    a2.text((0 if v_ != v_ else v_) + 1, i, "few villages" if (RG.villages.iloc[i] < 100) else f"{v_:.0f}%", va="center", fontsize=9)
a2.set_title("Villages with no usable weekday bus", fontsize=11.5, loc="left", color=INK); a2.set_xlim(0, 65)
title(fig, "Regions", "A bus counts once at every stop it calls at; London's few villages are not compared", y=0.985)
foot(fig); out(fig, "regions")

# ---------------------------------------------------------------- 7. model checks (forest)
M = R["H3"]; LAB = R["H3_labels"]
keys = [k for k in LAB if "imd_z" in M[k]["terms"] and k != "lpm"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 6.6), sharey=True); fig.subplots_adjust(left=0.33, right=0.97, top=0.84, bottom=0.16, wspace=0.08)
for ax, t, col, ttl in ((a1, "imd_z", "#2F5F8E", "Deprivation (IMD, per SD)"), (a2, "old_z", "#7A1F12", "Share aged 60+ (per SD)")):
    for i, k in enumerate(keys):
        v = M[k]["terms"][t]
        ax.plot([v["lo"], v["hi"]], [i, i], color=col, lw=2); ax.plot(v["or"], i, "o", color=col, ms=6 if k != "main" else 9)
    ax.axvline(1, color=MUT, lw=0.8, ls=":"); ax.set_xscale("log"); ax.set_title(ttl, fontsize=11.5, loc="left", color=INK)
    ax.set_xticks([0.5, 0.7, 1, 1.4]); ax.set_xticklabels(["0.5", "0.7", "1", "1.4"]); ax.set_xlim(0.45, 1.6)
    from matplotlib.ticker import NullFormatter, NullLocator; ax.xaxis.set_minor_formatter(NullFormatter()); ax.xaxis.set_minor_locator(NullLocator())
a1.set_yticks(range(len(keys))); a1.set_yticklabels([LAB[k] for k in keys], fontsize=9.5); a1.invert_yaxis()
fig.text(0.33, 0.085, "Odds ratio for having no usable weekday bus, with 95% interval (logit, rurality class and region held fixed; clustered by district)", fontsize=9, color=MUT)
title(fig, "The checks", "Holding rurality fixed: deprived areas less often unserved, older areas more often", y=0.975)
foot(fig, SRC); out(fig, "checks")

# ---------------------------------------------------------------- header.png
fig = plt.figure(figsize=(12, 6.3), dpi=100); fig.patch.set_facecolor(PAPER)
ax = fig.add_axes([0.52, 0.0, 0.48, 1.0]); ax.set_facecolor(PAPER)
rg.plot(ax=ax, color="#FFFDF6", edgecolor="#BFAE88", lw=0.4)
for c in ["good", "some", "few", "token", "desert"]:
    v = V[V.cat == c]; ax.scatter(v.x, v.y, s=1.2, c=CAT[c], lw=0, rasterized=True)
ax.set_xlim(120000, 660000); ax.set_ylim(5000, 670000); ax.set_aspect("equal"); ax.axis("off")
fig.text(0.05, 0.86, "BUS DESERTS", fontsize=15, family=MONO, color="#7A1F12")
fig.text(0.05, 0.645, "The villages with\nno bus and the\nlast bus home", fontsize=40, family=DISP, fontweight="bold", color=INK, va="center", linespacing=1.05)
fig.text(0.05, 0.30, f"{R['head']['v_poor_pc']:.0f}%", fontsize=58, family=DISP, fontweight="bold", color="#7A1F12")
fig.text(0.05, 0.23, "of English villages have no stop with\nfour or more weekday buses within 800 m", fontsize=14, color=INK, va="top")
fig.text(0.05, 0.06, "Dr Tristan Hotham · maps.tristanhotham.com/bus-deserts", fontsize=11, family=MONO, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER); plt.close(fig)
print(Image.open(f"{ROOT}/header.png").size, sorted(os.listdir(IMG)))
