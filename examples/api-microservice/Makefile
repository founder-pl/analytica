# ANALYTICA API Microservice - Makefile
# =====================================

.PHONY: help install setup dev start docker-up docker-down docker-build test clean deploy

# Default target
help:
	@echo "Analytica API Microservice"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make setup        - Copy .env.example to .env"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run development server"
	@echo "  make start        - Start the API"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start all services"
	@echo "  make docker-down  - Stop all services"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-logs  - View logs"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-apply    - Apply K8s manifests"
	@echo "  make k8s-delete   - Delete K8s resources"
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
	pip install -r requirements.txt

venv:
	python3 -m venv venv
	@echo "Run: source venv/bin/activate"

# ===========================================
# DEVELOPMENT
# ===========================================

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

start:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

# ===========================================
# DOCKER
# ===========================================

docker-build:
	docker build -t analytica/api-service .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-restart:
	docker-compose restart api

# ===========================================
# KUBERNETES
# ===========================================

k8s-apply:
	kubectl apply -f k8s/

k8s-delete:
	kubectl delete -f k8s/

k8s-logs:
	kubectl logs -f deployment/analytica-api

# ===========================================
# TESTING
# ===========================================

test:
	@echo "Running basic validation..."
	@test -f src/main.py || (echo "ERROR: src/main.py not found" && exit 1)
	@test -f requirements.txt || (echo "ERROR: requirements.txt not found" && exit 1)
	@test -f Dockerfile || (echo "ERROR: Dockerfile not found" && exit 1)
	@test -f docker-compose.yml || (echo "ERROR: docker-compose.yml not found" && exit 1)
	@test -d k8s || (echo "ERROR: k8s/ not found" && exit 1)
	@test -d pipelines || (echo "ERROR: pipelines/ not found" && exit 1)
	@echo "✅ All required files present"
	@echo ""
	@echo "Checking Python syntax..."
	@python3 -m py_compile src/main.py 2>/dev/null && echo "✅ src/main.py valid" || echo "❌ src/main.py syntax error"

test-api:
	@echo "Testing API endpoints..."
	curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ /health OK" || echo "❌ /health failed"

# ===========================================
# CLEANUP
# ===========================================

clean:
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete
	@echo "Cleaned build artifacts"
