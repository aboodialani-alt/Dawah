#!/usr/bin/env python3
"""Build one part page of the Dawah Study Library from a JSON content file.

Usage: build_part.py CONTENT.json TEMPLATE_PART.html OUT.html

TEMPLATE_PART.html is any existing part page (p3.html works). Its <head>/CSS and
closing <script> are reused so new parts match the library exactly.

Content schema (strings may contain light HTML: <em>, <strong>, <a>; bare & is escaped):
{
  "id": "p8", "roman": "VIII", "total_parts": "IX", "title": "...", "desc": "...",
  "prev": {"href": "p7.html", "label": "Part VII", "title": "Reading list"},
  "next": {"href": "p9.html", "label": "Part IX", "title": "..."} | null,
  "sections": [{
    "id": "s-gender", "title": "...", "intro": "...",
    "args": [{
      "title": "...", "thesis": "...",
      "premises": ["...", "..."], "conclusion": "...",
      "evidence": ["<strong>Lead.</strong> text", ...],
      "arabic": [{"text": "...", "cite": "49:13"}],
      "objections": [{"q": "...", "a": "..."}],
      "practice": {"q": "...", "a": "..."},
      "summary": "..."
    }],
    "cards": [["question", "answer"], ...]
  }]
}
"""
import json
import re
import sys

BARE_AMP = re.compile(r"&(?!#?\w+;)")


def h(s):
    """Escape bare ampersands only; content is trusted light HTML."""
    return BARE_AMP.sub("&amp;", s)


def attr(s):
    return h(s).replace('"', "&quot;")


def slug(s, n=50):
    t = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return t[:n].rstrip("-")


def brief(sec_id, i, total, a):
    aid = f"{sec_id}--{slug(a['title'])}"
    out = [
        f'<article class="brief" id="{aid}" data-arg="{aid}">',
        f'<header class="brief-head"><p class="kicker">Argument {i} of {total}</p><h3>{h(a["title"])}</h3>'
        f'<label class="done"><input type="checkbox" data-arg="{aid}" id="chk-{aid}"> Studied</label></header>',
        f'<div class="row r-thesis"><div class="lab">Thesis</div><div class="cell"><p>{h(a["thesis"])}</p></div></div>',
    ]
    lis = "".join(
        f'<li class=""><span class="ptag">P{k}</span><span>{h(p)}</span></li>'
        for k, p in enumerate(a["premises"], 1)
    )
    lis += f'<li class="concl"><span class="ptag">∴</span><span>{h(a["conclusion"])}</span></li>'
    out.append(f'<div class="row r-arg"><div class="lab">Argument</div><div class="cell"><ol class="syl">{lis}</ol></div></div>')
    ev = "\n".join(f"<li>{h(e)}</li>" for e in a["evidence"])
    out.append(f'<div class="row r-ev"><div class="lab">Evidence</div><div class="cell"><ul>\n{ev}\n</ul></div></div>')
    if a.get("arabic"):
        bq = "".join(
            f'<blockquote class="ar"><p lang="ar" dir="rtl">{x["text"]}</p><cite>{h(x["cite"])}</cite></blockquote>'
            for x in a["arabic"]
        )
        out.append(f'<div class="row r-ar"><div class="lab">Arabic</div><div class="cell">{bq}</div></div>')
    obj = "".join(
        f'<div class="obj"><p class="q">{h(o["q"])}</p><div class="a">'
        + "".join(f"<p>{h(par)}</p>" for par in (o["a"] if isinstance(o["a"], list) else [o["a"]]))
        + "</div></div>"
        for o in a["objections"]
    )
    out.append(f'<div class="row r-obj"><div class="lab">Objections</div><div class="cell">{obj}</div></div>')
    pr = a["practice"]
    rid = f"rb-{aid}"
    out.append(
        '<div class="row r-rebut"><div class="lab">Practice</div><div class="cell"><div class="rebut">'
        f'<p class="rb-tag">Your opponent says</p><p class="rb-q">“{h(pr["q"])}”</p>'
        '<p class="rb-hint">Answer it in your head first, then compare.</p>'
        f'<button type="button" class="rb-btn" aria-expanded="false" aria-controls="{rid}">Show a model answer</button>'
        f'<div class="rb-a" id="{rid}" hidden><p>{h(pr["a"])}</p></div></div></div></div>'
    )
    out.append(f'<div class="row r-sum"><div class="lab">In one breath</div><div class="cell"><p>{h(a["summary"])}</p></div></div>')
    out.append("</article>")
    return aid, "\n".join(out)


