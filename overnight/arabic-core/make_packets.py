"""Builds one translation packet per core argument: the English text, the verified Arabic of every Quran verse it cites,
the dataset Arabic of every hadith it cites (with gradings), and any review note. python3 -I make_packets.py <src pages> <dataset dir> <site dir> <out dir>"""
import html, json, re, sys
from pathlib import Path
src, ds, site, out = map(Path, sys.argv[1:5])
idx = json.loads((site / "idx.json").read_text(encoding="utf8"))
tracks = json.loads((site / "tracks.json").read_text(encoding="utf8"))
flags = json.loads((site / "flags.json").read_text(encoding="utf8"))
quran = {(v["chapter"], v["verse"]): v["text"] for v in json.loads((ds / "quran_ar.json").read_text(encoding="utf8"))["quran"]}
COLL = {"Bukhari": ("ara-bukhari", "hadithnumber"), "Muslim": ("ara-muslim", "arabicnumber"), "Abu Dawud": ("ara-abudawud", "hadithnumber"),
        "Tirmidhi": ("ara-tirmidhi", "hadithnumber"), "Ibn Majah": ("ara-ibnmajah", "hadithnumber"), "Nasa'i": ("ara-nasai", "hadithnumber")}
had = {}
for k, (fn, key) in COLL.items():
    d = {}
    for h in json.loads((ds / f"{fn}.json").read_text(encoding="utf8"))["hadiths"]:
        n = str(h.get(key, "")).split(".")[0]
        d.setdefault(n, h)
    had[k] = d
def plain(x):
    x = re.sub(r"</(p|li|div)>", "\n", x); x = re.sub(r"<[^>]+>", "", x)
    return re.sub(r"[ \t]+", " ", html.unescape(x)).strip()
ids = list(dict.fromkeys(s["id"] for t in tracks for s in t["steps"]))
pages = {}
for n, i in enumerate(ids, 1):
    p, a = i.split("#")
    s = pages.setdefault(p, (src / f"{p}.html").read_text(encoding="utf8"))
    m = re.search(r'<article class="brief" id="' + re.escape(a) + r'"[^>]*>(.*?)</article>', s, re.S)
    body = m.group(1)
    rows = {}
    for r in re.finditer(r'<div class="row (r-[a-z]+)"><div class="lab">(.*?)</div><div class="cell">(.*?)</div></div>(?=\s*(?:<div class="row|$))', body, re.S):
        rows[r.group(1)] = r.group(3)
    pk = {"n": n, "id": i, "title": html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))).strip()}
    pk["thesis"] = plain(rows.get("r-thesis", ""))
    pk["premises"] = [{"tag": html.unescape(re.sub(r"<[^>]+>", "", t)).strip(), "text": plain(x)} for t, x in re.findall(r'<li class="[^"]*"><span class="ptag">(.*?)</span><span>(.*?)</span></li>', rows.get("r-arg", ""), re.S)]
    ev = rows.get("r-ev", "")
    pk["evidence"] = [plain(x) for x in re.findall(r"<li>(.*?)</li>", ev, re.S)] or ([plain(ev)] if ev else [])
    pk["evidence"] = [re.sub(r"Tap to enlarge.*", "", e, flags=re.S).strip() for e in pk["evidence"] if e.strip()]
    pk["ar_quotes"] = [{"text": plain(t), "cite": plain(c)} for t, c in re.findall(r'<blockquote class="ar"><p[^>]*>(.*?)</p>\s*<cite>(.*?)</cite>', rows.get("r-ar", ""), re.S)]
    pk["objections"] = [{"q": plain(q), "a": re.sub(r"Tap to enlarge.*|Source .*", "", plain(a2), flags=re.S).strip()} for q, a2 in re.findall(r'<div class="obj"><p class="q">(.*?)</p><div class="a">(.*?)</div></div>', rows.get("r-obj", ""), re.S)]
    rb = rows.get("r-rebut", "")
    mq = re.search(r'class="rb-q">(.*?)</p>', rb, re.S); ma = re.search(r'class="rb-a"[^>]*>(.*?)</div>', rb, re.S)
    pk["practice"] = {"q": plain(mq.group(1)) if mq else "", "a": plain(ma.group(1)) if ma else ""}
    pk["sum"] = plain(rows.get("r-sum", ""))
    pk["caution"] = plain(rows.get("r-caution", ""))
    pk["review_note"] = flags.get(i, {}).get("text", "")
    alltext = json.dumps(pk, ensure_ascii=False)
    qr = {}
    for ch, v1, v2 in re.findall(r"\b(\d{1,3}):(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?", alltext):
        ch, v1 = int(ch), int(v1); v2 = int(v2) if v2 else v1
        if 1 <= ch <= 114 and all((ch, v) in quran for v in range(v1, v2 + 1)) and v2 - v1 < 6:
            qr[f"{ch}:{v1}" + (f"-{v2}" if v2 != v1 else "")] = " ".join(quran[(ch, v)] for v in range(v1, v2 + 1))
    pk["quran_arabic"] = qr
    hr = {}
    for c, ns in re.findall(r"\b(Bukhari|Muslim|Abu Dawud|Tirmidhi|Ibn Majah|Nasa'i)\s*((?:\d{1,5})(?:\s*(?:,|and)\s*\d{1,5})*)", alltext):
        for num in re.findall(r"\d{1,5}", ns):
            h = had[c].get(num)
            if h:
                hr[f"{c} {num}"] = {"arabic": re.sub(r"\s+", " ", h["text"])[:900], "grades": [[g["name"], g["grade"]] for g in h.get("grades", [])][:4]}
    pk["hadith_arabic"] = hr
    (out / f"{n:02d}.json").write_text(json.dumps(pk, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ids), "packets")
