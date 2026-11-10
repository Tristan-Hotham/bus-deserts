"""Step 6: index.html from code/page_template.html, code/page.css and the full-screen snippet, filled from data/results.json.
10.5281/zenodo.24116216, https://doi.org/10.5281/zenodo.24116216 and https://blog.tristanhotham.com/2026/10/31/bus-deserts/ stay for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")
t = fill(t, R)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
    assert bad not in vis, bad
assert 'site-nav.js' in t and 'data-fullscreen-map' in t
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
