# ---- SkyBook production image -------------------------------------------------
# Stage 1: install every dependency, build the frontend, then drop dev deps.
FROM node:20-bookworm-slim AS build
WORKDIR /app

# better-sqlite3 is a native module; these are needed if no prebuilt binary matches.
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ \
 && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build
# Keeps the compiled better-sqlite3 binding, removes vite/typescript/playwright.
RUN npm prune --omit=dev

# Stage 2: runtime only. No compilers, no build tooling.
FROM node:20-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3001
ENV SKYBOOK_DB_PATH=/data/skybook.db

# tsx is a normal dependency (it runs the TypeScript server), so no global install
# is needed here and dev-only tooling is not required at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/server ./server
COPY --from=build /app/scripts ./scripts
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/tsconfig.json ./tsconfig.json

# SQLite lives here. Mount a persistent volume at /data or all data is lost
# on every redeploy / restart / scale event.
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/api/health || exit 1

CMD ["npx", "tsx", "server/index.ts"]
