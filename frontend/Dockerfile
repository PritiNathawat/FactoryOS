# FactoryOS Frontend — Production Dockerfile
# ===========================================
# Multi-stage build for Next.js with standalone output mode.
#
# Stage 1 (deps):    Install node_modules
# Stage 2 (builder): Build the Next.js production bundle
# Stage 3 (runtime): Lean production image with standalone output only

# ── Stage 1: Dependencies ─────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production=false

# ── Stage 2: Build ────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

ARG BACKEND_INTERNAL_URL=http://backend:8000
ENV BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL}

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the production Next.js bundle
RUN npm run build

# ── Stage 3: Runtime ──────────────────────────────────────────
FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Create non-root user
RUN addgroup --gid 1001 --system nodejs && \
    adduser --system --uid 1001 nextjs

# Copy the standalone build output (requires output: 'standalone' in next.config.ts)
# If not using standalone, copy .next/ and public/ instead
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "server.js"]
