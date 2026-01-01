# Mobile React Native Example

> Cross-platform mobile app built with Analytica DSL + React Native

## 🎯 What You'll Build

A mobile financial analytics app with:
- Real-time expense tracking
- Budget monitoring with alerts
- Investment portfolio view
- Offline data sync
- Push notifications

## 📁 Structure

```
mobile-react-native/
├── Dockerfile
├── docker-compose.yml
├── package.json
├── app.json
├── App.tsx
├── src/
│   ├── screens/
│   │   ├── DashboardScreen.tsx
│   │   ├── BudgetScreen.tsx
│   │   └── InvestmentScreen.tsx
│   ├── components/
│   │   ├── KPICard.tsx
│   │   └── Chart.tsx
│   ├── services/
│   │   └── analytica.ts
│   └── hooks/
│       └── useDSL.ts
├── pipelines/
│   ├── mobile-dashboard.dsl
│   └── budget-tracker.dsl
└── README.md
```

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# iOS
npx pod-install
npm run ios

# Android
npm run android

# Start Metro bundler
npm start
```

## 📊 DSL Pipeline

### Mobile Dashboard Pipeline

```dsl
@pipeline mobile_dashboard:
    # Load user data
    data.fetch("/api/v1/user/dashboard")
    | transform.select("balance", "spending", "savings", "transactions")
    
    # Calculate metrics
    | metrics.calculate(metrics=["sum", "avg"], field="amount")
    
    # Generate mobile-optimized views
    | view.card(value="balance", title="Balance", icon="💳", style="success")
    | view.card(value="spending", title="This Month", icon="📉", style="warning")
    | view.card(value="savings", title="Savings", icon="🏦", style="info")
    | view.chart(type="line", x="date", y="balance", title="Balance Trend")
    | view.list(primary="description", secondary="amount", icon="category_icon", title="Recent Transactions")
    
    # Deploy to mobile
    | deploy.mobile(framework="react-native", platforms=["ios", "android"])
```

### Budget Tracker Pipeline

```dsl
@pipeline budget_tracker:
    data.from_input()
    | budget.load("current_month")
    | budget.variance()
    | budget.categorize(by="category")
    
    # KPI cards
    | view.card(value="total_budget", title="Budget", icon="📋", style="info")
    | view.card(value="spent", title="Spent", icon="💸", style="warning")
    | view.card(value="remaining", title="Left", icon="✅", style="success")
    
    # Category breakdown
    | view.chart(type="pie", x="category", y="amount", title="By Category")
    
    # Alert on overspend
    | alert.threshold(metric="spent_percent", operator="gt", threshold=90)
    | alert.send(channel="push", message="Budget alert: 90% spent!")
```

## 🐳 Docker Configuration

### docker-compose.yml

```yaml
services:
  # API Backend
  api:
    image: analytica/api:latest
    ports:
      - "18000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/analytica
    depends_on:
      - db

  # PostgreSQL
  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=analytica
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres

  # Push Notification Service
  push:
    image: analytica/push-service:latest
    environment:
      - FCM_KEY=${FCM_KEY}
      - APNS_KEY=${APNS_KEY}
```

## 📱 React Native Code

### App.tsx

```tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { AnalyticaProvider } from './src/services/analytica';
import DashboardScreen from './src/screens/DashboardScreen';
import BudgetScreen from './src/screens/BudgetScreen';
import InvestmentScreen from './src/screens/InvestmentScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <AnalyticaProvider apiUrl="http://localhost:18000">
      <NavigationContainer>
        <Tab.Navigator>
          <Tab.Screen name="Dashboard" component={DashboardScreen} />
          <Tab.Screen name="Budget" component={BudgetScreen} />
          <Tab.Screen name="Invest" component={InvestmentScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </AnalyticaProvider>
  );
}
```

### useDSL Hook

```typescript
// src/hooks/useDSL.ts
import { useState, useCallback } from 'react';
import { useAnalytica } from '../services/analytica';

export function useDSL() {
  const { execute } = useAnalytica();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  const runPipeline = useCallback(async (dsl: string, inputData?: any) => {
    setLoading(true);
    setError(null);
    try {
      const result = await execute(dsl, inputData);
      setData(result);
      return result;
    } catch (e: any) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [execute]);

  return { runPipeline, loading, error, data };
}
```

## 🚢 Deploy

```dsl
# Build and deploy mobile app
deploy.mobile(
    framework="react-native",
    platforms=["ios", "android"],
    release=true
)
| deploy.github_actions(
    workflow="build-mobile",
    triggers=["push", "release"],
    jobs=["build-ios", "build-android", "publish-stores"]
)
```

## 🔧 Commands

```bash
# Development
npm start                 # Start Metro bundler
npm run ios              # Run on iOS simulator
npm run android          # Run on Android emulator

# Build
npm run build:ios        # Build iOS release
npm run build:android    # Build Android APK/AAB

# Test
npm test                 # Run tests
npm run e2e:ios          # E2E tests on iOS
npm run e2e:android      # E2E tests on Android
```

## 📖 Learn More

- [React Native Docs](https://reactnative.dev/)
- [Deploy Atoms](../../docs/MODULES.md#deploy-module)
- [Alert Atoms](../../docs/MODULES.md#alerts-module)
