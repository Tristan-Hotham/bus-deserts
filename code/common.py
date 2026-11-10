"""Shared paths, constants and helpers for bus-deserts ("Bus deserts: the villages with no bus and the last bus home").

Raw inputs (read where they are, never copied):
  BUS/<region>_stops.csv   nine English regional GTFS feeds of the Department for Transport Bus Open Data Service (BODS,
                           data.bus-data.dft.gov.uk), timetables downloaded in 2026, reduced to one row per stop by
                           00_gtfs_reduce.py (Open Government Licence v3.0).
  SETTLE                   Wikidata UK settlements with coordinates, type and population (CC0).
  IOD                      English Indices of Deprivation 2025, File 7, LSOA 2021 (MHCLG, Open Government Licence v3.0).
  GEO/uk_topo.json         ONS country and region boundaries (Open Government Licence v3.0).
  SCR/ruc21_lsoa21.rda, SCR/boundaries_lsoa21.rda   ONS Rural Urban Classification 2021 and generalised LSOA 2021
                           boundaries as packaged in humaniverse/geographr on GitHub (data ONS, OGL v3.0).
"""
import json, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
SCR = os.environ.get("BD_SCRATCH", "/home/claude/scratch/bus-deserts")
BUS = os.environ.get("BD_BUS", "/home/claude/newdata/raw_new14/bus")
SETTLE = os.environ.get("BD_SETTLE", "/home/claude/newdata/raw_new8/uk_settlements.tsv")
IOD = os.environ.get("BD_IOD", "/home/claude/newdata/raw_new14/deprivation/IoD2025_File7_all_ranks_scores_deciles.csv")
GEO = os.environ.get("BD_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("BD_FONTS", "/home/claude/ref/fonts")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "bus-deserts"
TITLE = "Bus deserts"
SUBTITLE = "The villages with no bus and the last bus home"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
REGIONS = ["east_anglia", "east_midlands", "london", "north_east", "north_west", "south_east", "south_west",
           "west_midlands", "yorkshire"]
# ONS region names (E12 codes); the BODS "East Anglia" feed corresponds to the ONS East of England region
RGN_NAME = {"E12000001": "North East", "E12000002": "North West", "E12000003": "Yorkshire and The Humber",
            "E12000004": "East Midlands", "E12000005": "West Midlands", "E12000006": "East of England",
            "E12000007": "London", "E12000008": "South East", "E12000009": "South West"}
RGN_SHORT = {"E12000001": "North East", "E12000002": "North West", "E12000003": "Yorkshire",
             "E12000004": "East Midlands", "E12000005": "West Midlands", "E12000006": "East of England",
             "E12000007": "London", "E12000008": "South East", "E12000009": "South West"}
BUS_TYPES = {3} | set(range(200, 210)) | set(range(700, 718))
R800, R1600 = 800, 1600
TOKEN = 4          # fewer than 4 weekday departures = token service
EVENING = 19 * 60
KEEP_TYPES = {**{k: 4 for k in ("city", "big city", "county town", "city of United Kingdom", "border city", "port city",
                                  "largest city", "city status in the United Kingdom")},
              **{k: 3 for k in ("town", "market town", "town of the United Kingdom", "new town (UK)", "small town",
                                  "college town", "railway town", "resort town")},
              **{k: 2 for k in ("Village", "large village", "model village", "nucleated village", "garden village",
                                  "fishing village")},
              "hamlet": 1}
CLASS_NAME = {4: "city", 3: "town", 2: "village", 1: "hamlet"}
RUC_ORDER = ["Urban: Nearer to a major town or city", "Urban: Further from a major town or city",
             "Larger rural: Nearer to a major town or city", "Larger rural: Further from a major town or city",
             "Smaller rural: Nearer to a major town or city", "Smaller rural: Further from a major town or city"]
RUC_SHORT = {RUC_ORDER[0]: "Urban, near city", RUC_ORDER[1]: "Urban, far from city",
             RUC_ORDER[2]: "Larger rural, near city", RUC_ORDER[3]: "Larger rural, far from city",
             RUC_ORDER[4]: "Smaller rural, near city", RUC_ORDER[5]: "Smaller rural, far from city"}


def is_bus(rt):
    if not isinstance(rt, str) or not rt:
        return False
    return any(int(x) in BUS_TYPES for x in rt.split("|") if x.strip().lstrip("-").isdigit())


def hhmm(m):
    if m is None or m != m:
        return ""
    m = int(m)
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, p, indent=None):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, allow_nan=False, indent=indent,
                  separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "hm": return hhmm(v)
    if f == "m": return f"{round(float(v) / 1e6, 1)} million"
    raise ValueError(f)


def fill(t, R, keep=("DOI", "DOI_URL", "BLOG_URL")):
    return re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}",
                  lambda m: m.group(0) if m.group(1) in keep or m.group(1).startswith(("IMG", "TABLE"))
                  else fmt(get(R, m.group(1)), m.group(3)), t)


def bng(lon, lat):
    """lon/lat (WGS84) to British National Grid metres (pyproj)."""
    from pyproj import Transformer
    tr = Transformer.from_crs(4326, 27700, always_xy=True)
    return tr.transform(lon, lat)
