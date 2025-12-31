# ANALYTICA - Plan Kontynuacji i Refaktoryzacji Architektury

> DSL Schema Version: **2.0.0**

## Menu

- [Dokumentacja (INDEX)](INDEX.md)
- [README](../README.md)
- [Architektura](ARCHITECTURE.md)
- [API](API.md)
- [DSL](DSL.md)
- [Moduły](MODULES.md)
- [System punktów](POINTS.md)
- [Compliance](COMPLIANCE.md)
- [Views Roadmap](VIEWS_ROADMAP.md)
- [Mapa plików projektu](../PROJECT_FILES.md)

---

## 🌐 NOWE: Multiplatformowy DSL z Universal Data Sources

### Formaty DSL (v2.0)
| Format | Opis | Status |
|--------|------|--------|
| Native | `source.http() \| transform.filter()` | ✅ |
| JSON | Portable JSON schema | ✅ |
| YAML | Human-readable config | ✅ |
| TOML | Config-friendly | ✅ |
| XML | Enterprise integration | ✅ |

### Data Sources (source.*)

#### 🌐 Web Protocols
| Atom | Protokół | Przykład |
|------|----------|----------|
| `source.http` | HTTP/REST | `source.http(url="https://api.example.com")` |
| `source.graphql` | GraphQL | `source.graphql(endpoint="...", query="{...}")` |
| `source.websocket` | WebSocket | `source.websocket(url="wss://...")` |
| `source.sse` | Server-Sent Events | `source.sse(url="https://...")` |

#### 📡 IoT Protocols
| Atom | Protokół | Zastosowanie |
|------|----------|--------------|
| `source.mqtt` | MQTT/MQTTS | Sensory, smart home |
| `source.coap` | CoAP | Constrained devices |
| `source.amqp` | AMQP | RabbitMQ, message queues |
| `source.modbus` | Modbus TCP/RTU | Industrial PLC/SCADA |
| `source.opcua` | OPC-UA | Industrial automation |
| `source.serial` | Serial/RS232 | Arduino, sensors |

#### 🗄️ Databases
| Atom | Baza | Przykład |
|------|------|----------|
| `source.sql` | PostgreSQL, MySQL, SQLite | `source.sql(dsn="postgresql://...", query="...")` |
| `source.mongodb` | MongoDB | `source.mongodb(uri="...", collection="...")` |
| `source.redis` | Redis | `source.redis(url="...", key="...")` |
| `source.elasticsearch` | Elasticsearch | `source.elasticsearch(url="...", index="...")` |
| `source.influxdb` | InfluxDB | `source.influxdb(url="...", bucket="...")` |

#### ☁️ Cloud Storage
| Atom | Provider | Przykład |
|------|----------|----------|
| `source.s3` | AWS S3 | `source.s3(bucket="...", key="...")` |
| `source.azure_blob` | Azure Blob | `source.azure_blob(container="...")` |
| `source.gcs` | Google Cloud Storage | `source.gcs(bucket="...")` |

#### 📊 Streaming Platforms
| Atom | Platforma | Przykład |
|------|-----------|----------|
| `source.kafka` | Apache Kafka | `source.kafka(brokers="...", topic="...")` |
| `source.nats` | NATS | `source.nats(url="...", subject="...")` |

#### 🔌 External APIs
| Atom | Kategoria | Providers |
|------|-----------|-----------|
| `source.api` | Generic | OpenWeather, GitHub, Stripe, Slack, Discord |
| `source.weather` | Pogoda | OpenWeather, WeatherAPI |
| `source.finance` | Finanse | AlphaVantage, Binance, Polygon |
| `source.social` | Social Media | Twitter, Reddit |
| `source.blockchain` | Web3 | Ethereum, Bitcoin |

#### 📁 Files & Special
| Atom | Typ | Formaty |
|------|-----|---------|
| `source.file` | Local files | CSV, JSON, XML, Parquet, Excel |
| `source.ftp` | FTP/SFTP | Remote files |
| `source.scrape` | Web scraping | HTML parsing |
| `source.email` | IMAP | Email inbox |
| `source.calendar` | Calendar | Google, iCal |

### Data Sinks (sink.*)

#### 📤 Outputs
| Kategoria | Atomy |
|-----------|-------|
| Web | `sink.http`, `sink.webhook`, `sink.websocket` |
| IoT | `sink.mqtt`, `sink.modbus` |
| Databases | `sink.sql`, `sink.mongodb`, `sink.redis`, `sink.elasticsearch`, `sink.influxdb` |
| Cloud | `sink.s3`, `sink.azure_blob`, `sink.gcs` |
| Streaming | `sink.kafka` |
| Files | `sink.file` |
| Notifications | `sink.email`, `sink.sms`, `sink.slack`, `sink.discord`, `sink.telegram`, `sink.push` |
| Display | `sink.display`, `sink.dashboard` |

---

## 📊 Obecny Stan

