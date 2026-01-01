# ANALYTICA DSL

> Domain Specific Language for Analytics Pipelines

## Menu

- [Dokumentacja (INDEX)](INDEX.md)
- [README](../README.md)
- [Architektura](ARCHITECTURE.md)
- [API](API.md)
- [Moduły](MODULES.md)
- [System punktów](POINTS.md)
- [Compliance](COMPLIANCE.md)
- [Roadmap](ROADMAP.md)
- [Views Roadmap](VIEWS_ROADMAP.md)
- [Mapa plików projektu](../PROJECT_FILES.md)

## Overview

ANALYTICA DSL is a powerful, expressive language for building analytics pipelines. It provides:

- **Fluent API** for Python and JavaScript
- **DSL Syntax** for text-based pipeline definitions
- **CLI Tool** for shell-based execution
- **REST API** for remote execution
- **WebSocket** for streaming results

## Quick Start

### Python

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

### JavaScript

```javascript
import { Pipeline, Analytica } from '@analytica/sdk';

// Fluent API
const result = await Pipeline()
  .data.load('sales.csv')
  .transform.filter({ year: 2024 })
  .metrics.sum('amount')
  .execute();

// DSL String
const result = await Analytica.run('data.load("sales") | metrics.sum("amount")');
```

### CLI

```bash
# Run inline DSL
analytica run 'data.load("sales") | metrics.sum("amount")'

# Execute from file
analytica exec pipeline.dsl --var year=2024

# Interactive builder
analytica build
```

### REST API

```bash
# Execute pipeline
curl -X POST http://localhost:18000/api/v1/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{"dsl": "data.load(\"sales\") | metrics.sum(\"amount\")"}'
```

## DSL Syntax

### Basic Pipe Syntax

```dsl
# Single atom
data.load("sales.csv")

# Pipe chain
data.load("sales") | transform.filter(year=2024) | metrics.sum("amount")

# Multi-line
data.load("sales")
| transform.filter(year=2024)
| metrics.sum("amount")
```

### Variables

```dsl
# Define variable
$year = 2024
$threshold = 10000

# Use variable
data.load("sales") | transform.filter(year=$year)
```

### Named Pipelines

```dsl
@pipeline monthly_report:
    $month = "2024-01"
    data.load("sales")
    | transform.filter(month=$month)
    | metrics.calculate(["sum", "avg"])
    | report.generate("pdf")
```

### Parameters

```dsl
# Positional argument
data.load("sales.csv")

# Named arguments
transform.filter(year=2024, status="active")

# Mixed
data.load("sales", format="csv", encoding="utf-8")

# Array values
metrics.calculate(["sum", "avg", "count"])
```

## Atoms Reference

### data - Data Operations

```dsl
data.load(source)               # Load from file/dataset
data.query(sql)                 # Execute SQL query
data.fetch(url)                 # Fetch from URL
data.from_input()               # Use input data
```

### transform - Data Transformation

```dsl
transform.filter(field=value)   # Filter by conditions
transform.map(func, field)      # Apply function
transform.sort(by, order)       # Sort data
transform.limit(n)              # Limit results
transform.group_by(field1, ..)  # Group by fields
transform.aggregate(by, func)   # Aggregate data
transform.select(field1, ...)   # Select fields
transform.rename(old=new)       # Rename fields
```

### metrics - Statistics

```dsl
metrics.calculate(["sum", "avg"])  # Multiple metrics
metrics.sum(field)                 # Sum
metrics.avg(field)                 # Average
metrics.count()                    # Count
metrics.variance(field)            # Variance
metrics.percentile(field, p)       # Percentile
```

### report - Report Generation

```dsl
report.generate(format, template)  # Generate report
report.schedule(cron, recipients)  # Schedule
report.send(to)                    # Send report
```

### alert - Alerts & Notifications

```dsl
alert.when(condition)              # Define condition
alert.send(channel, message)       # Send alert
alert.threshold(field, op, value)  # Threshold check
```

### budget - Budget Operations

```dsl
budget.create(name)                # Create budget
budget.load(budget_id)             # Load budget
budget.compare(scenario)           # Compare scenarios
budget.variance()                  # Calculate variance
budget.categorize(by)              # Categorize items
```

### investment - Investment Analysis

```dsl
investment.analyze(params)         # Full analysis
investment.roi()                   # Calculate ROI
investment.npv(rate)               # Calculate NPV
investment.irr()                   # Calculate IRR
investment.payback()               # Payback period
investment.scenario(name, mult)    # Apply scenario
```

### forecast - Predictions

```dsl
forecast.predict(periods, model)   # Generate forecast
forecast.trend()                   # Analyze trend
forecast.seasonality()             # Seasonality
forecast.confidence(level)         # Confidence intervals
```

