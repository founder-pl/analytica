# ANALYTICA Mobile - Dashboard Pipelines
# ======================================

# ============================================================
# MAIN DASHBOARD
# ============================================================

@pipeline mobile_dashboard:
    # Load user financial data
    data.fetch("/api/v1/user/dashboard")
    
    # Calculate summary metrics
    | metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
    
    # Generate KPI cards
    | view.card(value="balance", title="Balance", icon="💳", style="success", format="currency")
    | view.card(value="spending_this_month", title="Spent", icon="📉", style="warning", format="currency")
    | view.card(value="savings", title="Savings", icon="🏦", style="info", format="currency")
    
    # Balance trend chart
    | view.chart(type="line", x="date", y="balance", title="Balance History")
    
    # Recent transactions list
    | view.list(
        primary="description",
        secondary="amount",
        icon="category_icon",
        title="Recent Transactions"
    )


# ============================================================
# EXPENSE TRACKER
# ============================================================

@pipeline expense_tracker:
    data.from_input()
    | transform.filter(type="expense")
    | transform.group_by("category")
    | transform.aggregate(by="category", func="sum")
    
    # Category breakdown
    | view.chart(type="pie", x="category", y="total", title="Spending by Category")
    
    # Top categories
    | transform.sort(by="total", order="desc")
    | transform.limit(5)
    | view.list(primary="category", secondary="total", icon="icon")


# ============================================================
# BUDGET MONITOR
# ============================================================

@pipeline budget_monitor:
    budget.load("current_month")
    | budget.variance()
    
    # Progress indicators
    | view.kpi(value="spent", target="budget", title="Budget Progress", icon="📊")
    | view.card(value="remaining", title="Remaining", icon="💰", style="success")
    | view.card(value="days_left", title="Days Left", icon="📅", style="info")
    
    # Category progress
    | view.chart(type="bar", x="category", y="spent_percent", title="Category Spending")
    
    # Overspend alert
    | alert.threshold(metric="spent_percent", operator="gt", threshold=100)
    | alert.send(channel="push", message="⚠️ Budget exceeded!")


# ============================================================
# INVESTMENT PORTFOLIO
# ============================================================

@pipeline investment_portfolio:
    data.fetch("/api/v1/user/investments")
    | metrics.calculate(metrics=["sum"], field="value")
    
    # Portfolio summary
    | view.card(value="total_value", title="Portfolio", icon="📈", style="success", format="currency")
    | view.card(value="daily_change", title="Today", icon="📊", style="info", format="percent")
    | view.card(value="total_return", title="Total Return", icon="💰", style="default", format="percent")
    
    # Asset allocation
    | view.chart(type="donut", x="asset_type", y="value", title="Allocation")
    
    # Holdings list
    | view.list(primary="name", secondary="value", icon="icon", title="Holdings")


# ============================================================
# QUICK ACTIONS
# ============================================================

@pipeline quick_expense:
    # Add expense from input
    data.from_input()
    | transform.map(func="add_timestamp")
    | export.to_api(url="/api/v1/expenses", method="POST")
    
    # Notification
    | alert.send(channel="local", message="Expense added!")


@pipeline quick_transfer:
    data.from_input()
    | transform.select("from_account", "to_account", "amount")
    | export.to_api(url="/api/v1/transfers", method="POST")


# ============================================================
# NOTIFICATIONS & ALERTS
# ============================================================

@pipeline daily_summary:
    data.fetch("/api/v1/user/daily-summary")
    | metrics.calculate(metrics=["sum", "count"], field="amount")
    
    # Send push notification
    | alert.send(
        channel="push",
        message="Daily Summary: Spent {{sum}} in {{count}} transactions"
    )


@pipeline low_balance_alert:
    data.fetch("/api/v1/user/balance")
    | alert.threshold(metric="balance", operator="lt", threshold=1000)
    | alert.send(channel="push", message="⚠️ Low balance alert!")


# ============================================================
# MOBILE DEPLOYMENT
# ============================================================

@pipeline deploy_mobile_app:
    deploy.mobile(
        framework="react-native",
        platforms=["ios", "android"],
        release=true,
        scheme="analytica"
    )
    | deploy.github_actions(
        workflow="build-mobile",
        triggers=["push", "release"],
        branches=["main"],
        jobs=["build-ios", "build-android", "test", "publish"]
    )
