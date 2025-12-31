# DSL-Driven Views - Roadmap

## Przegląd

System DSL-driven views pozwala na generowanie dynamicznych widoków UI bezpośrednio z pipeline'ów DSL. Backend generuje specyfikację widoków w JSON, a frontend (`ViewRenderer.js`) renderuje je do HTML.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DSL-DRIVEN VIEWS ARCHITECTURE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DSL Pipeline:                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ data.from_input()                                         │  │
│  │ | metrics.sum("amount")                                   │  │
│  │ | view.card(value="sum", title="Total", icon="💰")        │  │
│  │ | view.chart(type="bar", x="month", y="sales")            │  │
│  │ | view.table(columns=["month", "sales"])                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Backend Response (JSON):                                  │  │
│  │ {                                                         │  │
│  │   "data": {...},                                          │  │
│  │   "views": [                                              │  │
│  │     {"type": "card", "title": "Total", ...},              │  │
│  │     {"type": "chart", "chart_type": "bar", ...},          │  │
│  │     {"type": "table", "columns": [...], ...}              │  │
│  │   ]                                                       │  │
│  │ }                                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Frontend ViewRenderer:                                    │  │
│  │ ┌────────┐ ┌────────────┐ ┌────────────┐                 │  │
│  │ │ Card   │ │   Chart    │ │   Table    │                 │  │
│  │ │ 💰     │ │ ████       │ │ ┌─┬─┬─┐    │                 │  │
│  │ │ Total  │ │ ██ █ ██    │ │ │ │ │ │    │                 │  │
│  │ └────────┘ └────────────┘ └────────────┘                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Status implementacji

### ✅ Faza 1: Core (UKOŃCZONE)

| Komponent | Status | Opis |
|-----------|--------|------|
| `view.chart` | ✅ | Bar, line, pie, area, donut, gauge |
| `view.table` | ✅ | Auto-columns, sorting, pagination |
| `view.card` | ✅ | Metryki, ikony, style, trendy |
| `view.kpi` | ✅ | Progress bar, target vs actual |
| `view.grid` | ✅ | Grid layout dla wielu widoków |
| `view.dashboard` | ✅ | Kompletny dashboard z widgetami |
| `view.text` | ✅ | Text, markdown, HTML |
| `view.list` | ✅ | Lista z primary/secondary |
| `ViewRenderer.js` | ✅ | Frontend renderer |
| Testy jednostkowe | ✅ | 24/24 passed |

### 🔄 Faza 2: Enhanced Charts (W TRAKCIE)

| Komponent | Status | Planowane |
|-----------|--------|-----------|
| Interaktywne wykresy | 🔄 | Hover, click events |
| Animacje | 🔄 | Smooth transitions |
| Responsywność | 🔄 | Auto-resize |
| Eksport wykresów | ⏳ | PNG, SVG export |
| Drilldown | ⏳ | Kliknij → szczegóły |

### ⏳ Faza 3: Advanced Features (PLANOWANE)

| Komponent | Status | Planowane |
|-----------|--------|-----------|
| `view.form` | ⏳ | Formularze wejściowe |
| `view.map` | ⏳ | Mapy geograficzne |
| `view.timeline` | ⏳ | Timeline events |
| `view.tree` | ⏳ | Hierarchiczne dane |
| `view.pivot` | ⏳ | Pivot tables |
| Real-time updates | ⏳ | WebSocket streaming |
| Theming | ⏳ | Dark/light mode |

### ⏳ Faza 4: Dashboard Builder (PLANOWANE)

| Komponent | Status | Planowane |
|-----------|--------|-----------|
| Drag & drop | ⏳ | Wizualne układanie widgetów |
| Save/load layouts | ⏳ | Zapisywanie dashboardów |
| Sharing | ⏳ | Udostępnianie dashboardów |
| Scheduled refresh | ⏳ | Auto-odświeżanie |
| Export PDF | ⏳ | Eksport raportów |

---

## Przykłady użycia

### Prosty raport

```dsl
data.load("sales.csv")
| transform.filter(year=2024)
| metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
| view.card(value="sum", title="Total Sales", icon="💰", style="success")
| view.card(value="avg", title="Average Sale", icon="📊")
| view.card(value="count", title="Transactions", icon="🔢")
```

### Dashboard z wykresem i tabelą

```dsl
data.from_input()
| view.chart(type="bar", x="month", y="revenue", title="Monthly Revenue")
| view.table(columns=["month", "revenue", "growth"], title="Details")
```

### KPI Dashboard

```dsl
data.from_input()
| view.kpi(value="current_sales", target="sales_target", title="Sales Goal", icon="🎯")
| view.kpi(value="customers", target="customer_target", title="New Customers", icon="👥")
| view.chart(type="gauge", title="Performance")
```

### Multi-View z Grid

```dsl
data.load("metrics.json")
| view.grid(columns=3)
| view.card(value="revenue", title="Revenue", style="success")
| view.card(value="costs", title="Costs", style="warning")  
| view.card(value="profit", title="Profit", style="info")
| view.chart(type="line", x="date", y="value", title="Trend")
| view.table(title="Transaction Log")
```

---

## API Response Format

```json
{
  "status": "success",
  "execution_id": "exec_123",
  "result": {
    "data": {
      "total": 125000,
      "average": 2500,
      "count": 50,
      "items": [...]
    },
    "views": [
      {
        "type": "card",
        "id": "card_1",
        "title": "Total Sales",
        "value_field": "total",
        "format": "currency",
        "icon": "💰",
        "style": "success"
      },
      {
        "type": "chart",
        "id": "chart_1",
        "title": "Monthly Sales",
        "chart_type": "bar",
        "x_field": "month",
        "y_field": "sales",
        "show_legend": true,
        "show_grid": true
      },
      {
        "type": "table",
        "id": "table_1",
        "title": "Details",
        "columns": [
          {"field": "month", "header": "Month"},
          {"field": "sales", "header": "Sales", "format": "currency"}
        ],
        "sortable": true,
        "paginate": true,
        "page_size": 10
      }
    ]
  },
  "execution_time_ms": 45.2
}
```

---

## Frontend Integration

### Vanilla JS

```javascript
import { createViewRenderer } from '/ui/view-renderer.js';

// Initialize renderer
const renderer = createViewRenderer('#dashboard-container', {
  theme: 'light',
  locale: 'pl-PL',
  currency: 'PLN'
});

// Fetch and render
const response = await fetch('/api/v1/pipeline/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ dsl: '...' })
});

const data = await response.json();
renderer.render(data.result);
```

### React Integration (planowane)

```jsx
import { ViewRenderer } from '@analytica/react';

function Dashboard({ pipelineResult }) {
  return (
    <ViewRenderer 
      data={pipelineResult}
      theme="light"
      onViewClick={(view, data) => console.log(view, data)}
    />
  );
}
```

---

## Harmonogram

| Faza | Zakres | ETA |
|------|--------|-----|
| **Faza 1** | Core views | ✅ Ukończone |
| **Faza 2** | Enhanced charts | Q1 2025 |
| **Faza 3** | Advanced features | Q2 2025 |
| **Faza 4** | Dashboard builder | Q3 2025 |

---

## Powiązana dokumentacja

| Dokument | Opis |
|----------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architektura systemu |
| [MODULES.md](./MODULES.md) | Dokumentacja modułów (w tym Views) |
| [DSL.md](./DSL.md) | Język DSL |
| [API.md](./API.md) | REST API reference |

---

*Last updated: 2025-01-01*
