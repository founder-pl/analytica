# API Microservice Example

> REST API microservice built with Analytica DSL

## 🎯 What You'll Build

A production-ready API microservice with:
- DSL-powered data processing endpoints
- Authentication & authorization
- Rate limiting
- Metrics & monitoring
- Docker & Kubernetes deployment

## 📁 Structure

```
api-microservice/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── src/
│   ├── main.py
│   ├── routes/
│   │   ├── analytics.py
│   │   └── reports.py
│   ├── middleware/
│   │   └── auth.py
│   └── services/
│       └── dsl_executor.py
├── pipelines/
│   ├── analytics.dsl
│   └── reports.dsl
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── README.md
```

## 🚀 Quick Start

```bash
# Run with Docker
docker-compose up

# API available at
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/analytics/summary
```

## 📊 DSL Pipeline

### Analytics Endpoint Pipeline

```dsl
@pipeline analytics_summary:
    data.from_input()
    | transform.filter(status="active")
    | transform.group_by("category")
    | transform.aggregate(by="category", func="sum")
    | metrics.calculate(metrics=["sum", "avg", "count", "min", "max"], field="amount")
    | export.to_json()
```

### Report Generation Pipeline

```dsl
@pipeline generate_report:
    $format = "json"
    $template = "summary"
    
    data.from_input()
    | metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
    | report.generate(format=$format, template=$template)
    | export.to_api(url="/internal/reports", method="POST")
```

### Batch Processing Pipeline

```dsl
@pipeline batch_process:
    data.load("/data/pending-items.json")
    | transform.map(func="process_item")
    | transform.filter(status="processed")
    | metrics.count()
    | export.to_json()
    
    # Alert on failures
    | alert.threshold(metric="failed_count", operator="gt", threshold=0)
    | alert.send(channel="webhook", message="Batch processing errors detected")
```

## 🐳 Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY pipelines/ ./pipelines/

# Run
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/analytica
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=your-secret-key
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=analytica
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres

  redis:
    image: redis:7-alpine
```

## ☸️ Kubernetes Deployment

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytica-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytica-api
  template:
    spec:
      containers:
        - name: api
          image: analytica/api:latest
          ports:
            - containerPort: 8000
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/pipeline/execute` | Execute DSL pipeline |
| POST | `/api/v1/analytics/summary` | Get analytics summary |
| POST | `/api/v1/reports/generate` | Generate report |
| GET | `/api/v1/metrics` | Prometheus metrics |

## 🚢 Deploy

```dsl
# Full deployment pipeline
deploy.docker(image="analytica/api-service", tag="v1.0", port=8000)
| deploy.kubernetes(
    namespace="production",
    replicas=3,
    resources={"cpu": "500m", "memory": "512Mi"},
    ingress_host="api.analytica.io"
)
| deploy.github_actions(
    workflow="deploy-api",
    triggers=["push"],
    branches=["main"]
)
```

## 📖 Learn More

- [API Documentation](../../docs/API.md)
- [Deploy Atoms](../../docs/MODULES.md#deploy-module)
