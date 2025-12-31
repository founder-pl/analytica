# ANALYTICA Framework - Makefile
# Usage: make [target]

.PHONY: help build up down restart logs status clean test dev

# Default target
.DEFAULT_GOAL := help

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help: ## Show this help
	@echo ""
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║                    ANALYTICA Framework                        ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Domain-specific commands:$(NC)"
	@echo "  $(GREEN)make up-multiplan$(NC)       Start multiplan.pl"
	@echo "  $(GREEN)make up-planbudzetu$(NC)    Start planbudzetu.pl"
	@echo "  $(GREEN)make up-planinwestycji$(NC) Start planinwestycji.pl"
	@echo "  $(GREEN)make up-financial$(NC)      Start all financial domains"
	@echo ""

# ============================================================
# BUILD
# ============================================================

build: ## Build all Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	cd docker && docker-compose build

build-no-cache: ## Build without cache
	@echo "$(CYAN)Building Docker images (no cache)...$(NC)"
	cd docker && docker-compose build --no-cache

# ============================================================
# INFRASTRUCTURE
# ============================================================

up-infra: ## Start infrastructure (DB, Redis, Nginx)
	@echo "$(CYAN)Starting infrastructure...$(NC)"
	cd docker && docker-compose up -d postgres redis
	@sleep 3
	cd docker && docker-compose up -d nginx grafana prometheus

down-infra: ## Stop infrastructure
	cd docker && docker-compose stop postgres redis nginx grafana prometheus

# ============================================================
# ALL SERVICES
# ============================================================

up: ## Start all services
	@echo "$(CYAN)Starting all services...$(NC)"
	cd docker && docker-compose up -d
	@make status

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	cd docker && docker-compose down

restart: down up ## Restart all services

# ============================================================
# FINANCIAL DOMAINS
# ============================================================

up-multiplan: up-infra ## Start multiplan.pl (port 8010)
	@echo "$(CYAN)Starting multiplan.pl...$(NC)"
	cd docker && docker-compose up -d api-multiplan
	@echo "$(GREEN)multiplan.pl started on http://localhost:8010$(NC)"

up-planbudzetu: up-infra ## Start planbudzetu.pl (port 8011)
	@echo "$(CYAN)Starting planbudzetu.pl...$(NC)"
	cd docker && docker-compose up -d api-planbudzetu
	@echo "$(GREEN)planbudzetu.pl started on http://localhost:8011$(NC)"

up-planinwestycji: up-infra ## Start planinwestycji.pl (port 8012)
	@echo "$(CYAN)Starting planinwestycji.pl...$(NC)"
	cd docker && docker-compose up -d api-planinwestycji
	@echo "$(GREEN)planinwestycji.pl started on http://localhost:8012$(NC)"

up-financial: up-infra ## Start all financial domains
	@echo "$(CYAN)Starting financial domains...$(NC)"
	cd docker && docker-compose up -d api-multiplan api-planbudzetu api-planinwestycji
	@echo ""
	@echo "$(GREEN)Financial domains started:$(NC)"
	@echo "  - multiplan.pl:      http://localhost:8010"
	@echo "  - planbudzetu.pl:    http://localhost:8011"
	@echo "  - planinwestycji.pl: http://localhost:8012"

# ============================================================
# OTHER DOMAINS
# ============================================================

up-repox: up-infra ## Start repox.pl (hub, port 8000)
	cd docker && docker-compose up -d api-repox

up-alerts: up-infra ## Start alerts.pl (port 8003)
	cd docker && docker-compose up -d api-alerts

up-estymacja: up-infra ## Start estymacja.pl (port 8004)
	cd docker && docker-compose up -d api-estymacja

up-analytics: up-infra ## Start analytics domains
	cd docker && docker-compose up -d api-analizowanie api-przeanalizuj api-estymacja

# ============================================================
# LOGS & STATUS
# ============================================================