def build(content, template):
    src = open(template, encoding="utf-8").read()
    head = src[: src.index("<body>") + len("<body>")]
    tail = src[src.index('<dialog id="lb"'):]
    title = content["title"]
    head = re.sub(r"<title>.*?</title>", f"<title>{h(title)} · Dawah Study Library</title>", head, count=1, flags=re.S)

    secs_html, toc_items, n_args = [], [], 0
    for sec in content["sections"]:
        n = len(sec["args"])
        n_args += n
        briefs, toc_lis = [], []
        for i, a in enumerate(sec["args"], 1):
            aid, html = brief(sec["id"], i, n, a)
            briefs.append(html)
            toc_lis.append(f'<li><a href="#{aid}" data-arg="{aid}">{h(a["title"])}</a></li>')
        cards = ""
        if sec.get("cards"):
            items = "".join(
                f'<li><button type="button" class="card" aria-pressed="false"><span class="cq">{h(q)}</span>'
                f'<span class="ca">{h(ans)}</span></button></li>'
                for q, ans in sec["cards"]
            )
            cards = (
                f'<section class="cards" aria-label="Flashcards for {attr(sec["title"])}"><div class="cards-head">'
                f'<h4>Flashcards</h4><p>{len(sec["cards"])} cards. Tap a card to see the answer.</p>'
                f'<button type="button" class="reset">Hide all answers</button></div><ul>{items}</ul></section>'
            )
        secs_html.append(
            f'<section class="sec" id="{sec["id"]}"><header class="sec-head"><h2>{h(sec["title"])}</h2>'
            f'<p class="sec-count">{n} arguments</p></header><p class="sec-intro">{h(sec["intro"])}</p>'
            + "".join(briefs) + cards + "</section>"
        )
        toc_items.append(
            f'<li class="toc-sec"><details><summary><a href="#{sec["id"]}">{h(sec["title"])}</a></summary>'
            f'<ol>{"".join(toc_lis)}</ol></details></li>'
        )
    toc = "".join(toc_items)

    pager = ""
    pv, nx = content.get("prev"), content.get("next")
    if pv or nx:
        pager = '<nav class="pager" aria-label="Other parts">'
        if pv:
            pager += f'<a class="pg prev" href="{pv["href"]}"><span>← {h(pv["label"])}</span>{h(pv["title"])}</a>'
        if nx:
            pager += f'<a class="pg next" href="{nx["href"]}"><span>{h(nx["label"])} →</span>{h(nx["title"])}</a>'
        pager += "</nav>"

    notice_html = ""
    if content.get("notice"):
        notice_html = ('  <p class="desc" style="font-family:var(--f-ui);font-size:.88rem;border-left:3px solid var(--gold);'
                       f'padding-left:.8rem">{h(content["notice"])}</p>\n')
    body = f"""
<div class="wrap">
<nav class="topbar" aria-label="Library"><a class="home" href="index.html">← Dawah Study Library</a><span>Part {content["roman"]} of {content["total_parts"]}</span></nav>
<header class="phead">
  <p class="eyebrow">Part {content["roman"]} · {len(content["sections"])} sections · {n_args} arguments</p>
  <h1>{h(title)}</h1>
  <p class="desc">{h(content["desc"])}</p>
{notice_html}  <ul class="legend" aria-label="Each argument is laid out as"><li>Thesis</li><li>Argument (premises → conclusion)</li><li>Evidence &amp; screenshots</li><li>Arabic</li><li>Objections</li><li>Practice</li><li>In one breath</li></ul>
</header>
<div class="layout">
<aside>
  <div class="search">
    <label for="q" class="eyebrow" style="margin:0">Search this part</label>
    <input id="q" type="search" placeholder="Verse, name or keyword" autocomplete="off">
    <small id="qinfo" aria-live="polite"></small>
  </div>
  <div class="progress"><span id="prog">0 studied</span><div class="bar"><i id="progbar"></i></div></div>
  <details class="mtoc"><summary>Contents</summary><ol class="toc">{toc}</ol></details>
  <ol class="toc" id="toc">{toc}</ol>
</aside>
<main id="main">
{''.join(secs_html)}
<p class="empty" id="empty" hidden>No arguments match that search.</p>
{pager}
<footer>Written for the Dawah Study Library. Check each source before citing it in a debate. Tap any screenshot to open it full size.</footer>
</main>
</div>
</div>
"""
    return head + body + tail, n_args


def index_entries(content):
    """Search-index rows for index.html: {p, id, s, t, h}."""
    rows = []
    for sec in content["sections"]:
        for a in sec["args"]:
            rows.append({"p": content["id"], "id": f"{sec['id']}--{slug(a['title'])}", "s": sec["title"], "t": a["title"], "h": a["thesis"]})
    return rows


if __name__ == "__main__":
    content_path, template, out = sys.argv[1:4]
    content = json.load(open(content_path, encoding="utf-8"))
    html, n = build(content, template)
    open(out, "w", encoding="utf-8").write(html)
    json.dump(index_entries(content), open(out + ".index.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{out}: {n} arguments, {len(html)} bytes")
