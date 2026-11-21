import { chromium } from 'playwright';

const BASE = process.env.BASE || 'http://127.0.0.1:5173';
const routes = ['/', '/login', '/admin/login'];

const browser = await chromium.launch();
const results = [];

for (const route of routes) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];

  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 300)); });
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 400)));
  page.on('requestfailed', (r) => failedRequests.push(`${r.method()} ${r.url()} :: ${r.failure()?.errorText}`));

  let status = null;
  try {
    const resp = await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle', timeout: 45000 });
    status = resp?.status() ?? null;
    await page.waitForTimeout(1500);
  } catch (e) {
    pageErrors.push('NAVIGATION: ' + String(e).slice(0, 300));
  }

  const rootHtmlLen = await page.evaluate(() => document.getElementById('root')?.innerHTML?.length ?? -1).catch(() => -1);
  const text = (await page.evaluate(() => document.body?.innerText ?? '').catch(() => '')).trim();
  const file = `preview-${route.replace(/\W+/g, '_') || 'home'}.png`;
  await page.screenshot({ path: file, fullPage: false }).catch(() => {});

  results.push({ route, status, rootHtmlLen, textSnippet: text.slice(0, 220), consoleErrors, pageErrors, failedRequests, file });
  await ctx.close();
}

await browser.close();

for (const r of results) {
  console.log('='.repeat(70));
  console.log(`ROUTE ${r.route}  status=${r.status}  #root_innerHTML=${r.rootHtmlLen}`);
  console.log(`VISIBLE TEXT: ${r.textSnippet ? JSON.stringify(r.textSnippet) : '(EMPTY — nothing rendered)'}`);
  console.log(`PAGE ERRORS: ${r.pageErrors.length}`); r.pageErrors.forEach((e) => console.log('   ! ' + e));
  console.log(`CONSOLE ERRORS: ${r.consoleErrors.length}`); r.consoleErrors.forEach((e) => console.log('   ! ' + e));
  console.log(`FAILED REQUESTS: ${r.failedRequests.length}`); r.failedRequests.forEach((e) => console.log('   ! ' + e));
  console.log(`screenshot: ${r.file}`);
}
const bad = results.filter((r) => r.rootHtmlLen <= 0 || r.pageErrors.length);
console.log('='.repeat(70));
console.log(bad.length ? `RESULT: ${bad.length}/${results.length} route(s) FAILED TO RENDER` : `RESULT: all ${results.length} routes rendered with no page errors`);
process.exit(bad.length ? 1 : 0);
