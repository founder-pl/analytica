"""
ANALYTICA DSL - Data Definition Atoms
======================================
Atoms for defining and generating data within DSL pipelines.

Supports:
- Mock data generation
- SQL query definitions
- DQL (Data Query Language)
- Inline data definitions
- Computed fields and aggregations
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import random
import math

from ..core.registry import AtomRegistry


# ============================================================
# INLINE DATA ATOMS
# ============================================================

@AtomRegistry.register("data", "define")
def data_define(ctx, **params) -> Dict:
    """
    Define inline data directly in DSL.
    
    Usage:
        data.define(
            total_revenue=125000,
            avg_order=450,
            orders_count=278,
            growth_rate=12.5
        )
    """
    # All params become data fields
    data = {k: v for k, v in params.items() if not k.startswith('_')}
    
    ctx.log(f"Data defined: {list(data.keys())}")
    return data


@AtomRegistry.register("data", "mock")
def data_mock(ctx, **params) -> Dict:
    """
    Generate mock/sample data for testing.
    
    Usage:
        data.mock(type="sales", rows=100)
        data.mock(type="users", rows=50)
        data.mock(type="metrics", period="monthly")
    """
    mock_type = params.get("type", params.get("_arg0", "generic"))
    rows = params.get("rows", 10)
    period = params.get("period", "daily")
    
    generators = {
        "sales": _generate_sales_data,
        "users": _generate_users_data,
        "metrics": _generate_metrics_data,
        "orders": _generate_orders_data,
        "products": _generate_products_data,
        "financial": _generate_financial_data,
        "iot": _generate_iot_data,
    }
    
    generator = generators.get(mock_type, _generate_generic_data)
    data = generator(rows, period)
    
    ctx.log(f"Mock data generated: type={mock_type}, rows={rows}")
    return data


@AtomRegistry.register("data", "sample")
def data_sample(ctx, **params) -> Dict:
    """
    Get sample dataset for demos.
    
    Usage:
        data.sample(dataset="ecommerce")
        data.sample(dataset="finance")
    """
    dataset = params.get("dataset", params.get("_arg0", "ecommerce"))
    
    samples = {
        "ecommerce": {
            "total_revenue": 125000,
            "avg_order": 450,
            "orders_count": 278,
            "conversion_rate": 3.2,
            "monthly": [
                {"month": "Sty", "revenue": 15000, "orders": 33},
                {"month": "Lut", "revenue": 18000, "orders": 40},
                {"month": "Mar", "revenue": 22000, "orders": 49},
                {"month": "Kwi", "revenue": 19000, "orders": 42},
                {"month": "Maj", "revenue": 25000, "orders": 56},
                {"month": "Cze", "revenue": 26000, "orders": 58},
            ]
        },
        "finance": {
            "total_assets": 5000000,
            "total_liabilities": 2000000,
            "equity": 3000000,
            "roi": 15.5,
            "monthly": [
                {"month": "Sty", "income": 50000, "expenses": 35000},
                {"month": "Lut", "income": 55000, "expenses": 38000},
                {"month": "Mar", "income": 60000, "expenses": 40000},
            ]
        },
        "iot": {
            "devices_count": 150,
            "active_devices": 142,
            "avg_temperature": 23.5,
            "avg_humidity": 45.2,
            "readings": [
                {"sensor": "temp-01", "value": 22.5, "unit": "°C"},
                {"sensor": "temp-02", "value": 24.1, "unit": "°C"},
                {"sensor": "humid-01", "value": 45.0, "unit": "%"},
            ]
        },
        "hr": {
            "employees_count": 250,
            "avg_salary": 8500,
            "departments": 12,
            "turnover_rate": 8.5,
        }
    }
    
    data = samples.get(dataset, samples["ecommerce"])
    ctx.log(f"Sample dataset: {dataset}")
    return data


@AtomRegistry.register("data", "compute")
def data_compute(ctx, **params) -> Dict:
    """
    Compute derived values from existing data.
    
    Usage:
        data.compute(
            profit="revenue - costs",
            margin="profit / revenue * 100",
            growth="(current - previous) / previous * 100"
        )
    """
    data = ctx.get_data() or {}
    result = dict(data)
    
    for field, expr in params.items():
        if field.startswith('_'):
            continue
        try:
            # Simple expression evaluation (safe subset)
            value = _safe_eval(expr, result)
            result[field] = value
        except Exception as e:
            ctx.log(f"Compute error for {field}: {e}", level="warn")
            result[field] = None
    
    ctx.log(f"Computed fields: {[k for k in params.keys() if not k.startswith('_')]}")
    return result


@AtomRegistry.register("data", "aggregate")
def data_aggregate(ctx, **params) -> Dict:
    """
    Aggregate data with common functions.
    
    Usage:
        data.aggregate(
            total_revenue=("revenue", "sum"),
            avg_order=("order_value", "avg"),
            max_sale=("amount", "max"),
            count=("id", "count")
        )
    """
    data = ctx.get_data()
    if not isinstance(data, list):
        data = [data] if data else []
    
    result = {}
    for field, spec in params.items():
        if field.startswith('_'):
            continue
        
        if isinstance(spec, tuple) and len(spec) == 2:
            source_field, func = spec
        else:
            source_field, func = spec, "sum"
        
        values = [row.get(source_field, 0) for row in data if isinstance(row, dict)]
        
        if func == "sum":
            result[field] = sum(values)
        elif func == "avg":
            result[field] = sum(values) / len(values) if values else 0
        elif func == "min":
            result[field] = min(values) if values else 0
        elif func == "max":
            result[field] = max(values) if values else 0
        elif func == "count":
            result[field] = len(values)
    
    ctx.log(f"Aggregated: {list(result.keys())}")
    return result


# ============================================================
# QUERY ATOMS
# ============================================================

@AtomRegistry.register("data", "sql")
def data_sql(ctx, **params) -> Dict:
    """
    Define SQL query for data retrieval.
    
    Usage:
        data.sql(
            query="SELECT * FROM sales WHERE year = 2024",
            connection="postgresql://..."
        )
    """
    query = params.get("query", params.get("_arg0", ""))
    connection = params.get("connection", "")
    database = params.get("database", "")
    
    result = {
        "type": "sql",
        "query": query,
        "connection": connection,
        "database": database,
        "status": "pending"
    }
    
    ctx.log(f"SQL query defined")
    return result


@AtomRegistry.register("data", "dql")
def data_dql(ctx, **params) -> Dict:
    """
    Define DQL (Data Query Language) query.
    
    Usage:
        data.dql(
            select=["revenue", "orders", "customers"],
            from_source="sales",
            where={"year": 2024},
            group_by=["month"],
            order_by="revenue DESC"
        )
    """
    select = params.get("select", params.get("_arg0", ["*"]))
    from_source = params.get("from_source", params.get("from", ""))
    where = params.get("where", {})
    group_by = params.get("group_by", [])
    order_by = params.get("order_by", "")
    limit = params.get("limit", None)
    
    result = {
        "type": "dql",
        "select": select,
        "from": from_source,
        "where": where,
        "group_by": group_by,
        "order_by": order_by,
        "limit": limit,
        "status": "pending"
    }
    
    ctx.log(f"DQL query: SELECT {select} FROM {from_source}")
    return result


@AtomRegistry.register("data", "graphql_query")
def data_graphql_query(ctx, **params) -> Dict:
    """
    Define GraphQL query.
    
    Usage:
        data.graphql_query(
            query="{ users { id name email } }",
            variables={"limit": 10}
        )
    """
    query = params.get("query", params.get("_arg0", ""))
    variables = params.get("variables", {})
    operation = params.get("operation", "query")
    
    result = {
        "type": "graphql",
        "operation": operation,
        "query": query,
        "variables": variables,
        "status": "pending"
    }
    
    ctx.log(f"GraphQL {operation} defined")
    return result


# ============================================================
# TIMESERIES DATA ATOMS
# ============================================================

@AtomRegistry.register("data", "timeseries")
def data_timeseries(ctx, **params) -> Dict:
    """
    Generate time series data.
    
    Usage:
        data.timeseries(
            metric="revenue",
            start="2024-01-01",
            end="2024-12-31",
            interval="monthly",
            trend="growth"
        )
    """
    metric = params.get("metric", params.get("_arg0", "value"))
    start = params.get("start", "2024-01-01")
    end = params.get("end", "2024-12-31")
    interval = params.get("interval", "daily")
    trend = params.get("trend", "stable")
    base_value = params.get("base_value", 1000)
    
    data = _generate_timeseries(metric, start, end, interval, trend, base_value)
    
    ctx.log(f"Timeseries: {metric}, {interval}")
    return {"series": data, "metric": metric, "interval": interval}


@AtomRegistry.register("data", "kpi")
def data_kpi(ctx, **params) -> Dict:
    """
    Define KPI metrics with targets.
    
    Usage:
        data.kpi(
            revenue={"value": 125000, "target": 150000, "unit": "PLN"},
            customers={"value": 1250, "target": 1500, "trend": "+12%"}
        )
    """
    kpis = {}
    for name, spec in params.items():
        if name.startswith('_'):
            continue
        
        if isinstance(spec, dict):
            kpis[name] = {
                "value": spec.get("value", 0),
                "target": spec.get("target"),
                "unit": spec.get("unit", ""),
                "trend": spec.get("trend", ""),
                "status": _kpi_status(spec.get("value", 0), spec.get("target"))
            }
        else:
            kpis[name] = {"value": spec}
    
    ctx.log(f"KPIs defined: {list(kpis.keys())}")
    return kpis


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _safe_eval(expr: str, context: Dict) -> Any:
    """Safely evaluate simple mathematical expressions"""
    # Replace field names with values
    for key, value in context.items():
        if isinstance(value, (int, float)):
            expr = expr.replace(key, str(value))
    
    # Only allow basic math operations
    allowed = set('0123456789+-*/.() ')
    if not all(c in allowed for c in expr):
        raise ValueError(f"Invalid expression: {expr}")
    
    return eval(expr)


def _kpi_status(value, target) -> str:
    if target is None:
        return "neutral"
    ratio = value / target if target else 0
    if ratio >= 1:
        return "success"
    elif ratio >= 0.8:
        return "warning"
    return "danger"


def _generate_timeseries(metric, start, end, interval, trend, base_value):
    """Generate time series data points"""
    data = []
    months = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]
    
    for i, month in enumerate(months[:6]):
        if trend == "growth":
            value = base_value * (1 + i * 0.1) + random.uniform(-100, 100)
        elif trend == "decline":
            value = base_value * (1 - i * 0.05) + random.uniform(-100, 100)
        else:
            value = base_value + random.uniform(-200, 200)
        
        data.append({"period": month, metric: round(value, 2)})
    
    return data


def _generate_sales_data(rows, period):
    months = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze"]
    return {
        "total_revenue": 125000,
        "avg_order": 450,
        "orders_count": 278,
        "data": [
            {"month": m, "revenue": 15000 + i * 2000, "orders": 30 + i * 5}
            for i, m in enumerate(months[:rows])
        ]
    }


def _generate_users_data(rows, period):
    return {
        "total_users": rows * 100,
        "active_users": int(rows * 85),
        "new_users": int(rows * 15),
        "data": [
            {"id": i, "name": f"User {i}", "active": random.choice([True, True, True, False])}
            for i in range(1, rows + 1)
        ]
    }


def _generate_metrics_data(rows, period):
    return {
        "total_revenue": 125000,
        "avg_order": 450,
        "conversion_rate": 3.2,
        "bounce_rate": 45.5,
        "page_views": 50000,
        "sessions": 12000
    }


def _generate_orders_data(rows, period):
    return {
        "total": rows,
        "completed": int(rows * 0.85),
        "pending": int(rows * 0.10),
        "cancelled": int(rows * 0.05),
        "data": [
            {"id": f"ORD-{1000+i}", "amount": random.randint(100, 1000), "status": "completed"}
            for i in range(rows)
        ]
    }


def _generate_products_data(rows, period):
    categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
    return {
        "total": rows,
        "data": [
            {"id": i, "name": f"Product {i}", "price": random.randint(50, 500), "category": random.choice(categories)}
            for i in range(1, rows + 1)
        ]
    }


def _generate_financial_data(rows, period):
    return {
        "revenue": 500000,
        "expenses": 350000,
        "profit": 150000,
        "margin": 30.0,
        "monthly": [
            {"month": f"M{i+1}", "revenue": 40000 + i * 2000, "expenses": 28000 + i * 1000}
            for i in range(rows)
        ]
    }


def _generate_iot_data(rows, period):
    return {
        "devices": rows,
        "active": int(rows * 0.95),
        "readings": [
            {"sensor": f"sensor-{i}", "value": round(20 + random.uniform(-5, 10), 1), "unit": "°C"}
            for i in range(1, rows + 1)
        ]
    }


def _generate_generic_data(rows, period):
    return {
        "count": rows,
        "data": [{"id": i, "value": random.randint(1, 100)} for i in range(1, rows + 1)]
    }
