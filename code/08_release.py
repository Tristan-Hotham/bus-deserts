"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24116216, https://doi.org/10.5281/zenodo.24116216 and https://blog.tristanhotham.com/2026/10/31/bus-deserts/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Bus_Deserts"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
# fill numbers inside IMG tokens too, but keep the tokens themselves
post = re.sub(r"\{\{(?!IMG)([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP, set(re.findall(r"\{\{([^|}]+)\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", " - ", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered", "November"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
h = R["head"]
meta = {"title": "Bus deserts: the villages with no bus and the last bus home",
        "slug": "bus-deserts",
        "excerpt": f"I counted every timetabled bus in England on a Tuesday, Saturday and Sunday and checked every village. {h['v_poor_pc']:.0f}% have no stop with four or more weekday buses within 800 metres, {h['v_no_eve_pc']:.0f}% have no bus after seven in the evening and {h['v_no_sun_pc']:.0f}% have none on Sunday.",
        "seo_description": f"{h['v_poor_pc']:.0f}% of English villages have no usable weekday bus within 800 m and {h['v_no_sun_pc']:.0f}% no Sunday bus. Every stop and village mapped.",
        "tags": ["maps", "data visualisation", "buses", "public transport", "rural England", "villages", "transport poverty", "open data"],
        "header_alt": f"Title card on cream paper reading 'Bus deserts: the villages with no bus and the last bus home' with the figure {h['v_poor_pc']:.0f}% beside a map of England dotted with villages in red and blue."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
SKIP_DATA = {"site_stops.json", "site_names.json", "site_places.json"}     # page copies of data already in stops.csv.gz / settlements.csv
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        if fn not in SKIP_DATA:
            z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\\end\{quote\}", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "Bus Deserts: Villages Without a Usable Bus, the Last Bus Home and Who Lives Beyond the Network in England",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/bus-deserts/}}.</p>"
                        "<p>Sources: Department for Transport, Bus Open Data Service regional GTFS timetables (Open Government Licence v3.0); Wikidata (CC0); "
                        "English Indices of Deprivation 2025, MHCLG (OGL v3.0); ONS 2021 Rural Urban Classification and LSOA 2021 boundaries via the geographr R package (OGL v3.0); "
                        "ONS region and country boundaries (OGL v3.0). Text, figures and data CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["bus services", "rural accessibility", "transport poverty", "public transport supply", "GTFS", "Bus Open Data Service", "England", "villages"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "D" "SIT", "D" "CMS"):
    assert bad not in sj, bad
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