### export - Export Data

```dsl
export.to_csv(path)                # Export to CSV
export.to_json(path)               # Export to JSON
export.to_excel(path)              # Export to Excel
export.to_api(url, method)         # Send to API
```

### deploy - Deployment & CI/CD

```dsl
# Containers
deploy.docker(image="app", tag="v1", port=8000)
deploy.compose(services=["api", "db"], file="docker-compose.yml")

# Kubernetes
deploy.kubernetes(namespace="prod", replicas=3, image="app:v1")
deploy.helm(chart="analytica", release="prod", values="values.yaml")

# CI/CD Pipelines
deploy.github_actions(workflow="deploy", triggers=["push"])
deploy.gitlab_ci(stages=["build", "test", "deploy"])
deploy.jenkins(pipeline="Jenkinsfile")

# Cloud Platforms
deploy.aws(service="ecs", cluster="prod", region="eu-central-1")
deploy.vercel(project="my-app", prod=true)
deploy.netlify(site="my-site", prod=true)

# Application Targets
deploy.web(framework="react", build="npm run build")
deploy.desktop(framework="electron", platforms=["win", "mac", "linux"])
deploy.mobile(framework="react-native", platforms=["ios", "android"])

# Launch & Export
deploy.launch(platform="desktop", dir="/path/to/project")
deploy.bundle(target="standalone", include_runtime=true)
deploy.export_dsl(path="pipeline.dsl", format="native")
```

## Examples

### Budget Analysis (planbudzetu.pl)

```dsl
@pipeline budget_report:
    $budget_id = "budget_2024"
    budget.load($budget_id)
    | budget.variance()
    | report.generate("pdf", "budget_report")
    | report.send(["finance@company.pl"])
```

### Investment ROI (planinwestycji.pl)

```dsl
@pipeline roi_analysis:
    data.from_input()
    | investment.analyze(discount_rate=0.12)
    | investment.roi()
    | investment.npv(rate=0.1)
    | investment.payback()
    | report.generate("pdf", "investment_proposal")
```

### Sales Forecast (estymacja.pl)

```dsl
@pipeline sales_forecast:
    data.load("historical_sales")
    | forecast.predict(periods=90, model="prophet")
    | forecast.confidence(level=0.95)
    | report.generate("pdf", "forecast_report")
```

### Alert Pipeline (alerts.pl)

```dsl
@pipeline budget_alert:
    budget.load("current_budget")
    | metrics.calculate(["sum"])
    | alert.threshold("utilization", "gt", 0.9)
    | alert.send("slack", "Budget exceeded 90%!")
```

### More Examples (end-to-end)

#### Execute with variables + input_data (curl)

```bash
curl -X POST http://localhost:8012/api/v1/pipeline/execute \
  -H "Content-Type: application/json" \
  -d '{
    "dsl": "@pipeline quick_roi:\n  data.from_input() | investment.analyze(discount_rate=$rate) | investment.roi()",
    "variables": {"rate": 0.12},
    "input_data": {"initial_investment": 500000, "total_return": 740000},
    "domain": "planinwestycji.pl"
  }'
```

#### Validate DSL (curl)

```bash
curl -X POST http://localhost:8011/api/v1/pipeline/validate \
  -H "Content-Type: application/json" \
  -d '{"dsl": "data.load(\"sales\") | metrics.sum(\"amount\")"}'
```

#### Parse DSL to AST (curl)

```bash
curl -X POST http://localhost:8011/api/v1/pipeline/parse \
  -H "Content-Type: application/json" \
  -d '{"dsl": "data.load(\"sales\") | transform.filter(year=2024) | metrics.calculate([\"sum\",\"avg\"])"}'
```

#### Full set of pipelines

See `examples/pipelines.dsl` for a larger collection of ready-to-run pipelines.

## API Reference

### Python SDK

```python
from analytica import Pipeline, Analytica, configure

# Configure
configure(
    api_url='http://localhost:18000',
    domain='planbudzetu.pl',
    local_execution=True
)

# Create pipeline
p = Pipeline()
p.data.load('sales')
p.metrics.sum('amount')

# Get DSL
dsl = p.to_dsl()

# Execute
result = p.execute()

# Async
result = await p.execute_async()

# Client operations
Analytica.run(dsl)
Analytica.parse(dsl)
Analytica.validate(dsl)
Analytica.atoms()
```

### JavaScript SDK

