"""Citation audit: look up every hadith reference in the library against the open hadith dataset.

python3 -I audit.py <original pages dir> <dataset dir> <out json>

It does not decide whether a citation is right. It shows what the dataset says under that number and
flags the ones where the wording shares very little with the sentence that cites it, so a person can look.
"""
import html
import json
import re
import sys
from pathlib import Path

src, ds, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])

COLL = {
    "Bukhari": ("eng-bukhari", "hadithnumber"),
    "Muslim": ("eng-muslim", "arabicnumber"),
    "Abu Dawud": ("eng-abudawud", "hadithnumber"),
    "Tirmidhi": ("eng-tirmidhi", "hadithnumber"),
    "Ibn Majah": ("eng-ibnmajah", "hadithnumber"),
    "Nasa'i": ("eng-nasai", "hadithnumber"),
}
data = {}
for name, (fn, key) in COLL.items():
    h = json.loads((ds / f"{fn}.json").read_text(encoding="utf8"))["hadiths"]
    idx = {}
    for x in h:
        k = x.get(key)
        k = str(k).split(".")[0] if k is not None else None
        idx.setdefault(k, []).append(x)
    data[name] = idx

STOP = set("""the and that this with from for are was were his her their they them have has had not but what when which who whom whose will would shall should can could may might been being into onto than then there these those also very more most only some such any all one two three four five six seven eight nine ten said says say narrated reported hadith hadiths prophet messenger allah peace upon him bukhari muslim dawud tirmidhi majah nasai see also text evidence source graded sahih hasan daif authentic report reports narration narrations collection collections book chapter number""".split())


def words(t):
    return {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in STOP}


def plain(fragment):
    fragment = re.sub(r"<script.*?</script>|<style.*?</style>", "", fragment, flags=re.S)
    fragment = re.sub(r"</(p|li|div|h\d|blockquote|tr)>", "\n", fragment)
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


pat = re.compile(r"(?<!Non-)(?<!non-)\b(Bukhari|Muslim|Abu Daw[uū]d|Tirmidhi|Nasa'?i|Ibn M[aā]jah)\s*(?:no\.?\s*)?((?:\d{1,5})(?:\s*(?:,|and|&|;)\s*\d{1,5})*)(?!\d|st\b|nd\b|rd\b|th\b)")
norm = {"Abu Dawūd": "Abu Dawud", "Nasai": "Nasa'i", "Ibn Mājah": "Ibn Majah"}

idxpath = src.parent / "idx.json"
rows = []
for pf in sorted(src.glob("p[1-9].html")):
    pid = pf.stem
    s = pf.read_text(encoding="utf8")
    for m in re.finditer(r'<article class="brief" id="([^"]+)"[^>]*>(.*?)</article>', s, re.S):
        aid, body = m.group(1), m.group(2)
        title = re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))
        title = html.unescape(title).strip()
        text = plain(body)
        seen = set()
        for c in pat.finditer(text):
            coll = c.group(1).replace("ū", "u").replace("ā", "a")
            coll = {"Abu Dawud": "Abu Dawud", "Nasai": "Nasa'i", "Nasa'i": "Nasa'i", "Ibn Majah": "Ibn Majah"}.get(coll, coll)
            if coll not in COLL:
                continue
            start = text.rfind("\n", 0, c.start()) + 1
            end = text.find("\n", c.end())
            ctx = re.sub(r"\s+", " ", text[start: end if end > 0 else len(text)]).strip()
            for n in re.findall(r"\d{1,5}", c.group(2)):
                key = (coll, n, ctx[:80])
                if key in seen:
                    continue
                seen.add(key)
                hits = data[coll].get(n, [])
                row = {"p": pid, "a": aid, "title": title, "ref": f"{coll} {n}", "coll": coll, "n": n, "ctx": ctx[:520], "found": bool(hits)}
                if hits:
                    h = hits[0]
                    t = re.sub(r"\s+", " ", h["text"]).strip()
                    row["text"] = t[:520]
                    row["parts"] = len(hits)
                    row["grades"] = [[g["name"], g["grade"]] for g in h.get("grades", [])][:4]
                    cw, tw = words(ctx), words(" ".join(x["text"] for x in hits))
                    row["overlap"] = round(len(cw & tw) / max(1, len(cw)), 2)
                    row["cw"] = len(cw)
                    # a citation that sits next to a quotation is the one worth checking hardest
                    q = re.findall(r"[“\"]([^”\"]{25,300})[”\"]", ctx)
                    if q:
                        qw = words(" ".join(q))
                        row["quote_overlap"] = round(len(qw & tw) / max(1, len(qw)), 2) if qw else None
                    row["flag"] = "low overlap" if (len(cw) >= 5 and row["overlap"] < 0.08) else ""
                    if row.get("quote_overlap") is not None and row["quote_overlap"] < 0.2 and len(words(" ".join(q))) >= 4:
                        row["flag"] = "quote differs"
                    gr = [g for _, g in row["grades"]]
                    weak = [g for g in gr if re.search(r"da['’]?if|mawdu|munkar|batil", g, re.I)]
                    strong = [g for g in gr if re.search(r"sahih|hasan", g, re.I)]
                    if weak and strong:
                        row["flag"] = "grading disputed"
                    elif weak:
                        row["flag"] = "graded weak"
                    row["hl"] = c.group(0).strip()
                else:
                    row["flag"] = "not found"
                rows.append(row)

summary = {
    "total": len(rows),
    "not_found": sum(1 for r in rows if r["flag"] == "not found"),
    "disputed": sum(1 for r in rows if r["flag"] == "grading disputed"),
    "weak": sum(1 for r in rows if r["flag"] == "graded weak"),
    "quote_differs": sum(1 for r in rows if r["flag"] == "quote differs"),
    "low_overlap": sum(1 for r in rows if r["flag"] == "low overlap"),
    "with_grade": sum(1 for r in rows if r.get("grades")),
}
out.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
print(summary)
