#!/usr/bin/env python3
"""Apply proofreading fixes (find/replace within an argument) to the fixed site copy.
Usage: apply_proofread.py SITE_DIR PROOFREAD_DIR REPORT_DIR"""
import glob, html, json, os, re, sys
site, pdir, report = sys.argv[1:4]
INLINE = {"em", "strong", "span", "a", "sup", "sub", "i", "b", "cite", "br"}
TOKEN = re.compile(r"<[^>]*>|&#?\w+;|.", re.S)
def squeeze_map(frag):
    chars, offs = [], []
    for m in TOKEN.finditer(frag):
        tok = m.group(0)
        if tok.startswith("<") and len(tok) > 1: continue
        for c in html.unescape(tok):
            if c.isspace(): continue
            chars.append(c); offs.append((m.start(), m.end()))
    return "".join(chars), offs
norm = lambda s: "".join(c for c in html.unescape(s) if not c.isspace())
pages = {os.path.basename(f): open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(site, "p[0-9].html"))}
applied, skipped = [], []
for inf in sorted(glob.glob(os.path.join(pdir, "in_*.json"))):
    key = os.path.basename(inf)[3:]
    outf = os.path.join(pdir, "out_" + key)
    if not os.path.exists(outf): continue
    items = {x["n"]: x for x in json.load(open(inf, encoding="utf-8"))}
    for fx in json.load(open(outf, encoding="utf-8")):
        it = items.get(fx["n"]); rec = {"n": fx["n"], "arg_id": fx["arg_id"], "find": fx["find"], "replace": fx["replace"]}
        if not it: rec["reason"] = "no such item"; skipped.append(rec); continue
        page = it["page"]; text = pages[page]
        am = re.search(r'<article class="brief" id="%s".*?</article>' % re.escape(fx["arg_id"]), text, re.S)
        if not am: rec["reason"] = "argument not found"; skipped.append(rec); continue
        art, base = am.group(0), am.start()
        sq, offs = squeeze_map(art); t = norm(fx["find"])
        i = sq.find(t)
        if len(t) < 6 or i < 0: rec["reason"] = "not found"; skipped.append(rec); continue
        if sq.find(t, i + 1) >= 0: rec["reason"] = "ambiguous"; skipped.append(rec); continue
        hs, he = offs[i][0], offs[i + len(t) - 1][1]; span = art[hs:he]
        bad = [m.group(2).lower() for tg in re.findall(r"<[^>]*>", span) for m in [re.match(r"</?(\w+)", tg)] if m for m in [re.match(r"<(/?)(\w+)", tg)] if m.group(2).lower() not in INLINE]
        if bad: rec["reason"] = "crosses structure"; skipped.append(rec); continue
        stack, closers = [], []
        for tg in re.findall(r"<[^>]*>", span):
            mm = re.match(r"<(/?)(\w+)", tg)
            if not mm or mm.group(2).lower() == "br": continue
            nm = mm.group(2).lower()
            if mm.group(1):
                if stack and stack[-1][0] == nm: stack.pop()
                else: closers.append(tg)
            else: stack.append((nm, tg))
        keep = "".join(closers) + "".join(tg for _, tg in stack)
        new_art = art[:hs] + html.escape(fx["replace"], quote=False) + keep + art[he:]
        pages[page] = text[:base] + new_art + text[base + len(art):]
        applied.append(rec)
for p, t in pages.items(): open(os.path.join(site, p), "w", encoding="utf-8").write(t)
json.dump(applied, open(os.path.join(report, "proofread_applied.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(skipped, open(os.path.join(report, "proofread_skipped.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("proofread applied", len(applied), "skipped", len(skipped))
for s in skipped: print(" skipped:", s["reason"], s["arg_id"][:40], "|", s["find"][:60])
