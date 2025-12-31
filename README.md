# ANALYTICA Framework

> **Universal Analytics Framework - Multi-Domain Platform**
> 
> Jeden core. Wiele domen. Nieskończone możliwości.

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/softreck/analytica.git
cd analytica

# Start all services
make up

# Or start only financial domains
make up-financial

# Check status
make status
```

## 🌐 Ekosystem domen

### Port Mapping

| Domena | Typ | API Port | Frontend Port | URL |
|--------|-----|----------|---------------|-----|
| **repox.pl** | Hub | 8000 | 3000 | http://localhost:8000 |
| analizowanie.pl | General | 8001 | 3001 | http://localhost:8001 |
| przeanalizuj.pl | Voice | 8002 | 3002 | http://localhost:8002 |
| alerts.pl | Monitoring | 8003 | 3003 | http://localhost:8003 |
| estymacja.pl | Forecasting | 8004 | 3004 | http://localhost:8004 |
| retrospektywa.pl | Historical | 8005 | 3005 | http://localhost:8005 |
| persony.pl | Marketing | 8006 | 3006 | http://localhost:8006 |
| specyfikacja.pl | Documentation | 8007 | 3007 | http://localhost:8007 |
| nisza.pl | White-label | 8008 | 3008 | http://localhost:8008 |
| **multiplan.pl** | 💰 Financial | **8010** | 3010 | http://localhost:8010 |
| **planbudzetu.pl** | 💰 Financial | **8011** | 3011 | http://localhost:8011 |
| **planinwestycji.pl** | 💰 Financial | **8012** | 3012 | http://localhost:8012 |

### 💰 Domeny Finansowe (NEW!)

#### multiplan.pl - Planowanie finansowe w wielu scenariuszach
```
Port: 8010
Moduły: budget, forecast, reports, alerts
Funkcje:
  - Scenariusze: optymistyczny, realistyczny, pesymistyczny
  - Budżety departamentowe
  - Analiza wariancji
  - Rolling forecasts
```

#### planbudzetu.pl - Raporty finansowe pod kontrolą
```
Port: 8011
Moduły: budget, reports, alerts, forecast
Funkcje:
  - Śledzenie wydatków
  - Kategoryzacja transakcji
  - Raporty miesięczne/roczne
  - Alerty przekroczenia budżetu
```

#### planinwestycji.pl - Analizuj ROI, planuj inwestycje
```
Port: 8012
Moduły: investment, forecast, reports, budget
Funkcje:
  - Kalkulator ROI
  - Analiza NPV/IRR
  - Okres zwrotu (payback)
  - Analiza ryzyka
  - Porównanie scenariuszy
```

## 📦 Struktura projektu

```
analytica/
├── config/
│   ├── analytica.yaml           # Główna konfiguracja
│   └── domains/                  # Konfiguracje per-domena
│       ├── repox.yaml
│       ├── multiplan.yaml       # 💰 Financial
│       ├── planbudzetu.yaml     # 💰 Financial
│       ├── planinwestycji.yaml  # 💰 Financial
│       └── ...
├── src/
│   ├── core/
│   │   └── domain_router.py     # Routing domen
│   ├── modules/
│   │   ├── reports/
│   │   ├── alerts/
│   │   ├── budget/              # 💰 Moduł budżetowy
│   │   ├── investment/          # 💰 Moduł inwestycyjny
│   │   ├── forecast/
│   │   └── voice/
│   └── api/
│       └── main.py              # FastAPI application
├── docker/
│   ├── docker-compose.yml       # Wszystkie serwisy
│   ├── Dockerfile.api
│   ├── init-db.sql              # Schema bazy danych
│   └── prometheus.yml
├── nginx/
│   ├── nginx.conf               # Reverse proxy
│   └── domains/
├── scripts/
│   └── start.sh
├── Makefile
└── requirements.txt
```

## 🛠️ Komendy

### Makefile

```bash
# Wszystkie serwisy
make up                    # Start wszystkiego
make down                  # Stop wszystkiego
make status                # Status serwisów
make logs service=api-multiplan  # Logi konkretnego serwisu

# Domeny finansowe
make up-financial          # Start wszystkich domen finansowych
make up-multiplan          # Start tylko multiplan.pl
make up-planbudzetu        # Start tylko planbudzetu.pl
make up-planinwestycji     # Start tylko planinwestycji.pl

# Development
make dev                   # Start z hot reload
make shell-db              # Konsola PostgreSQL
make test-financial        # Test API finansowych

# Cleanup
make clean                 # Usuń kontenery i volumes
```

### Skrypt start.sh

```bash
./scripts/start.sh all        # Start wszystkiego
./scripts/start.sh financial  # Start domen finansowych
./scripts/start.sh multiplan  # Start konkretnej domeny
./scripts/start.sh status     # Status
./scripts/start.sh stop       # Stop
```

## 🔌 API Endpoints

### Wspólne dla wszystkich domen

```
GET  /                    # Health check + info o domenie
GET  /health              # Health check
GET  /v1/domain           # Konfiguracja domeny
GET  /v1/reports          # Lista szablonów raportów
POST /v1/reports/generate # Generuj raport
```

### multiplan.pl (Budżety + Scenariusze)

```
GET  /v1/budgets              # Lista budżetów
POST /v1/budgets              # Utwórz budżet
GET  /v1/budgets/scenarios    # Lista scenariuszy
GET  /v1/budgets/categories   # Kategorie budżetowe
POST /v1/forecast/predict     # Prognoza finansowa
```

### planbudzetu.pl (Raporty budżetowe)

```
GET  /v1/budgets              # Lista budżetów
POST /v1/budgets              # Utwórz budżet
GET  /v1/budgets/categories   # Kategorie
GET  /v1/alerts               # Alerty budżetowe
POST /v1/alerts               # Utwórz alert
GET  /v1/reports              # Szablony raportów
```

### planinwestycji.pl (Analiza inwestycji)

```
GET  /v1/investments              # Lista inwestycji
POST /v1/investments/analyze      # Analiza ROI/NPV/IRR
GET  /v1/investments/calculators  # Dostępne kalkulatory
POST /v1/forecast/predict         # Prognoza zwrotu
```

## 📊 Przykłady użycia API

### Analiza inwestycji (planinwestycji.pl)

```bash
curl -X POST http://localhost:8012/v1/investments/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nowa linia produkcyjna",
    "initial_investment": 500000,
    "discount_rate": 0.12,
    "investment_type": "capex",
    "cash_flows": [
      {"period": 1, "amount": 150000, "description": "Rok 1"},
      {"period": 2, "amount": 180000, "description": "Rok 2"},
      {"period": 3, "amount": 200000, "description": "Rok 3"},
      {"period": 4, "amount": 220000, "description": "Rok 4"},
      {"period": 5, "amount": 250000, "description": "Rok 5"}
    ]
  }'