status: ## Show status of all services
	@echo ""
	@echo "$(CYAN)Service Status:$(NC)"
	@cd docker && docker-compose ps
	@echo ""
	@echo "$(YELLOW)API Endpoints:$(NC)"
	@echo "┌────────────────────┬──────────┬────────────────────────────────┐"
	@echo "│ Domain             │ API Port │ Status                         │"
	@echo "├────────────────────┼──────────┼────────────────────────────────┤"
	@echo "│ repox.pl           │ 8000     │ http://localhost:8000          │"
	@echo "│ analizowanie.pl    │ 8001     │ http://localhost:8001          │"
	@echo "│ przeanalizuj.pl    │ 8002     │ http://localhost:8002          │"
	@echo "│ alerts.pl          │ 8003     │ http://localhost:8003          │"
	@echo "│ estymacja.pl       │ 8004     │ http://localhost:8004          │"
	@echo "│ retrospektywa.pl   │ 8005     │ http://localhost:8005          │"
	@echo "│ persony.pl         │ 8006     │ http://localhost:8006          │"
	@echo "│ specyfikacja.pl    │ 8007     │ http://localhost:8007          │"
	@echo "│ nisza.pl           │ 8008     │ http://localhost:8008          │"
	@echo "│ $(GREEN)multiplan.pl$(NC)       │ $(GREEN)8010$(NC)     │ $(GREEN)http://localhost:8010$(NC)          │"
	@echo "│ $(GREEN)planbudzetu.pl$(NC)     │ $(GREEN)8011$(NC)     │ $(GREEN)http://localhost:8011$(NC)          │"
	@echo "│ $(GREEN)planinwestycji.pl$(NC)  │ $(GREEN)8012$(NC)     │ $(GREEN)http://localhost:8012$(NC)          │"
	@echo "└────────────────────┴──────────┴────────────────────────────────┘"
	@echo ""
	@echo "$(YELLOW)Infrastructure:$(NC)"
	@echo "  - Grafana:    http://localhost:3100 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis:      localhost:6379"

logs: ## Show logs (usage: make logs service=api-multiplan)
	cd docker && docker-compose logs -f $(service)

logs-multiplan: ## Show multiplan.pl logs
	cd docker && docker-compose logs -f api-multiplan

logs-planbudzetu: ## Show planbudzetu.pl logs
	cd docker && docker-compose logs -f api-planbudzetu

logs-planinwestycji: ## Show planinwestycji.pl logs
	cd docker && docker-compose logs -f api-planinwestycji

# ============================================================
# DEVELOPMENT
# ============================================================

dev: ## Start in development mode with hot reload
	@echo "$(CYAN)Starting in development mode...$(NC)"
	cd docker && docker-compose up

shell-multiplan: ## Open shell in multiplan container
	cd docker && docker-compose exec api-multiplan /bin/sh

shell-db: ## Open PostgreSQL shell
	cd docker && docker-compose exec postgres psql -U analytica -d analytica

# ============================================================
# DATABASE
# ============================================================

db-reset: ## Reset database (WARNING: destroys data)
	@echo "$(YELLOW)Resetting database...$(NC)"
	cd docker && docker-compose down -v
	cd docker && docker-compose up -d postgres
	@sleep 5
	@echo "$(GREEN)Database reset complete$(NC)"

db-migrate: ## Run database migrations
	@echo "$(CYAN)Running migrations...$(NC)"
	# Add migration command here

db-seed: ## Seed database with sample data
	@echo "$(CYAN)Seeding database...$(NC)"
	# Add seed command here

# ============================================================
# TESTING
# ============================================================

test: ## Run tests
	@echo "$(CYAN)Running tests...$(NC)"
	cd docker && docker-compose exec api-repox pytest

test-financial: ## Test financial domains
	@echo "$(CYAN)Testing financial domains...$(NC)"
	curl -s http://localhost:8010/health | jq .
	curl -s http://localhost:8011/health | jq .
	curl -s http://localhost:8012/health | jq .

# ============================================================
# CLEANUP
# ============================================================

clean: ## Remove all containers and volumes
	@echo "$(YELLOW)Cleaning up...$(NC)"
	cd docker && docker-compose down -v --remove-orphans
	docker system prune -f

clean-images: ## Remove all images
	cd docker && docker-compose down --rmi all -v
