# ANALYTICA Desktop Electron App
# Build for multiple platforms using electron-builder

FROM electronuserland/builder:wine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source files
COPY electron/ ./electron/
COPY src/ ./src/
COPY pipelines/ ./pipelines/
COPY assets/ ./assets/

# Build for Linux (in Docker)
RUN npm run build:linux

# For Windows/Mac builds, use GitHub Actions or native machines

# Final stage - just copy artifacts
FROM alpine:latest
COPY --from=builder /app/dist /dist
CMD ["ls", "-la", "/dist"]
