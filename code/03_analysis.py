"""Step 3: every number. Descriptive results for Q1, Q2 and Q4, the planned LSOA models for Q3 with robustness and the
falsification test, all written to data/results.json (plus data/regions.csv, data/models.csv)."""
import warnings, numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
from common import *
warnings.simplefilter("ignore")

D = pd.read_parquet(f"{SCR}/stops.parquet")
S = pd.read_parquet(f"{SCR}/places.parquet")
L = pd.read_parquet(f"{SCR}/lsoa.parquet")
chk = jload(f"{DATA}/feed_checks.json")
R = {}
pc = lambda x: round(100 * float(x), 1)

# ---------------- feed ----------------
B = D[D.bus]
R["feed"] = {"rows": chk["rows_all_feeds"], "stops": chk["england_stops"], "bus_stops": chk["england_bus_stops"],
             "served": int((B.wk_n > 0).sum()), "zero_tue": int((B.wk_n == 0).sum()),
             "zero_tue_pc": pc((B.wk_n == 0).mean()),
             "zero_tue_weekend": int(((B.wk_n == 0) & ((B.sat_n > 0) | (B.sun_n > 0))).sum()),
             "dup": chk["dup_stop_ids"], "dup_both_served": chk["dup_both_served"], "dup_same": chk["dup_both_served_same"],
             "dup_same_pc": pc(chk["dup_both_served_same"] / chk["dup_both_served"]),
             "non_bus": int((~D.bus).sum()), "outside": chk["outside_england"],
             "wk_departures": int(B.wk_n.sum()), "sat_departures": int(B.sat_n.sum()), "sun_departures": int(B.sun_n.sum()),
             "sun_vs_wk_pc": pc(B.sun_n.sum() / B.wk_n.sum()), "sat_vs_wk_pc": pc(B.sat_n.sum() / B.wk_n.sum())}
ov = jload(os.path.join(ROOT, "code", "overrides.json"))["settlements"]
R["overrides"] = {"n": len(ov), "dropped": sum(1 for v in ov.values() if v.get("drop")), "moved": sum(1 for v in ov.values() if not v.get("drop"))}


# ---------------- settlements ----------------
def cat(best, d):
    return np.select([d > R800, best == 0, best < TOKEN, best < 12, best < 48], ["desert", "nostop", "token", "few", "some"], "good")


S["served800"] = S.d_served <= R800
S["cat"] = np.where(S.d_served > R800, "desert", np.where(S.best800 < TOKEN, "token", np.where(S.best800 < 12, "few", np.where(S.best800 < 48, "some", "good"))))
S["poor"] = (S.d_served > R800) | (S.best800 < TOKEN)
S["nostop800"] = S.stops800 == 0
S["stop_no_tue"] = (S.stops800 > 0) & (S.d_served > R800)


def sdesc(g):
    n = len(g)
    o = {"n": n, "desert": int((g.d_served > R800).sum()), "deep": int((g.d_served > R1600).sum()),
         "token": int((g.cat == "token").sum()), "poor": int(g.poor.sum()),
         "nostop": int(g.nostop800.sum()), "stop_no_tue": int(g.stop_no_tue.sum()),
         "few": int((g.cat == "few").sum()), "some": int((g.cat == "some").sum()), "good": int((g.cat == "good").sum()),
         "no_eve": int((~g.eve800).sum()), "no_sat": int((~g.sat800).sum()), "no_sun": int((~g.sun800).sum()),
         "d_median": float(g.d_served.median())}
    for k in list(o):
        if k not in ("n", "d_median"):
            o[k + "_pc"] = pc(o[k] / n)
    sv = g[~g.poor]                         # villages with a usable weekday service (4+ departures within 800 m)
    o["usable"] = len(sv)
    o["usable_no_eve_pc"] = pc((~sv.eve800).mean()) if len(sv) else None
    o["usable_no_sun_pc"] = pc((~sv.sun800).mean()) if len(sv) else None
    o["usable_no_sat_pc"] = pc((~sv.sat800).mean()) if len(sv) else None
    o["usable_last_median"] = float(sv.last800.median()) if len(sv) else None
    o["usable_last_before18_pc"] = pc((sv.last800 < 18 * 60).mean()) if len(sv) else None
    o["usable_last_before19_pc"] = pc((sv.last800 < 19 * 60).mean()) if len(sv) else None
    sw = g[g.best800 > 0]
    o["served_last_median"] = float(sw.last800.median()) if len(sw) else None
    o["best_median"] = float(sw.best800.median()) if len(sw) else None
    o["full"] = int((g.eve800 & g.sun800 & ~g.poor).sum()); o["full_pc"] = pc(o["full"] / n)
    return o


