#!/bin/bash
set -e
set -o pipefail

WORKSPACE="/workspace"
INNER_COMPOSE="$WORKSPACE/docker/docker-compose.e2e.inner.yml"
RESULTS_DIR="/results/e2e-dind"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$RESULTS_DIR"

echo "[dind] waiting for docker daemon..."
for i in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
    echo "[dind] docker daemon ready"
    break
  fi
  sleep 1
  if [ "$i" = "60" ]; then
    echo "[dind] docker daemon not ready" >&2
    exit 1
  fi
done

cd "$WORKSPACE"

echo "[dind] starting inner e2e stack (build + run tests)"
set +e

docker compose -f "$INNER_COMPOSE" down -v --remove-orphans >/dev/null 2>&1

# Run the stack and exit with the e2e-tests exit code
# Containers are kept so we can docker cp results after.
docker compose -f "$INNER_COMPOSE" up --build --abort-on-container-exit --exit-code-from e2e-tests
TEST_EXIT_CODE=$?

set -e

echo "[dind] copying results"
CID=$(docker compose -f "$INNER_COMPOSE" ps -q e2e-tests || true)
if [ -z "$CID" ]; then
  echo "[dind] ERROR: could not find e2e-tests container id" >&2
  echo "missing_container_id" > "$RESULTS_DIR/inner-${RUN_ID}.error.txt" 2>/dev/null || true
else
  docker cp "$CID:/app/results/." "$RESULTS_DIR/" || true
fi

docker compose -f "$INNER_COMPOSE" ps > "$RESULTS_DIR/inner-${RUN_ID}.compose-ps.txt" 2>/dev/null || true
docker compose -f "$INNER_COMPOSE" logs --no-color > "$RESULTS_DIR/inner-${RUN_ID}.compose.log" 2>/dev/null || true
docker compose -f "$INNER_COMPOSE" logs --no-color e2e-tests > "$RESULTS_DIR/inner-${RUN_ID}.e2e-tests.log" 2>/dev/null || true

docker compose -f "$INNER_COMPOSE" logs api > "$RESULTS_DIR/api.log" 2>/dev/null || true

echo "[dind] test exit code: $TEST_EXIT_CODE"

if [ "${KEEP_DIND}" != "true" ]; then
  echo "[dind] cleaning up inner stack"
  docker compose -f "$INNER_COMPOSE" down -v --remove-orphans >/dev/null 2>&1 || true
else
  echo "[dind] KEEP_DIND=true, keeping inner stack running"
fi

exit $TEST_EXIT_CODE
