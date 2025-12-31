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

## See Also

- [DSL Documentation](DSL.md)
- [API Reference](API.md)
- [Architecture Roadmap](ROADMAP.md)

---

*Last updated: 2024-12-31*
