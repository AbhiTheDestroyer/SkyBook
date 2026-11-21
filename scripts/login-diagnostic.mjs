import { chromium } from 'playwright';

// Reproduces the reported "always invalid credentials" by performing REAL logins
// and reporting the exact HTTP status + response body + on-screen error text.
const BASE = process.env.BASE || 'http://127.0.0.1:3001';

const CUSTOMER = { email: 'customer@skybook.com', password: 'SkyBook@123' };
const ADMIN = { email: 'admin@skybook.com', password: 'SkyBook@Admin123' };
const SUPER = { email: 'superadmin@skybook.com', password: 'SkyBook@Super123' };

const browser = await chromium.launch();

async function attempt({ label, path, creds, frameMode }) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const calls = [];
  const errs = [];

  page.on('pageerror', (e) => errs.push('PAGEERROR: ' + String(e).slice(0, 200)));
  page.on('response', async (r) => {
    if (r.url().includes('/api/auth/')) {
      let body = '';
      try { body = (await r.text()).slice(0, 200); } catch {}
      calls.push(`${r.status()} ${new URL(r.url()).pathname} :: ${body}`);
    }
  });

  if (frameMode === 'plain') {
    await page.goto(BASE + path, { waitUntil: 'networkidle', timeout: 40000 });
  } else {
    const attrs = frameMode === 'sandbox-opaque'
      ? 'sandbox="allow-scripts"'
      : 'sandbox="allow-scripts allow-same-origin"';
    await page.setContent(
      `<!doctype html><body style="margin:0"><iframe ${attrs} src="${BASE}${path}" style="width:1280px;height:900px;border:0"></iframe></body>`,
      { waitUntil: 'domcontentloaded' }
    );
    await page.waitForTimeout(6000);
  }

  const target = frameMode === 'plain'
    ? page
    : page.frames().find((f) => f.url().startsWith(BASE));

  let uiText = '';
  try {
    if (size(target)) {
      await target.fill('input[type=email]', creds.email).catch(() => {});
      await target.fill('input[type=password]', creds.password).catch(() => {});
      await target.click('button.primary').catch(() => {});
      await page.waitForTimeout(4000);
      uiText = (await target.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ').trim();
    }
  } catch (e) {
    errs.push('INTERACT: ' + String(e).slice(0, 160));
  }

  const errorShown = /Invalid email or password|Too many login attempts|does not have administrative access|failed/i.test(uiText)
    ? (uiText.match(/(Invalid email or password[^.]*\.|Too many login attempts[^.]*\.|[^.]*administrative access\.)/) || ['(error shown)'])[0]
    : null;

  console.log('='.repeat(72));
  console.log(`CASE: ${label}`);
  console.log(`  mode            : ${frameMode}`);
  console.log(`  auth API calls  : ${calls.length ? '' : 'NONE REACHED SERVER'}`);
  calls.forEach((c) => console.log('      ' + c));
  console.log(`  error on screen : ${errorShown ? '"' + errorShown + '"' : 'none'}`);
  console.log(`  landed on       : ${uiText.includes('control center') || uiText.includes('CONTROL CENTER') ? 'ADMIN DASHBOARD' : uiText.includes('Passenger sign in') || uiText.includes('Customer sign in') ? 'still on login page' : uiText.slice(0, 70)}`);
  if (errs.length) errs.slice(0, 3).forEach((e) => console.log('      ' + e));

  await ctx.close();
  return { errorShown, calls, errs };
}

function size(t) { return !!t; }

const results = [];
results.push(await attempt({ label: 'Customer login, normal page', path: '/login', creds: CUSTOMER, frameMode: 'plain' }));
results.push(await attempt({ label: 'Customer login, sandboxed iframe (preview panel)', path: '/login', creds: CUSTOMER, frameMode: 'sandbox-opaque' }));
results.push(await attempt({ label: 'Admin login, normal page', path: '/admin/login', creds: ADMIN, frameMode: 'plain' }));
results.push(await attempt({ label: 'Admin login, sandboxed iframe', path: '/admin/login', creds: ADMIN, frameMode: 'sandbox-opaque' }));
results.push(await attempt({ label: 'Super Admin login, normal page', path: '/admin/login', creds: SUPER, frameMode: 'plain' }));

await browser.close();

console.log('\n' + '='.repeat(72));
const failing = results.filter((r) => r.errorShown);
console.log(`SUMMARY: ${results.length - failing.length}/${results.length} cases logged in without an error`);
if (failing.length) console.log(`FAILING CASES: ${failing.length}`);
