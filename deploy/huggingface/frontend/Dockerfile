# =============================================================================
# FRONTEND — Hugging Face Spaces Dockerfile
# =============================================================================
# Builds and serves the Next.js frontend. Connects to the backend HF Space
# via NEXT_PUBLIC_API_URL environment variable.
# HF Spaces expects port 7860 by default.
# =============================================================================

FROM node:20-alpine AS builder

WORKDIR /app

COPY services/frontend/package.json services/frontend/package-lock.json* ./
RUN npm ci

COPY services/frontend/ .

# Build-time env: point to backend HF Space
# Users must replace this with their actual backend Space URL
ARG NEXT_PUBLIC_API_URL=https://iqraawan451512-todo-chatbot-backend.hf.space/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_USER_ID=default-user

RUN npm run build

# --- Production stage ---
FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/package.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public 2>/dev/null || true

EXPOSE 7860

# Next.js start on HF Spaces port
CMD ["npx", "next", "start", "-p", "7860"]
