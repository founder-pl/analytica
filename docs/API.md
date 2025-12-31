# ANALYTICA REST API Documentation

> Complete reference for the ANALYTICA REST API

## Base URLs

| Domain | Port | URL | UI |
|--------|------|-----|-----|
| **repox.pl** | 18000 | `http://localhost:18000` | `/ui/` |
| analizowanie.pl | 8001 | `http://localhost:8001` | `/ui/` |
| przeanalizuj.pl | 8002 | `http://localhost:8002` | `/ui/` |
| alerts.pl | 8003 | `http://localhost:8003` | `/ui/` |
| estymacja.pl | 8004 | `http://localhost:8004` | `/ui/` |
| retrospektywa.pl | 8005 | `http://localhost:8005` | `/ui/` |
| persony.pl | 8006 | `http://localhost:8006` | `/ui/` |
| specyfikacja.pl | 8007 | `http://localhost:8007` | `/ui/` |
| nisza.pl | 8008 | `http://localhost:8008` | `/ui/` |
| **multiplan.pl** | 8010 | `http://localhost:8010` | `/ui/` |
| **planbudzetu.pl** | 8011 | `http://localhost:8011` | `/ui/` |
| **planinwestycji.pl** | 8012 | `http://localhost:8012` | `/ui/` |

### Dostępne widoki web (repox.pl - port 18000)

| Endpoint | Opis |
|----------|------|
| `/ui/` | Dashboard UI - Pipeline Builder z DSL Views |
| `/landing/` | Landing pages - strony produktowe SaaS |
| `/landing/login.html` | Logowanie i rejestracja |
| `/docs` | Swagger UI - interaktywna dokumentacja API |
| `/redoc` | ReDoc - alternatywna dokumentacja API |

## Authentication

API wykorzystuje JWT (JSON Web Tokens) do uwierzytelniania.

### Rejestracja

```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secret123",
  "name": "Jan Kowalski",
  "company": "Firma Sp. z o.o."
}
```

**Response (201):**
```json
{
  "access_token": "eyJ1c2VyX2lkIjog...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "user_abc12345",
    "email": "user@example.com",
    "name": "Jan Kowalski",
    "company": "Firma Sp. z o.o.",
    "points_balance": 10,
    "plan": "free"
  }
}
```

> 💡 Nowi użytkownicy otrzymują **10 punktów GRATIS**

---

### Logowanie

```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ1c2VyX2lkIjog...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "user_abc12345",
    "email": "user@example.com",
    "name": "Jan Kowalski",
    "points_balance": 150,
    "plan": "subscription"
  }
}
```

**Demo user:**
- Email: `demo@analytica.pl`
- Password: `demo123`
- Points: 100

---

### Profil użytkownika

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user_abc12345",
  "email": "user@example.com",
  "name": "Jan Kowalski",
  "company": "Firma Sp. z o.o.",
  "points_balance": 150,
  "plan": "subscription",
  "created_at": "2024-12-01T10:00:00"
}
```

---

### Wylogowanie

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## System Punktów

### Sprawdzenie salda

```http
GET /api/v1/auth/points
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "user_abc12345",
  "points_balance": 150,
  "plan": "subscription",
  "transactions": [
    {
      "id": "tx_001",
      "type": "purchase",
      "amount": 200,
      "timestamp": "2024-12-01T10:00:00"
    },
    {
      "id": "tx_002",
      "type": "usage",
      "amount": -5,
      "description": "Pipeline execution",
      "timestamp": "2024-12-15T14:30:00"
    }
  ]
}
```

---

### Zakup punktów

```http
POST /api/v1/auth/points/purchase
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "amount": 100,
  "payment_method": "card"
}
```

**Response (200):**
```json
{
  "user_id": "user_abc12345",
  "points_balance": 250,
  "transaction_id": "tx_003",
  "amount": 100,
  "type": "purchase"
}
```

---

### Wykorzystanie punktów

```http
POST /api/v1/auth/points/use
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "amount": 5,
  "description": "Manual deduction"
}
```

**Response (200):**
```json
{
  "user_id": "user_abc12345",
  "points_balance": 145,
  "transaction_id": "tx_004",
  "amount": 5,
  "type": "usage"
}
```

**Response (402 - brak punktów):**
```json
{
  "detail": "Insufficient points. Need 5, have 3",
  "code": "INSUFFICIENT_POINTS"
}
```

---

### Przelicznik punktów

| Operacja | Koszt |
|----------|-------|
| `report.generate()` | 1 pkt |
| `budget.variance()` | 1 pkt |
| `investment.analyze()` | 1 pkt |
| `forecast.predict()` | 1 pkt |
| `data.*`, `transform.*`, `metrics.*` | 0 pkt |
| `alert.*`, `export.*` | 0 pkt |

📄 Więcej: [POINTS.md](./POINTS.md)

## Common Endpoints

All domains expose these endpoints:

### Health & Info

```http
GET /
```
Returns domain info and status.

**Response:**
```json
{
  "status": "healthy",
  "domain": "repox.pl",
  "port": 8000,
  "modules": ["reports", "alerts", "voice", "forecast", "budget", "investment"],
  "ui_url": "/ui/"
}
```

---

```http
GET /api/v1/health
```
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "dsl-api",
  "domain": "repox.pl"
}
```

