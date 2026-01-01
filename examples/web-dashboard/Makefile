# ANALYTICA Web Dashboard - Makefile
# ==================================

.PHONY: help install dev build start docker-up docker-down docker-build test clean

# Default target
help:
	@echo "Analytica Web Dashboard"
	@echo "======================="
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install dependencies"
	@echo "  make setup        - Copy .env.example to .env"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run development server"
	@echo "  make start        - Start the app"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start all services"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-logs  - View logs"
	@echo ""
	@echo "Other:"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean build artifacts"

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
	npm run dev

start:
	npm run start

# ===========================================
# DOCKER
# ===========================================

docker-build:
	docker build -t analytica/web-dashboard .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# ===========================================
# TESTING
# ===========================================

test:
	@echo "Running basic validation..."
	@test -f src/index.html || (echo "ERROR: src/index.html not found" && exit 1)
	@test -f src/app.js || (echo "ERROR: src/app.js not found" && exit 1)
	@test -f src/styles.css || (echo "ERROR: src/styles.css not found" && exit 1)
	@test -f package.json || (echo "ERROR: package.json not found" && exit 1)
	@test -f Dockerfile || (echo "ERROR: Dockerfile not found" && exit 1)
	@test -f docker-compose.yml || (echo "ERROR: docker-compose.yml not found" && exit 1)
	@test -f nginx.conf || (echo "ERROR: nginx.conf not found" && exit 1)
	@echo "✅ All required files present"
	@echo ""
	@echo "Checking package.json syntax..."
	@node -e "JSON.parse(require('fs').readFileSync('package.json'))" 2>/dev/null && echo "✅ package.json valid" || echo "❌ package.json invalid"
	@echo ""
	@echo "Checking HTML syntax..."
	@grep -q "<html" src/index.html && echo "✅ index.html valid" || echo "❌ index.html invalid"

# ===========================================
# CLEANUP
# ===========================================

clean:
	rm -rf node_modules/
	rm -rf dist/
	@echo "Cleaned build artifacts"