```javascript
import { Pipeline, Analytica, configure } from '@analytica/sdk';

// Configure
configure({
  apiUrl: 'http://localhost:18000',
  domain: 'planbudzetu.pl'
});

// Create pipeline
const p = Pipeline()
  .data.load('sales')
  .metrics.sum('amount');

// Get DSL
const dsl = p.toDSL();

// Execute
const result = await p.execute();

// Client operations
await Analytica.run(dsl);
await Analytica.parse(dsl);
await Analytica.validate(dsl);
await Analytica.atoms();
```

### CLI Commands

```bash
# Run DSL
analytica run '<dsl>'
analytica run - < pipeline.dsl

# Execute file
analytica exec pipeline.dsl
analytica exec pipeline.yaml --var key=value

# Validate
analytica validate pipeline.dsl

# List atoms
analytica list-atoms

# Interactive builder
analytica build

# Start API server
analytica serve --port 18000

# Convert formats
analytica convert pipeline.dsl --format json
```

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/pipeline/execute | Execute pipeline |
| POST | /api/v1/pipeline/parse | Parse DSL to AST |
| POST | /api/v1/pipeline/validate | Validate syntax |
| GET | /api/v1/atoms | List available atoms |
| POST | /api/v1/atoms/{type}/{action} | Execute single atom |
| GET | /api/v1/pipelines | List stored pipelines |
| POST | /api/v1/pipelines | Store pipeline |
| POST | /api/v1/pipelines/{id}/run | Run stored pipeline |

## Integration

### With Docker

```bash
# Start API (repox.pl)
make up-repox

# Run pipeline
curl http://localhost:18000/api/v1/pipeline/execute \
  -d '{"dsl": "data.load(\"sales\") | metrics.sum(\"amount\")"}'
```

### With Python Application

```python
from analytica import Pipeline

# In your application
def analyze_sales(year: int):
    return (Pipeline()
        .data.load('sales')
        .transform.filter(year=year)
        .metrics.calculate(['sum', 'avg', 'count'])
        .execute())
```

### With Frontend (React)

```jsx
import { Pipeline, Analytica } from '@analytica/sdk';

function Dashboard() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    Pipeline()
      .data.load('dashboard_data')
      .metrics.calculate(['sum', 'avg'])
      .execute()
      .then(setData);
  }, []);
  
  return <div>{JSON.stringify(data)}</div>;
}
```

### Universal UI (built-in)

Each domain API serves a universal UI at `GET /ui/`.

It reuses the JS DSL SDK (`/ui/sdk/analytica.js`) and works with both:

- Direct container ports, e.g. `http://localhost:8011/ui/` (planbudzetu.pl)
- Nginx domain routing, where `/api/*` is rewritten to `/` upstream

Typical URLs:

```text
http://localhost:18000/ui/   (repox.pl)
http://localhost:8010/ui/    (multiplan.pl)
http://localhost:8011/ui/    (planbudzetu.pl)
http://localhost:8012/ui/    (planinwestycji.pl)
```

The UI supports:

- Selecting atom type + action from `GET /api/v1/atoms`
- Editing step params as JSON
- Generating DSL via the SDK (`Pipeline().toDSL()`)
- Calling `parse`, `validate`, `execute` via `/api/v1/pipeline/*`

## Extending DSL

### Custom Atoms

```python
from analytica.dsl import AtomRegistry, PipelineContext

@AtomRegistry.register("custom", "my_action")
def custom_my_action(ctx: PipelineContext, param1: str, **params):
    """Custom atom implementation"""
    data = ctx.get_data()
    # Process data
    result = process(data, param1)
    return result
```

### Custom Pipeline File Format

```yaml
# pipeline.yaml
name: my_pipeline
version: "1.0"
domain: planbudzetu.pl

variables:
  year: 2024
  threshold: 10000

steps:
  - atom:
      type: data
      action: load
      params:
        source: sales.csv
  - atom:
      type: transform
      action: filter
      params:
        year: $year
  - atom:
      type: metrics
      action: sum
      params:
        field: amount
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DSL Layer                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  DSL Text   │  │   Fluent    │  │   REST/WS   │              │
│  │   Parser    │  │    API      │  │    API      │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │   Pipeline Executor   │                          │
│              └───────────┬───────────┘                          │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │    Atom Registry      │                          │
│              └───────────┬───────────┘                          │
│                          ▼                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │  Data   │ │Transform│ │ Metrics │ │ Budget  │ │Forecast │    │
│  │  Atoms  │ │  Atoms  │ │  Atoms  │ │  Atoms  │ │  Atoms  │    │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Powiązana dokumentacja

| Dokument | Opis |
|----------|------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architektura systemu |
| [API.md](./API.md) | REST API reference |
| [POINTS.md](./POINTS.md) | System punktów - cennik |
| [MODULES.md](./MODULES.md) | Moduły biznesowe |

---

## License

Apache 2

*Last updated: 2025-01-01*
