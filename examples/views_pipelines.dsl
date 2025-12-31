# ANALYTICA DSL - View Pipelines Examples
# ========================================
# Examples of DSL-driven views for dynamic UI rendering

# ============================================================
# Example 1: Simple Chart
# ============================================================

@pipeline sales_chart:
  data.from_input()
  | view.chart(type="bar", x="month", y="sales", title="Monthly Sales")

# Input data:
# [
#   {"month": "Jan", "sales": 12000},
#   {"month": "Feb", "sales": 15000},
#   {"month": "Mar", "sales": 18000}
# ]


# ============================================================
# Example 2: Data Table with Auto-Columns
# ============================================================

@pipeline transactions_table:
  data.from_input()
  | view.table(title="Transaction Log")

# Columns are auto-detected from data structure


# ============================================================
# Example 3: KPI Cards
# ============================================================

@pipeline kpi_cards:
  data.from_input()
  | view.card(value="revenue", title="Revenue", icon="💰", style="success")
  | view.card(value="orders", title="Orders", icon="📦", style="info")
  | view.card(value="customers", title="Customers", icon="👥", style="default")

# Input data:
# {"revenue": 125000, "orders": 342, "customers": 1250}


# ============================================================
# Example 4: KPI with Progress Bar
# ============================================================

@pipeline sales_target:
  data.from_input()
  | view.kpi(value="current", target="goal", title="Sales Target", icon="🎯")
  | view.kpi(value="new_customers", target="customer_goal", title="New Customers", icon="👥")

# Input data:
# {"current": 78500, "goal": 100000, "new_customers": 156, "customer_goal": 200}


# ============================================================
# Example 5: Line Chart for Trends
# ============================================================

@pipeline trend_analysis:
  data.from_input()
  | view.chart(type="line", x="date", y="value", title="Daily Trend", legend=true)

# Input data:
# [
#   {"date": "2024-01-01", "value": 100},
#   {"date": "2024-01-02", "value": 120},
#   {"date": "2024-01-03", "value": 115},
#   {"date": "2024-01-04", "value": 140}
# ]


# ============================================================
# Example 6: Pie Chart
# ============================================================

@pipeline market_share:
  data.from_input()
  | view.chart(type="pie", x="segment", y="value", title="Market Share")

# Input data:
# [
#   {"segment": "Enterprise", "value": 45},
#   {"segment": "SMB", "value": 35},
#   {"segment": "Startup", "value": 20}
# ]


# ============================================================
# Example 7: Full Dashboard
# ============================================================

@pipeline sales_dashboard:
  data.from_input()
  | view.card(value="total_revenue", title="Total Revenue", icon="💰", style="success")
  | view.card(value="total_orders", title="Total Orders", icon="📦", style="info")
  | view.card(value="conversion_rate", title="Conversion", icon="📈", style="warning")
  | view.chart(type="bar", x="month", y="revenue", title="Monthly Revenue")
  | view.chart(type="line", x="month", y="orders", title="Order Trend")
  | view.table(columns=["month", "revenue", "orders", "aov"], title="Monthly Details")

# Input data:
# {
#   "total_revenue": 485000,
#   "total_orders": 1250,
#   "conversion_rate": 3.2,
#   "data": [
#     {"month": "Jan", "revenue": 75000, "orders": 180, "aov": 417},
#     {"month": "Feb", "revenue": 82000, "orders": 210, "aov": 390},
#     {"month": "Mar", "revenue": 95000, "orders": 280, "aov": 339}
#   ]
# }


# ============================================================
# Example 8: Text with Markdown
# ============================================================

@pipeline report_summary:
  data.from_input()
  | view.text(content="**Executive Summary**\n\nTotal revenue: {{total_revenue}} PLN\nGrowth: {{growth}}%", format="markdown", title="Summary")
  | view.chart(type="bar", x="category", y="amount", title="By Category")

# Input data:
# {"total_revenue": 125000, "growth": 15.5, "data": [...]}


# ============================================================
# Example 9: List View
# ============================================================

@pipeline recent_activities:
  data.from_input()
  | view.list(primary="title", secondary="description", icon="icon", title="Recent Activities")

# Input data:
# [
#   {"title": "New Order", "description": "Order #1234 received", "icon": "📦"},
#   {"title": "Payment", "description": "Invoice #567 paid", "icon": "💳"},
#   {"title": "Shipment", "description": "Order #1230 shipped", "icon": "🚚"}
# ]


# ============================================================
# Example 10: Combined Pipeline with Metrics
# ============================================================

@pipeline sales_analysis_dashboard:
  data.from_input()
  | transform.filter(status="completed")
  | metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
  | view.card(value="sum", title="Total Sales", icon="💰", style="success")
  | view.card(value="avg", title="Average Order", icon="📊", style="info")
  | view.card(value="count", title="Orders", icon="🔢", style="default")
  | view.chart(type="bar", x="category", y="amount", title="Sales by Category")
  | view.table(title="Order Details")

# Input data:
# [
#   {"id": 1, "category": "Electronics", "amount": 1200, "status": "completed"},
#   {"id": 2, "category": "Clothing", "amount": 350, "status": "completed"},
#   {"id": 3, "category": "Electronics", "amount": 890, "status": "pending"}
# ]


# ============================================================
# Example 11: Gauge Chart
# ============================================================

@pipeline performance_gauge:
  data.from_input()
  | view.chart(type="gauge", title="System Load")

# Input data:
# [75, 100]  # [current, max]


# ============================================================
# Example 12: Area Chart
# ============================================================

@pipeline revenue_area:
  data.from_input()
  | view.chart(type="area", x="month", y="revenue", title="Revenue Over Time")

# Input data:
# [
#   {"month": "Q1", "revenue": 250000},
#   {"month": "Q2", "revenue": 320000},
#   {"month": "Q3", "revenue": 280000},
#   {"month": "Q4", "revenue": 410000}
# ]