R["settle"] = {c: sdesc(S[S.cls == c]) for c in ["city", "town", "village", "hamlet"]}
V = S[S.cls == "village"]
R["settle"]["village_hamlet"] = sdesc(S[S.cls.isin(["village", "hamlet"])])
# last bus distribution for villages with any weekday departure within 800 m
lv = V[V.best800 > 0].last800
bins = [0, 16 * 60, 18 * 60, 19 * 60, 20 * 60, 22 * 60, 24 * 60, 99 * 60]
labs = ["before 16:00", "16:00 to 17:59", "18:00 to 18:59", "19:00 to 19:59", "20:00 to 21:59", "22:00 to 23:59", "midnight or later"]
h = pd.cut(lv, bins, right=False, labels=labs).value_counts().reindex(labs)
R["last_hist"] = {"labels": labs, "n": [int(x) for x in h.values], "N": int(len(lv))}
R["x_last"] = {"before19": int(h.values[:3].sum()), "before19_pc": pc(h.values[:3].sum() / len(lv)),
               "from22": int(h.values[5:].sum()), "from22_pc": pc(h.values[5:].sum() / len(lv)), "median": float(lv.median())}
# share of villages with a bus still to come, by hour (for the slider and the GIF)
R["by_hour"] = {"hours": list(range(6, 25)),
                "villages_pc": [pc((V.best800 > 0).mean() * 0 + ((V.last800 >= hh * 60) & (V.best800 > 0)).mean()) for hh in range(6, 25)],
                "stops_pc": [pc((B[B.wk_n > 0].wk_last >= hh * 60).mean()) for hh in range(6, 25)],
                "stops_n": [int((B[B.wk_n > 0].wk_last >= hh * 60).sum()) for hh in range(6, 25)]}
for hh in (18, 19, 20, 21, 22):
    R["by_hour"][f"v{hh}"] = pc(((V.last800 >= hh * 60) & (V.best800 > 0)).mean())

# sensitivity for settlements (villages)
dec = V.coord.str.extract(r"POINT\(([-\d.]+) ([-\d.]+)\)")
nd = lambda x: len(x.rstrip("0").split(".")[1]) if "." in x else 0
prec = np.array([min(nd(a), nd(b)) for a, b in zip(dec[0], dec[1])])
R["settle_sens"] = {
    "r400_desert_pc": pc((V.best400 == 0).mean()), "r1200_desert_pc": pc((V.best1200 == 0).mean()),
    "r800_desert_pc": R["settle"]["village"]["desert_pc"],
    "allmodes_desert_pc": pc((V.d_served_all > R800).mean()),
    "token2_pc": pc(((V.d_served <= R800) & (V.best800 < 2)).mean()), "token6_pc": pc(((V.d_served <= R800) & (V.best800 < 6)).mean()),
    "poor_sumdup_pc": pc(((V.d_served > R800) | (V.bestsum800 < TOKEN)).mean()),
    "precise_n": int((prec >= 3).sum()), "precise_desert_pc": pc((V.d_served[prec >= 3] > R800).mean()),
    "coarse_n": int((prec <= 2).sum()), "coarse_desert_pc": pc((V.d_served[prec <= 2] > R800).mean()),
}

# examples for the text: villages with population given, largest deserts, checked list in NOTES
# ---------------- regions ----------------
L["poor"] = ((L.d_served > R800) | (L.best800 < TOKEN)).astype(int)
L["desert"] = (L.d_served > R800).astype(int)
L["token"] = ((L.d_served <= R800) & (L.best800 < TOKEN)).astype(int)
reg = []
for code, nm in RGN_SHORT.items():
    l = L[L.rgn == code]; b = B[B.rgn == code]; v = V[V.rgn == code]
    p = l["pop"].sum()
    reg.append({"code": code, "region": nm, "pop": int(p), "lsoas": len(l),
                "wk_dep": int(b.wk_n.sum()), "dep_per_1000": round(1000 * b.wk_n.sum() / p, 1),
                "sun_dep_per_1000": round(1000 * b.sun_n.sum() / p, 1),
                "pop_poor_pc": pc((l["pop"] * l.poor).sum() / p), "pop_desert_pc": pc((l["pop"] * l.desert).sum() / p),
                "villages": len(v), "v_desert_pc": pc((v.d_served > R800).mean()) if len(v) else None,
                "v_poor_pc": pc(v.poor.mean()) if len(v) else None,
                "v_no_eve_pc": pc((~v.eve800).mean()) if len(v) else None, "v_no_sun_pc": pc((~v.sun800).mean()) if len(v) else None,
                "zero_tue_pc": pc((b.wk_n == 0).mean())})
