# Desktop Electron Example

> Cross-platform desktop application built with Analytica DSL + Electron

## 🎯 What You'll Build

A native desktop financial analytics application with:
- Investment ROI calculator
- Budget management dashboard
- Offline-capable data processing
- System tray integration
- Native OS notifications

## 📁 Structure

```
desktop-electron/
├── Dockerfile
├── docker-compose.yml
├── package.json
├── electron/
│   ├── main.js
│   ├── preload.js
│   └── menu.js
├── src/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── components/
├── pipelines/
│   ├── investment.dsl
│   └── budget.dsl
└── README.md
```

## 🚀 Quick Start

```bash
# Development
npm install
npm run electron:dev

# Build for all platforms
npm run electron:build

# Build for specific platform
npm run build:win
npm run build:mac
npm run build:linux
```

## 📊 DSL Pipeline

### Investment Analysis Pipeline

```dsl
@pipeline investment_desktop:
    # Analyze investment from user input
    data.from_input()
    | investment.analyze(
        initial_investment=1000000,
        discount_rate=0.12,
        cash_flows=[200000, 300000, 400000, 500000, 600000]
    )
    
    # Calculate all metrics
    | investment.npv(rate=0.12)
    | investment.irr()
    | investment.payback()
    
    # Generate views
    | view.card(value="npv", title="NPV", icon="💰", style="success", format="currency")
    | view.card(value="roi", title="ROI", icon="📈", style="info", format="percent")
    | view.card(value="irr", title="IRR", icon="📊", style="default", format="percent")
    | view.card(value="payback_period", title="Payback", icon="⏱️", style="warning")
    | view.chart(type="bar", x="period", y="cash_flow", title="Cash Flows")
    | view.table(columns=["period", "cash_flow", "cumulative", "discounted"], title="Cash Flow Analysis")
    
    # Desktop deployment
    | deploy.desktop(framework="electron", platforms=["win", "mac", "linux"])
```

### Budget Management Pipeline

```dsl
@pipeline budget_desktop:
    budget.load("current_budget")
    | budget.variance()
    | budget.categorize(by="department")
    
    | view.card(value="total_budget", title="Total Budget", icon="💵", style="info")
    | view.card(value="spent", title="Spent", icon="📉", style="warning")
    | view.card(value="remaining", title="Remaining", icon="✅", style="success")
    | view.chart(type="pie", x="category", y="amount", title="Budget by Category")
    | view.chart(type="bar", x="department", y="variance", title="Variance by Department")
    
    # Alert on overspend
    | alert.threshold(metric="variance_percent", operator="gt", threshold=10)
```

## 🐳 Docker Build

### Dockerfile

```dockerfile
FROM electronuserland/builder:wine

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

# Build for all platforms
RUN npm run electron:build -- --linux --win --mac
```

### docker-compose.yml

```yaml
services:
  builder:
    build: .
    volumes:
      - ./dist:/app/dist
    command: npm run electron:build
  
  api:
    image: analytica/api:latest
    ports:
      - "18000:8000"
```

## 💻 Electron Configuration

### main.js

```javascript
const { app, BrowserWindow, ipcMain, Tray } = require('electron');
const path = require('path');

let mainWindow;
let tray;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        },
        icon: path.join(__dirname, '../assets/icon.png'),
        titleBarStyle: 'hiddenInset'
    });
    
    // Load app
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile('src/index.html');
    }
}

// IPC handlers for DSL execution
ipcMain.handle('execute-dsl', async (event, dsl, inputData) => {
    const response = await fetch('http://localhost:18000/api/v1/pipeline/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dsl, input_data: inputData })
    });
    return response.json();
});

app.whenReady().then(createWindow);
```

## 🚢 Deploy

```dsl
# Build and package desktop app
deploy.desktop(
    framework="electron",
    platforms=["win", "mac", "linux"],
    release=true,
    url="http://localhost:18000"
)
| deploy.github_actions(
    workflow="build-desktop",
    triggers=["push", "release"],
    jobs=["build-win", "build-mac", "build-linux", "publish"]
)
```

## 🔧 Commands

```bash
# Development
npm run electron:dev       # Start with hot reload
npm run dev               # Start renderer only

# Build
npm run electron:build    # Build for current platform
npm run build:win         # Build for Windows
npm run build:mac         # Build for macOS
npm run build:linux       # Build for Linux

# Package
npm run package           # Create distributable
npm run publish           # Publish to GitHub releases
```

## 📖 Learn More

- [Electron Docs](https://www.electronjs.org/docs)
- [Deploy Atoms](../../docs/MODULES.md#deploy-module)
- [Investment Atoms](../../docs/MODULES.md#investment-module)