### Co działa:
- ✅ DSL Parser z obsługą pozycyjnych i nazwanych parametrów
- ✅ Fluent API (PipelineBuilder) dla Python
- ✅ REST API z pełnym CRUD dla pipeline'ów
- ✅ Universal UI dostępne pod `/ui/` każdej domeny
- ✅ 12 domen API (repox, multiplan, planbudzetu, planinwestycji, alerts, etc.)
- ✅ Moduł Compliance (KSeF, CBAM, ESG, ViDA)
- ✅ Testy: unit, integration, e2e

### Architektura obecna:
```
┌─────────────────────────────────────────────────────────────┐
│                      NGINX (port 80)                        │
├─────────────────────────────────────────────────────────────┤
│  12x FastAPI Services (api-repox, api-multiplan, etc.)      │
│  Każdy serwis = ten sam kod + inna konfiguracja YAML        │
├─────────────────────────────────────────────────────────────┤
│  Shared: PostgreSQL, Redis, Prometheus, Grafana             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Plan Refaktoryzacji (Fazy)

### FAZA 1: Konsolidacja Core (Priorytet: WYSOKI)

#### 1.1 Wydzielenie pakietu `analytica-core`
```
src/
├── analytica/              # Nowy namespace package
│   ├── __init__.py
│   ├── core/
│   │   ├── config.py       # Unified configuration
│   │   ├── domain.py       # Domain registry & routing
│   │   └── exceptions.py   # Custom exceptions
│   ├── dsl/
│   │   ├── parser.py       # DSL parser (refactored)
│   │   ├── atoms/          # Atom implementations
│   │   ├── builder.py      # PipelineBuilder
│   │   └── executor.py     # Pipeline executor
│   ├── api/
│   │   ├── app.py          # FastAPI app factory
│   │   ├── routes/         # Modular routes
│   │   └── middleware/     # Auth, logging, etc.
│   └── compliance/         # Compliance modules
```

#### 1.2 Zadania:
- [x] Przenieść `src/dsl/core/parser.py` (900+ linii) do mniejszych modułów ✅
- [x] Wydzielić `AtomRegistry` do osobnego pliku (`registry.py`) ✅
- [x] Stworzyć `PipelineExecutor` jako osobną klasę (`executor.py`) ✅
- [x] Wydzielić `PipelineContext` (`context.py`) ✅
- [x] Dodać abstrakcję `AtomHandler` z walidacją parametrów ✅

### FAZA 2: Usprawnienie DSL (Priorytet: WYSOKI) ✅ UKOŃCZONE

#### 2.1 Automatyczna walidacja parametrów atomów
```python
# Nowa wersja z dekoratorem (ZAIMPLEMENTOWANE):
from src.dsl.core import AtomRegistry, atom_params, Required, Optional

@AtomRegistry.register("data", "load")
@atom_params(
    source=Required(str, description="Data source path or URL"),
    format=Optional(str, default="auto", description="Data format")
)
def data_load(ctx, source: str, format: str = "auto"):
    ...
```

#### 2.2 Zadania:
- [x] Stworzyć system typów dla parametrów (`Required`, `Optional`, `OneOf`) ✅
- [x] Automatyczne mapowanie `_arg0` -> pierwszy wymagany parametr ✅
- [x] Generowanie dokumentacji atomów z dekoratorów ✅
- [x] Walidacja w czasie parsowania (nie tylko wykonania) ✅

### FAZA 3: Modularyzacja API (Priorytet: ŚREDNI)

#### 3.1 Plugin system dla modułów
```python
# config/domains/multiplan.yaml
modules:
  - budget
  - forecast
  - reports

