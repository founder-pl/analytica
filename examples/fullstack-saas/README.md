# Full-Stack SaaS Example

> Complete SaaS application built with Analytica DSL

## 🎯 What You'll Build

A production-ready SaaS platform with:
- Multi-tenant architecture
- User authentication & authorization
- Subscription management
- Admin dashboard
- API backend
- Web frontend
- Background job processing

## 📁 Structure

```
fullstack-saas/
├── docker-compose.yml
├── Makefile
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py
│       ├── auth/
│       ├── billing/
│       └── api/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── worker/
│   ├── Dockerfile
│   └── tasks/
├── pipelines/
│   ├── onboarding.dsl
│   ├── billing.dsl
│   ├── analytics.dsl
│   └── reports.dsl
├── k8s/
│   └── *.yaml
└── README.md
```

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Open application
open http://localhost:3000

# API docs
open http://localhost:8000/docs
```

## 📊 DSL Pipelines

### User Onboarding Pipeline

```dsl
@pipeline user_onboarding:
    # Create user account
    data.from_input()
    | transform.select("email", "name", "company")
    | export.to_api(url="/internal/users", method="POST")
    
    # Initialize workspace
    | budget.create(name="Default Budget", scenario="realistic")
    
    # Send welcome email
    | alert.send(channel="email", message="Welcome to Analytica!")
    
    # Track analytics
    | metrics.count()
    | export.to_api(url="/internal/analytics/signup", method="POST")
```

### Billing Pipeline

```dsl
@pipeline process_subscription:
    $plan = "pro"
    
    data.from_input()
    | transform.select("user_id", "plan", "payment_method")
    
    # Create subscription
    | export.to_api(url="/billing/subscriptions", method="POST")
    
    # Update user limits
    | export.to_api(url="/internal/users/limits", method="PATCH")
    
    # Send confirmation
    | alert.send(channel="email", message="Subscription activated: {{plan}}")
```

### Usage Analytics Pipeline

```dsl
@pipeline usage_analytics:
    data.query("SELECT * FROM usage_events WHERE date >= CURRENT_DATE - INTERVAL '30 days'")
    | transform.group_by("user_id", "feature")
    | transform.aggregate(by="feature", func="count")
    
    # Generate insights
    | metrics.calculate(metrics=["sum", "avg"], field="usage_count")
    
    # Dashboard views
    | view.card(value="total_users", title="Active Users", icon="👥", style="success")
    | view.card(value="total_events", title="Events", icon="📊", style="info")
    | view.chart(type="line", x="date", y="events", title="Daily Usage")
    | view.chart(type="bar", x="feature", y="count", title="Feature Usage")
```

### Monthly Report Pipeline

```dsl
@pipeline monthly_report:
    $month = "2024-01"
    
    # Gather data
    data.query("SELECT * FROM subscriptions WHERE created_at >= '$month-01'")
    | metrics.calculate(metrics=["sum", "count"], field="amount")
    
    # Revenue metrics
    | view.card(value="mrr", title="MRR", icon="💰", style="success", format="currency")
    | view.card(value="new_customers", title="New Customers", icon="👥", style="info")
    | view.card(value="churn_rate", title="Churn", icon="📉", style="warning", format="percent")
    
    # Generate report
    | report.generate(format="pdf", template="monthly_saas_report")
    | report.send(to=["founders@company.com"])
```

## 🐳 Docker Configuration

### docker-compose.yml

```yaml
services:
  # Frontend (React)
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend

  # Backend (FastAPI)
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/analytica
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - db
      - redis

  # Background Worker
  worker:
    build: ./worker
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/analytica
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  # PostgreSQL
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=analytica
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend

volumes:
  pgdata:
  redisdata:
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         NGINX                                │
│                    (Load Balancer)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐              ┌─────────────┐             │
│   │  Frontend   │              │   Backend   │             │
│   │   (React)   │◄────────────►│  (FastAPI)  │             │
│   │   :3000     │              │    :8000    │             │
│   └─────────────┘              └──────┬──────┘             │
│                                       │                     │
│                          ┌────────────┼────────────┐       │
│                          │            │            │       │
│                    ┌─────▼─────┐ ┌────▼────┐ ┌────▼────┐  │
│                    │PostgreSQL │ │  Redis  │ │ Worker  │  │
│                    │  :5432    │ │  :6379  │ │ (Celery)│  │
│                    └───────────┘ └─────────┘ └─────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Authentication

```python
# JWT-based authentication
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify JWT token
    # Return user from database
    pass
```

## 💳 Billing Integration

```python
# Stripe integration
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

async def create_subscription(user_id: str, plan: str):
    # Create Stripe subscription
    subscription = stripe.Subscription.create(
        customer=user.stripe_customer_id,
        items=[{"price": PLAN_PRICES[plan]}]
    )
    return subscription
```

## 🚢 Deploy

```dsl
# Full SaaS deployment pipeline
deploy.docker(image="analytica/saas-backend", tag="v1.0")
| deploy.docker(image="analytica/saas-frontend", tag="v1.0")
| deploy.docker(image="analytica/saas-worker", tag="v1.0")
| deploy.compose(services=["backend", "frontend", "worker", "db", "redis", "nginx"])
| deploy.kubernetes(namespace="production", replicas=3)
| deploy.github_actions(
    workflow="deploy-saas",
    triggers=["push"],
    branches=["main"],
    jobs=["test", "build", "deploy-staging", "deploy-prod"]
)
```

## 🔧 Commands

```bash
# Development
make dev              # Start all services
make logs             # View logs
make shell-db         # Database shell
make shell-backend    # Backend shell

# Testing
make test             # Run all tests
make test-backend     # Backend tests
make test-frontend    # Frontend tests
make test-e2e         # E2E tests

# Deployment
make build            # Build all images
make push             # Push to registry
make deploy-staging   # Deploy to staging
make deploy-prod      # Deploy to production
```

## 📖 Learn More

- [Architecture](../../docs/ARCHITECTURE.md)
- [API Documentation](../../docs/API.md)
- [DSL Reference](../../docs/DSL.md)
- [Deploy Atoms](../../docs/MODULES.md#deploy-module)
