#!/usr/bin/env python3
"""Apply fact-check corrections to published part pages.

Usage: apply_fixes.py SITE_DIR RESULTS_DIR REPORT_DIR

For each finding with status error/misleading/weak_source and a non-null correction,
find the snippet inside its argument (matching ignores whitespace and inline tags),
and replace that span with the escaped correction text. A finding is skipped, and
logged, when the snippet is missing or ambiguous, or when the span crosses block
structure. Unverifiable findings and findings without a correction are only logged.
"""
import glob
import html
import json
import os
import re
import sys

site, results, report = sys.argv[1:4]
os.makedirs(report, exist_ok=True)
APPLY = {"error", "misleading", "weak_source"}
INLINE = {"em", "strong", "span", "a", "sup", "sub", "i", "b", "cite", "br"}
TOKEN = re.compile(r"<[^>]*>|&#?\w+;|.", re.S)


def squeeze_map(frag):
    """Return (squeezed_text, offsets) where offsets[i] = (html_start, html_end) of squeezed char i."""
    chars, offs = [], []
    for m in TOKEN.finditer(frag):
        tok = m.group(0)
        if tok.startswith("<") and len(tok) > 1:
            continue
        ch = html.unescape(tok)
        for c in ch:
            if c.isspace():
                continue
            chars.append(c)
            offs.append((m.start(), m.end()))
    return "".join(chars), offs


def norm(s):
    return "".join(c for c in html.unescape(s) if not c.isspace())


def tags_between(frag):
    return [re.match(r"</?(\w+)", t).group(1).lower() for t in re.findall(r"<[^>]*>", frag) if re.match(r"</?(\w+)", t)]


pages = {}
for f in glob.glob(os.path.join(site, "p[0-9].html")):
    pages[os.path.basename(f)] = open(f, encoding="utf-8").read()

applied, skipped = [], []
for rf in sorted(glob.glob(os.path.join(results, "*.json"))):
    data = json.load(open(rf, encoding="utf-8"))
    for f in data["findings"]:
        status, aid, snip, corr = f["status"], f["arg_id"], f.get("snippet", ""), f.get("correction")
        rec = {"file": os.path.basename(rf), "arg_id": aid, "status": status, "snippet": snip, "correction": corr, "problem": f.get("problem")}
        if status not in APPLY or not corr:
            rec["reason"] = "unverifiable" if status == "unverifiable" else "no correction supplied"
            skipped.append(rec)
            continue
        page = next((p for p, t in pages.items() if f'id="{aid}"' in t), None)
        if not page:
            rec["reason"] = "argument not found"
            skipped.append(rec)
            continue
        text = pages[page]
        am = re.search(r'<article class="brief" id="%s".*?</article>' % re.escape(aid), text, re.S)
        art, base = am.group(0), am.start()
        sq, offs = squeeze_map(art)
        target = norm(snip)
        if len(target) < 8:
            rec["reason"] = "snippet too short"
            skipped.append(rec)
            continue
        i = sq.find(target)
        if i < 0:
            rec["reason"] = "snippet not found"
            skipped.append(rec)
            continue
        if sq.find(target, i + 1) >= 0:
            rec["reason"] = "snippet ambiguous"
            skipped.append(rec)
            continue
        hs, he = offs[i][0], offs[i + len(target) - 1][1]
        span = art[hs:he]
        bad = [t for t in tags_between(span) if t not in INLINE]
        if bad:
            rec["reason"] = "span crosses structure: " + ",".join(sorted(set(bad)))
            skipped.append(rec)
            continue
        # keep inline tags balanced: re-emit closers/openers that the span cut across
        stack, closers = [], []
        for t in re.findall(r"<[^>]*>", span):
            mm = re.match(r"<(/?)(\w+)", t)
            if not mm or mm.group(2).lower() == "br":
                continue
            name = mm.group(2).lower()
            if mm.group(1):
                if stack and stack[-1][0] == name:
                    stack.pop()
                else:
                    closers.append(t)
            else:
                stack.append((name, t))
        keep = "".join(closers) + "".join(t for _, t in stack)
        # sentence-shape fixes
        c = corr.strip()
        prev_ch = sq[i - 1] if i > 0 else ""
        next_ch = sq[i + len(target)] if i + len(target) < len(sq) else ""
        if prev_ch and not prev_ch.isdigit() and prev_ch not in ".?!:\"”)∴" and len(c) > 2 and c[0].isupper() and c[1].islower():
            first = re.match(r"[A-Za-z']+", c).group(0)
            if first in {"The", "A", "An", "This", "These", "Those", "It", "In", "On", "By", "Some", "Many", "Most", "Both", "Either", "Early", "Later", "Only", "Several"}:
                c = c[0].lower() + c[1:]
        if c.endswith(".") and (next_ch in {".", ",", ";", ")", ":"} or next_ch.islower()):
            c = c[:-1]
        new_art = art[:hs] + html.escape(c, quote=False) + keep + art[he:]
        pages[page] = text[:base] + new_art + text[base + len(art):]
        rec["page"] = page
        rec["old_html"] = span
        applied.append(rec)

for p, t in pages.items():
    open(os.path.join(site, p), "w", encoding="utf-8").write(t)
json.dump(applied, open(os.path.join(report, "applied.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(skipped, open(os.path.join(report, "skipped.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import collections
print("applied", len(applied), "skipped", len(skipped), dict(collections.Counter(s["reason"].split(":")[0] for s in skipped)))
