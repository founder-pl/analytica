# ANALYTICA DSL Pipelines - Makefile
# ==================================

.PHONY: help setup test run-example validate clean

# Default API URL
API_URL ?= http://localhost:18000

# Default target
help:
	@echo "Analytica DSL Pipelines"
	@echo "======================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup           - Copy .env.example to .env"
	@echo ""
	@echo "Run Pipelines:"
	@echo "  make run-basic       - Run basic metrics example"
	@echo "  make run-budget      - Run budget analysis example"
	@echo "  make run-investment  - Run investment analysis example"
	@echo "  make run-views       - Run views example"
	@echo ""
	@echo "Validation:"
	@echo "  make validate        - Validate all DSL files"
	@echo "  make test            - Run all tests"
	@echo ""
	@echo "Variables:"
	@echo "  API_URL              - API endpoint (default: $(API_URL))"

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

# ===========================================
# RUN PIPELINES
# ===========================================

run-basic:
	@echo "Running basic metrics pipeline..."
	@curl -s -X POST $(API_URL)/api/v1/pipeline/execute \
		-H "Content-Type: application/json" \
		-d '{"dsl": "data.load(\"/landing/sample-data/sales.csv\") | metrics.sum(\"revenue\") | metrics.avg(\"revenue\")"}' \
		| python3 -m json.tool 2>/dev/null || cat

run-budget:
	@echo "Running budget analysis pipeline..."
	@curl -s -X POST $(API_URL)/api/v1/pipeline/execute \
		-H "Content-Type: application/json" \
		-d '{"dsl": "data.load(\"/landing/sample-data/finance.json\") | budget.variance() | view.card(value=\"variance\", title=\"Budget Variance\", icon=\"📊\")"}' \
		| python3 -m json.tool 2>/dev/null || cat

run-investment:
	@echo "Running investment analysis pipeline..."
	@curl -s -X POST $(API_URL)/api/v1/pipeline/execute \
		-H "Content-Type: application/json" \
		-d '{"dsl": "investment.analyze(initial_investment=100000, discount_rate=0.1, cash_flows=[30000, 40000, 50000]) | investment.npv(rate=0.1) | view.card(value=\"npv\", title=\"NPV\", icon=\"💰\")"}' \
		| python3 -m json.tool 2>/dev/null || cat

run-views:
	@echo "Running views pipeline..."
	@curl -s -X POST $(API_URL)/api/v1/pipeline/execute \
		-H "Content-Type: application/json" \
		-d '{"dsl": "data.load(\"/landing/sample-data/ecommerce.json\") | view.chart(type=\"bar\", x=\"month\", y=\"revenue\", title=\"Monthly Revenue\", data_path=\"monthly\")"}' \
		| python3 -m json.tool 2>/dev/null || cat

# ===========================================
# VALIDATION
# ===========================================

validate:
	@echo "Validating DSL files..."
	@for file in *.dsl; do \
		echo "Checking $$file..."; \
		test -f "$$file" && echo "  ✅ $$file exists" || echo "  ❌ $$file not found"; \
	done

# ===========================================
# TESTING
# ===========================================

test:
	@echo "Running DSL pipeline tests..."
	@echo ""
	@echo "1. Testing API connectivity..."
	@curl -s $(API_URL)/health | grep -q "ok\|healthy" && echo "  ✅ API is running" || echo "  ❌ API not available at $(API_URL)"
	@echo ""
	@echo "2. Checking DSL files..."
	@test -f pipelines.dsl && echo "  ✅ pipelines.dsl" || echo "  ❌ pipelines.dsl not found"
	@test -f views_pipelines.dsl && echo "  ✅ views_pipelines.dsl" || echo "  ❌ views_pipelines.dsl not found"
	@echo ""
	@echo "3. Testing basic DSL execution..."
	@curl -s -X POST $(API_URL)/api/v1/pipeline/execute \
		-H "Content-Type: application/json" \
		-d '{"dsl": "data.literal({\"test\": 1})"}' \
		| grep -q "test" && echo "  ✅ DSL execution works" || echo "  ❌ DSL execution failed"

# ===========================================
# CLEANUP
# ===========================================

clean:
	rm -rf output/
	rm -f *.log
	@echo "Cleaned output files"
