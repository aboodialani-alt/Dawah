import { createRequire } from 'module'; import http from 'http'; import fs from 'fs'; import path from 'path';
const require = createRequire('/opt/node22/lib/node_modules/'); const { chromium } = require('playwright');
const site = process.argv[2], out = process.argv[3];
const srv = http.createServer((q, r) => { const f = path.join(site, decodeURIComponent(q.url.split('?')[0]).replace(/^\//, '') || 'index.html'); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'content-type': f.endsWith('.json') ? 'application/json' : 'text/html; charset=utf-8' }); r.end(fs.readFileSync(f)); }).listen(0);
const base = `http://127.0.0.1:${srv.address().port}/`;
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const ctx = await b.newContext({ viewport: { width: 1200, height: 900 }, colorScheme: 'light' });
await ctx.addInitScript(() => {
  const sample = async (p, o) => ({ text: p.includes('Say the opponent') ? 'But the hadith were written two centuries later, so why trust them?' : 'Opening: why should anyone trust hadith at all?' });
  sample.json = async p => p.includes('"score"') ? { score: 7, strengths: ['clear'], gaps: ['no source'], revisit: [], drill: 'cite Bukhari 113' } : p.includes('"strong"') ? { strong: ['a'], missing: ['b'], sharper: 'say it shorter', next: 'dates' } : { covered: ['x'], missed: ['y'], tip: 't' };
  window.claude = { use: async n => n === 'sample' ? sample : null };
});
const res = []; const ok = (n, c) => res.push((c ? 'PASS ' : 'FAIL ') + n);
const p = await ctx.newPage(); p.setDefaultTimeout(6000); const errs = []; p.on('pageerror', e => errs.push(e.message));
await p.goto(base + 'learn.html'); await p.waitForTimeout(900);
ok('session built', (await p.locator('#deck .where').count()) === 1);
let seen = new Set();
for (let n = 0; n < 12 && (await p.locator('.sumr').count()) === 0; n++) {
  const kind = await p.locator('.where .pill').first().innerText(); seen.add(kind);
  if (/source/i.test(kind)) { await p.click('.opt >> nth=0'); await p.waitForTimeout(100); await p.click('#nx'); }
  else { await p.fill('#mine', 'some recalled words here'); await p.click('#rev'); await p.click('.rate [data-r="2"]'); }
  await p.waitForTimeout(80);
}
ok('three task types seen: ' + [...seen].join(' | '), seen.size === 3);
ok('summary shown', (await p.locator('.sumr').count()) === 1);
await p.screenshot({ path: out + '/learn-summary.png' });
await p.goto(base + 'learn.html'); await p.waitForTimeout(700); await p.screenshot({ path: out + '/learn-task.png' });
await p.goto(base + 'spar.html'); await p.waitForTimeout(800); await p.click('#go'); await p.waitForTimeout(500);
ok('opponent opened', (await p.locator('.msg.opp').count()) === 1);
await p.fill('#say', 'Because the sahifa of Hammam survives.'); await p.click('#send'); await p.waitForTimeout(500);
ok('reply arrived', (await p.locator('.msg.opp').count()) === 2);
await p.click('[data-c]'); await p.waitForTimeout(400); ok('coach shown', (await p.locator('.coach').count()) === 1);
await p.screenshot({ path: out + '/spar-chat.png' });
await p.click('#end'); await p.waitForTimeout(500); ok('debrief shown', (await p.locator('.deb .score').count()) === 1);
console.log(res.join('\n')); console.log(errs.length ? 'PAGE ERRORS: ' + errs.join(' | ') : 'no page errors');
await b.close(); srv.close();
