# ANALYTICA Framework

> **Universal Analytics Framework - Multi-Domain Platform**
> 
> Jeden core. Wiele domen. Nieskończone możliwości.

## Menu

- [Dokumentacja (INDEX)](docs/INDEX.md)
- [Architektura](docs/ARCHITECTURE.md)
- [API](docs/API.md)
- [DSL](docs/DSL.md)
- [Moduły](docs/MODULES.md)
- [System punktów](docs/POINTS.md)
- [Compliance](docs/COMPLIANCE.md)
- [Roadmap](docs/ROADMAP.md)
- [Views Roadmap](docs/VIEWS_ROADMAP.md)
- [Mapa plików projektu](PROJECT_FILES.md)

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

| Domena | Typ | Port | URL | UI |
|--------|-----|------|-----|-----|
| **repox.pl** | Hub | 18000 | http://localhost:18000 | `/ui/` |
| analizowanie.pl | General | 8001 | http://localhost:8001 | `/ui/` |
| przeanalizuj.pl | Voice | 8002 | http://localhost:8002 | `/ui/` |
| alerts.pl | Monitoring | 8003 | http://localhost:8003 | `/ui/` |
| estymacja.pl | Forecasting | 8004 | http://localhost:8004 | `/ui/` |
| retrospektywa.pl | Historical | 8005 | http://localhost:8005 | `/ui/` |
| persony.pl | Marketing | 8006 | http://localhost:8006 | `/ui/` |
| specyfikacja.pl | Documentation | 8007 | http://localhost:8007 | `/ui/` |
| nisza.pl | White-label | 8008 | http://localhost:8008 | `/ui/` |
| **multiplan.pl** | 💰 Financial | 8010 | http://localhost:8010 | `/ui/` |
| **planbudzetu.pl** | 💰 Financial | 8011 | http://localhost:8011 | `/ui/` |
| **planinwestycji.pl** | 💰 Financial | 8012 | http://localhost:8012 | `/ui/` |

### Dostępne widoki web

| URL | Opis |
|-----|------|
| http://localhost:18000/ui/ | Dashboard UI (Pipeline Builder) |
| http://localhost:18000/landing/ | Landing pages (SaaS) |
| http://localhost:18000/landing/login.html | Logowanie/Rejestracja |
| http://localhost:18000/docs | Swagger API docs |

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

- Pełna mapa plików: [PROJECT_FILES.md](PROJECT_FILES.md)
- Opis architektury i komponentów: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

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

# Testy
make test                  # Unit tests
make test-all              # Wszystkie testy
make test-e2e              # E2E (Docker)
make test-e2e-dind         # E2E (Docker-in-Docker)
make test-gui              # GUI (Playwright)

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

### DSL-Driven Views (NEW!)

Generuj dynamiczne widoki UI bezpośrednio z DSL:

```dsl
data.from_input()
| view.card(value="total", title="Total Sales", icon="💰", style="success")
| view.chart(type="bar", x="month", y="sales", title="Monthly Sales")
| view.table(columns=["month", "sales", "growth"])
```

**Dostępne widoki:**
- `view.chart` - Wykresy (bar, line, pie, area, donut, gauge)
- `view.table` - Tabele z sortowaniem i paginacją
- `view.card` - Karty metryczne z ikonami
- `view.kpi` - Wskaźniki KPI z progress bar
- `view.grid` - Grid layout
- `view.dashboard` - Kompletny dashboard

📄 Dokumentacja: [docs/VIEWS_ROADMAP.md](docs/VIEWS_ROADMAP.md)

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
analytica serve --port 18000
```

### REST API

```bash
curl -X POST http://localhost:18000/api/v1/pipeline/execute \
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
| `deploy` | Deployment & CI/CD | `deploy.docker("app")` |
| `view` | UI Components | `view.chart(type="bar")` |

📖 Pełna dokumentacja: [docs/DSL.md](docs/DSL.md)

## 🖥️ Universal UI

Każde API domenowe udostępnia wbudowany interfejs pod `/ui/`:

| Domena | URL |
|--------|-----|
| repox.pl | http://localhost:18000/ui/ |
| multiplan.pl | http://localhost:8010/ui/ |
| planbudzetu.pl | http://localhost:8011/ui/ |
| planinwestycji.pl | http://localhost:8012/ui/ |

UI pozwala na:
- Wizualne budowanie pipeline'ów DSL
- Podgląd wygenerowanego DSL
- Wykonywanie pipeline'ów (parse/validate/execute)
- Przeglądanie dostępnych atomów

## 📚 Dokumentacja

