"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Bus_Deserts.pdf and .tex. The DOI stays the placeholder https://doi.org/10.5281/zenodo.24116216 unless the environment
variable DOI is set:  DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess, pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Bus_Deserts"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
F = R["feed"]
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Data flow.}\\label{tab:sample}\\begin{tabular}{lr}\\toprule Item & Number\\\\\\midrule\n"
      f"Stop rows in the nine regional files & {F['rows']:,}\\\\\n\\quad stop ids in more than one file & {F['dup']:,}\\\\\n"
      f"\\quad of which served in both copies & {F['dup_both_served']:,}\\\\\n\\quad of which with equal Tuesday counts & {F['dup_same']:,}\\\\\n"
      f"Stops in England after deduplication & {F['stops']:,}\\\\\n\\quad bus and coach stops & {F['bus_stops']:,}\\\\\n"
      f"\\quad with a Tuesday departure (served) & {F['served']:,}\\\\\n\\quad with no Tuesday departure & {F['zero_tue']:,}\\\\\n"
      f"\\quad tram, metro, rail or ferry only & {F['non_bus']:,}\\\\\\midrule\n"
      f"Weekday (Tuesday) stop departures & {F['wk_departures']:,}\\\\\nSaturday stop departures & {F['sat_departures']:,}\\\\\nSunday stop departures & {F['sun_departures']:,}\\\\\\midrule\n"
      f"Villages / hamlets / towns / cities (Wikidata, England) & {R['settle']['village']['n']:,} / {R['settle']['hamlet']['n']:,} / {R['settle']['town']['n']:,} / {R['settle']['city']['n']:,}\\\\\n"
      f"\\quad settlement points corrected or dropped by hand & {R['overrides']['n']}\\\\\n"
      f"Small areas (LSOA 2021, England) & {R['lsoa']['n']:,}\\\\\n\\quad residents (mid 2022) & {R['lsoa']['pop']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = ""
for c, lab in (("hamlet", "Hamlets"), ("village", "Villages"), ("town", "Towns"), ("city", "Cities")):
    s = R["settle"][c]
    rows += (f"{lab} & {s['n']:,} & {s['desert_pc']:.1f} & {s['deep_pc']:.1f} & {s['token_pc']:.1f} & {s['poor_pc']:.1f} & "
             f"{s['no_eve_pc']:.1f} & {s['no_sat_pc']:.1f} & {s['no_sun_pc']:.1f} & {s['full_pc']:.1f}\\\\\n")
TC = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Bus service within 800 m by settlement type (\\% of places). Desert: no stop with a Tuesday "
      "departure within 800 m; deep: none within 1.6 km; token: busiest stop within 800 m has 1 to 3 Tuesday departures; no usable bus: desert or token; "
      "evening: any departure from 19:00; full: usable weekday service, evening bus and Sunday bus.}\\label{tab:classes}"
      "\\begin{tabular}{lrrrrrrrrr}\\toprule & N & Desert & Deep & Token & No usable & No evening & No Sat. & No Sun. & Full\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{k} & {v['lsoas']:,} & {v['pop'] / 1e6:.2f} & {v['old_pc']:.1f} & {v['desert_pc']:.1f} & {v['poor_pc']:.1f} & {v['no_eve_pc']:.1f} & {v['no_sun_pc']:.1f}\\\\\n"
               for k, v in R["by_ruc"].items())
TR_ = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Small areas by 2021 rural-urban class: residents (millions), share aged 60 and over, and "
       "population-weighted shares (\\%) without a served stop within 800 m (desert), without a usable weekday bus, without an evening bus and without a Sunday bus.}\\label{tab:ruc}"
       "\\begin{tabular}{lrrrrrrr}\\toprule Class & LSOAs & Residents (m) & Aged 60+ & Desert & No usable & No evening & No Sunday\\\\\\midrule\n" + rows +
       "\\bottomrule\\end{tabular}\\end{table}")
m = R["H3"]["main"]; ln = R["H3"]["lpm"]
rows = ""
for t, v in m["terms"].items():
    p = "$<$0.001" if v["p"] < 0.001 else f"{v['p']:.3f}"
    rows += f"{tex(v['label'])} & {v['or']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}] & {v['ame']:.2f} [{v['ame_lo']:.2f}, {v['ame_hi']:.2f}] & {p}\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Planned model: logit of having no usable weekday bus within 800 m, LSOAs in England. Reference class: urban, nearer a major town or city. "
      f"Region fixed effects included. Standard errors clustered by local authority district ({m['clusters']}). N = {m['n']:,}; mean outcome {m['mean_y_pc']:.1f}\\%; pseudo-$R^2$ {m['pseudo_r2']:.2f}. "
      "AME: average marginal effect in percentage points.}\\label{tab:main}"
      "\\begin{tabular}{lllr}\\toprule Term & Odds ratio [95\\% CI] & AME [95\\% CI] & $p$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
