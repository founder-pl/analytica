# ANALYTICA Framework v2 - Project Files
# =======================================
# Generated: 2024-12-31

## 📁 STRUCTURE OVERVIEW

```
analytica/
├── 📁 config/                    # Configuration files
├── 📁 docker/                    # Docker & deployment
├── 📁 docs/                      # Documentation
├── 📁 examples/                  # Usage examples
├── 📁 nginx/                     # Reverse proxy config
├── 📁 scripts/                   # Deployment scripts
├── 📁 src/                       # Source code
│   ├── 📁 api/                   # REST API
│   ├── 📁 connectors/            # Database connectors
│   ├── 📁 core/                  # Core framework
│   ├── 📁 dsl/                   # DSL engine
│   │   ├── 📁 api/               # DSL REST API
│   │   ├── 📁 atoms/             # Atomic operations
│   │   ├── 📁 cli/               # Command line
│   │   └── 📁 core/              # Parser & executor
│   ├── 📁 exporters/             # File exporters
│   ├── 📁 importers/             # File importers
│   ├── 📁 integrations/          # External integrations
│   │   ├── 📁 banking/           # MT940, PSD2, banks
│   │   ├── 📁 erp/               # SAP, Comarch, Sage
│   │   ├── 📁 global/            # Stripe, PayPal, QuickBooks
│   │   └── 📁 polish/            # iFirma, Fakturownia
│   ├── 📁 modules/               # Business modules
│   └── 📁 sdk/                   # Client SDKs
│       ├── 📁 js/                # JavaScript SDK
│       └── 📁 python/            # Python SDK
└── 📁 tests/                     # Test suite
    ├── 📁 e2e/                   # End-to-end tests
    ├── 📁 fixtures/              # Test data
    ├── 📁 integration/           # Integration tests
    └── 📁 unit/                  # Unit tests
```

## 📋 COMPLETE FILE LIST

### Root Files
- `Makefile` - Build & run commands (40+ targets)
- `README.md` - Project documentation
- `requirements.txt` - Python dependencies
- `pytest.ini` - Test configuration
- `analytica` - CLI entrypoint script

### Configuration (config/)
- `analytica.yaml` - Global framework config
- `domains/alerts.yaml` - Alerts domain config
- `domains/multiplan.yaml` - Multiplan domain config
- `domains/planbudzetu.yaml` - Budget domain config
- `domains/planinwestycji.yaml` - Investment domain config
- `domains/repox.yaml` - Hub domain config

### Docker (docker/)
- `Dockerfile.api` - API container
- `docker-compose.yml` - Full 12-domain infrastructure
- `docker-compose.financial.yml` - Lightweight 3-domain setup
- `init-db.sql` - Database schema
- `prometheus.yml` - Monitoring config

### Documentation (docs/)
- `DSL.md` - Complete DSL documentation

### Examples (examples/)
- `pipelines.dsl` - DSL pipeline examples
- `usage_javascript.js` - JavaScript SDK examples
- `usage_python.py` - Python SDK examples

### Nginx (nginx/)
- `nginx.conf` - Main config
- `domains/proxy_params.conf` - Proxy parameters

### Scripts (scripts/)
- `start.sh` - Deployment script

### Source Code (src/)

#### API (src/api/)
- `__init__.py`
- `main.py` - FastAPI application

#### Connectors (src/connectors/)
- `__init__.py`
- `data_connectors.py` - PostgreSQL, MySQL, MongoDB, Redis, S3, REST

#### Core (src/core/)
- `__init__.py`
- `domain_router.py` - Multi-domain routing

#### DSL Engine (src/dsl/)
- `__init__.py`
- `api/__init__.py`
- `api/server.py` - DSL REST API server
- `atoms/__init__.py`
- `atoms/implementations.py` - 50+ atomic operations
- `cli/__init__.py`
- `cli/main.py` - CLI tool
- `core/__init__.py`
- `core/parser.py` - DSL parser & executor

