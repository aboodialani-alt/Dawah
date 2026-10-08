/* DA v2 layer: command bar, palette search (attacks + arguments), per-argument tools, reading modes,
   queue (shared db, falls back to this browser), "draft a reel" via Claude, reviewer notes.
   Exposes window.DA2 for the hub, drill and review pages. Never edits the library text. */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const AR = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
  const arN = n => String(n).replace(/\d/g, d => AR[d]);
  const ROMAN = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6, VII: 7, VIII: 8, IX: 9 };

  /* ---------- tiny helpers ---------- */
  let toastEl, toastT;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'toast'; toastEl.setAttribute('role', 'status'); document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add('on');
    clearTimeout(toastT); toastT = setTimeout(() => toastEl.classList.remove('on'), 2200);
  }
  async function copy(text, okMsg) {
    try { await navigator.clipboard.writeText(text); toast(okMsg || 'Copied'); return true; }
    catch (e) {
      const ta = document.createElement('textarea'); ta.value = text; ta.style.cssText = 'position:fixed;opacity:0;top:0';
      document.body.appendChild(ta); ta.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch (_) {}
      ta.remove(); toast(ok ? (okMsg || 'Copied') : 'Copy blocked here: select the text and copy it'); return ok;
    }
  }
  function applyTheme(t) {
    const r = document.documentElement;
    if (t === 'light' || t === 'dark') r.setAttribute('data-theme', t); else r.removeAttribute('data-theme');
  }
  applyTheme(store.get('da2:theme'));

  /* ---------- index + search ---------- */
  let idxP;
  function loadIdx() {
    if (!idxP) idxP = fetch('idx.json').then(r => r.json()).then(d => {
      d.byId = new Map(d.briefs.map(b => [b.id, b]));
      d.partBy = new Map(d.parts.map(p => [p.id, p]));
      return d;
    });
    return idxP;
  }
  const norm = s => (s || '').toLowerCase().normalize('NFKD').replace(/[̀-ًͯ-ٰٟ]/g, '').replace(/[ʿʾ'’‘`"“”]/g, '');
  const STOP = new Set(['the', 'a', 'an', 'is', 'are', 'of', 'to', 'and', 'in', 'that', 'it', 'was', 'for', 'on', 'be', 'by', 'as', 'with', 'this', 'they', 'say', 'says', 'not']);
  function prep(d) {
    if (d._prep) return;
    d.briefs.forEach(b => {
      b._t = norm(b.title); b._th = norm(b.thesis); b._s = norm(b.sum); b._e = norm(b.evs); b._k = norm(b.sec);
      b.obj.forEach(o => { o._q = norm(o.q); o._a = norm(o.a); });
    });
    d._prep = true;
  }
  function tokens(q) { return norm(q).split(/[^a-z0-9؀-ۿ:]+/).filter(t => t && (t.length > 1 || /\d/.test(t)) && !STOP.has(t)); }
  function search(d, q, limit = 40) {
    prep(d);
    const tk = tokens(q); if (!tk.length) return { tk, hits: [] };
    const nq = norm(q).trim();
    const has = (f, t) => f.indexOf(t) >= 0;
    const hits = [];
    // short queries must match every word; long pasted sentences need about 60% of their words
    const need = tk.length <= 3 ? tk.length : Math.max(3, Math.ceil(tk.length * 0.6));
    const enough = all => tk.filter(t => has(all, t)).length >= need;
    d.briefs.forEach(b => {
      b.obj.forEach(o => {
        const all = o._q + ' ' + o._a + ' ' + b._t;
        if (!enough(all)) return;
        let s = 0; tk.forEach(t => { if (has(o._q, t)) s += 5; if (has(o._a, t)) s += 1.5; if (has(b._t, t)) s += 2; });
        if (nq.length > 5 && has(o._q, nq)) s += 8;
        hits.push({ type: 'atk', b, o, s });
      });
      const all = b._t + ' ' + b._th + ' ' + b._s + ' ' + b._e + ' ' + b._k;
      if (enough(all)) {
        let s = 0; tk.forEach(t => { if (has(b._t, t)) s += 4; if (has(b._th, t)) s += 3; if (has(b._s, t)) s += 2; if (has(b._e, t)) s += 1; if (has(b._k, t)) s += 1; });
        if (nq.length > 5 && (has(b._t, nq) || has(b._th, nq))) s += 8;
        hits.push({ type: 'arg', b, s });
      }
    });
    hits.sort((x, y) => y.s - x.s);
    return { tk, hits: hits.slice(0, limit) };
  }
  /* Arabic claims: the library text is English, so Claude turns the claim into one English sentence first */
  const hasAr = s => /[\u0600-\u06FF]/.test(s), trCache = new Map();
  async function smartSearch(d, q, limit) {
    if (!hasAr(q)) return Object.assign(search(d, q, limit), { via: null });
    const key = q.trim(); let en = trCache.get(key);
    if (!en) {
      const sample = await getSample();
      if (!sample) return { tk: [], hits: [], via: null, needSample: true };
      try {
        const r = await sample('Translate this claim into plain English in one short sentence. Output only the sentence, with no quotes and no commentary:\n' + key.slice(0, 500), { cache: true, modelTier: 'quick' });
        en = r.text.trim().replace(/^["“]|["”]$/g, ''); trCache.set(key, en);
      } catch (e) { return { tk: [], hits: [], via: null, failed: true }; }
    }
    return Object.assign(search(d, en, limit), { via: en });
  }
  function mark(text, tk) {
    let out = esc(text);
    tk.forEach(t => {
      if (t.length < 2) return;
      const re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
      out = out.replace(re, '<mark>$1</mark>');
    });
    return out;
  }
  const href = b => b.p + '.html#' + b.a;

  /* ---------- queue ---------- */
  const Q = { map: new Map(), subs: [], db: null };
  const qkey = id => id.replace(/[^a-zA-Z0-9-]/g, '_').slice(0, 140);
  function qnotify() { Q.subs.forEach(f => { try { f(Q.map); } catch (e) {} }); }
  function qLocalLoad() { try { const o = JSON.parse(store.get('da2:queue') || '{}'); Q.map = new Map(Object.entries(o)); } catch (e) { Q.map = new Map(); } }
  function qLocalSave() { store.set('da2:queue', JSON.stringify(Object.fromEntries(Q.map))); }
  qLocalLoad();
  async function initDb() {
    try {
      if (!window.claude || !window.claude.use) return;
      const db = await window.claude.use('db'); if (!db) return;
      Q.db = db;
      db.collection('queue').onSnapshot(s => { Q.map = new Map(s.docs.map(d => [d.id, d.data()])); qnotify(); }, () => {});
    } catch (e) {}
  }
  async function qToggle(b) {
    const k = qkey(b.id);
    if (Q.map.has(k)) {
      Q.map.delete(k); qnotify();
      if (Q.db) { try { await Q.db.doc('queue/' + k).delete(); } catch (e) { toast('Could not remove from the shared queue'); } } else qLocalSave();
      toast('Removed from the video queue'); return false;
    }
    const rec = { id: b.id, title: b.title, part: b.p, sec: b.sec, href: href(b), at: Date.now() };
    Q.map.set(k, rec); qnotify();
    if (Q.db) { try { await Q.db.doc('queue/' + k).set(rec); } catch (e) { toast('Saved here only (shared queue refused the write)'); qLocalSave(); } } else qLocalSave();
    toast('Added to the video queue'); return true;
  }
  const qHas = b => Q.map.has(qkey(b.id));

  /* ---------- Claude (sample) ---------- */
  const STYLES = {
    A: 'Style A (Ali Amery): open with "السلام عليكم"; read the opponent\'s source first and then react to it; use rhetorical questions and repetition; formal Arabic with some Iraqi flavour if the language is Arabic; end flat on a fork.',
    B: 'Style B (challenge clip): 36-118 seconds. The first 3 seconds put one pointed question or challenge to the opponent. Show the opponent\'s claim, then the source with the key line highlighted, then one decisive answer, then the fork ending. No intro.',
    C: 'Style C (versus): 60-140 seconds. Open on a contrast: the opponent\'s claim side by side with the verified text. Resolve it in one beat. One light humor or meme beat is allowed.'
  };
  async function getSample() { try { return window.claude && window.claude.use ? await window.claude.use('sample') : null; } catch (e) { return null; } }
  function draftPrompt(brief, style, lang, secs) {
    return [
      'You are helping write a short Instagram Reel script for a dawah channel.',
      'RULES: Use ONLY the facts, quotes, numbers and source references that appear in the BRIEF below. Do not add any verse, hadith, grading, date, name or quote that is not in the brief. Label interpretations as interpretations. If something needed is missing, write NEEDS SOURCE instead of guessing. Tone: firm and direct with light humor allowed, no insults, no mocking real people, no call to action. End on a fork: "You are free: if X, then Y."',
      STYLES[style],
      'Language: ' + lang + '. Target length: about ' + secs + ' seconds.',
      'OUTPUT FORMAT: 1) HOOK (first 3 seconds). 2) BEATS with approximate seconds. 3) ON-SCREEN TEXT lines. 4) SOURCE LINES to show on screen (exact references from the brief). 5) FORK ENDING. 6) CLAIM CHECK: a list of every factual claim in the script and the brief line it came from.',
      '--- BRIEF ---', brief
    ].join('\n\n');
  }
  function cellText(cell) {
    const parts = [];
    $$('li', cell).forEach(li => parts.push('- ' + li.textContent.trim().replace(/\s+/g, ' ')));
    $$('.obj', cell).forEach(o => parts.push('They say: ' + (($('.q', o) || {}).textContent || '').trim() + '\nAnswer: ' + (($('.a', o) || {}).textContent || '').trim().replace(/\s+/g, ' ')));
    if (!parts.length) return cell.textContent.trim().replace(/\s+/g, ' ');
    return parts.join('\n');
  }
  function briefText(article) {
    const title = ($('h3', article) || {}).textContent || '';
    const out = ['# ' + title.trim()];
    $$('.row', article).forEach(r => {
      const lab = ($('.lab', r) || {}).textContent || '', cell = $('.cell', r);
      if (!cell) return;
      if (r.classList.contains('r-rebut')) return;
      out.push('## ' + lab.trim() + '\n' + cellText(cell));
    });
    return out.join('\n\n');
  }
  let dlg;
  function ensureDlg() {
    if (dlg) return dlg;
    dlg = document.createElement('div'); dlg.className = 'dlg'; dlg.setAttribute('role', 'dialog'); dlg.setAttribute('aria-modal', 'true');
    dlg.innerHTML = '<div class="dlg-box"><div class="dlg-head"><h4></h4><button class="btn2" type="button" data-x>Close</button></div><div class="dlg-body"></div></div>';
    document.body.appendChild(dlg);
    dlg.addEventListener('click', e => { if (e.target === dlg || e.target.hasAttribute('data-x')) closeDlg(); });
    return dlg;
  }
  let dlgAbort = null;
  function closeDlg() { if (dlg) dlg.classList.remove('on'); if (dlgAbort) { dlgAbort.abort(); dlgAbort = null; } }
  function openDlg(title, html) { const d = ensureDlg(); $('h4', d).textContent = title; $('.dlg-body', d).innerHTML = html; d.classList.add('on'); return $('.dlg-body', d); }

  async function openDraft(article, bdata) {
    const body = openDlg('Draft a reel from this argument',
      '<label>Style<select id="dr-style"><option value="B">B · Challenge clip (English front)</option><option value="C">C · Versus</option><option value="A">A · Ali Amery (Arabic front)</option></select></label>' +
      '<label>Language<select id="dr-lang"><option>English</option><option>Arabic (formal, Iraqi flavour)</option></select></label>' +
      '<label>Length in seconds<input id="dr-secs" type="text" value="60"></label>' +
      '<div class="row-btns"><button class="btn1" type="button" id="dr-go">Draft it</button></div>' +
      '<p class="note-s">Claude drafts only from this argument\'s own text and lists every claim it used. It is a draft: check each source yourself before recording.</p>' +
      '<pre id="dr-out" hidden></pre><div class="row-btns" id="dr-act" hidden><button class="btn2" type="button" id="dr-copy">Copy script</button></div>');
    const sample = await getSample();
    const go = $('#dr-go', body), out = $('#dr-out', body);
    if (!sample) { go.disabled = true; out.hidden = false; out.textContent = 'Drafting needs this page to be open inside Claude. Use "Copy brief" and paste it into a chat instead.'; return; }
    go.addEventListener('click', async () => {
      const text = briefText(article);
      go.disabled = true; out.hidden = false; out.innerHTML = '<span class="spin"></span> Thinking…'; $('#dr-act', body).hidden = true;
      dlgAbort = new AbortController();
      try {
        const r = await sample(draftPrompt(text, $('#dr-style', body).value, $('#dr-lang', body).value, $('#dr-secs', body).value || '60'),
          { signal: dlgAbort.signal, cache: false, modelTier: 'default', onText: u => { out.textContent = u.text; } });
        out.textContent = r.text; $('#dr-act', body).hidden = false;
        $('#dr-copy', body).onclick = () => copy(r.text, 'Script copied');
      } catch (e) {
        if (e && e.code === 'cancelled') return;
        out.textContent = e && e.code === 'not_granted' ? 'Permission was not granted, so nothing was sent.' : 'Could not draft this one (' + ((e && e.code) || 'error') + '). Try again in a moment.';
      } finally { go.disabled = false; }
    });
  }

  /* ---------- queue dialog ---------- */
  function openQueue() {
    const items = [...Q.map.values()].sort((a, b) => (a.at || 0) - (b.at || 0));
    const body = openDlg('Video queue (' + items.length + ')',
      (items.length ? '<ol style="margin:0;padding-left:1.2rem;display:grid;gap:.5rem">' + items.map(i =>
        '<li><a href="' + esc(i.href) + '">' + esc(i.title) + '</a> <span class="note-s">· ' + esc(i.sec || '') + '</span> <button class="btn2" data-rm="' + esc(i.id) + '" type="button" style="padding:.1rem .6rem;font-size:.75rem">Remove</button></li>').join('') + '</ol>' +
        '<div class="row-btns"><button class="btn1" id="q-copy" type="button">Copy as video plan</button></div>' +
        '<p class="note-s">' + (Q.db ? 'This queue is shared: Claude can read it and plan the next videos from it.' : 'Saved in this browser only. Open the page inside Claude to share it.') + '</p>'
        : '<p>Nothing queued yet. On any argument, press “Queue for video” to line it up for the next reel.</p>'));
    $$('[data-rm]', body).forEach(b => b.addEventListener('click', async () => {
      const k = qkey(b.getAttribute('data-rm')); Q.map.delete(k); qnotify();
      if (Q.db) { try { await Q.db.doc('queue/' + k).delete(); } catch (e) {} } else qLocalSave();
      openQueue();
    }));
    const c = $('#q-copy', body);
    if (c) c.onclick = () => copy('Video plan, in order:\n' + items.map((i, n) => (n + 1) + '. ' + i.title + ' (' + i.sec + ') ' + i.href).join('\n'), 'Plan copied');
  }

  /* ---------- palette ---------- */
  let pal, palSel = 0, palHits = [];
  function ensurePal() {
    if (pal) return pal;
    pal = document.createElement('div'); pal.className = 'pal'; pal.setAttribute('role', 'dialog'); pal.setAttribute('aria-modal', 'true'); pal.setAttribute('aria-label', 'Search the library');
    pal.innerHTML = '<div class="pal-box"><div class="pal-in"><span aria-hidden="true">⌕</span><input id="pal-q" type="search" placeholder="Paste what they said, or search a verse, name or topic" autocomplete="off"></div>' +
      '<div class="pal-hint">Attacks are matched against the objections each argument already answers. ↑ ↓ to move · Enter to open · Esc to close</div><div class="pal-list" id="pal-list"></div></div>';
    document.body.appendChild(pal);
    pal.addEventListener('click', e => { if (e.target === pal) closePal(); });
    const inp = $('#pal-q', pal);
    let t; inp.addEventListener('input', () => { clearTimeout(t); t = setTimeout(runPal, hasAr(inp.value) ? 700 : 90); });
    inp.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { palSel = Math.min(palHits.length - 1, palSel + 1); selPal(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { palSel = Math.max(0, palSel - 1); selPal(); e.preventDefault(); }
      else if (e.key === 'Enter') { const h = palHits[palSel]; if (h) { location.href = href(h.b); closePal(); } }
    });
    return pal;
  }
  function selPal() { $$('.pal-item', pal).forEach((el, i) => { el.setAttribute('aria-selected', i === palSel ? 'true' : 'false'); if (i === palSel) el.scrollIntoView({ block: 'nearest' }); }); }
  async function runPal() {
    const list = $('#pal-list', pal), q = $('#pal-q', pal).value;
    if (!q.trim()) { list.innerHTML = '<div class="pal-empty">Type or paste a claim. Try “hadith were written 200 years later”.</div>'; palHits = []; return; }
    const d = await loadIdx();
    if (hasAr(q)) list.innerHTML = '<div class="pal-empty"><span class="spin"></span> Translating your claim…</div>';
    const r = await smartSearch(d, q, 30); if ($('#pal-q', pal).value !== q) return; palHits = r.hits;
    if (r.needSample) { list.innerHTML = '<div class="pal-empty">Searching in Arabic needs this page open inside Claude. Try the English words instead.</div>'; return; }
    if (!r.hits.length) { list.innerHTML = '<div class="pal-empty">No match' + (r.via ? ' for “' + esc(r.via) + '”' : '') + '. Try fewer or simpler words.</div>'; return; }
    list.innerHTML = r.hits.map((h, i) => {
      const p = d.partBy.get(h.b.p);
      const title = h.type === 'atk' ? h.o.q : h.b.title;
      const sub = (r.via && i === 0 ? 'Searched for: ' + r.via + ' · ' : '') + (h.type === 'atk' ? 'Part ' + p.no + ' · ' + h.b.title : 'Part ' + p.no + ' · ' + h.b.sec);
      return '<a class="pal-item" role="option" aria-selected="' + (i === 0) + '" href="' + esc(href(h.b)) + '"><span class="tag ' + h.type + '">' + (h.type === 'atk' ? 'Attack' : 'Argument') + '</span><span class="t">' + mark(title, r.tk) + '</span><span class="s">' + esc(sub) + '</span></a>';
    }).join('');
    palSel = 0;
  }
  function openPal() { ensurePal().classList.add('on'); const i = $('#pal-q', pal); i.focus(); i.select(); runPal(); }
  function closePal() { if (pal) pal.classList.remove('on'); }

  /* ---------- command bar ---------- */
  function mountBar(opts) {
    opts = opts || {};
    const bar = document.createElement('div'); bar.className = 'dabar';
    bar.innerHTML = '<a class="brand" href="index.html"><span class="mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="5" y="5" width="14" height="14"/><rect x="5" y="5" width="14" height="14" transform="rotate(45 12 12)"/><circle cx="12" cy="12" r="2.6"/></svg></span><span class="lbl">Dawah Study Library</span></a><span class="crumb">' + esc(opts.crumb || '') + '</span><span class="sp"></span>' +
      '<button type="button" data-pal aria-label="Search"><svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="6.8" cy="6.8" r="4.6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10.4 10.4L14 14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span class="lbl">Search</span> <kbd>/</kbd></button>' +
      (opts.modes ? '<span class="seg" role="group" aria-label="Reading mode"><button type="button" data-mode="skim" title="Thesis and one-breath summary only">Skim</button><button type="button" data-mode="full" title="Everything">Full</button><button type="button" data-mode="drill" title="Attacks first, answers hidden">Drill</button></span>' : '') +
      '<button type="button" data-queue aria-label="Video queue"><svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 3.5h12M2 8h12M2 12.5h8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span class="lbl">Queue</span> <span class="qn">0</span></button>' +
      '<button type="button" data-theme aria-label="Switch theme"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.8a6.2 6.2 0 0 1 0 12.4z" fill="currentColor"/></svg></button>';
    const host = $('.wrap') || document.body;
    host.insertBefore(bar, host.firstChild);
    $('[data-pal]', bar).addEventListener('click', openPal);
    $('[data-queue]', bar).addEventListener('click', openQueue);
    $('[data-theme]', bar).addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme');
      const dark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
      const next = dark ? 'light' : 'dark'; store.set('da2:theme', next); applyTheme(next);
    });
    const upd = () => { const n = $('.qn', bar); if (n) n.textContent = Q.map.size; };
    Q.subs.push(upd); upd();
    if (opts.modes) {
      const set = m => {
        document.body.classList.remove('m-skim', 'm-drill'); if (m !== 'full') document.body.classList.add('m-' + m);
        $$('[data-mode]', bar).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.mode === m))); store.set('da2:mode', m);
      };
      $$('[data-mode]', bar).forEach(b => b.addEventListener('click', () => set(b.dataset.mode)));
      set(store.get('da2:mode') || 'full');
    }
    return bar;
  }

  document.addEventListener('keydown', e => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName || '') || (e.target && e.target.isContentEditable);
    if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === '/' && !typing)) { e.preventDefault(); openPal(); }
    else if (e.key === 'Escape') { closePal(); closeDlg(); }
  });

  /* ---------- part-page enhancements ---------- */
  async function enhancePart() {
    const briefs = $$('article.brief'); if (!briefs.length) return;
    const pm = location.pathname.match(/p(\d)\.html/);
    const crumbSrc = ($('.topbar span') || {}).textContent || '';
    const h1 = ($('.phead h1') || {}).textContent || '';
    mountBar({ crumb: (crumbSrc ? crumbSrc.replace(/ of IX/, '') + ' · ' : '') + h1, modes: true });
    const ph = $('.phead');
    if (ph) {
      const pn = pm ? pm[1] : (ROMAN[(crumbSrc.match(/Part ([IVX]+)/) || [])[1]] || '');
      if (pn) { const s = document.createElement('span'); s.className = 'bignum'; s.setAttribute('aria-hidden', 'true'); s.textContent = arN(pn); ph.appendChild(s); }
    }
    let flags = {};
    try { flags = await fetch('flags.json').then(r => r.json()); } catch (e) {}
    const pid = pm ? 'p' + pm[1] : '';
    const reg = new Map();
    briefs.forEach(art => {
      const head = $('.brief-head', art), k = $('.kicker', head);
      const n = (k && (k.textContent.match(/Argument (\d+)/) || [])[1]) || '';
      if (n) { const sp = document.createElement('span'); sp.className = 'numeral'; sp.setAttribute('aria-hidden', 'true'); sp.textContent = arN(n); head.insertBefore(sp, head.firstChild); }
      const b = { id: pid + '#' + art.id, p: pid, a: art.id, title: ($('h3', art) || {}).textContent.trim(), sec: (art.closest('.sec') ? (($('h2', art.closest('.sec')) || {}).textContent || '') : '') };
      reg.set(art, b);
      const tools = document.createElement('div'); tools.className = 'tools';
      tools.innerHTML = '<button type="button" data-q aria-pressed="false">＋ Queue for video</button><button type="button" class="draft" data-d>✎ Draft a reel</button><button type="button" data-c>Copy brief</button><button type="button" data-l>Copy link</button>';
      head.appendChild(tools);
      $('[data-q]', tools).addEventListener('click', () => qToggle(b));
      $('[data-d]', tools).addEventListener('click', () => openDraft(art, b));
      $('[data-c]', tools).addEventListener('click', () => copy(briefText(art), 'Brief copied'));
      $('[data-l]', tools).addEventListener('click', () => copy(location.href.split('#')[0] + '#' + art.id, 'Link copied'));
      const f = flags[b.id];
      let anchorEl = head;
      if (f) {
        const n2 = document.createElement('div'); n2.className = 'rnote' + (f.level === 'care' ? '' : ' info');
        n2.innerHTML = '<b>' + esc(f.level === 'care' ? 'Reviewer note' : 'Note') + '</b><span>' + esc(f.text) + (f.source ? ' <em>(' + esc(f.source) + ')</em>' : '') + '</span>';
        head.after(n2); anchorEl = n2;
      }
      const ex = document.createElement('div'); ex.className = 'exp'; ex.innerHTML = '<button type="button">Show the full argument</button>';
      $('button', ex).addEventListener('click', () => { art.classList.toggle('open'); $('button', ex).textContent = art.classList.contains('open') ? 'Back to the short version' : 'Show the full argument'; });
      anchorEl.after(ex);
    });
    $$('.obj .q').forEach(q => q.addEventListener('click', () => { if (document.body.classList.contains('m-drill')) q.parentElement.classList.toggle('show'); }));
    const syncQ = () => reg.forEach((b, art) => { const on = qHas(b); art.classList.toggle('queued', on); const btn = $('[data-q]', art); btn.setAttribute('aria-pressed', String(on)); btn.textContent = on ? '✓ In the video queue' : '＋ Queue for video'; });
    Q.subs.push(syncQ); syncQ();

    // reading progress + current item in contents
    const bar = document.createElement('div'); bar.className = 'rprog'; document.body.appendChild(bar);
    addEventListener('scroll', () => { const h = document.documentElement; const p = h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight); bar.style.width = (p * 100).toFixed(1) + '%'; }, { passive: true });
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(es => {
        es.forEach(e => { if (e.isIntersecting) { $$('.toc a.cur').forEach(a => a.classList.remove('cur')); $$('.toc a[data-arg="' + e.target.id + '"]').forEach(a => a.classList.add('cur')); } });
      }, { rootMargin: '-20% 0px -70% 0px' });
      briefs.forEach(b => io.observe(b));
    }
    // keyboard: j/k next/previous, x studied, q queue
    let cur = -1;
    const go = i => { cur = Math.max(0, Math.min(briefs.length - 1, i)); briefs.forEach(b => b.classList.remove('focus')); briefs[cur].classList.add('focus'); briefs[cur].scrollIntoView({ block: 'start' }); history.replaceState(null, '', '#' + briefs[cur].id); };
    document.addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey || /^(INPUT|TEXTAREA|SELECT)$/.test((e.target || {}).tagName || '')) return;
      if (e.key === 'j') { go(cur + 1); } else if (e.key === 'k') { go(cur < 0 ? 0 : cur - 1); }
      else if (e.key === 'x' && cur >= 0) { $('.done input', briefs[cur]).click(); }
      else if (e.key === 'q' && cur >= 0) { qToggle(reg.get(briefs[cur])); }
    });
    const flash = () => { const t = location.hash && document.getElementById(location.hash.slice(1)); if (t && t.classList.contains('brief')) { cur = briefs.indexOf(t); briefs.forEach(b => b.classList.remove('focus')); t.classList.add('focus'); } };
    addEventListener('hashchange', flash); flash();
  }

  window.DA2 = { $, $$, store, esc, arN, toast, copy, loadIdx, search, smartSearch, hasAr, mark, href, prep, norm, tokens, mountBar, openPal, Q, qToggle, qHas, openQueue, getSample, openDlg, closeDlg, enhancePart, STYLES };
  initDb();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', enhancePart); else enhancePart();
})();