LAB = R["H3_labels"]
rows = ""
for k, lab in LAB.items():
    v = R["H3"][k]; T = v["terms"]
    dep = T.get("imd_z") or T.get("inc_z") or T.get("ind_z")
    nm = "IMD" if "imd_z" in T else ("Income" if "inc_z" in T else "Indoors")
    if k == "lpm":
        a = f"{T['imd_z']['b']:.2f} [{T['imd_z']['lo']:.2f}, {T['imd_z']['hi']:.2f}] pp"; b = f"{T['old_z']['b']:.2f} [{T['old_z']['lo']:.2f}, {T['old_z']['hi']:.2f}] pp"
    else:
        a = f"{nm} {dep['or']:.2f} [{dep['lo']:.2f}, {dep['hi']:.2f}]"; b = f"{T['old_z']['or']:.2f} [{T['old_z']['lo']:.2f}, {T['old_z']['hi']:.2f}]"
        if k == "falsify_both":
            a = f"IMD {T['imd_z']['or']:.2f} [{T['imd_z']['lo']:.2f}, {T['imd_z']['hi']:.2f}]; Indoors {T['ind_z']['or']:.2f}"
    rows += f"{tex(lab)} & {a} & {b} & {v['n']:,}\\\\\n"
TRB = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Planned checks: odds ratios (95\\% CI) per standard deviation for deprivation and for the share aged 60 and over. "
       "The linear probability model reports percentage-point effects. All models include the rural-urban class and region fixed effects; standard errors clustered by district.}\\label{tab:robust}"
       "\\begin{tabular}{p{5.4cm}p{5.1cm}lr}\\toprule Check & Deprivation & Aged 60+ & N\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(r['region'])} & {r['pop'] / 1e6:.2f} & {r['dep_per_1000']:.0f} & {r['sun_dep_per_1000']:.0f} & {r['pop_poor_pc']:.1f} & {r['villages']:,} & "
               f"{'' if r['villages'] < 100 else format(r['v_poor_pc'], '.1f')} & {'' if r['villages'] < 100 else format(r['v_no_sun_pc'], '.1f')} & {r['zero_tue_pc']:.1f}\\\\\n"
               for r in sorted(R["regions"].values(), key=lambda r: -r["dep_per_1000"]))
TG = ("\\begin{table}[htbp]\\centering\\footnotesize\\caption{Regions: residents (millions), weekday and Sunday stop departures per 1,000 residents, population share without a usable weekday bus, "
      "villages and shares without a usable weekday bus and without a Sunday bus (not shown for London's 25 villages), and share of bus stops with no Tuesday departure.}\\label{tab:regions}"
      "\\begin{tabular}{lrrrrrrrr}\\toprule Region & Res. (m) & Wk/1,000 & Sun/1,000 & Pop. no usable & Villages & No usable & No Sunday & Stops 0 Tue\\\\\\midrule\n" + rows +
      "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(k)} & {v['terms']['imd_z']['or']:.2f} [{v['terms']['imd_z']['lo']:.2f}, {v['terms']['imd_z']['hi']:.2f}] & {v['terms']['old_z']['or']:.2f} [{v['terms']['old_z']['lo']:.2f}, {v['terms']['old_z']['hi']:.2f}] & {v['n']:,}\\\\\n"
               for k, v in R["H3"]["loo"].items())
TL = ("\\begin{table}[htbp]\\centering\\small\\caption{Leave one region out: odds ratios (95\\% CI) from the main model with the named region dropped.}\\label{tab:loo}"
      "\\begin{tabular}{llll}\\toprule Region left out & IMD (per SD) & Aged 60+ (per SD) & N\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(f"{ROOT}/code/paper_template.tex", encoding="utf-8").read()
for k, v in (("SAMPLE", TS), ("CLASSES", TC), ("RUC", TR_), ("MAIN", TM), ("ROBUST", TRB), ("REGIONS", TG), ("LOO", TL)):
    t = t.replace("{{TABLE_" + k + "}}", v)
t = t.replace("{{AI}}", AI)
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m_: fmt(get(R, m_.group(1)), m_.group(3)).replace("%", "\\%"), t)
doi = os.environ.get("DOI")
t_out = t.replace("DOIURLPLACEHOLDER", f"https://doi.org/{doi}" if doi else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t_out.replace("\\{\\{DOI\\_URL\\}\\}", "")
for bad in ("—", "–", "D" "SIT", "D" "CMS", "pre-" "registered"):
    assert bad not in t_out, bad
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(t_out)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = open(f"{OUT}/{NAME}.log", encoding="utf-8", errors="ignore").read()
print("undefined refs:", log.count("undefined"), "| pages:", re.findall(r"Output written on .*?\((\d+) pages", log),
      "| overfull:", log.count("Overfull"))
for e in ("aux", "log", "out"):
    p = f"{OUT}/{NAME}.{e}"
    if os.path.exists(p): os.remove(p)
txt = subprocess.run(["pdftotext", f"{OUT}/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
body = txt.split("References")[0] if "References" in txt else txt
print("words (whole pdf):", len(txt.split()), "| before references:", len(body.split()))
ab = re.search(r"Abstract(.*?)Keywords", txt, re.S)
print("abstract words:", len(ab.group(1).split()) if ab else None)
