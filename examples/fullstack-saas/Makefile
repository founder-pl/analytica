# ANALYTICA Full-Stack SaaS - Makefile
# =====================================

.PHONY: help dev up down logs build test deploy

help:
	@echo "Analytica SaaS - Available Commands"
	@echo "===================================="
	@echo "  make dev           - Start development environment"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make logs          - View logs"
	@echo "  make build         - Build all images"
	@echo "  make test          - Run all tests"
	@echo "  make deploy-staging - Deploy to staging"
	@echo "  make deploy-prod   - Deploy to production"

# ===========================================
# DEVELOPMENT
# ===========================================

dev:
	docker-compose up -d db redis
	cd backend && uvicorn src.main:app --reload --port 8000 &
	cd frontend && npm run dev &

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker

# ===========================================
# DATABASE
# ===========================================

shell-db:
	docker-compose exec db psql -U postgres -d analytica

migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(name)"

# ===========================================
# BUILD
# ===========================================

build:
	docker-compose build

build-backend:
	docker build -t analytica/saas-backend:latest ./backend

build-frontend:
	docker build -t analytica/saas-frontend:latest ./frontend

build-worker:
	docker build -t analytica/saas-worker:latest ./worker

push:
	docker push analytica/saas-backend:latest
	docker push analytica/saas-frontend:latest
	docker push analytica/saas-worker:latest

# ===========================================
# TESTING
# ===========================================

test:
	make test-backend
	make test-frontend

test-backend:
	cd backend && pytest -v

test-frontend:
	cd frontend && npm test

test-e2e:
	cd e2e && npm test

# ===========================================
# DEPLOYMENT
# ===========================================

deploy-staging:
	kubectl apply -f k8s/staging/

deploy-prod:
	kubectl apply -f k8s/production/

rollback:
	kubectl rollout undo deployment/analytica-backend
	kubectl rollout undo deployment/analytica-frontend

# ===========================================
# UTILITIES
# ===========================================

clean:
	docker-compose down -v
	docker system prune -f

seed:
	docker-compose exec backend python -m src.scripts.seed

backup-db:
	docker-compose exec db pg_dump -U postgres analytica > backup_$(shell date +%Y%m%d).sql
