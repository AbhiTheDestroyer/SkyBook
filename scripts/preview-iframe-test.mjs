import { chromium } from 'playwright';

// Reproduces the preview panel's environment: the app loaded inside a sandboxed
// iframe. Uses CDP (via Playwright frame.evaluate) to inspect the frame contents
// even though a sandboxed frame has an opaque origin the parent cannot reach.
const BASE = process.env.BASE || 'http://127.0.0.1:5173';

const scenarios = [
  { name: 'sandbox="allow-scripts"          (likely preview panel)', attrs: 'sandbox="allow-scripts"' },
  { name: 'sandbox="allow-scripts allow-same-origin"', attrs: 'sandbox="allow-scripts allow-same-origin"' },
  { name: 'no sandbox (plain iframe)', attrs: '' },
];

const browser = await chromium.launch();

for (const s of scenarios) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 } });
  const page = await ctx.newPage();
  const log = [];

  page.on('pageerror', (e) => log.push('PAGEERROR: ' + String(e).slice(0, 240)));
  page.on('console', (m) => {
    if (m.type() === 'error') log.push('CONSOLE: ' + m.text().slice(0, 200));
  });
  page.on('requestfailed', (r) => log.push('REQFAIL: ' + r.method() + ' ' + r.url().slice(0, 90)));

  // Harvest HTTP statuses for any 403/401 the app receives
  const statuses = [];
  page.on('response', (r) => {
    const u = new URL(r.url()).pathname;
    if (r.status() >= 400) statuses.push(r.status() + ' ' + u);
  });

  await page.setContent(
    `<!doctype html><html><body style="margin:0">
       <iframe ${s.attrs} src="${BASE}/" style="width:1280px;height:860px;border:0"></iframe>
     </body></html>`,
    { waitUntil: 'domcontentloaded' }
  );

  await page.waitForTimeout(9000);

  // Inspect inside the sandboxed frame via CDP (works despite opaque origin)
  let rootLen = null, text = '', cookieOk = null, lsOk = null;
  const frame = page.frames().find((f) => f.url().startsWith(BASE));
  if (frame) {
    rootLen = await frame.evaluate(() => document.getElementById('root')?.innerHTML?.length ?? -1).catch((e) => 'ERR:' + e.message.slice(0, 60));
    text = await frame.evaluate(() => (document.body?.innerText || '').trim().slice(0, 160)).catch(() => '');
    cookieOk = await frame.evaluate(() => { try { void document.cookie; return 'readable'; } catch (e) { return 'THROWS: ' + e.name; } }).catch(() => 'n/a');
    lsOk = await frame.evaluate(() => { try { void localStorage.length; return 'readable'; } catch (e) { return 'THROWS: ' + e.name; } }).catch(() => 'n/a');
  }

  console.log('='.repeat(72));
  console.log('SCENARIO: ' + s.name);
  console.log('  frame found     : ' + (frame ? frame.url().slice(0, 60) : 'NONE'));
  console.log('  #root innerHTML : ' + rootLen);
  console.log('  document.cookie : ' + cookieOk);
  console.log('  localStorage    : ' + lsOk);
  console.log('  visible text    : ' + (text ? JSON.stringify(text) : '(EMPTY - BLANK PAGE)'));
  console.log('  http >=400      : ' + (statuses.length ? [...new Set(statuses)].join(', ') : 'none'));
  console.log('  errors          : ' + (log.length ? '' : 'none'));
  [...new Set(log)].slice(0, 6).forEach((l) => console.log('      ' + l));

  await page.screenshot({ path: `iframe-${s.name.replace(/[^a-z0-9]+/gi, '_').slice(0, 28)}.png` }).catch(() => {});
  await ctx.close();
}

await browser.close();
