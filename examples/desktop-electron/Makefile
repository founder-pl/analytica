# ANALYTICA Desktop Electron - Makefile
# =====================================

.PHONY: help install dev build build-linux build-mac build-win clean docker-build test

# Default target
help:
	@echo "Analytica Desktop Electron"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install dependencies"
	@echo "  make setup        - Copy .env.example to .env"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run in development mode"
	@echo "  make start        - Run the app"
	@echo ""
	@echo "Build:"
	@echo "  make build        - Build for current platform"
	@echo "  make build-linux  - Build for Linux (AppImage, deb)"
	@echo "  make build-mac    - Build for macOS (dmg, zip)"
	@echo "  make build-win    - Build for Windows (nsis, portable)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Linux version in Docker"
	@echo ""
	@echo "Other:"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make test         - Run tests"

# ===========================================
# SETUP
# ===========================================

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
	else \
		echo ".env already exists"; \
	fi

install: setup
	npm install

# ===========================================
# DEVELOPMENT
# ===========================================

dev:
	npm run electron:dev

start:
	npm start

# ===========================================
# BUILD
# ===========================================

build:
	npm run electron:build

build-linux:
	npm run build:linux

build-mac:
	npm run build:mac

build-win:
	npm run build:win

# ===========================================
# DOCKER BUILD
# ===========================================

docker-build:
	docker-compose run --rm builder

docker-up:
	docker-compose up -d api db redis

docker-down:
	docker-compose down

# ===========================================
# TESTING
# ===========================================

test:
	@echo "Running basic validation..."
	@test -f electron/main.js || (echo "ERROR: electron/main.js not found" && exit 1)
	@test -f electron/preload.js || (echo "ERROR: electron/preload.js not found" && exit 1)
	@test -f src/index.html || (echo "ERROR: src/index.html not found" && exit 1)
	@test -f src/app.js || (echo "ERROR: src/app.js not found" && exit 1)
	@test -f package.json || (echo "ERROR: package.json not found" && exit 1)
	@echo "✅ All required files present"
	@echo ""
	@echo "Checking package.json syntax..."
	@node -e "JSON.parse(require('fs').readFileSync('package.json'))" 2>/dev/null && echo "✅ package.json valid" || echo "❌ package.json invalid"

# ===========================================
# CLEANUP
# ===========================================

clean:
	rm -rf dist/
	rm -rf node_modules/
	rm -rf .cache/
	@echo "Cleaned build artifacts"
