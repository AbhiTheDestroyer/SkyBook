#!/usr/bin/env bash
# SkyBook single-port preview on 3001 (UI + API from one server).
#
# Why: in `npm run dev` the API only serves /api and Vite owns the UI on 5173.
# Setting SERVE_FRONTEND=true makes the Express server also serve the built
# frontend, so everything is reachable on 3001 alone.
#
# node_modules/ and dist/ are excluded from workspace snapshots, so both are
# rebuilt here on demand. data/skybook.db persists and is never touched.
#
# Usage:  bash scripts/start-app-3001.sh [PORT]
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${1:-3001}"

echo "[1/5] Checking dependencies..."
if [ ! -x node_modules/.bin/tsx ]; then
  echo "      node_modules missing -> npm ci"
  npm ci --no-audit --no-fund
else
  echo "      node_modules OK ($(ls node_modules | wc -l) packages)"
fi

echo "[2/5] Freeing port ${PORT}..."
pids=$(ss -ltnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | sort -u || true)
if [ -n "${pids:-}" ]; then
  echo "      killing stale pids: $pids"
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  sleep 1
else
  echo "      port free"
fi

echo "[3/5] Checking frontend build..."
if [ -f dist/index.html ]; then
  echo "      dist/ present"
else
  echo "      dist/ missing -> npm run build"
  npm run build
fi

echo "[4/5] Checking database..."
if [ -f data/skybook.db ]; then
  echo "      data/skybook.db present ($(du -h data/skybook.db | cut -f1))"
else
  echo "      no database yet - it will be created and seeded on boot"
fi

echo "[5/5] Starting single-port server on ${PORT}..."
if [ -n "${E2B_SANDBOX_ID:-}" ]; then
  echo "      LIVE PREVIEW -> https://${PORT}-${E2B_SANDBOX_ID}.e2b.app"
else
  echo "      LIVE PREVIEW -> http://localhost:${PORT}/"
fi

export PORT
export ENABLE_DEV_SESSIONS=true   # keeps demo logins working for previews
export SERVE_FRONTEND=true        # API server also serves the built UI
exec npx tsx server/index.ts
