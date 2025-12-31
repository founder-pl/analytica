#!/bin/bash
# ANALYTICA Framework - E2E Test Runner
# ======================================
# Runs full E2E tests in Docker environment
#
# Usage:
#   ./scripts/run-e2e-tests.sh          # Run all E2E tests
#   ./scripts/run-e2e-tests.sh --build  # Rebuild images before running
#   ./scripts/run-e2e-tests.sh --keep   # Keep containers running after tests

set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.e2e.yml"

RESULTS_DIR="$PROJECT_ROOT/test-results"
LOGS_DIR="$RESULTS_DIR/logs"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_LOG="$LOGS_DIR/e2e-${RUN_ID}.runner.log"

mkdir -p "$LOGS_DIR"
exec > >(tee -a "$RUN_LOG") 2>&1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
BUILD_FLAG=""
KEEP_RUNNING=false

for arg in "$@"; do
    case $arg in
        --build)
            BUILD_FLAG="--build"
            ;;
        --keep)
            KEEP_RUNNING=true
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build    Rebuild Docker images before running tests"
            echo "  --keep     Keep containers running after tests complete"
            echo "  --help     Show this help message"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        ANALYTICA E2E Test Suite                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Use docker compose or docker-compose
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

cd "$PROJECT_ROOT"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Saving docker logs snapshot...${NC}"
    {
        echo "run_id=$RUN_ID"
        echo "compose_file=$COMPOSE_FILE"
        echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$LOGS_DIR/e2e-${RUN_ID}.meta.txt" 2>/dev/null || true

    $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps > "$LOGS_DIR/e2e-${RUN_ID}.compose-ps.txt" 2>/dev/null || true
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --no-color > "$LOGS_DIR/e2e-${RUN_ID}.compose.log" 2>/dev/null || true
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --no-color api > "$LOGS_DIR/e2e-${RUN_ID}.api.log" 2>/dev/null || true
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --no-color postgres > "$LOGS_DIR/e2e-${RUN_ID}.postgres.log" 2>/dev/null || true
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --no-color redis > "$LOGS_DIR/e2e-${RUN_ID}.redis.log" 2>/dev/null || true

    if [ "$KEEP_RUNNING" = false ]; then
        echo -e "\n${YELLOW}Cleaning up containers...${NC}"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
    else
        echo -e "\n${YELLOW}Keeping containers running (use 'docker-compose -f docker/docker-compose.e2e.yml down -v' to stop)${NC}"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Stop any existing containers
echo -e "${YELLOW}Stopping existing E2E containers...${NC}"
$DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true

# Build and start services
echo -e "\n${BLUE}Starting E2E environment...${NC}"
$DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d $BUILD_FLAG postgres redis api

# Wait for API to be ready
echo -e "\n${YELLOW}Waiting for API to be ready...${NC}"
MAX_RETRIES=60
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:18080/health > /dev/null 2>&1; then
        echo -e "${GREEN}API is ready!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "\n${RED}Error: API failed to start within timeout${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs api
    exit 1
fi

# Run E2E tests
echo -e "\n${BLUE}Running E2E tests...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEST_EXIT_CODE=0

if [ "$KEEP_RUNNING" = true ]; then
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d $BUILD_FLAG e2e-tests || TEST_EXIT_CODE=$?
    if docker inspect e2e-tests >/dev/null 2>&1; then
        TEST_EXIT_CODE=$(docker wait e2e-tests 2>/dev/null || echo 1)
    fi
else
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up $BUILD_FLAG --abort-on-container-exit --exit-code-from e2e-tests postgres redis api e2e-tests || TEST_EXIT_CODE=$?
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Copy test results
mkdir -p "$RESULTS_DIR"
if docker inspect e2e-tests >/dev/null 2>&1; then
    docker cp "e2e-tests:/app/results/." "$RESULTS_DIR/" 2>/dev/null || true
fi

# Summary
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ All E2E tests passed!                                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ Some E2E tests failed                                   ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo -e "${BLUE}Test results saved to: $RESULTS_DIR${NC}"

if [ -f "$RESULTS_DIR/e2e-report.html" ]; then
    echo -e "${BLUE}HTML report: file://$RESULTS_DIR/e2e-report.html${NC}"
fi

exit $TEST_EXIT_CODE
