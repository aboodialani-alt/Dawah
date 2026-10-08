"""Reads the nine DA part pages and writes idx.json (search + drill data).

Usage: python3 -I extract.py <src_dir> <out_dir>
Content is only read, never changed.
"""
import html
import json
import re
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def text(fragment):
    fragment = re.sub(r"</(p|li|div|h\d|blockquote)>", "\n", fragment)
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment)
    fragment = re.sub(r"[ \t]+", " ", fragment)
    return re.sub(r"\n\s*\n+", "\n", fragment).strip()


# ---- parts metadata from the old hub
hub = (src / "index.html").read_text(encoding="utf8")
parts = []
for m in re.finditer(
    r'<article class="part" data-part="(p\d)"><a class="part-link" href="[^"]+"><p class="part-no">([^<]*)</p><h2>(.*?)</h2></a><p class="part-desc">(.*?)</p>',
    hub,
    re.S,
):
    pid, no, title, desc = m.groups()
    parts.append(
        {
            "id": pid,
            "no": re.sub(r"\s*·.*", "", html.unescape(no)).replace("Part ", "").strip(),
            "new": "New" in no,
            "title": text(title),
            "desc": text(desc),
        }
    )
assert len(parts) == 9, len(parts)

briefs = []
for part in parts:
    s = (src / f"{part['id']}.html").read_text(encoding="utf8")
    # section headings: id -> title
    secs = {}
    for m in re.finditer(r'<section class="sec" id="([^"]+)"[^>]*>.*?<h2[^>]*>(.*?)</h2>', s, re.S):
        secs[m.group(1)] = text(m.group(2))
    pos_sec = [(m.start(), m.group(1)) for m in re.finditer(r'<section class="sec" id="([^"]+)"', s)]
    for m in re.finditer(r'<article class="brief" id="([^"]+)"[^>]*>(.*?)</article>', s, re.S):
        bid, body = m.group(1), m.group(2)
        sec_id = None
        for p, sid in pos_sec:
            if p < m.start():
                sec_id = sid
        title = text(re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))
        kicker = text(re.search(r'<p class="kicker">(.*?)</p>', body, re.S).group(1))
        rows = {}
        for r in re.finditer(r'<div class="row (r-[a-z]+)"><div class="lab">(.*?)</div><div class="cell">(.*?)</div></div>(?=\s*(?:<div class="row|</article>|$))', body, re.S):
            rows[r.group(1)] = r.group(3)
        objs = []
        for o in re.finditer(r'<div class="obj"><p class="q">(.*?)</p><div class="a">(.*?)</div></div>', rows.get("r-obj", ""), re.S):
            objs.append({"q": text(o.group(1)), "a": text(o.group(2))})
        rb = rows.get("r-rebut", "")
        prac = None
        mq = re.search(r'class="rb-q">(.*?)</p>', rb, re.S)
        ma = re.search(r'class="rb-a"[^>]*>(.*?)</div>', rb, re.S)
        if mq:
            prac = {"q": text(mq.group(1)), "a": text(ma.group(1)) if ma else ""}
        ev = text(rows.get("r-ev", ""))
        briefs.append(
            {
                "id": f"{part['id']}#{bid}",
                "p": part["id"],
                "a": bid,
                "sec": secs.get(sec_id, ""),
                "title": title,
                "kicker": kicker,
                "thesis": text(rows.get("r-thesis", "")),
                "sum": text(rows.get("r-sum", "")),
                "caution": text(rows.get("r-caution", "")),
                "ar": bool(rows.get("r-ar")),
                "obj": objs,
                "prac": prac,
                "evs": ev[:1400],
            }
        )

data = {"parts": parts, "briefs": briefs}
(out / "idx.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
n_obj = sum(len(b["obj"]) for b in briefs)
print("parts", len(parts), "briefs", len(briefs), "objections", n_obj, "practice", sum(1 for b in briefs if b["prac"]),
      "caution", sum(1 for b in briefs if b["caution"]), "bytes", (out / "idx.json").stat().st_size)
