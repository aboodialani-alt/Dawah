"""Assembles and checks the Arabic core.

python3 -I build_ar.py <dataset dir> <site dir>
Checks every translated card: valid shape, Arabic-Indic digits, and that every quoted text is copied from a verified source given in its
packet (Quran Uthmani text, the library's own Arabic quotes, or the hadith dataset), not back-translated. Writes <site>/ar-core.json and
a report to report.md.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
ds, site = Path(sys.argv[1]), Path(sys.argv[2])
tracks = json.loads((site / "tracks.json").read_text(encoding="utf8"))
track_of = {}
for t in tracks:
    for s in t["steps"]:
        track_of.setdefault(s["id"], t["id"])


def skel(t):
    t = re.sub(r"[ً-ٰٟۖ-ۭـ࣓-ࣿؐ-ؚ]", "", t)
    t = t.translate(str.maketrans("أإآٱ", "اااا")).replace("ى", "ي").replace("ی", "ي").replace("ک", "ك").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    t = re.sub(r"[^ء-ي ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


KEYS = ["n", "id", "title", "thesis", "premises", "evidence", "quotes", "objections", "practice", "sum", "omitted", "check"]
out, report = [], ["# Arabic core check", ""]
problems = 0
for pf in sorted((HERE / "packets").glob("*.json")):
    pk = json.loads(pf.read_text(encoding="utf8"))
    of = HERE / "out" / pf.name
    if not of.exists():
        report.append(f"- {pf.name}: **missing translation**"); problems += 1; continue
    try:
        tr = json.loads(of.read_text(encoding="utf8"))
    except Exception as e:
        report.append(f"- {pf.name}: **invalid JSON** ({e})"); problems += 1; continue
    issues = []
    for k in KEYS:
        if k not in tr:
            issues.append(f"missing field {k}")
    if tr.get("id") != pk["id"]:
        issues.append("id does not match packet")
    sources = [skel(v) for v in pk["quran_arabic"].values()] + [skel(q["text"]) for q in pk["ar_quotes"]] + [skel(h["arabic"]) for h in pk["hadith_arabic"].values()]
    for q in tr.get("quotes", []):
        s = skel(q.get("text", ""))
        if s and not any(s in src or (len(s) > 30 and s[:30] in src and s[-30:] in src) for src in sources):
            issues.append("quote not found in its verified sources: " + q.get("text", "")[:60])
    body = json.dumps({k: tr.get(k) for k in ("title", "thesis", "premises", "evidence", "objections", "practice", "sum")}, ensure_ascii=False)
    latin = re.findall(r"(?<![A-Za-z\-])[0-9]+(?![A-Za-z])", re.sub(r"\([^)]*[A-Za-z][^)]*\)", "", body))
    if len(latin) > 3:
        issues.append(f"{len(latin)} Latin digits in the Arabic text")
    tr["track"] = track_of.get(pk["id"], "")
    out.append(tr)
    status = "ok" if not issues else "; ".join(issues)
    if issues:
        problems += 1
    report.append(f"- {pf.name} {pk['title'][:60]}: {status}")
    if tr.get("omitted"):
        report.append("  - omitted: " + " | ".join(tr["omitted"]))
(site / "ar-core.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf8")
report.insert(2, f"{len(out)} cards, {problems} with something to look at.")
(HERE / "report.md").write_text("\n".join(report) + "\n", encoding="utf8")
print(len(out), "cards,", problems, "flagged")
