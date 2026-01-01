# Web Dashboard Example

> Complete web dashboard application built with DSL

## 🎯 What You'll Build

A real-time sales analytics dashboard with:
- KPI cards (revenue, orders, customers)
- Interactive charts (bar, line, pie)
- Data tables with filtering/sorting
- Auto-refresh from API
- Responsive design

## 📁 Structure

```
web-dashboard/
├── Dockerfile
├── docker-compose.yml
├── package.json
├── src/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── pipelines/
│   ├── dashboard.dsl
│   └── api.dsl
└── README.md
```

## 🚀 Quick Start

```bash
# Start with Docker
docker-compose up

# Open browser
open http://localhost:3000
```

## 📊 DSL Pipeline

### Main Dashboard Pipeline

```dsl
@pipeline sales_dashboard:
    # Load and process data
    data.load("/api/sales")
    | transform.filter(status="completed")
    | metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
    
    # Generate views
    | view.card(value="sum", title="Total Revenue", icon="💰", style="success")
    | view.card(value="count", title="Orders", icon="📦", style="info")
    | view.card(value="avg", title="Avg Order", icon="📊", style="default")
    | view.chart(type="bar", x="month", y="revenue", title="Monthly Revenue")
    | view.chart(type="line", x="date", y="orders", title="Order Trend")
    | view.table(columns=["date", "product", "amount", "status"], title="Recent Orders")
    
    # Deploy configuration
    | deploy.web(framework="react", build="npm run build")
    | deploy.docker(image="analytica/web-dashboard", port=3000)
```

### API Backend Pipeline

```dsl
@pipeline dashboard_api:
    data.from_input()
    | transform.select("date", "product", "amount", "status")
    | metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
    | export.to_json()
```

## 🐳 Docker Configuration

### Dockerfile

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 3000
```

### docker-compose.yml

```yaml
services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
  
  api:
    image: analytica/api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/analytica
    depends_on:
      - db
  
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=analytica
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## 🔧 Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

## 📱 Frontend Code

### app.js

```javascript
import { Pipeline, Analytica } from '@analytica/sdk';
import { createViewRenderer } from '/ui/view-renderer.js';

// Configure SDK
Analytica.configure({
    apiUrl: 'http://localhost:18000',
    autoRefresh: 30000
});

// Create dashboard
async function loadDashboard() {
    const result = await Pipeline()
        .data.load('/api/sales')
        .transform.filter({ status: 'completed' })
        .metrics.calculate(['sum', 'avg', 'count'], 'amount')
        .view.card({ value: 'sum', title: 'Revenue', icon: '💰' })
        .view.chart({ type: 'bar', x: 'month', y: 'revenue' })
        .view.table({ columns: ['date', 'product', 'amount'] })
        .execute();
    
    const renderer = createViewRenderer('#dashboard');
    renderer.render(result);
}

// Initialize
loadDashboard();
setInterval(loadDashboard, 30000);
```

## 🚢 Deploy

```dsl
# Full deployment pipeline
deploy.docker(image="analytica/web-dashboard", tag="v1.0", port=3000)
| deploy.kubernetes(namespace="prod", replicas=3, ingress_host="dashboard.example.com")
| deploy.github_actions(workflow="deploy", triggers=["push"], branches=["main"])
```

## 📖 Learn More

- [DSL Reference](../../docs/DSL.md)
- [View Atoms](../../docs/MODULES.md#views-module)
- [Deploy Atoms](../../docs/MODULES.md#deploy-module)
