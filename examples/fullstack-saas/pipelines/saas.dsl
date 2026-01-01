# ANALYTICA Full-Stack SaaS - DSL Pipelines
# ==========================================

# ============================================================
# USER ONBOARDING
# ============================================================

@pipeline user_signup:
    data.from_input()
    | transform.select("email", "name", "company", "plan")
    
    # Create user in database
    | export.to_api(url="/internal/users", method="POST")
    
    # Initialize default workspace
    | budget.create(name="My First Budget", scenario="realistic")
    
    # Send welcome email
    | alert.send(channel="email", message="Welcome to Analytica, {{name}}!")
    
    # Track signup event
    | export.to_api(url="/internal/analytics/events", method="POST")


@pipeline user_onboarding_complete:
    data.from_input()
    | transform.select("user_id", "completed_steps")
    
    # Check completion
    | metrics.count()
    
    # If all steps completed
    | alert.threshold(metric="completed", operator="eq", threshold=5)
    | alert.send(channel="email", message="🎉 Onboarding complete! Here's your quick start guide.")


# ============================================================
# BILLING & SUBSCRIPTIONS
# ============================================================

@pipeline create_subscription:
    $plan = "pro"
    
    data.from_input()
    | transform.select("user_id", "plan", "payment_method_id")
    
    # Create Stripe subscription
    | export.to_api(url="/billing/subscriptions", method="POST")
    
    # Update user plan
    | export.to_api(url="/internal/users/plan", method="PATCH")
    
    # Send confirmation
    | alert.send(channel="email", message="Your {{plan}} subscription is now active!")


@pipeline process_invoice:
    data.from_input()
    | transform.select("invoice_id", "amount", "status")
    
    # Update invoice status
    | export.to_api(url="/billing/invoices/{{invoice_id}}", method="PATCH")
    
    # If paid, extend subscription
    | alert.threshold(metric="status", operator="eq", threshold="paid")
    | export.to_api(url="/internal/subscriptions/extend", method="POST")


@pipeline handle_failed_payment:
    data.from_input()
    | transform.filter(status="failed")
    
    # Send dunning email
    | alert.send(channel="email", message="⚠️ Payment failed. Please update your payment method.")
    
    # Schedule retry
    | export.to_api(url="/billing/retry", method="POST")


# ============================================================
# USAGE ANALYTICS
# ============================================================

@pipeline track_usage:
    data.from_input()
    | transform.select("user_id", "feature", "timestamp", "metadata")
    | export.to_api(url="/internal/usage", method="POST")


@pipeline usage_dashboard:
    data.query("SELECT * FROM usage_events WHERE date >= CURRENT_DATE - INTERVAL '30 days'")
    | transform.group_by("date", "feature")
    | transform.aggregate(by="date", func="count")
    | metrics.calculate(metrics=["sum", "avg"], field="count")
    
    # Dashboard views
    | view.card(value="total_events", title="Total Events", icon="📊", style="info")
    | view.card(value="dau", title="Daily Active Users", icon="👥", style="success")
    | view.card(value="avg_session", title="Avg Session", icon="⏱️", style="default")
    | view.chart(type="line", x="date", y="events", title="Daily Events")
    | view.chart(type="bar", x="feature", y="count", title="Feature Usage")


@pipeline mrr_tracking:
    data.query("SELECT * FROM subscriptions WHERE status = 'active'")
    | metrics.sum("monthly_amount")
    
    | view.card(value="mrr", title="MRR", icon="💰", style="success", format="currency")
    | view.card(value="arr", title="ARR", icon="📈", style="info", format="currency")
    | view.chart(type="area", x="month", y="mrr", title="MRR Growth")


# ============================================================
# REPORTS
# ============================================================

@pipeline weekly_metrics_report:
    data.query("SELECT * FROM metrics WHERE date >= CURRENT_DATE - INTERVAL '7 days'")
    | metrics.calculate(metrics=["sum", "avg", "count"], field="value")
    
    | view.card(value="signups", title="New Signups", icon="👥", style="success")
    | view.card(value="revenue", title="Revenue", icon="💰", style="info", format="currency")
    | view.card(value="churn", title="Churn Rate", icon="📉", style="warning", format="percent")
    
    | report.generate(format="html", template="weekly_metrics")
    | report.send(to=["team@company.com"])


@pipeline monthly_investor_report:
    $month = "2024-01"
    
    data.query("SELECT * FROM company_metrics WHERE month = '$month'")
    | metrics.calculate(metrics=["sum", "avg"], field="value")
    
    # KPIs
    | view.card(value="mrr", title="MRR", icon="💰", style="success", format="currency")
    | view.card(value="customers", title="Customers", icon="👥", style="info")
    | view.card(value="ltv", title="LTV", icon="💎", style="default", format="currency")
    | view.card(value="cac", title="CAC", icon="📊", style="warning", format="currency")
    
    # Charts
    | view.chart(type="line", x="month", y="mrr", title="MRR Trend")
    | view.chart(type="bar", x="month", y="signups", title="Monthly Signups")
    
    | report.generate(format="pdf", template="investor_report")
    | report.send(to=["investors@company.com"])


# ============================================================
# ALERTS & MONITORING
# ============================================================

@pipeline system_health_check:
    data.fetch("/internal/health")
    
    # Check all services
    | alert.threshold(metric="api_health", operator="ne", threshold="healthy")
    | alert.send(channel="slack", message="🚨 API unhealthy!")
    
    | alert.threshold(metric="db_health", operator="ne", threshold="healthy")
    | alert.send(channel="pagerduty", message="🚨 Database unhealthy!")


@pipeline churn_alert:
    data.query("SELECT * FROM subscriptions WHERE status = 'cancelled' AND cancelled_at >= CURRENT_DATE - INTERVAL '1 day'")
    | metrics.count()
    
    | alert.threshold(metric="count", operator="gt", threshold=5)
    | alert.send(channel="slack", message="⚠️ High churn alert: {{count}} cancellations today")


@pipeline revenue_milestone:
    data.query("SELECT SUM(monthly_amount) as mrr FROM subscriptions WHERE status = 'active'")
    
    | alert.threshold(metric="mrr", operator="gt", threshold=100000)
    | alert.send(channel="slack", message="🎉 MRR milestone reached: ${{mrr}}!")


# ============================================================
# DEPLOYMENT
# ============================================================

@pipeline deploy_saas:
    # Build all services
    deploy.docker(image="analytica/saas-backend", tag="v1.0", port=8000)
    | deploy.docker(image="analytica/saas-frontend", tag="v1.0", port=3000)
    | deploy.docker(image="analytica/saas-worker", tag="v1.0")
    
    # Deploy with compose
    | deploy.compose(
        services=["backend", "frontend", "worker", "db", "redis", "nginx"],
        file="docker-compose.yml"
    )
    
    # Or deploy to Kubernetes
    | deploy.kubernetes(
        namespace="production",
        replicas=3,
        resources={"cpu": "1000m", "memory": "1Gi"}
    )
    
    # CI/CD
    | deploy.github_actions(
        workflow="deploy-saas",
        triggers=["push", "release"],
        branches=["main"],
        jobs=["lint", "test", "build", "deploy-staging", "e2e-test", "deploy-prod"]
    )
