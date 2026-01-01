# DSL Pipelines - Examples

> Core DSL syntax examples and pipeline templates

## Files

| File | Description |
|------|-------------|
| `pipelines.dsl` | Complete DSL examples for all modules |
| `views_pipelines.dsl` | View-specific pipeline examples |
| `usage_python.py` | Python SDK usage examples |
| `usage_javascript.js` | JavaScript SDK usage examples |

## Quick Examples

### Basic Pipeline

```dsl
data.load("sales.csv")
| transform.filter(year=2024)
| metrics.sum("amount")
| view.card(value="sum", title="Total Sales", icon="💰")
```

### Budget Analysis

```dsl
budget.load("budget_2024")
| budget.variance()
| view.chart(type="bar", x="category", y="variance")
| report.generate(format="pdf")
```

### Investment ROI

```dsl
investment.analyze(
    initial_investment=500000,
    discount_rate=0.12,
    cash_flows=[150000, 200000, 250000, 300000]
)
| view.card(value="npv", title="NPV", icon="💰")
| view.card(value="roi", title="ROI %", icon="📈")
```

### Forecast

```dsl
data.load("historical_sales")
| forecast.predict(periods=12, method="linear")
| view.chart(type="line", x="period", y="predicted")
```

## Run Examples

```bash
# Via API
curl -X POST http://localhost:18000/api/v1/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{"dsl": "data.load(\"sales\") | metrics.sum(\"amount\")"}'

# Via Python
python usage_python.py

# Via JavaScript
node usage_javascript.js
```
