# ANALYTICA Web Dashboard - DSL Pipelines
# ========================================

# ============================================================
# MAIN DASHBOARD PIPELINE
# ============================================================

@pipeline main_dashboard:
    # Load sales data from API
    data.load("/api/v1/sales")
    
    # Filter completed orders
    | transform.filter(status="completed")
    
    # Calculate key metrics
    | metrics.calculate(metrics=["sum", "avg", "count", "min", "max"], field="amount")
    
    # Generate KPI cards
    | view.card(value="sum", title="Total Revenue", icon="💰", style="success", format="currency")
    | view.card(value="count", title="Total Orders", icon="📦", style="info")
    | view.card(value="avg", title="Average Order", icon="📊", style="default", format="currency")
    
    # Generate charts
    | view.chart(type="bar", x="month", y="revenue", title="Monthly Revenue", colors=["#3b82f6"])
    | view.chart(type="line", x="date", y="orders", title="Daily Orders Trend", legend=true)
    | view.chart(type="pie", x="category", y="amount", title="Sales by Category")
    
    # Generate data table
    | view.table(
        columns=["date", "product", "category", "amount", "status"],
        title="Recent Transactions",
        sortable=true,
        filterable=true,
        paginate=true,
        page_size=20
    )


# ============================================================
# KPI SUMMARY PIPELINE
# ============================================================

@pipeline kpi_summary:
    data.from_input()
    | metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
    | view.card(value="sum", title="Revenue", icon="💰", style="success")
    | view.card(value="count", title="Orders", icon="📦", style="info")
    | view.card(value="avg", title="AOV", icon="📊", style="default")


# ============================================================
# REVENUE ANALYSIS PIPELINE
# ============================================================

@pipeline revenue_analysis:
    $period = "monthly"
    
    data.load("/api/v1/revenue")
    | transform.group_by("month")
    | transform.aggregate(by="month", func="sum")
    | metrics.calculate(metrics=["sum", "avg"], field="revenue")
    
    # Trend analysis
    | forecast.trend()
    | forecast.predict(periods=3, method="linear")
    
    # Visualize
    | view.chart(type="area", x="month", y="revenue", title="Revenue Trend")
    | view.chart(type="line", x="month", y="predicted", title="Revenue Forecast")


# ============================================================
# PRODUCT PERFORMANCE PIPELINE
# ============================================================

@pipeline product_performance:
    data.load("/api/v1/products/sales")
    | transform.group_by("product_id", "product_name")
    | transform.aggregate(by="product_id", func="sum")
    | transform.sort(by="total_sales", order="desc")
    | transform.limit(10)
    
    | view.chart(type="bar", x="product_name", y="total_sales", title="Top 10 Products")
    | view.table(columns=["product_name", "total_sales", "units_sold", "avg_price"], title="Product Details")


# ============================================================
# CUSTOMER INSIGHTS PIPELINE
# ============================================================

@pipeline customer_insights:
    data.load("/api/v1/customers/metrics")
    | metrics.calculate(metrics=["count", "avg"], field="lifetime_value")
    
    | view.card(value="count", title="Total Customers", icon="👥", style="info")
    | view.card(value="avg", title="Avg LTV", icon="💎", style="success", format="currency")
    | view.chart(type="pie", x="segment", y="count", title="Customer Segments")


# ============================================================
# REAL-TIME MONITORING PIPELINE
# ============================================================

@pipeline realtime_monitor:
    data.fetch("/api/v1/metrics/realtime")
    
    # Check for anomalies
    | alert.anomaly(std_multiplier=2.0)
    | alert.threshold(metric="error_rate", operator="gt", threshold=5)
    
    # Display gauges
    | view.chart(type="gauge", title="Server Load")
    | view.card(value="requests_per_sec", title="RPS", icon="⚡", style="info")
    | view.card(value="error_rate", title="Error Rate", icon="⚠️", style="warning", format="percent")


# ============================================================
# DEPLOYMENT PIPELINE
# ============================================================

@pipeline deploy_dashboard:
    # Build and deploy web app
    deploy.web(framework="react", build="npm run build", output="dist")
    | deploy.docker(image="analytica/web-dashboard", tag="latest", port=3000)
    | deploy.kubernetes(
        namespace="production",
        replicas=3,
        resources={"cpu": "500m", "memory": "512Mi"},
        ingress_host="dashboard.analytica.io"
    )
    | deploy.github_actions(
        workflow="deploy-dashboard",
        triggers=["push"],
        branches=["main"],
        jobs=["build", "test", "deploy"]
    )
