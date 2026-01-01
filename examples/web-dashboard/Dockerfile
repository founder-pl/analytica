# ANALYTICA Web Dashboard
# Multi-stage build for production

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY src/ ./src/
COPY pipelines/ ./pipelines/

# Build (if using bundler)
# RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/src /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy DSL pipelines for reference
COPY --from=builder /app/pipelines /usr/share/nginx/html/pipelines

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
