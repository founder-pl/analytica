# ANALYTICA DSL - Examples
# ========================

# ============================================================
# BASIC EXAMPLES
# ============================================================

# Simple data loading and metrics
@pipeline basic_metrics:
    data.load("sales.csv") | metrics.sum("amount")

# Filtering and aggregation
@pipeline sales_by_month:
    data.load("sales")
    | transform.filter(year=2024)
    | transform.group_by("month")
    | transform.aggregate(by="month", func="sum")
    | metrics.calculate(["sum", "avg", "count"])

# ============================================================
# BUDGET PIPELINES (planbudzetu.pl)
# ============================================================

# Monthly budget report
@pipeline monthly_budget_report:
    $month = "2024-01"
    budget.load("budget_2024")
    | transform.filter(month=$month)
    | budget.variance()
    | report.generate(format="pdf", template="monthly_budget")

# Budget vs actual comparison
@pipeline budget_vs_actual:
    $budget_id = "bdgt_2024_q1"
    budget.load($budget_id)
    | budget.compare(scenario="actual")
    | metrics.variance("amount")
    | report.generate(format="xlsx")
    | report.send(to=["finance@company.pl"])

# Category breakdown
@pipeline expense_by_category:
    data.load("expenses_2024")
    | budget.categorize(by="category")
    | transform.aggregate(by="category", func="sum")
    | transform.sort(by="amount", order="desc")
    | report.generate(format="pdf", template="expense_breakdown")

# ============================================================
# INVESTMENT PIPELINES (planinwestycji.pl)
# ============================================================

# ROI analysis
@pipeline investment_roi:
    $initial = 500000
    $cash_flows = [150000, 180000, 200000, 220000, 250000]
    data.from_input()
    | investment.analyze(
        initial_investment=$initial,
        cash_flows=$cash_flows,
        discount_rate=0.12
    )
    | investment.roi()
    | investment.npv(rate=0.1)
    | investment.payback()

# Scenario comparison
@pipeline investment_scenarios:
    data.load("investment_proposal")
    | investment.scenario(name="optimistic", multiplier=1.2)
    | investment.analyze()
    | export.to_json()

# Full investment report
@pipeline investment_report:
    $investment_id = "inv_2024_001"
    data.load($investment_id)
    | investment.analyze(discount_rate=0.15)
    | investment.roi()
    | investment.npv(rate=0.15)
    | investment.irr()
    | investment.payback()
    | report.generate(format="pdf", template="investment_proposal")
    | report.send(to=["board@company.pl"])

# ============================================================
# MULTI-PLAN PIPELINES (multiplan.pl)
# ============================================================

# Multi-scenario budget planning
@pipeline scenario_planning:
    $base_budget = "budget_2025"
    budget.load($base_budget)
    | investment.scenario(name="optimistic", multiplier=1.15)
    | budget.variance()
    | export.to_json(path="scenario_optimistic.json")

# Rolling forecast
@pipeline rolling_forecast:
    data.load("actuals_ytd")
    | forecast.predict(periods=6, model="prophet")
    | forecast.confidence(level=0.95)
    | budget.compare(scenario="planned")
    | report.generate(format="xlsx", template="rolling_forecast")

# ============================================================
# ALERTS PIPELINES (alerts.pl)
# ============================================================

# Budget threshold alert
@pipeline budget_alert:
    $threshold = 0.9
    budget.load("current_budget")
    | metrics.calculate(["sum"], field="actual")
    | alert.threshold(field="utilization", operator="gt", value=$threshold)
    | alert.send(channel="slack", message="Budget threshold exceeded!")

# Anomaly detection
@pipeline anomaly_alert:
    data.load("daily_expenses")
    | metrics.calculate(["avg", "std"])
    | alert.when("value > avg + 2 * std")
    | alert.send(channel="email")

# ============================================================
# FORECAST PIPELINES (estymacja.pl)
# ============================================================

# Sales forecast
@pipeline sales_forecast:
    data.load("historical_sales")
    | forecast.predict(periods=90, model="prophet")
    | forecast.trend()
    | forecast.seasonality()
    | forecast.confidence(level=0.95)
    | report.generate(format="pdf", template="forecast_report")

# Revenue projection
@pipeline revenue_projection:
    $months = 12
    data.load("revenue_history")
    | transform.filter(year=2024)
    | forecast.predict(periods=$months)
    | metrics.calculate(["sum", "avg"])
    | export.to_excel(path="revenue_projection.xlsx")

# ============================================================
# REPORT PIPELINES
# ============================================================

# Executive summary
@pipeline executive_summary:
    $period = "2024-Q4"
    data.load("financials")
    | transform.filter(period=$period)
    | metrics.calculate(["sum", "avg", "count"])
    | report.generate(format="pptx", template="executive_summary")
    | report.send(to=["ceo@company.pl", "cfo@company.pl"])

# Scheduled weekly report
@pipeline weekly_report:
    data.load("weekly_metrics")
    | metrics.calculate(["sum", "avg"])
    | report.generate(format="pdf", template="weekly_summary")
    | report.schedule(cron="0 9 * * MON", recipients=["team@company.pl"])

# ============================================================
# DATA TRANSFORMATION PIPELINES
# ============================================================

# Data cleaning
@pipeline clean_data:
    data.load("raw_transactions")
    | transform.filter(amount_gt=0)
    | transform.rename(old_name="new_name", trx_date="date")
    | transform.select("date", "amount", "category")
    | export.to_csv(path="cleaned_data.csv")

# Aggregation pipeline
@pipeline aggregate_data:
    data.load("transactions")
    | transform.group_by("category", "month")
    | transform.aggregate(by="amount", func="sum")
    | transform.sort(by="total", order="desc")
    | transform.limit(10)
    | export.to_json()

# ============================================================
# COMPLEX MULTI-STEP PIPELINES
# ============================================================

# Full financial analysis
@pipeline full_analysis:
    $year = 2024
    $budget_id = "budget_2024"
    
    # Load and filter data
    data.load("financials")
    | transform.filter(year=$year)
    
    # Calculate metrics
    | metrics.calculate(["sum", "avg", "count", "min", "max"])
    
    # Budget comparison
    | budget.load($budget_id)
    | budget.compare(scenario="actual")
    | budget.variance()
    
    # Generate forecast
    | forecast.predict(periods=6)
    | forecast.confidence(level=0.9)
    
    # Create alerts
    | alert.threshold(field="variance_pct", operator="gt", value=10)
    
    # Generate report
    | report.generate(format="pdf", template="full_analysis")
    | report.send(to=["finance@company.pl"])
    
    # Export data
    | export.to_excel(path="analysis_2024.xlsx")

# ============================================================
# API INTEGRATION PIPELINES
# ============================================================

# Fetch and process external data
@pipeline external_data:
    data.fetch("https://api.example.com/data")
    | transform.filter(status="active")
    | metrics.calculate(["count"])
    | export.to_api(url="https://internal.api/webhook", method="POST")

# Sync with ERP
@pipeline erp_sync:
    data.query("SELECT * FROM invoices WHERE status = 'pending'")
    | transform.map(func="calculate_vat")
    | export.to_api(url="https://erp.company.pl/api/invoices")
