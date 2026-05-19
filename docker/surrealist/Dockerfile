ARG SURREALIST_VERSION=surrealist-v3.8.5

# ── Stage 1: build ───────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

ARG SURREALIST_VERSION

RUN apk add --no-cache git

RUN git clone --depth 1 \
    --branch ${SURREALIST_VERSION} \
    https://github.com/surrealdb/surrealist.git /app

WORKDIR /app

RUN npm ci

# Surrealist использует Vite — стандартный build даёт web-сборку в dist/
RUN npm run build 2>/dev/null || npm run build:web

# ── Stage 2: serve ────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
