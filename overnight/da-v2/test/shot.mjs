// Screenshot + smoke test for the DA v2 site. Usage: node shot.mjs <siteDir> <outDir> <page#hash> [more pages...]
// Serves the folder over http (so fetch('idx.json') works) and stubs window.claude (db + sample).
import { createRequire } from 'module';
import http from 'http';
import fs from 'fs';
import path from 'path';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');
const [site, out, ...pages] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.js': 'text/javascript', '.css': 'text/css' };
const srv = http.createServer((q, r) => {
  const f = path.join(site, decodeURIComponent(q.url.split('?')[0].replace(/^\//, '')) || 'index.html');
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); r.end(fs.readFileSync(f));
}).listen(0);
const port = srv.address().port;
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
const stub = ({ seed, room }) => {
  const mem = JSON.parse(JSON.stringify(seed || {}));
  if (room) { try { localStorage.setItem('sb:room', room); } catch (e) {} }
  const col = name => ({
    onSnapshot(n) { const emit = () => n({ docs: Object.entries(mem[name] || {}).map(([id, d]) => ({ id, data: () => d })) }); setTimeout(emit, 30); (col._l = col._l || {})[name] = emit; return () => {}; },
    doc: id => ({
      set: async d => { (mem[name] = mem[name] || {})[id] = d; col._l && col._l[name] && col._l[name](); },
      delete: async () => { delete (mem[name] || {})[id]; col._l && col._l[name] && col._l[name](); },
      get: async () => ({ exists: !!(mem[name] || {})[id], data: () => (mem[name] || {})[id] })
    })
  });
  const sample = async (p, o) => { const t = 'HOOK: stub script\n(' + p.length + ' chars of prompt)'; o && o.onText && o.onText({ text: t, delta: t }); return { text: t, truncated: false }; };
  sample.json = async () => ({});
  window.claude = { use: async n => (n === 'db' ? { collection: col, doc: p => col(p.split('/')[0]).doc(p.split('/')[1]) } : n === 'sample' ? sample : null) };
};
const SEED = process.env.SEED;
const errs = [];
for (const spec of pages) {
  for (const [w, h, scheme, tag] of [[1440, 900, 'light', 'd-light'], [1440, 900, 'dark', 'd-dark'], [390, 844, 'dark', 'm-dark']]) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: scheme });
    await ctx.addInitScript(stub, { seed: SEED ? JSON.parse(fs.readFileSync(SEED, 'utf8')) : null, room: process.env.ROOM || null });
    const p = await ctx.newPage();
    p.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|net::|Failed to load resource/.test(m.text())) errs.push(spec + ' ' + tag + ' console: ' + m.text()); });
    p.on('pageerror', e => errs.push(spec + ' ' + tag + ' pageerror: ' + e.message));
    await p.goto(`http://127.0.0.1:${port}/${spec}`, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(Number(process.env.WAIT || 700));
    const name = spec.replace(/[^a-z0-9]/gi, '_') + '__' + tag;
    await p.screenshot({ path: path.join(out, name + '.png'), fullPage: !!process.env.FULL });
    if (spec.includes('#') && process.env.ELEMENT) { const el = await p.$('#' + spec.split('#')[1]); if (el) await el.screenshot({ path: path.join(out, name + '__el.png') }); }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    if (ov) errs.push(spec + ' ' + tag + ' horizontal overflow');
    await ctx.close();
  }
}
console.log(errs.length ? errs.join('\n') : 'no errors');
await b.close(); srv.close();