# Automatyczne ładowanie:
# src/analytica/modules/budget/
# src/analytica/modules/forecast/
# src/analytica/modules/reports/
```

#### 3.2 Zadania:
- [ ] Stworzyć interfejs `Module` z metodami `register_routes()`, `register_atoms()`
- [ ] Lazy loading modułów na podstawie konfiguracji
- [ ] Dependency injection dla modułów

### FAZA 4: Skalowalność (Priorytet: ŚREDNI)

#### 4.1 Event-driven architecture
```
┌─────────┐    ┌─────────┐    ┌─────────┐
│   API   │───▶│  Queue  │───▶│ Workers │
│ Gateway │    │ (Redis) │    │ (Celery)│
└─────────┘    └─────────┘    └─────────┘
```

#### 4.2 Zadania:
- [ ] Dodać Celery dla długich pipeline'ów
- [ ] WebSocket dla real-time updates
- [ ] Rate limiting per domain
- [ ] Caching wyników pipeline'ów (Redis)

### FAZA 5: Developer Experience (Priorytet: ŚREDNI)

#### 5.1 CLI improvements
```bash
# Nowe komendy
analytica atom list                    # Lista atomów
analytica atom info data.load          # Dokumentacja atomu
analytica pipeline validate file.dsl   # Walidacja
analytica pipeline run file.dsl --watch # Hot reload
analytica domain create mydomain.pl    # Generator domeny
```

#### 5.2 Zadania:
- [ ] Rozbudować CLI (`src/cli/`)
- [ ] Dodać generator projektów (cookiecutter)
- [ ] VS Code extension z syntax highlighting dla .dsl
- [ ] Playground online (WASM?)

### FAZA 6: Observability (Priorytet: NISKI)

#### 6.1 Distributed tracing
- [ ] OpenTelemetry integration
- [ ] Trace ID przez cały pipeline
- [ ] Jaeger/Zipkin export

#### 6.2 Metryki
- [ ] Pipeline execution time per atom
- [ ] Error rates per domain
- [ ] Custom business metrics

---

## 📁 Proponowana Struktura Plików (po refaktoryzacji)

```
analytica/
├── src/
│   └── analytica/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py           # Configuration management
│       │   ├── domain.py           # Domain registry
│       │   ├── exceptions.py       # Custom exceptions
│       │   └── types.py            # Shared types
│       ├── dsl/
│       │   ├── __init__.py
│       │   ├── tokenizer.py        # DSL tokenizer
│       │   ├── parser.py           # DSL parser
│       │   ├── builder.py          # PipelineBuilder
│       │   ├── executor.py         # PipelineExecutor
│       │   ├── context.py          # PipelineContext
│       │   └── atoms/
│       │       ├── __init__.py
│       │       ├── registry.py     # AtomRegistry
│       │       ├── base.py         # Base atom classes
│       │       ├── data.py         # data.* atoms
│       │       ├── transform.py    # transform.* atoms
│       │       ├── metrics.py      # metrics.* atoms
│       │       ├── budget.py       # budget.* atoms
│       │       ├── investment.py   # investment.* atoms
│       │       ├── forecast.py     # forecast.* atoms
│       │       ├── alert.py        # alert.* atoms
│       │       ├── report.py       # report.* atoms
│       │       └── export.py       # export.* atoms
│       ├── api/
│       │   ├── __init__.py
│       │   ├── factory.py          # App factory
│       │   ├── dependencies.py     # FastAPI dependencies
│       │   ├── middleware/
│       │   │   ├── auth.py
│       │   │   ├── logging.py
│       │   │   └── cors.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── pipeline.py     # /api/v1/pipeline/*
│       │       ├── atoms.py        # /api/v1/atoms/*
│       │       ├── domain.py       # Domain-specific routes
│       │       └── health.py       # Health checks
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── base.py             # Module interface
│       │   ├── budget/
│       │   ├── investment/
│       │   ├── forecast/
│       │   ├── reports/
│       │   └── alerts/
│       ├── compliance/
│       │   ├── __init__.py
│       │   ├── ksef.py
│       │   ├── cbam.py
│       │   ├── esg.py
│       │   └── vida.py
│       ├── sdk/
│       │   ├── python/             # Python SDK (pip install analytica)
│       │   └── js/                 # JS SDK (@analytica/sdk)
│       └── cli/
│           ├── __init__.py
│           └── main.py             # CLI entry point
├── config/
│   ├── analytica.yaml
│   └── domains/
├── docker/
├── tests/
├── docs/
│   ├── DSL.md
│   ├── COMPLIANCE.md
│   ├── ROADMAP.md                  # Ten plik
│   └── API.md
└── examples/
    └── pipelines/
```

---

## 🚀 Quick Wins (do zrobienia teraz)

1. **Rozbicie `parser.py`** - 900+ linii to za dużo
2. **Automatyczne mapowanie `_arg0`** - usunąć boilerplate z atomów
3. **Dokumentacja API** - OpenAPI schema export
4. **CI/CD** - GitHub Actions dla testów

---

## 📅 Timeline (propozycja)

| Faza | Czas | Priorytet |
|------|------|-----------|
| Faza 1: Konsolidacja Core | 2-3 dni | 🔴 Wysoki |
| Faza 2: Usprawnienie DSL | 2-3 dni | 🔴 Wysoki |
| Faza 3: Modularyzacja API | 3-4 dni | 🟡 Średni |
| Faza 4: Skalowalność | 1 tydzień | 🟡 Średni |
| Faza 5: Developer Experience | 1 tydzień | 🟡 Średni |
| Faza 6: Observability | 3-4 dni | 🟢 Niski |

---

## 📚 Dokumentacja

| Dokument | Opis | Status |
|----------|------|--------|
| [README.md](../README.md) | Główna dokumentacja | ✅ |
| [docs/DSL.md](DSL.md) | DSL reference | ✅ |
| [docs/COMPLIANCE.md](COMPLIANCE.md) | Moduł zgodności | ✅ |
| [docs/ROADMAP.md](ROADMAP.md) | Plan rozwoju (ten plik) | ✅ |
| docs/API.md | REST API reference | 📝 TODO |
| docs/ARCHITECTURE.md | Architektura systemu | 📝 TODO |
| docs/CONTRIBUTING.md | Dla kontrybutorów | 📝 TODO |

---

*Ostatnia aktualizacja: 2024-12-31*
