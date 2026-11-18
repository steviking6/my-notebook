# Next.js frontend image (local docker compose + Cloud Run).

# ---- 1. Build ----
FROM node:26-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- 2. Run: only the standalone output (no dev dependencies, no source) ----
FROM node:26-slim
WORKDIR /app
ENV NODE_ENV=production \
    PORT=8080 \
    HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static

# BACKEND_URL and APP_API_KEY are read at runtime (server side only),
# so the same image works locally and on Cloud Run.
USER node
CMD ["node", "server.js"]