RG = pd.DataFrame(reg)
RG.to_csv(f"{DATA}/regions.csv", index=False)
R["regions"] = {r["region"]: r for r in reg}
ne = RG[RG.region != "London"]
R["reg"] = {"dep_max": ne.loc[ne.dep_per_1000.idxmax(), "region"], "dep_max_v": float(ne.dep_per_1000.max()),
            "dep_min": ne.loc[ne.dep_per_1000.idxmin(), "region"], "dep_min_v": float(ne.dep_per_1000.min()),
            "london_v": float(RG.loc[RG.region == "London", "dep_per_1000"].iloc[0]),
            "eng_v": round(1000 * B.wk_n.sum() / L["pop"].sum(), 1),
            "vpoor_max": RG.loc[RG.v_poor_pc.idxmax(), "region"], "vpoor_max_v": float(RG.v_poor_pc.max()),
            "vpoor_min": ne.loc[ne.v_poor_pc.idxmin(), "region"], "vpoor_min_v": float(ne.v_poor_pc.min())}

# ---------------- LSOA descriptives ----------------
P = L["pop"].sum()
R["lsoa"] = {"n": len(L), "pop": int(P), "pop_desert": int((L["pop"] * L.desert).sum()), "pop_desert_pc": pc((L["pop"] * L.desert).sum() / P),
             "pop_poor": int((L["pop"] * L.poor).sum()), "pop_poor_pc": pc((L["pop"] * L.poor).sum() / P),
             "pop_token": int((L["pop"] * L.token).sum()),
             "lsoa_poor": int(L.poor.sum()), "lsoa_poor_pc": pc(L.poor.mean()), "lsoa_desert": int(L.desert.sum()),
             "pop_no_eve_pc": pc((L["pop"] * (~L.eve800)).sum() / P), "pop_no_sun_pc": pc((L["pop"] * (~L.sun800)).sum() / P),
             "pop60_poor": int((L.pop60 * L.poor).sum()), "pop60_poor_pc": pc((L.pop60 * L.poor).sum() / L.pop60.sum()),
             "centroid_poor_pc": pc((L["pop"] * ((L.d_served_cent > R800) | (L.best800_cent < TOKEN))).sum() / P)}
rr = {}
for k in RUC_ORDER:
    l = L[L.ruc == k]
    rr[RUC_SHORT[k]] = {"lsoas": len(l), "pop": int(l["pop"].sum()), "poor_pc": pc((l["pop"] * l.poor).sum() / l["pop"].sum()),
                        "desert_pc": pc((l["pop"] * l.desert).sum() / l["pop"].sum()),
                        "no_eve_pc": pc((l["pop"] * (~l.eve800)).sum() / l["pop"].sum()), "no_sun_pc": pc((l["pop"] * (~l.sun800)).sum() / l["pop"].sum()),
                        "old_pc": pc(l.pop60.sum() / l["pop"].sum()), "imd_median": float(l.imd.median())}
R["by_ruc"] = rr
rural = L.ruc.str.startswith(("Larger rural", "Smaller rural"))
R["lsoa"]["rural_pop"] = int(L.loc[rural, "pop"].sum())
R["lsoa"]["rural_poor_pc"] = pc((L["pop"] * L.poor)[rural].sum() / L.loc[rural, "pop"].sum())
R["lsoa"]["urban_poor_pc"] = pc((L["pop"] * L.poor)[~rural].sum() / L.loc[~rural, "pop"].sum())
R["lsoa"]["poor_rural_share_pc"] = pc((L["pop"] * L.poor)[rural].sum() / (L["pop"] * L.poor).sum())
R["by_imd"] = {int(d): {"poor_pc": pc((g["pop"] * g.poor).sum() / g["pop"].sum()),
                        "poor_pc_rural": pc((g["pop"] * g.poor)[rural[g.index]].sum() / max(g.loc[rural[g.index], "pop"].sum(), 1)),
                        "poor_pc_urban": pc((g["pop"] * g.poor)[~rural[g.index]].sum() / g.loc[~rural[g.index], "pop"].sum()),
                        "dep_best_median": float(g.best800.median())}
               for d, g in L.groupby("imd_dec")}
