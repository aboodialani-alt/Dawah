#!/usr/bin/env python3
"""Integrate newly built parts into the library's hub page and older part pages.

Usage: integrate.py LIVE_DIR OUT_DIR PUBLISH_DIR

LIVE_DIR     folder holding the current published index.html and p1..p7.html
OUT_DIR      folder holding built pN.html (+ .index.json) for the new parts
PUBLISH_DIR  folder to write the changed/new files into
"""
import html
import json
import os
import re
import sys

live, out, pub = sys.argv[1:4]
os.makedirs(pub, exist_ok=True)

NEW = [
    ("p8", "VIII", "Modern ideological challenges",
     "Feminism and women in public life, sexuality and gender identity, liberalism and secularism, and apostasy and blasphemy: the questions that come up in nearly every modern debate."),
    ("p9", "IX", "The Quran under attack: text, sources and history",
     "The readings, the Sana’a palimpsest and radiocarbon dates, the Syriac-sources theory, the Petra and “Mecca did not exist” claims, and the charges of grammatical error and abrogation."),
]
TOTAL_PARTS = "IX"

content = {}
for pid, *_ in NEW:
    content[pid] = json.load(open(os.path.join(os.path.dirname(__file__), "..", "content", f"{pid}.json"), encoding="utf-8"))

new_rows = []
for pid, *_ in NEW:
    new_rows += json.load(open(os.path.join(out, f"{pid}.html.index.json"), encoding="utf-8"))
n_new = len(new_rows)

# ---- hub page
idx = open(os.path.join(live, "index.html"), encoding="utf-8").read()
m = re.search(r"const IDX=(\[.*?\]);", idx, re.S)
old_idx = json.loads(m.group(1))
all_idx = old_idx + new_rows
idx = idx.replace(m.group(0), "const IDX=" + json.dumps(all_idx, ensure_ascii=False) + ";")

m = re.search(r"const META=(\[.*?\]);", idx, re.S)
meta = json.loads(m.group(1))
for pid, *_ in NEW:
    meta.append({"id": pid, "args": [r["id"] for r in new_rows if r["p"] == pid]})
idx = idx.replace(m.group(0), "const META=" + json.dumps(meta, ensure_ascii=False) + ";")

idx = idx.replace("const NAMES={", "const NAMES={" + ",".join(f"{pid}:'Part {rom}'" for pid, rom, *_ in NEW) + ",")

total = len(all_idx)
idx = idx.replace("<span><b>7</b> parts</span><span><b>222</b> arguments</span>",
                  f"<span><b>{len(meta)}</b> parts</span><span><b>{total}</b> arguments</span>")
idx = idx.replace("0 of 222 arguments studied", f"0 of {total} arguments studied")


def card(pid, rom, title, desc):
    c = content[pid]
    n = sum(len(s["args"]) for s in c["sections"])
    secs = "".join(
        f'<li><a href="{pid}.html#{s["id"]}">{html.escape(s["title"], quote=True)}</a><span>{len(s["args"])}</span></li>'
        for s in c["sections"]
    )
    return (
        f'<article class="part" data-part="{pid}"><a class="part-link" href="{pid}.html"><p class="part-no">Part {rom} · New</p>'
        f'<h2>{html.escape(title, quote=True)}</h2></a><p class="part-desc">{html.escape(desc, quote=True)} Pending fact-check.</p>'
        f'<div class="pbar"><i></i></div><p class="pcount"><b>0</b> of {n} arguments studied</p>'
        f'<ol class="part-secs">{secs}</ol></article>'
    )


cards = "".join(card(*x) for x in NEW)
idx = idx.replace("</section>\n<footer>", cards + "</section>\n<footer>", 1)
assert cards in idx, "part cards not inserted"

idx = idx.replace(
    '<span id="pdfnote">(all parts, answers shown, about 480 pages)</span></p>',
    '<span id="pdfnote">(Parts I to VII, answers shown, about 480 pages)</span></p>'
    '<p class="pdfdl"><a href="Dawah-Study-Library-Part-VIII.pdf" target="_blank" rel="noopener">Part VIII PDF</a> · '
    '<a href="Dawah-Study-Library-Part-IX.pdf" target="_blank" rel="noopener">Part IX PDF</a> '
    '<span>(new parts, one PDF each)</span></p>',
)
idx = idx.replace("Check every source before you cite it in a debate.",
                  "Parts VIII and IX were added later from published scholarship and have not yet been fact-checked. Check every source before you cite it in a debate.")
open(os.path.join(pub, "index.html"), "w", encoding="utf-8").write(idx)

# ---- older parts: "Part X of VII" -> "of IX"; p7 gets a next link
for i in range(1, 8):
    f = f"p{i}.html"
    s = open(os.path.join(live, f), encoding="utf-8").read()
    s2 = re.sub(r"(<span>Part [IVX]+ of )VII(</span>)", r"\g<1>" + TOTAL_PARTS + r"\2", s)
    if i == 7:
        marker = '<nav class="pager" aria-label="Other parts">'
        a = s2.index(marker)
        b = s2.index("</a></nav>", a) + len("</a>")
        s2 = (s2[:b] + '<a class="pg next" href="p8.html"><span>Part VIII →</span>Modern ideological challenges</a>' + s2[b:])
    if s2 != s:
        open(os.path.join(pub, f), "w", encoding="utf-8").write(s2)

for pid, *_ in NEW:
    open(os.path.join(pub, f"{pid}.html"), "w", encoding="utf-8").write(open(os.path.join(out, f"{pid}.html"), encoding="utf-8").read())
print("hub updated:", len(meta), "parts,", total, "arguments;", n_new, "new")