- Pełne menu dokumentacji: [docs/INDEX.md](docs/INDEX.md)
- [docs/MODULES.md](docs/MODULES.md) - Moduły: Budget, Investment, Forecast, Reports, Alerts, Voice
- [docs/COMPLIANCE.md](docs/COMPLIANCE.md) - Moduł zgodności: KSeF, CBAM, ESG, ViDA
- [docs/ROADMAP.md](docs/ROADMAP.md) - Plan rozwoju i refaktoryzacji architektury
- [examples/pipelines.dsl](examples/pipelines.dsl) - Przykłady pipeline'ów DSL

### Landing Pages (SaaS)

| Produkt | URL | Specjalizacja |
|---------|-----|---------------|
| **Analytica** | `/landing/` | Strona główna ekosystemu |
| **PlanBudzetu.pl** | `/landing/planbudzetu.html` | Planowanie budżetu |
| **PlanInwestycji.pl** | `/landing/planinwestycji.html` | Analiza inwestycji |
| **MultiPlan.pl** | `/landing/multiplan.html` | Planowanie scenariuszowe |
| **Estymacja.pl** | `/landing/estymacja.html` | Prognozowanie AI |
| **Logowanie** | `/landing/login.html` | Rejestracja i logowanie |

## 🧪 Testowanie

```bash
# Unit tests
make test

# Wszystkie testy (unit + integration)
make test-all

# E2E (Docker)
make test-e2e
make test-e2e-build
make test-e2e-keep

# E2E (Docker-in-Docker)
make test-e2e-dind
make test-e2e-dind-build
make test-e2e-dind-keep
make logs-e2e-dind

# Debug (Docker-in-Docker, keep)
export DOCKER_HOST=tcp://localhost:23750
docker ps

# GUI (Playwright)
make test-gui
make test-gui-headed
make test-gui-docker

# Health-checks domen
curl http://localhost:8010/health  # multiplan
curl http://localhost:8011/health  # planbudzetu
curl http://localhost:8012/health  # planinwestycji
```

## 📄 License



---

Built with ❤️ by Softreck R&D Team

---

## 🏛️ Compliance Module (2025-2030)

ANALYTICA zawiera kompletny moduł zgodności z regulacjami prawnymi:

### 🇵🇱 Polska
| Regulacja | Termin | Status |
|-----------|--------|--------|
| **KSeF** - Krajowy System e-Faktur | 02.2026 | ✅ Gotowy |
| **E-Doręczenia** - doręczenia elektroniczne | 01.2026 | ✅ Gotowy |

### 🇪🇺 Unia Europejska
| Regulacja | Termin | Status |
|-----------|--------|--------|
| **CSRD/ESG** - raportowanie zrównoważonego rozwoju | 2025-2027 | ✅ Gotowy |
| **CBAM** - mechanizm węglowy | 2026 | ✅ Gotowy |
| **ViDA** - VAT in Digital Age | 2025-2030 | ✅ Gotowy |
| **DAC7/DAC8** - wymiana informacji platform | 2025 | ✅ Gotowy |

### Szybki start

```python
from analytica.compliance import ComplianceChecker

# Sprawdź wszystkie regulacje dla firmy
checker = ComplianceChecker(
    company_name="Moja Firma Sp. z o.o.",
    nip="1234567890",
    country="PL",
    employees=150,
    revenue_eur=10000000
)

# Raport zgodności
results = checker.check_all()

# Harmonogram wdrożeń
timeline = checker.get_timeline()
for item in timeline:
    print(f"{item['date']} - {item['regulation']}: {item['action']}")
```

### Przykłady użycia

#### KSeF - Faktura elektroniczna
```python
from analytica.compliance import create_simple_invoice, KSeFClient

invoice = create_simple_invoice(
    seller_nip="1234567890",
    seller_name="Sprzedawca",
    buyer_nip="0987654321",
    buyer_name="Kupujący",
    items=[{"name": "Usługa", "quantity": 1, "unit_price": 1000, "vat": "23"}]
)

with KSeFClient(nip="1234567890", token="xxx") as client:
    response = client.send_invoice(invoice)
```

#### CBAM - Oblicz zobowiązanie
```python
from analytica.compliance import CBAMCalculator

liability = CBAMCalculator.calculate_cbam_liability(
    emissions_tco2=Decimal("100"),
    carbon_price_paid_eur=Decimal("500")
)
print(f"Do zapłaty: {liability['net_liability_eur']} EUR")
```

#### ESG - Kalkulator CO2
```python
from analytica.compliance import CarbonCalculator

scope2 = CarbonCalculator.calculate_scope2(
    electricity_kwh=Decimal("500000"),
    country="pl"
)
print(f"Emisje Scope 2: {scope2.amount_tonnes_co2e} tCO2e")
```

📖 Pełna dokumentacja: [docs/COMPLIANCE.md](docs/COMPLIANCE.md)