L["oldq"] = pd.qcut(L.old, 5, labels=False) + 1
R["by_old"] = {int(q): {"poor_pc": pc((g["pop"] * g.poor).sum() / g["pop"].sum()), "old_lo": pc(g.old.min()), "old_hi": pc(g.old.max())}
               for q, g in L.groupby("oldq")}

# ---------------- Q3 models ----------------
L["ruc_s"] = pd.Categorical(L.ruc.map(RUC_SHORT), categories=[RUC_SHORT[k] for k in RUC_ORDER])
z = lambda x: (x - x.mean()) / x.std()
L["imd_z"] = z(L.imd); L["old_z"] = z(L.old); L["inc_z"] = z(L.income); L["ind_z"] = z(L.indoors)
L["rgn_s"] = L.rgn.map(RGN_SHORT)
FORM = "y ~ C(ruc_s) + imd_z + old_z + C(rgn_s)"
TERMS = {"imd_z": "IMD score (per SD)", "old_z": "Share aged 60+ (per SD)", "inc_z": "Income deprivation (per SD)",
         "ind_z": "Indoors living environment (per SD)"}
for k in RUC_ORDER[1:]:
    TERMS[f"C(ruc_s)[T.{RUC_SHORT[k]}]"] = RUC_SHORT[k]


def fit(df, y, form=FORM, lpm=False):
    d = df.assign(y=y).dropna(subset=["y", "imd_z", "old_z", "ruc_s"])
    if d.rgn_s.nunique() < 2:
        form = form.replace(" + C(rgn_s)", "")
    if lpm:
        m = smf.ols(form, d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.lad)[0]})
    else:
        m = smf.logit(form, d).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(d.lad)[0]}, maxiter=200)
    out = {"n": int(m.nobs), "clusters": int(d.lad.nunique()), "terms": {}}
    ci = m.conf_int()
    for t in m.params.index:
        if t in TERMS:
            b, lo, hi = m.params[t], ci.loc[t, 0], ci.loc[t, 1]
            if lpm:
                out["terms"][t] = {"label": TERMS[t], "b": round(100 * b, 2), "lo": round(100 * lo, 2), "hi": round(100 * hi, 2), "p": float(m.pvalues[t])}
            else:
                out["terms"][t] = {"label": TERMS[t], "or": round(float(np.exp(b)), 3), "lo": round(float(np.exp(lo)), 3), "hi": round(float(np.exp(hi)), 3), "p": float(m.pvalues[t])}
    if not lpm:
        me = m.get_margeff(at="overall")
        sf = me.summary_frame()
        for t in sf.index:
            if t in out["terms"]:
                out["terms"][t].update({"ame": round(100 * sf.loc[t, "dy/dx"], 2), "ame_lo": round(100 * sf.loc[t, "Conf. Int. Low"], 2),
                                        "ame_hi": round(100 * sf.loc[t, "Cont. Int. Hi."], 2)})
        out["pseudo_r2"] = round(float(m.prsquared), 3)
    out["mean_y_pc"] = pc(d.y.mean())
    return out


Y = L.poor
M = {"main": fit(L, Y)}
M["r400"] = fit(L, ((L.d_served > 400) | (L.best400 < TOKEN)).astype(int))
M["r1200"] = fit(L, ((L.d_served > 1200) | (L.best1200 < TOKEN)).astype(int))
M["tok2"] = fit(L, ((L.d_served > R800) | (L.best800 < 2)).astype(int))
M["tok6"] = fit(L, ((L.d_served > R800) | (L.best800 < 6)).astype(int))
M["allmodes"] = fit(L, ((L.d_served_all > R800) | (L.best800_all < TOKEN)).astype(int))
M["sumdup"] = fit(L, ((L.d_served > R800) | (L.bestsum800 < TOKEN)).astype(int))
M["centroid"] = fit(L, ((L.d_served_cent > R800) | (L.best800_cent < TOKEN)).astype(int))
M["income"] = fit(L, Y, FORM.replace("imd_z", "inc_z"))
M["lpm"] = fit(L, Y, lpm=True)
M["nolondon"] = fit(L[L.rgn != "E12000007"], Y[L.rgn != "E12000007"])
M["desert_only"] = fit(L, L.desert)
nd_ = L.desert == 0
M["token_only"] = fit(L[nd_], L.token[nd_])
M["falsify"] = fit(L, Y, FORM.replace("imd_z", "ind_z"))
M["falsify_both"] = fit(L, Y, FORM + " + ind_z")
loo = {}
for code, nm in RGN_SHORT.items():
    k = L.rgn != code
    loo[nm] = fit(L[k], Y[k])
