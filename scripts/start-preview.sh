#!/usr/bin/env bash
# Self-healing SkyBook preview launcher.
#
# Why this exists: node_modules/ is excluded from workspace snapshots, so it is
# wiped between sessions. Without this, every restart fails with
# "concurrently: not found" or "tsc: not found".
#
# Usage:  bash scripts/start-preview.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/4] Checking dependencies..."
if [ ! -d node_modules ] || [ ! -x node_modules/.bin/concurrently ]; then
  echo "      node_modules missing/incomplete -> npm ci"
  npm ci --no-audit --no-fund
else
  echo "      node_modules OK ($(ls node_modules | wc -l) packages)"
fi

echo "[2/4] Freeing preview ports 5173 / 3001..."
for p in 5173 3001; do
  pids=$(ss -ltnp 2>/dev/null | grep ":$p " | grep -oP 'pid=\K[0-9]+' | sort -u || true)
  if [ -n "${pids:-}" ]; then
    echo "      killing stale pids on $p: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
  fi
done

echo "[3/4] Checking database..."
if [ -f data/skybook.db ]; then
  echo "      data/skybook.db present ($(du -h data/skybook.db | cut -f1))"
else
  echo "      no database found - it will be created and seeded on boot"
fi

echo "[4/4] Starting dev stack (Vite 5173 + API 3001)..."
# Sandbox IDs change between sessions, so any previously shared preview URL can
# silently point at a dead host. Print the CURRENT one instead of hardcoding it.
if [ -n "${E2B_SANDBOX_ID:-}" ]; then
  echo "      LIVE PREVIEW -> https://5173-${E2B_SANDBOX_ID}.e2b.app"
else
  echo "      LIVE PREVIEW -> http://localhost:5173/ (no E2B_SANDBOX_ID set)"
fi

exec npm run dev
