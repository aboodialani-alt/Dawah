import { createRequire } from 'module'; import fs from 'fs'; import http from 'http';
const require = createRequire('/opt/node22/lib/node_modules/'); const { chromium } = require('playwright');
const html = fs.readFileSync('site/index.html', 'utf8');
const titles = JSON.parse(html.match(/const DA_TITLES = (\[.*?\]);\n/s)[1]);
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const ctx = await b.newContext({ viewport: { width: 1300, height: 1000 } });
const t0 = titles[3];
await ctx.addInitScript(({ t0 }) => {
  localStorage.setItem('sb:room', 'claims');
  const sample = async () => ({ text: '' }); sample.json = async () => ({ claims: [
    { text: 'The hadith were only written two hundred years after the Prophet.', who: '', lang: 'en', priority: 1, da: t0 },
    { text: 'Some brand new claim nobody has answered.', who: 'Speaker X', lang: 'en', priority: 2, da: 'not a real title' }] });
  window.claude = { use: async n => n === 'sample' ? sample : null };
}, { t0 });
const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); r.end(html); }).listen(0);
const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
await p.goto('http://127.0.0.1:' + srv.address().port + '/'); await p.waitForTimeout(400);
await p.fill('#in-text', 'x'.repeat(60)); await p.click('#in-go'); await p.waitForTimeout(500);
console.log('rows', await p.locator('#in-out tbody tr').count(), 'gap chips', await p.locator('#in-out .chip').count());
await p.click('#in-log'); await p.waitForTimeout(300);
console.log('claims table rows', await p.locator('section.card.wrapx tbody tr').count());
await p.click('[data-room=overview]'); await p.waitForTimeout(300);
console.log('gap card', await p.locator('text=Gaps in the library').count());
await p.screenshot({ path: process.argv[2] || 'intake.png' });
console.log(errs.length ? errs : 'no page errors');
await b.close(); srv.close();