M["loo"] = loo
LAB = {"main": "Main specification", "r400": "Radius 400 m", "r1200": "Radius 1,200 m", "tok2": "Token threshold 2 departures",
       "tok6": "Token threshold 6 departures", "allmodes": "Tram, metro, rail and ferry stops included",
       "sumdup": "Cross-feed duplicates summed", "centroid": "LSOA geometric centroid", "income": "Income deprivation instead of IMD",
       "lpm": "Linear probability model", "nolondon": "London excluded", "desert_only": "Outcome: no served stop within 800 m",
       "token_only": "Outcome: token service (LSOAs with a stop)", "falsify": "Falsification: Indoors sub-domain instead of IMD",
       "falsify_both": "IMD and Indoors sub-domain together"}
R["H3"] = M
R["H3_labels"] = LAB
mm = M["main"]["terms"]
R["x"] = {"imd_or": mm["imd_z"]["or"], "imd_lo": mm["imd_z"]["lo"], "imd_hi": mm["imd_z"]["hi"],
          "old_or": mm["old_z"]["or"], "old_lo": mm["old_z"]["lo"], "old_hi": mm["old_z"]["hi"],
          "imd_ame": mm["imd_z"]["ame"], "old_ame": mm["old_z"]["ame"],
          "lrn_or": mm[f"C(ruc_s)[T.{RUC_SHORT[RUC_ORDER[2]]}]"]["or"],
          "srf_or": mm[f"C(ruc_s)[T.{RUC_SHORT[RUC_ORDER[5]]}]"]["or"],
          "srf_ame": mm[f"C(ruc_s)[T.{RUC_SHORT[RUC_ORDER[5]]}]"]["ame"],
          "imd_loo_min": min(v["terms"]["imd_z"]["or"] for v in loo.values()), "imd_loo_max": max(v["terms"]["imd_z"]["or"] for v in loo.values()),
          "old_loo_min": min(v["terms"]["old_z"]["or"] for v in loo.values()), "old_loo_max": max(v["terms"]["old_z"]["or"] for v in loo.values()),
          "imd_rob_min": min(M[k]["terms"]["imd_z"]["or"] for k in LAB if k not in ("lpm", "income", "falsify") and "imd_z" in M[k]["terms"]),
          "imd_rob_max": max(M[k]["terms"]["imd_z"]["or"] for k in LAB if k not in ("lpm", "income", "falsify") and "imd_z" in M[k]["terms"]),
          "old_rob_min": min(M[k]["terms"]["old_z"]["or"] for k in LAB if k != "lpm"),
          "old_rob_max": max(M[k]["terms"]["old_z"]["or"] for k in LAB if k != "lpm")}
rows = []
for k, lab in LAB.items():
    for t, v in M[k]["terms"].items():
        rows.append({"model": k, "label": lab, "term": v["label"], **{a: v.get(a) for a in ("or", "lo", "hi", "b", "p", "ame", "ame_lo", "ame_hi")}, "n": M[k]["n"]})
pd.DataFrame(rows).to_csv(f"{DATA}/models.csv", index=False)

R["x_extra"] = {"usable_no_eve": int((~V.poor & ~V.eve800).sum()), "usable_no_sun": int((~V.poor & ~V.sun800).sum())}
w_ = S[S.qid == "Q1881422"]
R["x_woburn"] = f"{float(w_.d_served.iloc[0]) / 1000:.1f}" if len(w_) else "n/a"
# headline numbers
v = R["settle"]["village"]
R["head"] = {"villages": v["n"], "v_desert_pc": v["desert_pc"], "v_poor_pc": v["poor_pc"], "v_poor": v["poor"],
             "v_no_eve_pc": v["no_eve_pc"], "v_no_sun_pc": v["no_sun_pc"], "v_full_pc": v["full_pc"],
             "v_ok_pc": round(100 - v["poor_pc"], 1)}
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("feed", "head", "lsoa", "x", "reg")}, indent=1))
print(json.dumps(R["settle"]["village"], indent=1)); print(json.dumps(R["by_ruc"], indent=1))
