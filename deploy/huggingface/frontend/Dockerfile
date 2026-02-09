# =============================================================================
# FRONTEND — Hugging Face Spaces Dockerfile
# =============================================================================
# Builds and serves the Next.js frontend. Connects to the backend HF Space
# via NEXT_PUBLIC_API_URL environment variable.
# HF Spaces expects port 7860 by default.
#
# NOTE: When pushing to HF Space, copy frontend files to the Space root.
#       This Dockerfile expects package.json, src/, etc. at the build context root.
# =============================================================================

FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

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

EXPOSE 7860

# Next.js start on HF Spaces port
CMD ["npx", "next", "start", "-p", "7860"]
