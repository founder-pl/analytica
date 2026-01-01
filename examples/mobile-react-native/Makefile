# ANALYTICA Mobile React Native - Makefile
# ========================================

.PHONY: help install setup ios android start build-ios build-android docker-build test clean

# Default target
help:
	@echo "Analytica Mobile React Native"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install         - Install dependencies"
	@echo "  make setup           - Copy .env.example to .env"
	@echo "  make pod-install     - Install iOS pods"
	@echo ""
	@echo "Development:"
	@echo "  make start           - Start Metro bundler"
	@echo "  make ios             - Run on iOS simulator"
	@echo "  make android         - Run on Android emulator"
	@echo ""
	@echo "Build:"
	@echo "  make build-ios       - Build iOS release"
	@echo "  make build-android   - Build Android APK"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    - Build Android APK in Docker"
	@echo "  make docker-api      - Start API backend"
	@echo ""
	@echo "Other:"
	@echo "  make test            - Run tests"
	@echo "  make clean           - Clean build artifacts"

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

pod-install:
	cd ios && pod install

# ===========================================
# DEVELOPMENT
# ===========================================

start:
	npm start

ios:
	npm run ios

android:
	npm run android

# ===========================================
# BUILD
# ===========================================

build-ios:
	npm run build:ios

build-android:
	npm run build:android

# ===========================================
# DOCKER
# ===========================================

docker-build:
	docker-compose run --rm android-builder

docker-api:
	docker-compose up -d api db redis

docker-down:
	docker-compose down

# ===========================================
# TESTING
# ===========================================

test:
	@echo "Running basic validation..."
	@test -f package.json || (echo "ERROR: package.json not found" && exit 1)
	@test -f Dockerfile || (echo "ERROR: Dockerfile not found" && exit 1)
	@test -f docker-compose.yml || (echo "ERROR: docker-compose.yml not found" && exit 1)
	@test -d pipelines || (echo "ERROR: pipelines/ not found" && exit 1)
	@echo "✅ All required files present"
	@echo ""
	@echo "Checking package.json syntax..."
	@node -e "JSON.parse(require('fs').readFileSync('package.json'))" 2>/dev/null && echo "✅ package.json valid" || echo "❌ package.json invalid"

# ===========================================
# CLEANUP
# ===========================================

clean:
	rm -rf node_modules/
	rm -rf ios/Pods/
	rm -rf android/build/
	rm -rf dist/
	@echo "Cleaned build artifacts"