```

**Response:**
```json
{
  "investment_id": "inv_20241230120000",
  "name": "Nowa linia produkcyjna",
  "roi": 100.0,
  "npv": 220847.23,
  "irr": null,
  "payback_period": 2.94,
  "profitability_index": 1.44,
  "risk_level": "low"
}
```

### Tworzenie budżetu (multiplan.pl)

```bash
curl -X POST http://localhost:8010/v1/budgets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Budżet Q1 2025",
    "period_start": "2025-01-01",
    "period_end": "2025-03-31",
    "scenario": "realistic",
    "categories": [
      {"name": "Wynagrodzenia", "planned": 150000, "actual": 0},
      {"name": "Marketing", "planned": 30000, "actual": 0},
      {"name": "IT", "planned": 20000, "actual": 0}
    ]
  }'
```

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (port 80)                         │
│                      Domain-based routing                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ repox   │ │multiplan│ │planbud- │ │planinw- │ │ alerts  │  │
│  │  :8000  │ │  :8010  │ │żetu:8011│ │estycji  │ │  :8003  │  │
│  │         │ │         │ │         │ │  :8012  │ │         │  │
│  │   HUB   │ │FINANCIAL│ │FINANCIAL│ │FINANCIAL│ │MONITOR  │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
│       │          │          │          │          │          │
├───────┴──────────┴──────────┴──────────┴──────────┴──────────┤
│                    SHARED CORE MODULES                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ Reports  │ │ Budget   │ │Investment│ │ Forecast │         │
│  │ Engine   │ │ Module   │ │ Module   │ │ Engine   │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
├─────────────────────────────────────────────────────────────────┤
│                       DATA LAYER                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ PostgreSQL │  │   Redis    │  │ Prometheus │               │
│  │   :5432    │  │   :6379    │  │   :9090    │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## 🔐 Environment Variables

Stwórz plik `.env` w katalogu `docker/`:

```env
# Database
POSTGRES_USER=analytica
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=analytica

# Redis
REDIS_URL=redis://redis:6379

# AI APIs (opcjonalne)
CLAUDE_API_KEY=sk-...
WHISPER_API_KEY=sk-...

# Payments (opcjonalne)
STRIPE_SECRET_KEY=sk_...
```

## 📈 Monitoring

- **Grafana**: http://localhost:3100 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🔤 DSL - Domain Specific Language

ANALYTICA DSL umożliwia budowanie pipeline'ów analitycznych w prosty sposób:

### Python SDK

```python
from analytica import Pipeline, run

# Fluent API
result = (Pipeline()
    .data.load('sales.csv')
    .transform.filter(year=2024)
    .metrics.sum('amount')
    .execute())

# DSL String
result = run('data.load("sales") | metrics.sum("amount")')
```

### JavaScript SDK

```javascript
import { Pipeline, Analytica } from '@analytica/sdk';

const result = await Pipeline()
  .data.load('sales.csv')
  .transform.filter({ year: 2024 })
  .metrics.sum('amount')
  .execute();
```

### CLI

```bash
# Run inline
analytica run 'data.load("sales") | metrics.sum("amount")'

# From file
analytica exec monthly_report.pipe --var year=2024

# Interactive builder
analytica build

# Start API server
analytica serve --port 8080
```

### REST API

```bash
curl -X POST http://localhost:8080/api/v1/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{"dsl": "data.load(\"sales\") | metrics.sum(\"amount\")"}'
```

### Dostępne Atomy

| Atom | Opis | Przykład |
|------|------|---------|
| `data` | Ładowanie danych | `data.load("file.csv")` |
| `transform` | Transformacje | `transform.filter(year=2024)` |
| `metrics` | Statystyki | `metrics.sum("amount")` |
| `report` | Raporty | `report.generate("pdf")` |
| `alert` | Alerty | `alert.threshold("x", "gt", 100)` |
| `budget` | Budżety | `budget.variance()` |
| `investment` | Inwestycje | `investment.roi()` |
| `forecast` | Prognozy | `forecast.predict(30)` |
| `export` | Eksport | `export.to_csv("out.csv")` |

📖 Pełna dokumentacja: [docs/DSL.md](docs/DSL.md)

## 🧪 Testowanie

```bash
# Test wszystkich API
make test-financial

# Pojedyncze testy
curl http://localhost:8010/health  # multiplan
curl http://localhost:8011/health  # planbudzetu
curl http://localhost:8012/health  # planinwestycji

# Test z jq
curl -s http://localhost:8012/v1/investments/calculators | jq .
```

## 📄 License

Proprietary - Softreck Sp. z o.o.

---

Built with ❤️ by Softreck R&D Team
