# ANALYTICA Modules Documentation

> Business logic modules for domain-specific functionality

## Overview

ANALYTICA uses a modular architecture where each module provides:
- **DSL Atoms** - Operations callable from DSL pipelines
- **API Routes** - REST endpoints for direct access
- **Calculators** - Business logic utilities

## Available Modules

| Module | Description | DSL Prefix |
|--------|-------------|------------|
| [Budget](#budget-module) | Budget management, variance analysis | `budget.*` |
| [Investment](#investment-module) | ROI, NPV, IRR calculations | `investment.*` |
| [Forecast](#forecast-module) | Time series forecasting | `forecast.*` |
| [Reports](#reports-module) | Report generation | `report.*` |
| [Alerts](#alerts-module) | Threshold monitoring | `alert.*` |
| [Voice](#voice-module) | Speech-to-text, NL→DSL | `voice.*` |

---

## Budget Module

**Location:** `src/modules/budget/`

### Features
- Budget creation and management
- Variance analysis (planned vs actual)
- Expense categorization
- Multi-scenario budgeting (optimistic/realistic/pessimistic)

### DSL Atoms

#### `budget.create`
Create a new budget.

```dsl
budget.create(name="Q1 2025", scenario="realistic")
```

**Parameters:**
- `name` (str) - Budget name
- `period_start` (str) - Start date (YYYY-MM-DD)
- `period_end` (str) - End date (YYYY-MM-DD)
- `scenario` (str) - One of: optimistic, realistic, pessimistic
- `lines` (list) - Budget line items

#### `budget.variance`
Calculate budget variance.

```dsl
budget.variance(planned=100000, actual=95000)
```

**Parameters:**
- `budget_id` (str) - Existing budget ID, or
- `planned` (float) - Planned amount
- `actual` (float) - Actual amount

**Returns:**
```json
{
  "planned": 100000,
  "actual": 95000,
  "variance": -5000,
  "variance_percent": -5.0,
  "status": "under"
}
```

#### `budget.categorize`
Categorize expenses automatically.

```dsl
data.from_input() | budget.categorize()
```

### Python Usage

```python
from src.modules.budget import BudgetCalculator, Budget, BudgetLine
from decimal import Decimal

# Calculate variance
result = BudgetCalculator.calculate_variance(
    planned=Decimal("100000"),
    actual=Decimal("95000")
)

# Create budget
budget = Budget(
    id="budget_001",
    name="Q1 2025",
    period_start=date(2025, 1, 1),
    period_end=date(2025, 3, 31),
)
budget.add_line(BudgetLine(
    category="marketing",
    name="Digital Ads",
    planned=Decimal("50000"),
    actual=Decimal("48000"),
))
```

---

## Investment Module

**Location:** `src/modules/investment/`

### Features
- ROI (Return on Investment) calculation
- NPV (Net Present Value) analysis
- IRR (Internal Rate of Return)
- Payback period calculation
- Risk assessment

### DSL Atoms

#### `investment.analyze`
Full investment analysis.

```dsl
investment.analyze(
  name="New Project",
  initial_investment=100000,
  discount_rate=0.12,
  cash_flows=[30000, 40000, 50000, 60000]
)
```

**Returns:**
```json
{
  "investment_id": "inv_abc12345",
  "name": "New Project",
  "roi": 80.0,
  "npv": 15234.56,
  "irr": 22.5,
  "payback_period": 2.67,
  "profitability_index": 1.15,
  "risk_level": "low",
  "recommendation": "proceed"
}
```

#### `investment.roi`
Calculate ROI only.

```dsl
investment.roi(initial_investment=100000, total_returns=180000)
```

#### `investment.npv`
Calculate NPV.

```dsl
investment.npv(
  initial_investment=100000,
  discount_rate=0.1,
  cash_flows=[30000, 40000, 50000]
)
```

#### `investment.irr`
Calculate Internal Rate of Return.

```dsl
investment.irr(
  initial_investment=100000,
  cash_flows=[30000, 40000, 50000, 60000]
)
```

#### `investment.payback`
Calculate payback period.

```dsl
investment.payback(
  initial_investment=100000,
  cash_flows=[30000, 40000, 50000]
)
```

### Python Usage

```python
from src.modules.investment import InvestmentCalculator
from decimal import Decimal

# Full analysis
result = InvestmentCalculator.calculate_npv(
    initial_investment=Decimal("100000"),
    cash_flows=[Decimal("30000"), Decimal("40000"), Decimal("50000")],
    discount_rate=Decimal("0.12")
)

# IRR calculation
irr = InvestmentCalculator.calculate_irr(
    initial_investment=Decimal("100000"),
    cash_flows=[Decimal("30000"), Decimal("40000"), Decimal("50000"), Decimal("60000")]
)
```

---

## Forecast Module

**Location:** `src/modules/forecast/`

### Features
- Moving average
- Exponential smoothing
- Linear trend analysis
- Multi-period forecasting
- Trend detection

### DSL Atoms

#### `forecast.predict`
Generate forecast predictions.

```dsl
forecast.predict(data=[100, 110, 120, 130], periods=3, method="linear")
```

**Parameters:**
- `data` (list) - Historical data points
- `periods` (int) - Number of periods to forecast
- `method` (str) - One of: linear, moving_average, exponential

**Returns:**
```json
{
  "method": "linear",
  "historical_count": 4,
  "predictions": [
    {"period": 5, "value": 140.0, "lower_bound": 130.0, "upper_bound": 150.0},
    {"period": 6, "value": 150.0, "lower_bound": 138.0, "upper_bound": 162.0},
    {"period": 7, "value": 160.0, "lower_bound": 146.0, "upper_bound": 174.0}
  ],
  "trend": "up"
}
```

#### `forecast.trend`
Analyze trend in data.

```dsl
forecast.trend(data=[100, 110, 120, 130])
```

**Returns:**
```json
{
  "trend": "up",
  "slope": 10.0,
  "intercept": 90.0,
  "data_points": 4
}
```

#### `forecast.smooth`
Apply smoothing to data.

```dsl
forecast.smooth(data=[100, 120, 110, 130], method="exponential", alpha=0.3)
```

### Python Usage

```python
from src.modules.forecast import ForecastCalculator, ForecastMethod

# Predict next 3 periods
predictions = ForecastCalculator.forecast_next(
    data=[100.0, 110.0, 120.0, 130.0],
    periods=3,
    method=ForecastMethod.LINEAR
)

# Detect trend
trend = ForecastCalculator.detect_trend([100.0, 110.0, 120.0, 130.0])
# Returns: TrendDirection.UP
```

---

## Reports Module

**Location:** `src/modules/reports/`

### Features
- Multiple output formats (PDF, Excel, HTML, JSON, CSV)
- Template-based reports
- Scheduled report generation
- Email/webhook distribution

### DSL Atoms

#### `report.generate`
Generate a report.

```dsl
report.generate(template="executive_summary", format="html", title="Q1 Report")
```

**Parameters:**
- `template` (str) - Template ID
- `format` (str) - Output format: html, json, csv, pdf, excel
- `title` (str) - Report title
- `data` (dict) - Report data

**Built-in Templates:**
- `executive_summary` - High-level overview
- `financial_report` - Detailed financials
- `budget_variance` - Budget vs actual

#### `report.schedule`
Schedule recurring report.

```dsl
report.schedule(template="executive_summary", frequency="weekly", recipients=["team@company.pl"])
```

**Frequencies:** once, daily, weekly, monthly, quarterly

#### `report.send`
Send report to recipients.

```dsl
report.send(report_id="report_123", recipients=["ceo@company.pl"], method="email")
```

### Python Usage

```python
from src.modules.reports import ReportGenerator

# Generate HTML report
html = ReportGenerator.generate_html(
    title="Q1 Summary",
    data={
        "summary": {"revenue": 1000000, "costs": 800000},
        "key_metrics": {"growth": "15%", "margin": "20%"}
    },
    sections=["summary", "key_metrics"]
)
```

---

## Alerts Module

**Location:** `src/modules/alerts/`

### Features
- Threshold-based alerts
- Anomaly detection
- Multi-channel notifications (email, webhook, Slack)
- Alert history

### DSL Atoms

#### `alert.threshold`
Check value against threshold.

```dsl
alert.threshold(metric="expenses", value=150000, operator="gt", threshold=100000)
```

**Operators:** gt, gte, lt, lte, eq, neq

**Returns:**
```json
{
  "metric": "expenses",
  "value": 150000,
  "threshold": 100000,
  "triggered": true,
  "message": "expenses (150000) exceeded threshold (100000)",
  "alert_id": "alert_abc123"
}
```

#### `alert.create`
Create an alert rule.

```dsl
alert.create(
  name="Budget Alert",
  metric="spending",
  operator="gt",
  threshold=50000,
  severity="warning",
  channels=["email"]
)
```

#### `alert.send`
Send alert notification.

```dsl
alert.send(channel="email", recipient="admin@company.pl", message="Alert!")
```

#### `alert.anomaly`
Detect anomaly in data.

```dsl
alert.anomaly(values=[100, 102, 98, 101, 99], current=150)
```

**Returns:**
```json
{
  "is_anomaly": true,
  "current_value": 150,
  "mean": 100.0,
  "std": 1.58,
  "lower_bound": 96.84,
  "upper_bound": 103.16,
  "deviation": 31.65
}
```

### Python Usage

```python
from src.modules.alerts import AlertEngine, AlertRule, ComparisonOperator

# Check threshold
result = AlertEngine.check_threshold(
    metric="budget",
    value=150000,
    operator="gt",
    threshold=100000
)

# Detect anomaly
anomaly = AlertEngine.detect_anomaly(
    values=[100.0, 102.0, 98.0, 101.0],
    current=150.0,
    std_multiplier=2.0
)
```

---

## Voice Module

**Location:** `src/modules/voice/`

### Features
- Speech-to-text transcription
- Voice command parsing
- Natural language to DSL conversion
- Support for Polish and English

### DSL Atoms

#### `voice.transcribe`
Transcribe audio to text.

```dsl
voice.transcribe(audio_url="https://...", language="pl")
```

#### `voice.parse`
Parse voice text into structured command.

```dsl
voice.parse(text="oblicz sumę sprzedaży")
```

**Returns:**
```json
{
  "raw_text": "oblicz sumę sprzedaży",
  "intent": "calculate",
  "entities": {"matched_groups": ["oblicz", "sumę", "sprzedaży"]},
  "dsl": "metrics.sum(\"sprzedaży\")",
  "confidence": 0.85
}
```

#### `voice.to_dsl`
Convert voice text directly to DSL.

```dsl
voice.to_dsl(text="wygeneruj raport miesięczny")
```

**Returns:**
```json
{
  "input": "wygeneruj raport miesięczny",
  "dsl": "report.generate(\"miesięczny\")",
  "intent": "report",
  "confidence": 0.85,
  "can_execute": true
}
```

### Supported Voice Commands (Polish)

| Command Pattern | Generated DSL |
|-----------------|---------------|
| "załaduj dane X" | `data.load("X")` |
| "oblicz sumę X" | `metrics.sum("X")` |
| "oblicz średnią X" | `metrics.avg("X")` |
| "wygeneruj raport X" | `report.generate("X")` |
| "prognozuj X na N dni" | `forecast.predict(N)` |
| "ustaw alert X powyżej N" | `alert.threshold("X", "gt", N)` |

### Python Usage

```python
from src.modules.voice import VoiceCommandParser

# Parse Polish voice command
command = VoiceCommandParser.parse("oblicz sumę sprzedaży")
print(command.dsl)  # metrics.sum("sprzedaży")
print(command.intent)  # calculate
print(command.confidence)  # 0.85
```

---

## Creating Custom Modules

### Module Structure

```python
from src.modules import BaseModule

class MyModule(BaseModule):
    name = "mymodule"
    version = "1.0.0"
    
    def get_routes(self) -> List[Any]:
        """Return FastAPI routes"""
        return []
    
    def get_atoms(self) -> Dict[str, Any]:
        """Return DSL atoms"""
        return {
            "mymodule.action": self.my_action,
        }
    
    def my_action(self, **kwargs):
        """Atom implementation"""
        value = kwargs.get("value", kwargs.get("_arg0"))
        return {"result": value * 2}
```

### Registering Module

```python
from src.modules import register_module
from mymodule import MyModule

register_module(MyModule())
```

---

## Views Module

**Location:** `src/modules/views/` + `src/dsl/atoms/implementations.py`

DSL atoms for generating view specifications that can be rendered dynamically by the frontend.

### Features
- Generate chart, table, card, KPI views from DSL
- Automatic column detection for tables
- Multiple views in single pipeline
- Data preservation through view chain

### DSL Atoms

#### `view.chart`
Generate chart view specification.

```dsl
data.from_input()
| view.chart(type="bar", x="month", y="sales", title="Sales Chart")
```

**Parameters:**
- `type` (str) - Chart type: bar, line, pie, area, scatter, donut, gauge
- `x` (str) - X-axis field name
- `y` (str) - Y-axis field name
- `series` (list) - Multiple series field names
- `title` (str) - Chart title
- `colors` (list) - Custom color palette
- `legend` (bool) - Show legend (default: true)

---

#### `view.table`
Generate table view specification.

```dsl
data.from_input()
| view.table(columns=["name", "amount", "date"], title="Transactions")
```

**Parameters:**
- `columns` (list) - Column names or specs (auto-detected if empty)
- `title` (str) - Table title
- `sortable` (bool) - Enable sorting (default: true)
- `filterable` (bool) - Enable filtering (default: true)
- `paginate` (bool) - Enable pagination (default: true)
- `page_size` (int) - Rows per page (default: 10)

---

#### `view.card`
Generate metric card specification.

```dsl
metrics.sum("amount")
| view.card(value="sum", title="Total Sales", icon="💰", style="success")
```

**Parameters:**
- `value` (str) - Field name for main value
- `title` (str) - Card title
- `format` (str) - Value format: number, currency, percent
- `icon` (str) - Icon (emoji or icon name)
- `style` (str) - Card style: default, success, warning, danger, info
- `trend` (str) - Field name for trend indicator

---

#### `view.kpi`
Generate KPI widget specification.

```dsl
data.from_input()
| view.kpi(value="current", target="goal", title="Progress", icon="📈")
```

**Parameters:**
- `value` (str) - Field name for current value
- `target` (str) - Field name for target value
- `title` (str) - KPI title
- `format` (str) - Value format
- `icon` (str) - Icon
- `progress` (bool) - Show progress bar (default: true)

---

#### `view.grid`
Generate grid layout specification.

```dsl
view.grid(columns=3, gap=20)
```

**Parameters:**
- `columns` (int) - Number of columns (default: 2)
- `gap` (int) - Gap between items in pixels (default: 16)
- `items` (list) - List of view specifications

---

#### `view.dashboard`
Generate complete dashboard specification.

```dsl
view.dashboard(layout="grid", title="Sales Dashboard", refresh=30)
```

**Parameters:**
- `layout` (str) - Layout type: grid, flex, stack
- `widgets` (list) - List of widget specifications
- `title` (str) - Dashboard title
- `refresh` (int) - Auto-refresh interval in seconds

---

#### `view.text`
Generate text/markdown view.

```dsl
view.text(content="**Summary**: Total sales increased by 15%", format="markdown")
```

**Parameters:**
- `content` (str) - Text content (supports {{field}} placeholders)
- `format` (str) - Format type: text, markdown, html
- `title` (str) - Title

---

#### `view.list`
Generate list view specification.

```dsl
data.from_input()
| view.list(primary="name", secondary="description", icon="icon")
```

**Parameters:**
- `primary` (str) - Primary text field
- `secondary` (str) - Secondary text field
- `icon` (str) - Icon field

### Example: Multi-View Dashboard

```dsl
data.from_input()
| view.card(value="total", title="Total Sales", icon="💰", style="success")
| view.chart(type="bar", x="month", y="sales", title="Monthly Sales")
| view.table(columns=["month", "sales", "growth"], title="Details")
```

**Result:**
```json
{
  "data": [...],
  "views": [
    {"type": "card", "title": "Total Sales", ...},
    {"type": "chart", "chart_type": "bar", ...},
    {"type": "table", "columns": [...], ...}
  ]
}
```

### Frontend Rendering

Views are rendered by `ViewRenderer.js`:

```javascript
import { createViewRenderer } from '/ui/view-renderer.js';

const renderer = createViewRenderer('#container');
renderer.render(apiResponse);
```

---

## Powiązana dokumentacja

| Dokument | Opis |
|----------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architektura systemu |
| [API.md](./API.md) | REST API reference |
| [DSL.md](./DSL.md) | Język DSL - składnia, atomy |
| [POINTS.md](./POINTS.md) | System punktów - cennik |
| [ROADMAP.md](./ROADMAP.md) | Plan rozwoju |

---

*Last updated: 2025-01-01*
