import { createRequire } from 'module'; import http from 'http'; import fs from 'fs'; import path from 'path';
const require = createRequire('/opt/node22/lib/node_modules/'); const { chromium } = require('playwright');
const site = process.argv[2];
const srv = http.createServer((q, r) => { const f = path.join(site, q.url.split('?')[0].replace(/^\//, '') || 'index.html'); if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'content-type': f.endsWith('.json') ? 'application/json' : 'text/html; charset=utf-8' }); r.end(fs.readFileSync(f)); }).listen(0);
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const ctx = await b.newContext({ viewport: { width: 1300, height: 900 } });
await ctx.addInitScript(() => { const s = async () => ({ text: 'The hadith were only written down two hundred years after the Prophet.' }); window.claude = { use: async n => n === 'sample' ? s : null }; });
const p = await ctx.newPage(); p.setDefaultTimeout(4000); const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => console.log('console:', m.type(), m.text().slice(0, 200)));
await p.goto(`http://127.0.0.1:${srv.address().port}/index.html`); await p.waitForTimeout(500);
await p.fill('#fq', 'الأحاديث كُتبت بعد مئتي سنة من وفاة النبي'); await p.waitForTimeout(1600);
console.log('via line:', await p.locator('#results .note-s').first().innerText().catch(() => 'none'));
console.log('result cards:', await p.locator('#results .res').count());
console.log('first:', (await p.locator('#results .res .q, #results .res h3').first().innerText().catch(() => 'none')).slice(0, 100));
// palette
console.log('html results:', (await p.locator('#results').innerHTML()).slice(0, 300)); await p.keyboard.press('Escape'); await p.click('h1'); await p.keyboard.press('/'); await p.waitForTimeout(200);
await p.fill('#pal-q', 'الأحاديث كُتبت متأخرة'); await p.waitForTimeout(1500);
console.log('palette items:', await p.locator('.pal-item').count());
console.log(errs.length ? errs : 'no page errors');
await b.close(); srv.close();
