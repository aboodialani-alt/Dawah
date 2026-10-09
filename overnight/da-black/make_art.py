"""Builds the data for the two argument tabs.

python3 -I make_art.py <original DA source dir> <da-v2 site dir>
Writes art/p1.json .. art/p9.json (the original articulated format of every argument, row by row, taken unchanged from the
original DA) and avoid.json (reviewer notes and citation-audit warnings per argument, for the "What to avoid" section).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
src, site = Path(sys.argv[1]), Path(sys.argv[2])
(HERE / "art").mkdir(exist_ok=True)

ROW = re.compile(r'<div class="row r-([a-z]+)"><div class="lab">(.*?)</div><div class="cell">(.*)</div></div>\s*$', re.S)
imgs = set()
for i in range(1, 10):
    h = (src / f"p{i}.html").read_text(encoding="utf8")
    out = {}
    for m in re.finditer(r'<article class="brief" id="([^"]+)".*?</header>(.*?)</article>', h, re.S):
        aid, body = m.group(1), m.group(2)
        rows = []
        # rows are top-level siblings that each start on a new line
        for chunk in re.split(r'\n(?=<div class="row r-)', body.strip()):
            r = ROW.match(chunk.strip())
            if not r:
                continue
            kind, lab, cell = r.groups()
            cell = re.sub(r'<button type="button" class="rb-btn"[^>]*>.*?</button>', '', cell, flags=re.S)
            cell = cell.replace('<div class="rb-a"', '<div class="rb-a" data-ans').replace(' hidden>', '>')
            cell = re.sub(r'<p class="rb-hint">.*?</p>', '', cell, flags=re.S)
            cell = re.sub(r'<span class="zoom">.*?</span>', '', cell)
            imgs.update(re.findall(r'src="(img/[^"]+)"', cell))
            rows.append({"k": kind, "lab": re.sub(r"<[^>]+>", "", lab), "html": cell})
        out[aid] = rows
    (HERE / "art" / f"p{i}.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf8")
    print(f"p{i}: {len(out)} arguments")

flags = json.loads((site / "flags.json").read_text(encoding="utf8"))
audit = json.loads((site / "audit.json").read_text(encoding="utf8"))["rows"]
avoid = {}
for k, v in flags.items():
    p, a = k.split("#", 1)
    avoid.setdefault(p + "." + a, []).append({"t": "note", "text": v["text"]})
WHY = {"grading disputed": "Scholars grade this report differently.", "graded weak": "Graded weak.", "quote differs": "The library's wording differs from the hadith text."}
for r in audit:
    if r["flag"] in WHY:
        g = r.get("grades") or []
        gtxt = "; ".join(f"{x[0]}: {x[1]}" for x in g if isinstance(x, (list, tuple)) and len(x) == 2)
        avoid.setdefault(r["p"] + "." + r["a"], []).append({"t": "ref", "ref": r["ref"], "text": WHY[r["flag"]] + (" Grades: " + gtxt + "." if gtxt else "")})
(HERE / "avoid.json").write_text(json.dumps(avoid, ensure_ascii=False), encoding="utf8")
(HERE / "imgs.txt").write_text("\n".join(sorted(imgs)) + "\n")
print(len(avoid), "arguments with warnings;", len(imgs), "screenshots referenced")
