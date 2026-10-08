"""Compare every Arabic Quran quotation in the library with the Uthmani text in the open Quran dataset.

python3 -I quran_audit.py <original pages dir> <dataset dir> <out json>
Only the consonantal skeleton is compared (vowel marks, small signs, alef and yeh variants and verse markers are ignored),
so a flag means words differ, not that a diacritic does.
"""
import difflib
import html
import json
import re
import sys
from pathlib import Path

src, ds, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ar = {(v["chapter"], v["verse"]): v["text"] for v in json.loads((ds / "quran_ar.json").read_text(encoding="utf8"))["quran"]}
en = {(v["chapter"], v["verse"]): v["text"] for v in json.loads((ds / "quran_en.json").read_text(encoding="utf8"))["quran"]}


def skel(t):
    t = re.sub(r"[ً-ٰٟۖ-ۭـ࣓-ࣿؐ-ؚ]", "", t)
    t = t.replace("ٱ", "ا").translate(str.maketrans("أإآٱ", "اااا")).replace("ى", "ي").replace("ی", "ي").replace("ک", "ك").replace("ۀ", "ه").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    t = re.sub(r"[۝۞۩‌‍‏‎]", "", t)
    t = re.sub(r"[^ء-يٱ-ۓ ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


rows = []
for pf in sorted(src.glob("p[1-9].html")):
    s = pf.read_text(encoding="utf8")
    for m in re.finditer(r'<article class="brief" id="([^"]+)"[^>]*>(.*?)</article>', s, re.S):
        aid, body = m.group(1), m.group(2)
        title = html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))).strip()
        for b in re.finditer(r'<blockquote class="ar">(.*?)</blockquote>', body, re.S):
            seg = b.group(1)
            ps = re.findall(r'<p[^>]*lang="ar"[^>]*>(.*?)</p>', seg, re.S)
            cite = re.search(r"<cite>(.*?)</cite>", seg, re.S)
            if not ps or not cite:
                continue
            text = html.unescape(re.sub(r"<[^>]+>", "", " ".join(ps))).strip()
            c = html.unescape(re.sub(r"<[^>]+>", "", cite.group(1))).strip()
            mm = re.search(r"(\d{1,3}):(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?", c)
            row = {"p": pf.stem, "a": aid, "title": title, "cite": c, "text": text[:400]}
            if not mm:
                row["kind"] = "not a verse reference"
                rows.append(row)
                continue
            ch, v1 = int(mm.group(1)), int(mm.group(2)); v2 = int(mm.group(3) or v1)
            verses = [(ch, v) for v in range(v1, v2 + 1)]
            if not all(k in ar for k in verses):
                row["kind"] = "no such verse"; rows.append(row); continue
            ref = skel(" ".join(ar[k] for k in verses))
            got = skel(text)
            # the library may quote only part of a range; compare against the best matching window too
            r_full = difflib.SequenceMatcher(None, got, ref, autojunk=False).ratio()
            sm = difflib.SequenceMatcher(None, got, ref, autojunk=False)
            matched = sum(b.size for b in sm.get_matching_blocks())
            cover = matched / max(1, len(got))  # share of the library's text found in the reference, in order
            row.update({"ratio": round(r_full, 3), "cover": round(cover, 3), "ref_ar": " ".join(ar[k] for k in verses)[:500], "ref_en": " ".join(en.get(k, "") for k in verses)[:500]})
            row["kind"] = "match" if cover >= 0.97 else ("partial" if cover >= 0.85 else "differs")
            rows.append(row)
summary = {k: sum(1 for r in rows if r["kind"] == k) for k in ("match", "partial", "differs", "no such verse", "not a verse reference")}
summary["total"] = len(rows)
out.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
print(summary)
for r in rows:
    if r["kind"] in ("differs", "no such verse", "partial"):
        print(r["kind"], r["p"], r["cite"], r.get("cover"), "|", r["title"][:50])
