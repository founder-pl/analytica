#!/bin/bash
# ANALYTICA Framework - E2E Docker-in-Docker Test Runner

set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.e2e.dind.yml"

RESULTS_DIR="$PROJECT_ROOT/test-results/e2e-dind"
LOGS_DIR="$RESULTS_DIR/logs"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_LOG="$LOGS_DIR/e2e-dind-${RUN_ID}.runner.log"

mkdir -p "$LOGS_DIR"
exec > >(tee -a "$RUN_LOG") 2>&1

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
      echo "Usage: $0 [--build] [--keep]"
      exit 0
      ;;
  esac
done

if docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
else
  DOCKER_COMPOSE="docker-compose"
fi

cleanup() {
  echo "[dind] saving outer logs snapshot"
  {
    echo "run_id=$RUN_ID"
    echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "compose_file=$COMPOSE_FILE"
  } > "$LOGS_DIR/e2e-dind-${RUN_ID}.meta.txt" 2>/dev/null || true

  $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps > "$LOGS_DIR/e2e-dind-${RUN_ID}.outer-ps.txt" 2>/dev/null || true
  $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --no-color > "$LOGS_DIR/e2e-dind-${RUN_ID}.outer-compose.log" 2>/dev/null || true
  $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --no-color runner > "$LOGS_DIR/e2e-dind-${RUN_ID}.outer-runner.log" 2>/dev/null || true
  $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --no-color dind > "$LOGS_DIR/e2e-dind-${RUN_ID}.outer-dind.log" 2>/dev/null || true

  if [ "$KEEP_RUNNING" = false ]; then
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v --remove-orphans >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

mkdir -p "$PROJECT_ROOT/test-results/e2e-dind"

if [ "$KEEP_RUNNING" = true ]; then
  export KEEP_DIND=true
else
  export KEEP_DIND=false
fi

if [ "$KEEP_RUNNING" = true ]; then
  echo "[dind] starting outer dind stack in background (keep mode)"
  $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d $BUILD_FLAG

  RUNNER_ID=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" ps -q runner)
  if [ -z "$RUNNER_ID" ]; then
    echo "[dind] runner container not found" >&2
    exit 1
  fi

  echo "[dind] waiting for runner to finish: $RUNNER_ID"
  EXIT_CODE=$(docker wait "$RUNNER_ID")
  echo "[dind] runner exited with: $EXIT_CODE"
  echo "[dind] keeping dind running for debugging"
  echo "[dind] inner docker available on host: DOCKER_HOST=tcp://localhost:23750"
  echo "[dind] stop with: docker compose -f docker/docker-compose.e2e.dind.yml down -v"
  exit "$EXIT_CODE"
else
  $DOCKER_COMPOSE -f "$COMPOSE_FILE" up $BUILD_FLAG --abort-on-container-exit --exit-code-from runner
fi
