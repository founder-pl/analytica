# ANALYTICA API Microservice - Analytics Pipelines
# ================================================

# ============================================================
# DATA ANALYTICS
# ============================================================

@pipeline analytics_summary:
    data.from_input()
    | transform.filter(status="active")
    | metrics.calculate(metrics=["sum", "avg", "count", "min", "max"], field="amount")
    | export.to_json()


@pipeline analytics_by_category:
    data.from_input()
    | transform.group_by("category")
    | transform.aggregate(by="category", func="sum")
    | transform.sort(by="total", order="desc")
    | metrics.calculate(metrics=["sum", "avg"], field="total")
    | export.to_json()


@pipeline analytics_time_series:
    data.from_input()
    | transform.group_by("date")
    | transform.aggregate(by="date", func="sum")
    | forecast.trend()
    | export.to_json()


# ============================================================
# BATCH PROCESSING
# ============================================================

@pipeline batch_process:
    data.load("/data/pending.json")
    | transform.map(func="process_item")
    | transform.filter(processed=true)
    | metrics.count()
    | export.to_json()
    
    # Alert on failures
    | alert.threshold(metric="failed", operator="gt", threshold=0)
    | alert.send(channel="webhook", message="Batch errors: {{failed}}")


@pipeline batch_aggregate:
    $date = "2024-01-01"
    
    data.query("SELECT * FROM transactions WHERE date >= $date")
    | transform.group_by("account_id")
    | transform.aggregate(by="account_id", func="sum")
    | export.to_api(url="/internal/aggregates", method="POST")


# ============================================================
# REAL-TIME PROCESSING
# ============================================================

@pipeline realtime_metrics:
    data.from_input()
    | metrics.calculate(metrics=["sum", "count"], field="value")
    | alert.threshold(metric="sum", operator="gt", threshold=10000)
    | export.to_json()


@pipeline stream_aggregate:
    data.from_input()
    | transform.map(func="enrich")
    | transform.filter(valid=true)
    | metrics.calculate(metrics=["sum", "avg"], field="amount")
    | export.to_api(url="/metrics/ingest", method="POST")


# ============================================================
# API DEPLOYMENT
# ============================================================

@pipeline deploy_api:
    deploy.docker(
        image="analytica/api-service",
        tag="latest",
        port=8000,
        env={"LOG_LEVEL": "INFO"}
    )
    | deploy.kubernetes(
        namespace="production",
        replicas=3,
        resources={"cpu": "500m", "memory": "512Mi"}
    )
    | deploy.github_actions(
        workflow="deploy-api",
        triggers=["push"],
        branches=["main"]
    )