---

## DSL Pipeline API

### List Available Atoms

```http
GET /api/v1/atoms
```

**Response:**
```json
{
  "data": ["load", "query", "fetch", "from_input"],
  "transform": ["filter", "sort", "limit", "group_by", "aggregate", "select", "rename"],
  "metrics": ["calculate", "sum", "avg", "count", "min", "max"],
  "budget": ["create", "variance", "categorize", "compare"],
  "investment": ["analyze", "roi", "npv", "irr", "payback", "scenario"],
  "forecast": ["predict", "trend", "smooth"],
  "alert": ["threshold", "send", "create"],
  "report": ["generate", "schedule", "send"],
  "export": ["to_csv", "to_json", "to_excel", "to_api"]
}
```

---

### Get Atom Type Actions

```http
GET /api/v1/atoms/{atom_type}
```

**Parameters:**
- `atom_type` - Type of atom (data, transform, metrics, etc.)

**Response:**
```json
{
  "type": "metrics",
  "actions": ["calculate", "sum", "avg", "count", "min", "max"]
}
```

---

### Execute Single Atom

```http
POST /api/v1/atoms/{atom_type}/{action}
```

**Request Body:**
```json
{
  "input_data": [1, 2, 3, 4, 5],
  "params": {}
}
```

**Response:**
```json
{
  "status": "success",
  "result": 5
}
```

---

### Parse Pipeline

```http
POST /api/v1/pipeline/parse
```

Parse DSL code without executing it.

**Request Body:**
```json
{
  "dsl": "data.load(\"sales.csv\") | metrics.sum(\"amount\")"
}
```

**Response:**
```json
{
  "name": null,
  "steps": [
    {
      "atom": {
        "type": "data",
        "action": "load",
        "params": {"_arg0": "sales.csv"}
      },
      "condition": null,
      "on_error": "stop"
    },
    {
      "atom": {
        "type": "metrics",
        "action": "sum",
        "params": {"_arg0": "amount"}
      },
      "condition": null,
      "on_error": "stop"
    }
  ],
  "variables": {},
  "dsl_normalized": "data.load(\"sales.csv\") | metrics.sum(\"amount\")",
  "json_representation": {...}
}
```

---

### Validate Pipeline

```http
POST /api/v1/pipeline/validate
```

Validate DSL syntax and check for unknown atoms.

**Request Body:**
```json
{
  "dsl": "data.load(\"test\") | unknown.action()"
}
```

**Response:**
```json
{
  "valid": false,
  "errors": ["Unknown atom: unknown.action"],
  "warnings": []
}
```

---

### Execute Pipeline

```http
POST /api/v1/pipeline/execute
```

Execute a DSL pipeline.

**Request Body:**
```json
{
  "dsl": "data.from_input() | metrics.count()",
  "variables": {},
  "input_data": [1, 2, 3, 4, 5],
  "domain": null
}
```

**Response:**
```json
{
  "execution_id": "exec_20241231100000_abc12345",
  "status": "success",
  "result": 5,
  "logs": [
    "Executing: data.from_input()",
    "Executing: metrics.count()"
  ],
  "errors": [],
  "execution_time_ms": 2.34
}
```

---

## Stored Pipelines API

### List Stored Pipelines

```http
GET /api/v1/pipelines
```

**Response:**
```json
{
  "pipelines": [
    {
      "id": "pipe_abc12345",
      "name": "Daily Sales Report",
      "dsl": "data.load(\"sales\") | metrics.sum(\"amount\")",
      "description": "Calculate daily sales",
      "tags": ["sales", "daily"],
      "created_at": "2024-12-31T10:00:00"
    }
  ],
  "count": 1
}
```

---

### Create Pipeline

```http
POST /api/v1/pipelines
```

**Request Body:**
```json
{
  "name": "My Pipeline",
  "dsl": "data.load(\"test\") | metrics.count()",
  "description": "Test pipeline",
  "tags": ["test"]
}
```

**Response:**
```json
{
  "id": "pipe_abc12345",
  "name": "My Pipeline",
  "dsl": "data.load(\"test\") | metrics.count()",
  "description": "Test pipeline",
  "tags": ["test"],
  "created_at": "2024-12-31T10:00:00"
}
```

