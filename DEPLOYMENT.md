# Making SkyBook Permanently Live

> **Read this first.** A permanent deployment needs a host you control. Nothing
> running inside this chat sandbox can be permanent: the sandbox is wiped between
> sessions, and background processes stop. Everything below is prepared, tested
> and ready — the only missing piece is a host account.

---

## TL;DR — pick one

| Option | Permanence | Cost | Data survives restarts? | Effort |
|---|---|---|---|---|
| **A. VPS + Docker Compose + Caddy** | ✅ truly permanent | ~$5/mo | ✅ named volume | ~10 min |
| **B. Render (paid plan)** | ✅ permanent | $7/mo+ | ✅ only with paid disk | ~5 min |
| **C. Fly.io + volume** | ✅ permanent | ~$2–5/mo | ✅ volume | ~10 min |
| **D. Render/Railway FREE tier** | ⚠️ demo only | $0 | ❌ **erased on every restart** | ~5 min |

**Recommendation: Option A.** It is the only one that gives you automatic HTTPS,
persistent data, and no vendor lock-in, and all the config is already written.

---

## Option A — VPS + Docker Compose + Caddy (recommended)

You need: a VPS (Hetzner/DigitalOcean/Linode, ~$5/mo), a domain, and ports 80 + 443 open.

```bash
# On the VPS
git clone <your-repo> /opt/skybook && cd /opt/skybook

cat > .env <<'EOF'
DOMAIN=skybook.yourdomain.com
SKYBOOK_ADMIN_PASSWORD=<a long random value>
EOF

docker compose up -d
```

Caddy obtains and renews the Let's Encrypt certificate automatically. HTTPS is
**mandatory, not optional** — production session cookies are `Secure`, so login
silently fails over plain HTTP.

Data lives in the `skybook-data` volume and survives restarts, redeploys and
reboots. **Do not delete that volume** — it holds every user, booking and waitlist entry.

Verify it:

```bash
node scripts/verify-deployment.mjs https://skybook.yourdomain.com
```

---

## Option B — Render (Blueprint included)

`render.yaml` is ready. Push to GitHub → Render → **New → Blueprint**.

**You must use a paid instance type.** Render's free tier has an ephemeral
filesystem, so the SQLite database is erased on every deploy and restart. The
`disk:` block in `render.yaml` requires a paid plan.

Set `SKYBOOK_ADMIN_PASSWORD` and `CORS_ORIGIN` (your Render URL) in the dashboard.

---

## Option C — Fly.io (config included)

```bash
fly launch --no-deploy
fly volumes create skybook_data --size 1 --region bom
fly secrets set SKYBOOK_ADMIN_PASSWORD='<long-random-value>'
fly deploy
```

`fly.toml` is ready, including the volume mount at `/data` and a health check.
Fly terminates TLS for you.

---

## Option D — free tier (temporary only)

Works for a demo you don't mind losing. On Render's free tier, or any host without
a persistent disk, **every restart erases all data** — accounts, bookings, waitlists.
Say so to anyone you show it to. Use `Procfile` / `render.yaml` as-is but drop the
`disk:` block.

---

## What I fixed to make permanent deployment real

| Fix | Why it mattered |
|---|---|
| `PORT` env support | Was hardcoded to 3001; hosts inject their own port, so the app would never have received traffic |
| Server serves the built frontend | No `express.static` existed; UI and API were separate deployments |
| `SKYBOOK_DB_PATH` | DB path was hardcoded to `./data/` — ephemeral on most hosts |
| `CORS_ORIGIN` | CORS was wide open |
| `TRUST_PROXY` | Behind a proxy every visitor shares one IP; the login rate limiter would lock everyone out together |
| Removed `x-powered-by`, added `nosniff` + `Referrer-Policy` | Baseline hygiene for a public host |
| `SKYBOOK_DEMO_USERS=false` | Demo accounts were seeded with a **published password**; now they get unguessable ones |
| `tsx` moved to dependencies | Hosts that prune dev dependencies could not start the server |
| Missing assets now 404 | The SPA fallback returned `200 index.html` for missing `.js` files, causing MIME errors and bad caching |

### Verified in production mode (not dev)

```
node scripts/verify-deployment.mjs http://127.0.0.1:4100
12/12 checks passed
```

- `/api/health` ok, frontend served, SPA deep routes work
- Missing asset → **404** (caught by the verifier as a real bug, then fixed)
- Unknown `/api` route → 404 JSON, not HTML
- `/api/auth/demo-session` → **404** with `ENABLE_DEV_SESSIONS=false`
- Admin APIs → **401** anonymous
- Bootstrap admin login works with `SKYBOOK_ADMIN_PASSWORD`; wrong password → 401
- `passengerx@demo.com` / `Passenger@123` → **401** with `SKYBOOK_DEMO_USERS=false`
- `nosniff` set, `x-powered-by` removed, no framing block

### Still NOT verified — stated plainly

- **The Docker image has never been built.** Docker is unavailable in the sandbox.
- **`docker-compose.yml` and `Caddyfile` have never been run.** Same reason.
- **No real host, no real domain, no real TLS.** All testing was localhost.
- **No backup/restore drill.** SQLite is one file — back it up, and test a restore.

---

## Honest blockers before real customers can pay you

1. **Flights are synthetic.** `/api/health` reports `DEMO_DYNAMIC`. Wire `AMADEUS_API_KEY` /
   `AMADEUS_API_SECRET` or users book flights that do not exist.
2. **Payments fail closed.** No Razorpay keys → checkout disabled. It never fakes success.
3. **No email/SMS/push.** Booking confirmations never leave the app.
4. **SQLite suits one small node.** Not multiple instances or real concurrency. Move to
   Postgres before genuine traffic.
5. **`/api/demo/reset` can wipe the database.** Admin-only and confirmation-gated, but
   consider removing it from production builds.

---

## Go-live checklist

- [ ] `NODE_ENV=production`, `ENABLE_DEV_SESSIONS=false`
- [ ] `SKYBOOK_ADMIN_PASSWORD` set (strong, unique)
- [ ] `SKYBOOK_DEMO_USERS=false` on any public host
- [ ] `TRUST_PROXY=1` when behind Caddy/Render/Fly
- [ ] Persistent volume mounted at `/data`; `SKYBOOK_DB_PATH=/data/skybook.db`
- [ ] HTTPS working and you have **logged in successfully in a browser**
- [ ] `CORS_ORIGIN` set to your real domain
- [ ] `node scripts/verify-deployment.mjs https://your-domain` → 12/12
- [ ] Database backup scheduled, and a restore tested
