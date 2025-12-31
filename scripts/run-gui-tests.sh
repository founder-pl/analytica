#!/bin/bash
# ANALYTICA Framework - GUI Test Runner
# ======================================
# Runs Playwright GUI tests against running API
#
# Usage:
#   ./scripts/run-gui-tests.sh              # Run against API_BASE_URL from .env or localhost:18000
#   ./scripts/run-gui-tests.sh --headed     # Run with visible browser
#   ./scripts/run-gui-tests.sh --docker     # Run in Docker

set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RESULTS_DIR="$PROJECT_ROOT/test-results"
LOGS_DIR="$RESULTS_DIR/logs"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_LOG="$LOGS_DIR/gui-${RUN_ID}.runner.log"

mkdir -p "$LOGS_DIR"
exec > >(tee -a "$RUN_LOG") 2>&1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
# If API_BASE_URL is not provided, try reading it from .env, otherwise fallback to localhost:18000.
if [ -z "${API_BASE_URL}" ]; then
    if [ -f "$PROJECT_ROOT/.env" ]; then
        ENV_URL=$(grep -E '^API_BASE_URL=' "$PROJECT_ROOT/.env" | tail -n 1 | cut -d= -f2-)
        ENV_URL="${ENV_URL%\"}"
        ENV_URL="${ENV_URL#\"}"
        if [ -n "$ENV_URL" ]; then
            API_BASE_URL="$ENV_URL"
        fi
    fi
fi

API_BASE_URL="${API_BASE_URL:-http://localhost:18000}"
HEADED=""
USE_DOCKER=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --headed)
            HEADED="--headed"
            ;;
        --docker)
            USE_DOCKER=true
            ;;
        --url=*)
            API_BASE_URL="${arg#*=}"
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --headed     Run with visible browser window"
            echo "  --docker     Run tests in Docker container"
            echo "  --url=URL    Set API base URL (default: from .env or http://localhost:18000)"
            echo "  --help       Show this help message"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        ANALYTICA GUI Test Suite (Playwright)               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}API URL: ${API_BASE_URL}${NC}"
echo ""

# Check if API is running
echo -e "${YELLOW}Checking API availability...${NC}"
MAX_RETRIES=60
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -fsS "${API_BASE_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}API is available!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "\n${RED}Error: API not available at ${API_BASE_URL}${NC}"
    echo -e "${YELLOW}Make sure the API is running:${NC}"
    echo "  make dev"
    echo "  # or"
    echo "  PYTHONPATH=src uvicorn src.api.main:app --host 0.0.0.0 --port 18000"
    echo ""
    echo -e "${YELLOW}Tip:${NC} try: curl -v ${API_BASE_URL}/health"
    exit 1
fi

cd "$PROJECT_ROOT"

if [ "$USE_DOCKER" = true ]; then
    echo -e "\n${BLUE}Running GUI tests in Docker...${NC}"
    docker run --rm \
        --network host \
        -e API_BASE_URL="${API_BASE_URL}" \
        -v "$PROJECT_ROOT/tests:/app/tests:ro" \
        -v "$PROJECT_ROOT/test-results:/app/results" \
        mcr.microsoft.com/playwright/python:v1.40.0-jammy \
        pytest /app/tests/e2e/test_gui.py -v \
        --tb=short \
        --junitxml=/app/results/gui-results.xml \
        --html=/app/results/gui-report.html \
        --self-contained-html \
        -x
else
    echo -e "\n${BLUE}Running GUI tests locally...${NC}"
    
    # Check if playwright is installed
    if ! python3 -c "import playwright" 2>/dev/null; then
        echo -e "${YELLOW}Installing Playwright...${NC}"
        pip install playwright
        playwright install chromium
    fi

    if ! python3 -c "import pytest_html" 2>/dev/null; then
        pip install pytest-html
    fi
    
    # Run tests
    API_BASE_URL="${API_BASE_URL}" \
    PYTHONPATH=src \
    python3 -m pytest tests/e2e/test_gui.py -v \
        --tb=short \
        --junitxml="$RESULTS_DIR/gui-results.xml" \
        --html="$RESULTS_DIR/gui-report.html" \
        --self-contained-html \
        ${HEADED} \
        -x
fi

echo ""
echo -e "${GREEN}GUI tests completed!${NC}"
