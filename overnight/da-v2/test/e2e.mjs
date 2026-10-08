import { createRequire } from 'module'; import http from 'http'; import fs from 'fs'; import path from 'path';
const require = createRequire('/opt/node22/lib/node_modules/'); const { chromium } = require('playwright');
const site = process.argv[2];
const srv = http.createServer((q, r) => { const f = path.join(site, decodeURIComponent(q.url.split('?')[0]).replace(/^\//, '') || 'index.html'); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'content-type': f.endsWith('.json') ? 'application/json' : 'text/html; charset=utf-8' }); r.end(fs.readFileSync(f)); }).listen(0);
const base = `http://127.0.0.1:${srv.address().port}/`;
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const ctx = await b.newContext({ viewport: { width: 1300, height: 900 } });
await ctx.addInitScript(() => {
  const mem = {}, subs = {};
  const emit = n => (subs[n] || []).forEach(f => f({ docs: Object.entries(mem[n] || {}).map(([id, d]) => ({ id, data: () => d })) }));
  const col = n => ({ onSnapshot(f) { (subs[n] = subs[n] || []).push(f); setTimeout(() => emit(n), 20); return () => {}; },
    doc: id => ({ set: async d => { (mem[n] = mem[n] || {})[id] = d; emit(n); window.__db = mem; }, delete: async () => { delete (mem[n] || {})[id]; emit(n); window.__db = mem; } }) });
  const sample = async (p, o) => { const t = 'DRAFT OK ' + p.length; o && o.onText && o.onText({ text: t, delta: t }); return { text: t }; };
  sample.json = async () => ({ score: 2, hit: ['a'], missed: ['b'], tip: 'tip' });
  window.claude = { use: async n => n === 'db' ? { collection: col, doc: p => col(p.split('/')[0]).doc(p.split('/')[1]) } : n === 'sample' ? sample : null };
});
const results = []; const ok = (n, c) => results.push((c ? 'PASS ' : 'FAIL ') + n);
const p = await ctx.newPage(); p.setDefaultTimeout(5000); const errs = [];
p.on('pageerror', e => errs.push(e.message));
// part page: queue + draft + modes + copy
await p.goto(base + 'p8.html#s-gender--equal-in-worth-different-in-role'); await p.waitForTimeout(600);
await p.click('article.brief >> nth=0 >> [data-q]'); await p.waitForTimeout(200);
ok('queue counter 1', (await p.locator('.dabar .qn').innerText()) === '1');
ok('db has queue doc', await p.evaluate(() => Object.keys((window.__db || {}).queue || {}).length === 1));
await p.click('article.brief >> nth=0 >> [data-d]'); await p.waitForTimeout(200);
await p.click('#dr-go'); await p.waitForTimeout(400);
ok('draft output', (await p.locator('#dr-out').innerText()).startsWith('DRAFT OK'));
await p.keyboard.press('Escape');
await p.click('[data-mode=skim]'); ok('skim hides evidence', !(await p.locator('article.brief >> nth=0 >> .r-ev').isVisible()));
await p.click('[data-mode=drill]'); await p.click('article.brief >> nth=0 >> .obj .q'); ok('drill reveals answer', await p.locator('article.brief >> nth=0 >> .obj.show .a').first().isVisible());
await p.click('[data-mode=full]'); ok('full shows evidence', await p.locator('article.brief >> nth=0 >> .r-ev').isVisible());
await p.click('.dabar [data-queue]'); ok('queue dialog lists item', (await p.locator('.dlg .dlg-body li').count()) === 1);
await p.click('[data-rm]'); await p.waitForTimeout(200); await p.keyboard.press('Escape');
ok('queue emptied', (await p.locator('.dabar .qn').innerText()) === '0');
// hub: finder, tracks, shelf
await p.goto(base + 'index.html'); await p.waitForTimeout(800);
await p.fill('#fq', 'hadith written'); await p.waitForTimeout(500); ok('finder results', (await p.locator('#results .res').count()) > 0);
await p.click('.track >> nth=0 >> button'); ok('track opens', await p.locator('.track >> nth=0 >> ol').isVisible());
ok('five tracks', (await p.locator('.track').count()) === 5);
ok('nine tiles', (await p.locator('.tile').count()) === 9);
ok('audit card count', (await p.locator('#n-audit').innerText()) !== '0');
// drill
await p.goto(base + 'drill.html'); await p.waitForTimeout(700);
await p.fill('#mine', 'my answer is long enough'); await p.click('#rev'); ok('model answer shown', await p.locator('.ans').isVisible());
await p.keyboard.press('3'); await p.waitForTimeout(200); ok('rating advances', (await p.locator('#meter').innerText()).includes('1'));
await p.fill('#mine', 'second answer long enough'); await p.click('#grade'); await p.waitForTimeout(500); ok('grading shown', (await p.locator('.grade').innerText()).includes('Score 2'));
// review
await p.goto(base + 'review.html'); await p.waitForTimeout(700);
await p.click('#it1 [data-d=yes]'); await p.waitForTimeout(200); ok('review accepted state', (await p.locator('#it1 .state').innerText()) === 'Accepted');
ok('review decision in db', await p.evaluate(() => !!((window.__db || {}).review || {})['item-1']));
await p.click('#it2 [data-d=no]'); await p.fill('#a-hijab', 'x'); await p.click('#saveq'); await p.waitForTimeout(200);
ok('questions saved', await p.evaluate(() => !!((window.__db || {}).review || {}).questions));
// audit
await p.goto(base + 'audit.html'); await p.waitForTimeout(900);
ok('audit rows', (await p.locator('.row2').count()) > 10);
await p.click('[data-f=all]'); await p.waitForTimeout(200); ok('audit all > look', (await p.locator('#list .row2').count()) > 100);
ok('quran section', await p.locator('#qsec').isVisible());
console.log(results.join('\n')); console.log(errs.length ? 'PAGE ERRORS: ' + errs.join(' | ') : 'no page errors');
await b.close(); srv.close();
