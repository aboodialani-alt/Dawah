#!/usr/bin/env python3
"""Extract plain text of every argument in a part page, for fact-checking.
Usage: extract_args.py PART.html OUT.json"""
import html, json, re, sys
src = open(sys.argv[1], encoding="utf-8").read()
def txt(x):
    x = re.sub(r"</(p|li|div|h\d|blockquote)>", "\n", x)
    x = re.sub(r"<[^>]+>", " ", x)
    return re.sub(r"[ \t]+", " ", html.unescape(x)).strip()
out = []
for m in re.finditer(r'<section class="sec" id="([^"]+)">(.*?)(?=<section class="sec"|<p class="empty")', src, re.S):
    sec_id, body = m.group(1), m.group(2)
    sec_title = txt(re.search(r"<h2>(.*?)</h2>", body, re.S).group(1))
    for a in re.finditer(r'<article class="brief" id="([^"]+)".*?</article>', body, re.S):
        t = re.search(r"<h3>(.*?)</h3>", a.group(0), re.S)
        rows = {}
        for r in re.finditer(r'<div class="row r-(\w+)">.*?<div class="cell">(.*?)</div></div>\s*(?=<div class="row|</article>)', a.group(0), re.S):
            rows[r.group(1)] = txt(r.group(2))
        out.append({"id": a.group(1), "section": sec_id, "section_title": sec_title, "title": txt(t.group(1)), "rows": rows,
                    "full_text": txt(re.sub(r'<header class="brief-head">.*?</header>', "", a.group(0), flags=re.S))})
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sys.argv[1], len(out), "arguments")