#### Exporters (src/exporters/)
- `__init__.py`
- `file_exporters.py` - CSV, Excel, JSON, XML, PDF, HTML

#### Importers (src/importers/)
- `__init__.py`
- `file_importers.py` - CSV, Excel, JSON, XML, JPK, MT940

#### Integrations (src/integrations/)
- `__init__.py`
- `banking/__init__.py`
- `banking/banking.py` - MT940, PSD2, mBank, ING
- `erp/__init__.py`
- `erp/erp_systems.py` - SAP, Comarch, Sage, Enova
- `global/__init__.py`
- `global/global_apis.py` - Stripe, PayPal, QuickBooks, Xero
- `polish/__init__.py`
- `polish/accounting.py` - iFirma, Fakturownia, inFakt

#### Modules (src/modules/)
- `__init__.py`
- `alerts/__init__.py`
- `budget/__init__.py`
- `forecast/__init__.py`
- `investment/__init__.py`
- `reports/__init__.py`
- `voice/__init__.py`

#### SDKs (src/sdk/)
- `__init__.py`
- `js/analytica.js` - JavaScript SDK
- `js/analytica.d.ts` - TypeScript definitions
- `js/package.json` - NPM package config
- `python/__init__.py`
- `python/analytica.py` - Python SDK

### Tests (tests/)
- `__init__.py`
- `conftest.py` - Pytest fixtures
- `e2e/__init__.py`
- `e2e/test_pipelines.py` - E2E pipeline tests
- `fixtures/sample_data.json` - Test data
- `integration/__init__.py`
- `integration/test_api.py` - API integration tests
- `unit/__init__.py`
- `unit/test_dsl_parser.py` - Parser unit tests

## 📊 STATISTICS

| Category | Count |
|----------|-------|
| Python files | 35 |
| JavaScript files | 2 |
| TypeScript files | 1 |
| Configuration files | 12 |
| Documentation files | 3 |
| Test files | 5 |
| **Total files** | **~60** |

## 🧪 TESTS

### E2E Tests (tests/e2e/)
- `test_pipelines.py` - 50+ E2E test cases
  - Basic pipelines
  - Budget module (planbudzetu.pl)
  - Investment module (planinwestycji.pl)
  - Multiplan module (multiplan.pl)
  - Alert module (alerts.pl)
  - Forecast module (estymacja.pl)
  - Reports & exports
  - Fluent API
  - Error handling

### Integration Tests (tests/integration/)
- `test_api.py` - API endpoint tests
  - Pipeline execution
  - Pipeline parsing
  - Pipeline validation
  - Atoms API
  - Stored pipelines
  - Health checks
  - Async execution

### Unit Tests (tests/unit/)
- `test_dsl_parser.py` - Parser & builder tests
  - Tokenizer tests
  - Parser tests
  - Pipeline builder tests
  - Atom tests
  - Context tests
  - Definition tests

## 🔌 INTEGRATIONS

### Polish Accounting
- **iFirma** - HMAC-SHA1 authentication
- **Fakturownia** - API token
- **inFakt** - API key

### Banking
- **MT940 Parser** - SWIFT format
- **mBank PSD2** - Open Banking API
- **ING Polska PSD2** - Open Banking API

### ERP Systems
- **SAP Business One** - Service Layer API
- **Comarch Optima** - REST API
- **Sage Symfonia** - OAuth2 API
- **Enova365** - REST API

### Global APIs
- **Stripe** - Payments
- **PayPal** - Payments
- **QuickBooks** - Accounting
- **Xero** - Accounting

### Data Connectors
- **PostgreSQL** - SQL database
- **MySQL** - SQL database
- **SQLite** - Embedded database
- **MongoDB** - NoSQL database
- **Redis** - Cache & messaging
- **S3** - Cloud storage
- **REST API** - Generic connector

## 🚀 QUICK START

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start API server
python -m uvicorn src.dsl.api.server:app --port 8080

# Use CLI
./analytica run 'data.load("sales") | metrics.sum("amount")'
```
