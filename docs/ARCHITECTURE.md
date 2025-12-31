# Analytica Platform - Architektura Systemu

## Spis Treści

- [Przegląd](#przegląd)
- [Architektura wysokopoziomowa](#architektura-wysokopoziomowa)
- [Komponenty systemu](#komponenty-systemu)
- [Produkty SaaS](#produkty-saas)
- [System punktów](#system-punktów)
- [API Reference](#api-reference)
- [Przepływ danych](#przepływ-danych)
- [Bezpieczeństwo](#bezpieczeństwo)

---

## Przegląd

Analytica to platforma SaaS składająca się z 4 specjalizowanych produktów finansowych, połączonych wspólnym językiem DSL i systemem punktów.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYTICA PLATFORM                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ PlanBudzetu │ │PlanInwestycji│ │  MultiPlan  │ │ Estymacja │ │
│  │    .pl      │ │     .pl     │ │     .pl     │ │    .pl    │ │
│  │   Budget    │ │  Investment │ │  Scenarios  │ │ Forecast  │ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬─────┘ │
│         │               │               │              │        │
│  ┌──────┴───────────────┴───────────────┴──────────────┴─────┐ │
│  │                    DSL PIPELINE ENGINE                     │ │
│  │    data.* | transform.* | metrics.* | report.* | alert.*  │ │
│  └────────────────────────────┬──────────────────────────────┘ │
│                               │                                 │
│  ┌────────────────────────────┴──────────────────────────────┐ │
│  │                    REST API + AUTH                         │ │
│  │              JWT Tokens | Points System                    │ │
│  └────────────────────────────┬──────────────────────────────┘ │
│                               │                                 │
│  ┌────────────────────────────┴──────────────────────────────┐ │
│  │                 Frontend UI / SDK / CLI                    │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architektura wysokopoziomowa

### Warstwy systemu

| Warstwa | Technologia | Opis |
|---------|-------------|------|
| **Frontend** | HTML/CSS/JS | Landing pages, Dashboard UI, Pipeline Builder |
| **API** | FastAPI | REST API, Authentication, Points management |
| **DSL Engine** | Python | Parser, Executor, Atom Registry |
| **Modules** | Python | Budget, Investment, Forecast, Reports, Alerts, Voice |
| **Storage** | In-memory / DB | Users, Sessions, Pipelines, Results |

### Struktura katalogów

```
analytica/
├── docs/                      # 📚 Dokumentacja
│   ├── ARCHITECTURE.md        # Ten plik
│   ├── API.md                 # REST API reference
│   ├── MODULES.md             # Dokumentacja modułów
│   ├── POINTS.md              # System punktów
│   └── DSL.md                 # Język DSL
│
├── src/
│   ├── api/                   # 🔌 REST API
│   │   ├── main.py            # FastAPI application
│   │   └── auth.py            # Authentication & Points
│   │
│   ├── dsl/                   # 🧩 DSL Engine
│   │   ├── core/
│   │   │   └── parser.py      # Tokenizer, Parser, Executor
│   │   └── atoms/
│   │       └── implementations.py  # Atom functions
│   │
│   ├── modules/               # 📦 Business Modules
│   │   ├── budget/            # Budget management
│   │   ├── investment/        # Investment analysis
│   │   ├── forecast/          # AI forecasting
│   │   ├── reports/           # Report generation
│   │   ├── alerts/            # Alert engine
│   │   └── voice/             # Voice commands
│   │
│   ├── frontend/              # 🖥️ Frontend
│   │   ├── landing/           # Landing pages (SaaS)
│   │   │   ├── index.html     # Main landing
│   │   │   ├── planbudzetu.html
│   │   │   ├── planinwestycji.html
│   │   │   ├── multiplan.html
│   │   │   ├── estymacja.html
│   │   │   └── login.html     # Auth page
│   │   ├── app.js             # Dashboard app
│   │   └── styles.css         # Styles
│   │
│   └── sdk/                   # 📱 SDKs
│       └── js/
│           └── analytica.js   # JavaScript SDK
│
├── tests/                     # 🧪 Tests
│   ├── unit/
│   ├── e2e/
│   └── integration/
│
└── docker/                    # 🐳 Docker
    └── docker-compose.yml
```

---

## Komponenty systemu

### 1. DSL Engine (`src/dsl/`)

Serce systemu - parser i executor języka DSL.

```python
# Przykład pipeline
data.load("sales.csv")
| transform.filter(year=2024)
| metrics.sum("amount")
| report.generate(format="pdf")
```

**Komponenty:**
- `DSLTokenizer` - tokenizacja kodu DSL
- `DSLParser` - parsowanie do AST
- `AtomRegistry` - rejestr dostępnych atomów
- `PipelineExecutor` - wykonywanie pipeline'ów

📄 Więcej: [DSL.md](./DSL.md)

### 2. REST API (`src/api/`)

FastAPI application z endpointami:

| Endpoint | Opis |
|----------|------|
| `POST /api/v1/auth/register` | Rejestracja |
| `POST /api/v1/auth/login` | Logowanie (JWT) |
| `GET /api/v1/auth/me` | Profil użytkownika |
| `POST /api/v1/auth/points/purchase` | Zakup punktów |
| `POST /api/v1/auth/points/use` | Wykorzystanie punktów |
| `POST /api/v1/pipeline/execute` | Wykonanie DSL |
| `POST /api/v1/pipeline/parse` | Parsowanie DSL |
| `GET /api/v1/atoms` | Lista atomów |

📄 Więcej: [API.md](./API.md)

### 3. Business Modules (`src/modules/`)

| Moduł | Funkcje | Atomy DSL |
|-------|---------|-----------|
| **Budget** | Budżety, wariancje, kategorie | `budget.load`, `budget.variance`, `budget.categorize` |
| **Investment** | ROI, NPV, IRR, payback | `investment.analyze`, `investment.roi`, `investment.npv` |
| **Forecast** | Prognozy AI, trendy | `forecast.predict`, `forecast.trend`, `forecast.smooth` |
| **Reports** | PDF, Excel, HTML | `report.generate`, `report.send`, `report.schedule` |
| **Alerts** | Progi, anomalie | `alert.threshold`, `alert.anomaly`, `alert.send` |
| **Voice** | Komendy głosowe | `voice.transcribe`, `voice.parse`, `voice.to_dsl` |

📄 Więcej: [MODULES.md](./MODULES.md)

### 4. Authentication (`src/api/auth.py`)

JWT-based authentication z systemem punktów:

```python
# Register → Login → Get Token → Use API
POST /api/v1/auth/register
  { "email": "...", "password": "...", "name": "..." }
  → { "access_token": "JWT...", "user": { "points_balance": 10 } }

# Użyj tokena w nagłówku
Authorization: Bearer <token>
```

📄 Więcej: [POINTS.md](./POINTS.md)

---

## Produkty SaaS

### PlanBudzetu.pl 📊

**Specjalizacja:** Planowanie i analiza budżetu

**Funkcje:**
- Analiza wariancji (plan vs wykonanie)
- Kategoryzacja wydatków (AI)
- Prognozy budżetowe
- Automatyczne raporty

**Atomy DSL:**
```
budget.load() | budget.variance() | budget.categorize()
```

**URL:** `/landing/planbudzetu.html`

---

### PlanInwestycji.pl 📈

**Specjalizacja:** Analiza opłacalności inwestycji

**Funkcje:**
- ROI (Return on Investment)
- NPV (Net Present Value)
- IRR (Internal Rate of Return)
- Payback period
- Analiza scenariuszy

**Atomy DSL:**
```
investment.analyze() | investment.roi() | investment.npv() | investment.irr()
```

**URL:** `/landing/planinwestycji.html`

---

### MultiPlan.pl 🎯

**Specjalizacja:** Planowanie wieloscenariuszowe

**Funkcje:**
- Scenariusze what-if
- Rolling forecast
- Analiza wrażliwości
- Automatyczne triggery

**Atomy DSL:**
```
investment.scenario(name="optimistic") | forecast.predict() | budget.compare()
```

**URL:** `/landing/multiplan.html`

---

### Estymacja.pl 🤖

**Specjalizacja:** Prognozowanie AI/ML

**Funkcje:**
- Predykcja trendów
- Wykrywanie sezonowości
- Detekcja anomalii
- Przedziały ufności

**Atomy DSL:**
```
forecast.predict(method="linear") | forecast.trend() | forecast.confidence()
```

**URL:** `/landing/estymacja.html`

---

## System punktów

### Model biznesowy

```
┌────────────────────────────────────────────────────────────────┐
│                     SYSTEM PUNKTÓW                              │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  💳 PAKIET PUNKTÓW          🔄 SUBSKRYPCJA      🏢 ENTERPRISE  │
│  ─────────────────          ─────────────       ────────────── │
│  • Jednorazowy zakup        • 199 zł/mies.      • Indywidualne │
│  • 50-10 000 pkt            • 250 pkt/mies.     • Zapytanie    │
│  • Ważność 12 mies.         • Rollover          • On-premise   │
│  • od 1 zł/pkt              • 0.80 zł/pkt       • Custom SLA   │
│                             • Roczna: 1 990 zł  • Integracje   │
│                             • +500 pkt bonus    • Dedykowany   │
│                                                   opiekun      │
└────────────────────────────────────────────────────────────────┘
```

### Przelicznik punktów

| Operacja | Koszt | Przykład |
|----------|-------|----------|
| Raport budżetowy | 1 pkt | `budget.variance() \| report.generate()` |
| Analiza ROI/NPV/IRR | 1 pkt | `investment.analyze()` |
| Scenariusz what-if | 1 pkt | `investment.scenario()` |
| Prognoza AI | 1 pkt | `forecast.predict()` |
| Alert | 0 pkt | `alert.threshold()` (darmowe) |
| Export | 0 pkt | `export.to_json()` (darmowe) |

📄 Więcej: [POINTS.md](./POINTS.md)

---

## API Reference

### Szybki start

```bash
# 1. Rejestracja
curl -X POST http://localhost:18000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123","name":"Jan"}'

# 2. Logowanie
curl -X POST http://localhost:18000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'
# → { "access_token": "eyJ...", "user": { "points_balance": 10 } }

# 3. Wykonanie DSL
curl -X POST http://localhost:18000/api/v1/pipeline/execute \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"dsl": "budget.create(name=\"Test\") | budget.variance()"}'
```

📄 Pełna dokumentacja: [API.md](./API.md)

---

## Przepływ danych

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Frontend│────▶│  API    │────▶│  DSL    │────▶│ Modules │
│   UI    │     │ + Auth  │     │ Engine  │     │         │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
     │               │               │               │
     │               ▼               │               ▼
     │         ┌─────────┐           │         ┌─────────┐
     │         │ Points  │           │         │ Results │
     │         │ System  │           │         │         │
     │         └─────────┘           │         └─────────┘
     │                               │               │
     └───────────────────────────────┴───────────────┘
                        Response
```

### Przykładowy flow

1. **User** → Loguje się przez `/landing/login.html`
2. **Frontend** → Wysyła JWT token do API
3. **API** → Weryfikuje token, sprawdza punkty
4. **DSL Engine** → Parsuje i wykonuje pipeline
5. **Modules** → Wykonują logikę biznesową
6. **API** → Odejmuje punkty, zwraca wynik
7. **Frontend** → Wyświetla wynik

---

## Bezpieczeństwo

### Authentication

- **JWT Tokens** - 24h validity
- **Password hashing** - SHA256 + salt
- **CORS** - Configurable origins

### Authorization

- **Bearer token** w nagłówku `Authorization`
- **Points check** przed operacjami płatnymi
- **Rate limiting** (planowane)

### Data

- **HTTPS** w produkcji
- **Input validation** - Pydantic models
- **SQL injection protection** - parametryzowane zapytania

---

## Port Mapping

| Domena | Port | URL | Opis |
|--------|------|-----|------|
| **repox.pl** | 18000 | http://localhost:18000 | Hub główny |
| analizowanie.pl | 8001 | http://localhost:8001 | General analytics |
| przeanalizuj.pl | 8002 | http://localhost:8002 | Voice commands |
| alerts.pl | 8003 | http://localhost:8003 | Monitoring |
| estymacja.pl | 8004 | http://localhost:8004 | Forecasting |
| retrospektywa.pl | 8005 | http://localhost:8005 | Historical |
| persony.pl | 8006 | http://localhost:8006 | Marketing |
| specyfikacja.pl | 8007 | http://localhost:8007 | Documentation |
| nisza.pl | 8008 | http://localhost:8008 | White-label |
| **multiplan.pl** | 8010 | http://localhost:8010 | Financial planning |
| **planbudzetu.pl** | 8011 | http://localhost:8011 | Budget management |
| **planinwestycji.pl** | 8012 | http://localhost:8012 | Investment analysis |

### Widoki dla KLIENTÓW (oferta, logowanie)

| URL | Opis |
|-----|------|
| http://localhost:18000/landing/ | **Strona główna** - oferta produktów SaaS |
| http://localhost:18000/landing/login.html | **Logowanie/Rejestracja** - panel klienta |
| http://localhost:18000/landing/planbudzetu.html | Oferta PlanBudzetu.pl |
| http://localhost:18000/landing/planinwestycji.html | Oferta PlanInwestycji.pl |
| http://localhost:18000/landing/multiplan.html | Oferta MultiPlan.pl |
| http://localhost:18000/landing/estymacja.html | Oferta Estymacja.pl |

### Widoki dla DEVELOPERÓW (narzędzia)

| URL | Opis |
|-----|------|
| http://localhost:18000/ui/ | Dashboard UI - Pipeline Builder z DSL Views |
| http://localhost:18000/docs | Swagger API docs |
| http://localhost:18000/redoc | ReDoc API docs |

---

## Linki do dokumentacji

| Dokument | Opis |
|----------|------|
| [README.md](../README.md) | Quick start i przegląd |
| [API.md](./API.md) | REST API reference |
| [MODULES.md](./MODULES.md) | Dokumentacja modułów |
| [POINTS.md](./POINTS.md) | System punktów |
| [DSL.md](./DSL.md) | Język DSL |
| [VIEWS_ROADMAP.md](./VIEWS_ROADMAP.md) | DSL-driven views |
| [ROADMAP.md](./ROADMAP.md) | Plan rozwoju |

---

## Uruchomienie

```bash
# Development
make up
# → http://localhost:18000/ui/          # Dashboard UI
# → http://localhost:18000/landing/     # Landing pages
# → http://localhost:18000/docs         # Swagger API docs

# Testy
make test
# lub
pytest tests/ -v
```

---

*Ostatnia aktualizacja: 2025-01-01*
