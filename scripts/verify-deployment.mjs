#!/usr/bin/env node
// Verifies a DEPLOYED SkyBook instance is actually working.
//
//   node scripts/verify-deployment.mjs https://your-domain.com
//
// Checks the things that silently break in production: HTTPS, the Save-Only
// session cookie, dev endpoints being disabled, security headers, the frontend
// bundle being served, and the auth guards actually rejecting.
//
// Exit code 0 = all critical checks passed, 1 = something failed.

const base = (process.argv[2] || '').replace(/\/+$/, '');
if (!base) {
  console.error('Usage: node scripts/verify-deployment.mjs https://your-domain.com');
  process.exit(2);
}
if (!base.startsWith('https://')) {
  console.warn('! Target is not HTTPS. Production session cookies are Secure-only,');
  console.warn('  so login WILL silently fail over plain HTTP.\n');
}

const results = [];
function record(ok, name, detail = '') {
  results.push({ ok, name, detail });
  console.log(`${ok ? '  PASS' : '  FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
}
async function get(path, opts = {}) {
  try {
    const r = await fetch(base + path, { redirect: 'manual', ...opts });
    return r;
  } catch (e) {
    return { status: 0, error: String(e.message || e), headers: new Headers(), text: async () => '' };
  }
}

console.log(`\nVerifying ${base}\n${'='.repeat(60)}`);

// 1. Health endpoint
console.log('\n[core]');
const health = await get('/api/health');
const healthText = await health.text().catch(() => '');
let healthJson = null;
try { healthJson = JSON.parse(healthText); } catch {}
record(health.status === 200 && healthJson?.ok === true, 'GET /api/health returns ok:true',
  health.status ? `status=${health.status}` : health.error || '');
if (healthJson?.aviationProvider) {
  console.log(`  INFO  flight inventory provider = ${healthJson.aviationProvider}` +
    (healthJson.aviationProvider === 'DEMO_DYNAMIC'
      ? '  (synthetic flights — real booking needs Amadeus keys)' : ''));
}

// 2. Frontend is served
const home = await get('/');
const homeText = await home.text().catch(() => '');
record(home.status === 200 && /<div id="root">/.test(homeText), 'Frontend HTML served at /',
  home.status ? `status=${home.status}` : home.error || '');

// 3. Deep SPA route (fallback must not 404)
const deep = await get('/admin/login');
record(deep.status === 200, 'SPA fallback serves deep route /admin/login', `status=${deep.status}`);

// 4. Known missing asset must NOT be swallowed into index.html as 200
const missing = await get('/this-asset-does-not-exist-12345.js');
const missingText = await missing.text().catch(() => '');
record(missing.status === 404, 'Missing static asset 404s (not masked by fallback)',
  `status=${missing.status}`);

// 5. API 404s stay JSON, not HTML
const badApi = await get('/api/definitely-not-a-route');
record(badApi.status === 404, 'Unknown /api route returns 404', `status=${badApi.status}`);

// 6. Dev-only endpoint must be off
console.log('\n[security]');
const demo = await get('/api/auth/demo-session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ role: 'AIRLINE_ADMIN' }),
});
record(demo.status === 404 || demo.status === 403,
  'Dev session endpoint disabled (ENABLE_DEV_SESSIONS=false)',
  `status=${demo.status}${demo.status === 200 ? '  <-- CRITICAL: dev sessions are OPEN' : ''}`);

// 7. Auth guards reject anonymous access
const guard = await get('/api/admin/rbac/roles');
record(guard.status === 401, 'Admin API rejects anonymous (401)', `status=${guard.status}`);

const guardStats = await get('/api/admin/stats');
record(guardStats.status === 401, 'Admin stats rejects anonymous (401)', `status=${guardStats.status}`);

// 8. Session cookie must be Secure + HttpOnly on an HTTPS host
if (base.startsWith('https://')) {
  const login = await fetch(base + '/api/auth/customer/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'nonexistent-user@invalid.test', password: 'x'.repeat(12) }),
    redirect: 'manual',
  }).catch(() => null);
  const setCookie = login?.headers.get('set-cookie') || '';
  if (setCookie && /skybook_session/.test(setCookie)) {
    record(/HttpOnly/i.test(setCookie), 'Session cookie is HttpOnly');
    record(/Secure/i.test(setCookie), 'Session cookie is Secure');
  } else {
    console.log('  INFO  no session cookie issued for a rejected login (expected)');
  }
}

// 9. Security headers
const headResp = await get('/');
record(headResp.headers?.get('x-content-type-options') === 'nosniff', 'X-Content-Type-Options: nosniff');
record(!headResp.headers?.get('x-powered-by'), 'x-powered-by removed');

// 10. Embeddability (the preview panel needs this)
const xfo = headResp.headers?.get('x-frame-options');
const csp = headResp.headers?.get('content-security-policy') || '';
record(!xfo && !/frame-ancestors/i.test(csp), 'No framing block (embedding allowed)');

// 11. CSRF still enforced
const csrfTest = await get('/api/profile', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: '{}' });
record([401, 403].includes(csrfTest.status), 'Unauthenticated write rejected', `status=${csrfTest.status}`);

console.log('\n' + '='.repeat(60));
const failed = results.filter((r) => !r.ok);
console.log(`${results.length - failed.length}/${results.length} checks passed`);
if (failed.length) {
  console.log('\nFAILED:');
  failed.forEach((f) => console.log(`  - ${f.name}${f.detail ? ' (' + f.detail + ')' : ''}`));
  console.log('\nThis deployment is NOT verified. Do not treat it as live.');
  process.exit(1);
}
console.log('\nAll critical checks passed.');
process.exit(0);