---

### Get Pipeline

```http
GET /api/v1/pipelines/{pipeline_id}
```

---

### Delete Pipeline

```http
DELETE /api/v1/pipelines/{pipeline_id}
```

---

### Run Stored Pipeline

```http
POST /api/v1/pipelines/{pipeline_id}/run
```

**Request Body:**
```json
{
  "variables": {"year": 2024},
  "input_data": [...]
}
```

---

## Domain-Specific Endpoints

### Reports Module

```http
GET /v1/reports
```
List available report templates.

```http
POST /v1/reports/generate
```
Generate a report.

**Request Body:**
```json
{
  "template": "executive_summary",
  "data": {...},
  "format": "html"
}
```

---

### Budgets Module

```http
GET /v1/budgets
```
List budgets.

```http
POST /v1/budgets
```
Create budget.

**Request Body:**
```json
{
  "name": "Q1 2025 Budget",
  "period_start": "2025-01-01",
  "period_end": "2025-03-31",
  "scenario": "realistic",
  "categories": [
    {"name": "Marketing", "planned": 50000}
  ]
}
```

---

### Investments Module

```http
POST /v1/investments/analyze
```
Full investment analysis.

**Request Body:**
```json
{
  "name": "New Project",
  "initial_investment": 100000,
  "discount_rate": 0.12,
  "cash_flows": [
    {"period": 1, "amount": 30000},
    {"period": 2, "amount": 40000},
    {"period": 3, "amount": 50000}
  ]
}
```

**Response:**
```json
{
  "investment_id": "inv_abc12345",
  "name": "New Project",
  "roi": 20.0,
  "npv": 15234.56,
  "irr": 18.5,
  "payback_period": 2.67,
  "profitability_index": 1.15,
  "risk_level": "medium",
  "recommendation": "proceed"
}
```

---

### Alerts Module

```http
GET /v1/alerts
```
List active alerts.

```http
POST /v1/alerts
```
Create alert rule.

**Request Body:**
```json
{
  "name": "Budget Exceeded",
  "metric": "expenses",
  "operator": "gt",
  "threshold": 100000,
  "severity": "warning",
  "channels": ["email"]
}
```

---

### Forecast Module

```http
POST /v1/forecast/predict
```
Generate forecast.

**Request Body:**
```json
{
  "data": [100, 110, 120, 130, 140],
  "periods": 3,
  "method": "linear"
}
```

**Response:**
```json
{
  "method": "linear",
  "historical_count": 5,
  "predictions": [
    {"period": 6, "value": 150.0, "lower_bound": 140.0, "upper_bound": 160.0},
    {"period": 7, "value": 160.0, "lower_bound": 148.0, "upper_bound": 172.0},
    {"period": 8, "value": 170.0, "lower_bound": 156.0, "upper_bound": 184.0}
  ],
  "trend": "up"
}
```

---

## Error Handling

All errors return appropriate HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 402 | Payment Required - Insufficient points |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data |
| 500 | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

---

## Rate Limiting

Currently no rate limiting. Future versions will implement:
- 1000 requests/minute per IP
- Higher limits for authenticated users

---

## SDK Examples

### Python

```python
from analytica import Pipeline, run

# Fluent API
result = (Pipeline()
    .data.load("sales.csv")
    .transform.filter(year=2024)
    .metrics.sum("amount")
    .execute())

# DSL string
result = run('data.load("sales") | metrics.sum("amount")')
```

### JavaScript

```javascript
import { Analytica } from '@analytica/sdk';

const client = new Analytica('http://localhost:8000');

// Execute DSL
const result = await client.execute('data.load("sales") | metrics.count()');

// With input data
const result = await client.execute(
  'data.from_input() | metrics.sum("value")',
  { input_data: [{value: 10}, {value: 20}] }
);
```

### cURL

```bash
# Execute pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{"dsl": "data.from_input() | metrics.count()", "input_data": [1,2,3]}'

# Parse pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/parse \
  -H "Content-Type: application/json" \
  -d '{"dsl": "data.load(\"test\") | metrics.sum(\"x\")"}'
```

---

## WebSocket (Future)

Real-time pipeline execution updates:

```
ws://localhost:8000/ws/pipeline/{execution_id}
```

---

## OpenAPI Schema

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Powiązana dokumentacja

| Dokument | Opis |
|----------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architektura systemu |
| [POINTS.md](./POINTS.md) | System punktów - cennik, modele zakupu |
| [DSL.md](./DSL.md) | Język DSL - składnia, atomy |
| [MODULES.md](./MODULES.md) | Moduły biznesowe |

---

*Last updated: 2025-01-01*
