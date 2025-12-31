# ANALYTICA Framework - Dokumentacja (Index)

## Menu

- [README](../README.md)
- [Architektura](ARCHITECTURE.md)
- [API](API.md)
- [DSL](DSL.md)
- [Moduły](MODULES.md)
- [System punktów](POINTS.md)
- [Compliance](COMPLIANCE.md)
- [Roadmap](ROADMAP.md)
- [Views Roadmap](VIEWS_ROADMAP.md)
- [Mapa plików projektu](../PROJECT_FILES.md)

## Menu (rozszerzone)

### Start

- [Quick Start (README)](../README.md#-quick-start)
- [Komendy (Makefile)](../Makefile)
- [Konfiguracja środowiska (.env.example)](../.env.example)

### Testowanie

- [Testy - overview](#testowanie)
- [E2E (Docker)](../docker/docker-compose.e2e.yml)
- [E2E (Docker-in-Docker)](../docker/docker-compose.e2e.dind.yml)
- [GUI (Playwright)](../tests/e2e/test_gui.py)

### Docker / Deployment

- [Docker Compose (pełny stack)](../docker/docker-compose.yml)
- [Docker Compose (financial)](../docker/docker-compose.financial.yml)
- [Docker Compose (E2E)](../docker/docker-compose.e2e.yml)
- [Docker Compose (E2E Docker-in-Docker)](../docker/docker-compose.e2e.dind.yml)
- [Docker Compose (E2E inner, uruchamiane w dind)](../docker/docker-compose.e2e.inner.yml)

- [Dockerfile API](../docker/Dockerfile.api)
- [Dockerfile E2E (pytest + Playwright)](../docker/Dockerfile.e2e)
- [Dockerfile E2E Postgres (dla dind)](../docker/Dockerfile.e2e.postgres)
- [Dockerfile E2E dind-runner](../docker/Dockerfile.e2e.dind-runner)

### Skrypty

- [Start systemu](../scripts/start.sh)
- [E2E (Docker)](../scripts/run-e2e-tests.sh)
- [E2E (Docker-in-Docker)](../scripts/run-e2e-dind.sh)
- [GUI (Playwright)](../scripts/run-gui-tests.sh)

### Dokumentacja tematyczna

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [API.md](API.md)
- [DSL.md](DSL.md)
- [MODULES.md](MODULES.md)
- [ROADMAP.md](ROADMAP.md)
- [VIEWS_ROADMAP.md](VIEWS_ROADMAP.md)
- [COMPLIANCE.md](COMPLIANCE.md)
- [POINTS.md](POINTS.md)

### Kod (entry points)

- [API app](../src/api/main.py)
- [Auth](../src/api/auth.py)
- [URI launcher](../src/core/uri_launcher/handler.py)
- [DSL parser / executor](../src/dsl/core/parser.py)
- [DSL context](../src/dsl/core/context.py)
- [Atoms: deploy](../src/dsl/atoms/deploy.py)

## Testowanie

### Komendy Makefile

- `make test`
- `make test-all`
- `make test-e2e`
- `make test-e2e-dind`
- `make test-gui`

### E2E (Docker)

- Compose: `docker/docker-compose.e2e.yml`
- Runner: `scripts/run-e2e-tests.sh`
- Wyniki: `test-results/` (HTML/XML)
- Logi: `test-results/logs/` (snapshot + output runnera)

### E2E (Docker-in-Docker)

- Compose: `docker/docker-compose.e2e.dind.yml`
- Runner: `scripts/run-e2e-dind.sh`
- Inner compose: `docker/docker-compose.e2e.inner.yml`
- Wyniki: `test-results/e2e-dind/`
- Logi: `test-results/e2e-dind/logs/` (outer) oraz `test-results/e2e-dind/inner-*.compose.log` (inner)

Debug (tryb `--keep`):

- `make test-e2e-dind-keep`
- Podgląd inner dockera z hosta:
  - `export DOCKER_HOST=tcp://localhost:23750`
  - `docker ps`
- Zatrzymanie:
  - `docker compose -f docker/docker-compose.e2e.dind.yml down -v`

### GUI (Playwright)

- Testy: `tests/e2e/test_gui.py`
- Runner: `scripts/run-gui-tests.sh`
- Logi: `test-results/logs/`

## Troubleshooting

### DSL Editor: `NetworkError when attempting to fetch resource`

- Upewnij się, że nie otwierasz pliku jako `file://...`.
  - Poprawnie: `http://localhost:18000/landing/dsl-editor.html`
- Sprawdź API:
  - `curl -v http://localhost:18000/health`
- Wymuś bazę API (jeśli UI/Proxy działa na innym porcie/host):
  - `http://localhost:18000/landing/dsl-editor.html?apiBase=http://localhost:18000`
- Jeśli UI i API są na różnych originach:
  - ustaw `DEV_CORS_ALL=true` (dev) albo `ANALYTICA_CORS_ORIGINS=...`
