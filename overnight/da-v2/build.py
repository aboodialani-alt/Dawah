"""Builds the DA v2 site folder.

python3 -I build.py <src_dir_with_original_pages> <site_dir>
Reads p1..p9.html, injects the v2 layer, writes new hub/drill/review pages plus data files.
The original text of every argument is left exactly as it is.
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
src, site = Path(sys.argv[1]), Path(sys.argv[2])
site.mkdir(parents=True, exist_ok=True)

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:ital@0;1&family=Instrument+Sans:wght@400;500;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Reem+Kufi:wght@500&display=swap">')


def tile(color):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120' fill='none' stroke='{color}' stroke-width='1'>"
           "<rect x='30' y='30' width='60' height='60'/><rect x='30' y='30' width='60' height='60' transform='rotate(45 60 60)'/>"
           "<circle cx='60' cy='60' r='15'/><path d='M0 0L30 30M120 0L90 30M0 120L30 90M120 120L90 90M60 0V16M60 104V120M0 60H16M104 60H120'/></svg>")
    return 'url("data:image/svg+xml,' + svg.replace('#', '%23').replace('"', "'") + '")'


TILE_CSS = (
    ":root{--tile:" + tile("#8d5f0c") + ";}"
    "@media (prefers-color-scheme: dark){:root:not([data-theme=\"light\"]){--tile:" + tile("#e2b55d") + ";}}"
    ":root[data-theme=\"dark\"]{--tile:" + tile("#e2b55d") + ";}"
)
CSS = TILE_CSS + (HERE / "v2.css").read_text(encoding="utf8")
JS = (HERE / "v2.js").read_text(encoding="utf8")
EARLY = "<script>try{var t=localStorage.getItem('da2:theme');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>"

n = 0
for i in range(1, 10):
    s = (src / f"p{i}.html").read_text(encoding="utf8")
    if "id=\"v2css\"" in s:
        raise SystemExit("source already has the v2 layer")
    s = s.replace("</head>", FONTS + EARLY + "<style id=\"v2css\">" + CSS + "</style></head>", 1)
    s = s.replace("</body>", "<script id=\"v2js\">" + JS + "</script></body>", 1)
    (site / f"p{i}.html").write_text(s, encoding="utf8")
    n += 1

# reviewer notes (kept outside the library text; pending the owner's approval)
flags = json.loads((HERE / "flags.json").read_text(encoding="utf8"))
(site / "flags.json").write_text(json.dumps(flags, ensure_ascii=False, indent=1), encoding="utf8")

# review desk data from the drafted additions (kept outside the library)
draft = (HERE.parent.parent / "da-drafts" / "DA-additions-draft.md").read_text(encoding="utf8")
head, *blocks = re.split(r"(?m)^## ", draft)
items, questions = [], ""
for blk in blocks:
    title, _, body = blk.partition("\n")
    m = re.match(r"(\d+)\.\s*(.*)", title)
    if m:
        items.append({"n": int(m.group(1)), "where": m.group(2).strip(), "md": body.strip().rstrip("-").strip()})
    elif title.startswith("Needs your decision"):
        questions = body.strip()
(site / "review.json").write_text(json.dumps({"intro": head.replace("# DA additions: draft for review", "").strip().rstrip("-").strip(), "items": items, "questions": questions}, ensure_ascii=False), encoding="utf8")
print("review items", len(items))

# study tracks: resolve titles to argument ids so a rename cannot silently break a path
idx = json.loads((site / "idx.json").read_text(encoding="utf8"))
tracks = json.loads((HERE / "tracks.json").read_text(encoding="utf8"))
for t in tracks:
    for s in t["steps"]:
        hit = [x for x in idx["briefs"] if x["p"] == s["p"] and (x["title"].strip() == s["t"].strip() or x["title"].startswith(s["t"].strip()))]
        if len(hit) != 1:
            raise SystemExit(f"track {t['id']}: cannot resolve {s['t']!r}")
        s["id"] = hit[0]["id"]; s["title"] = hit[0]["title"]; s["a"] = hit[0]["a"]; s["why"] = s.get("why", "").strip()
        del s["t"]
(site / "tracks.json").write_text(json.dumps(tracks, ensure_ascii=False), encoding="utf8")
print("tracks", len(tracks), "steps", sum(len(t["steps"]) for t in tracks))

# optional extra pages
for name in ("hub", "drill", "review", "audit", "learn", "spar", "sheet"):
    tpl = HERE / f"{name}.html"
    if tpl.exists():
        out = "index.html" if name == "hub" else f"{name}.html"
        t = tpl.read_text(encoding="utf8")
        t = t.replace("<!--V2HEAD-->", FONTS + EARLY + "<style id=\"v2css\">" + CSS + "</style>")
        t = t.replace("<!--V2JS-->", "<script id=\"v2js\">" + JS + "</script>")
        if name != "hub":
            # standalone page: needs its own document skeleton (only the main page is wrapped by the host)
            m = re.search(r"<title>.*?</title>", t, re.S)
            title = m.group(0)
            t = t.replace(title, "", 1)
            cut = t.index("</style>", t.index('id="v2css"') + 20)
            cut = t.index("</style>", cut + 8) + 8  # end of the page's own style block
            head, body = t[:cut], t[cut:]
            t = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
                 + title + head + "</head><body>" + body.replace("</body>", "") + "</body></html>")
        (site / out).write_text(t, encoding="utf8")
        print("wrote", out)
print("parts injected:", n)
