# ANALYTICA DSL - Examples

> Complete examples showing how to build applications using DSL

## 📁 Examples Structure

| Folder | Description | Platforms |
|--------|-------------|-----------|
| [dsl-pipelines](./dsl-pipelines/) | DSL syntax examples and pipeline templates | All |
| [web-dashboard](./web-dashboard/) | Full web dashboard application | Web (React) |
| [desktop-electron](./desktop-electron/) | Desktop application with Electron | Windows, macOS, Linux |
| [mobile-react-native](./mobile-react-native/) | Mobile app with React Native | iOS, Android |
| [api-microservice](./api-microservice/) | REST API microservice | Docker, K8s |
| [fullstack-saas](./fullstack-saas/) | Complete SaaS application | Full stack |

## 🚀 Quick Start

Each example includes:
- `README.md` - Detailed setup instructions
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Multi-service orchestration
- `*.dsl` - DSL pipeline definitions
- Source code and configuration

### Run Any Example

```bash
cd examples/<example-name>
docker-compose up
```

### Deploy with DSL

```dsl
# Generate deployment for any platform
deploy.docker(image="my-app", tag="v1.0")
| deploy.kubernetes(namespace="prod", replicas=3)
| deploy.github_actions(workflow="ci-cd")
```

## 📊 DSL Pipelines Overview

### Data → Analysis → Views → Deploy

```
┌─────────┐    ┌───────────┐    ┌─────────┐    ┌──────────┐
│  Data   │ →  │ Transform │ →  │  Views  │ →  │  Deploy  │
│  load   │    │  metrics  │    │  chart  │    │  docker  │
│  fetch  │    │  forecast │    │  table  │    │  k8s     │
│  query  │    │  budget   │    │  card   │    │  web     │
└─────────┘    └───────────┘    └─────────┘    └──────────┘
```

## 🎯 Use Cases

| Use Case | Example | DSL Pipeline |
|----------|---------|--------------|
| Sales Dashboard | web-dashboard | `data.load → metrics → view.chart → deploy.web` |
| Financial App | desktop-electron | `budget.load → investment.analyze → view.card → deploy.desktop` |
| Mobile Analytics | mobile-react-native | `data.fetch → transform → view.dashboard → deploy.mobile` |
| API Service | api-microservice | `data.from_input → metrics → export.to_api → deploy.docker` |
| Full SaaS | fullstack-saas | Complete pipeline with auth, DB, frontend |

## 📖 Documentation

- [DSL Reference](../docs/DSL.md)
- [Modules](../docs/MODULES.md)
- [API](../docs/API.md)
- [Views](../docs/VIEWS_ROADMAP.md)
