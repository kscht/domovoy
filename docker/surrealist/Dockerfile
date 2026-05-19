ARG SURREALIST_VERSION=surrealist-v3.8.5

# ── Stage 1: build ───────────────────────────────────────────────────────────
FROM oven/bun:1-alpine AS builder

ARG SURREALIST_VERSION

RUN apk add --no-cache git

RUN git clone --depth 1 \
    --branch ${SURREALIST_VERSION} \
    https://github.com/surrealdb/surrealist.git /app

WORKDIR /app

RUN bun install --frozen-lockfile

# Surrealist использует Vite — стандартный build даёт web-сборку в dist/
RUN bun run build 2>/dev/null || bun run build:web

# ── Stage 2: serve ────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
