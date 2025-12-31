"""
ANALYTICA DSL - Atom Implementations
=====================================
Concrete implementations of atomic operations for pipelines
"""

from typing import Any, Dict, List, Optional, Union
import json
import csv
import io
from datetime import datetime, date
from decimal import Decimal

from ..core.parser import AtomRegistry, PipelineContext


# ============================================================
# DATA ATOMS
# ============================================================

@AtomRegistry.register("data", "load")
def data_load(ctx: PipelineContext, source: str = None, **params) -> Any:
    """Load data from various sources"""
    source = source or params.get('_arg0')
    
    if not source:
        raise ValueError("Source is required for data.load")
    
    ctx.log(f"Loading data from: {source}")
    
    # Determine source type
    if source.endswith('.csv'):
        return _load_csv(source, params)
    elif source.endswith('.json'):
        return _load_json(source, params)
    elif source.startswith('http'):
        return _load_http(source, params)
    elif source.startswith('db:'):
        return _load_database(source[3:], params)
    else:
        # Assume it's a dataset reference
        return {"_ref": source, "_type": "dataset", **params}


def _load_csv(path: str, params: Dict) -> List[Dict]:
    """Load CSV file"""
    # In production, this would actually load the file
    # For now, return mock structure
    return {"_type": "csv", "_path": path, "_loaded": True}


def _load_json(path: str, params: Dict) -> Any:
    """Load JSON file"""
    return {"_type": "json", "_path": path, "_loaded": True}


def _load_http(url: str, params: Dict) -> Any:
    """Load from HTTP endpoint"""
    return {"_type": "http", "_url": url, "_loaded": True}


def _load_database(query: str, params: Dict) -> Any:
    """Load from database"""
    return {"_type": "database", "_query": query, "_loaded": True}


@AtomRegistry.register("data", "query")
def data_query(ctx: PipelineContext, sql: str, **params) -> Any:
    """Execute SQL query"""
    ctx.log(f"Executing query: {sql[:50]}...")
    return {"_type": "query_result", "_sql": sql, **params}


@AtomRegistry.register("data", "fetch")
def data_fetch(ctx: PipelineContext, url: str, method: str = "GET", **params) -> Any:
    """Fetch data from URL"""
    ctx.log(f"Fetching: {method} {url}")
    return {"_type": "fetch_result", "_url": url, "_method": method, **params}


@AtomRegistry.register("data", "from_input")
def data_from_input(ctx: PipelineContext, data: Any = None, **params) -> Any:
    """Use provided data as input"""
    return data or ctx.get_data()


# ============================================================
# TRANSFORM ATOMS
# ============================================================

@AtomRegistry.register("transform", "filter")
def transform_filter(ctx: PipelineContext, **conditions) -> Any:
    """Filter data by conditions"""
    data = ctx.get_data()
    ctx.log(f"Filtering with conditions: {conditions}")
    
    if isinstance(data, list):
        # Simple list filtering
        result = []
        for item in data:
            if _matches_conditions(item, conditions):
                result.append(item)
        return result

    if isinstance(data, dict):
        preferred_keys = ["data", "rows", "readings", "monthly", "items", "records"]
        for key in preferred_keys:
            if isinstance(data.get(key), list):
                filtered = [item for item in data[key] if _matches_conditions(item, conditions)]
                out = dict(data)
                out[key] = filtered
                return out

        list_keys = [k for k, v in data.items() if isinstance(v, list)]
        if len(list_keys) == 1:
            key = list_keys[0]
            filtered = [item for item in data[key] if _matches_conditions(item, conditions)]
            out = dict(data)
            out[key] = filtered
            return out
    
    return {"_type": "filtered", "_data": data, "_conditions": conditions}


def _matches_conditions(item: Dict, conditions: Dict) -> bool:
    """Check if item matches all conditions"""
    if not isinstance(item, dict):
        return False

    for key, value in conditions.items():
        if key.startswith('_'):
            continue

        if "__" in key:
            field, op = key.split("__", 1)
        else:
            field, op = key, "eq"

        if field not in item:
            return False

        item_val = item.get(field)

        if op == "eq":
            if item_val != value:
                return False
        elif op == "ne":
            if item_val == value:
                return False
        elif op == "gt":
            if item_val is None or item_val <= value:
                return False
        elif op == "gte":
            if item_val is None or item_val < value:
                return False
        elif op == "lt":
            if item_val is None or item_val >= value:
                return False
        elif op == "lte":
            if item_val is None or item_val > value:
                return False
        elif op == "in":
            if not isinstance(value, (list, tuple, set)):
                return False
            if item_val not in value:
                return False
        elif op == "contains":
            if isinstance(item_val, str):
                if str(value) not in item_val:
                    return False
            elif isinstance(item_val, (list, tuple, set)):
                if value not in item_val:
                    return False
            else:
                return False
        else:
            # Unknown operator -> treat as non-match
            return False

    return True


@AtomRegistry.register("transform", "map")
def transform_map(ctx: PipelineContext, func: str, field: str = None, **params) -> Any:
    """Map function over data"""
    data = ctx.get_data()
    ctx.log(f"Mapping function: {func} on field: {field}")
    return {"_type": "mapped", "_data": data, "_func": func, "_field": field}


@AtomRegistry.register("transform", "sort")
def transform_sort(ctx: PipelineContext, by: str, order: str = "asc", **params) -> Any:
    """Sort data by field"""
    data = ctx.get_data()
    ctx.log(f"Sorting by: {by} ({order})")
    
    if isinstance(data, list):
        reverse = order.lower() == "desc"
        return sorted(data, key=lambda x: x.get(by, 0), reverse=reverse)
    
    return {"_type": "sorted", "_data": data, "_by": by, "_order": order}


@AtomRegistry.register("transform", "limit")
def transform_limit(ctx: PipelineContext, n: int = None, **params) -> Any:
    """Limit number of results"""
    n = n if n is not None else params.get('_arg0', 10)
    data = ctx.get_data()
    
    if isinstance(data, list):
        return data[:n]
    
    return {"_type": "limited", "_data": data, "_n": n}


@AtomRegistry.register("transform", "group_by")
def transform_group_by(ctx: PipelineContext, fields: List[str] = None, **params) -> Any:
    """Group data by fields"""
    data = ctx.get_data()
    fields = fields or params.get('_arg0', [])
    
    ctx.log(f"Grouping by: {fields}")
    return {"_type": "grouped", "_data": data, "_fields": fields}


@AtomRegistry.register("transform", "aggregate")
def transform_aggregate(ctx: PipelineContext, by: str, func: str = "sum", **params) -> Any:
    """Aggregate data"""
    data = ctx.get_data()
    ctx.log(f"Aggregating by: {by} using {func}")
    return {"_type": "aggregated", "_data": data, "_by": by, "_func": func}


@AtomRegistry.register("transform", "select")
def transform_select(ctx: PipelineContext, fields: List[str] = None, **params) -> Any:
    """Select specific fields"""
    data = ctx.get_data()
    fields = fields or []
    
    if isinstance(data, list):
        return [{k: v for k, v in item.items() if k in fields} for item in data]
    
    return {"_type": "selected", "_data": data, "_fields": fields}


@AtomRegistry.register("transform", "rename")
def transform_rename(ctx: PipelineContext, **mapping) -> Any:
    """Rename fields"""
    data = ctx.get_data()
    
    if isinstance(data, list):
        result = []
        for item in data:
            new_item = {}
            for k, v in item.items():
                new_key = mapping.get(k, k)
                new_item[new_key] = v
            result.append(new_item)
        return result
    
    return {"_type": "renamed", "_data": data, "_mapping": mapping}


# ============================================================
# METRICS ATOMS
# ============================================================

@AtomRegistry.register("metrics", "calculate")
def metrics_calculate(ctx: PipelineContext, metrics: List[str] = None, field: str = None, **params) -> Dict:
    """Calculate multiple metrics"""
    data = ctx.get_data()
    metrics = metrics or params.get('_arg0', ['sum', 'avg', 'count'])
    
    ctx.log(f"Calculating metrics: {metrics}")
    
    result = {}
    values = _extract_values(data, field)
    
    if 'sum' in metrics:
        result['sum'] = sum(values) if values else 0
    if 'avg' in metrics:
        result['avg'] = sum(values) / len(values) if values else 0
    if 'count' in metrics:
        result['count'] = len(values)
    if 'min' in metrics:
        result['min'] = min(values) if values else 0
    if 'max' in metrics:
        result['max'] = max(values) if values else 0
    
    return result


def _extract_values(data: Any, field: str = None) -> List[float]:
    """Extract numeric values from data"""
    if isinstance(data, list):
        if field:
            return [float(item.get(field, 0)) for item in data if isinstance(item, dict)]
        return [float(x) for x in data if isinstance(x, (int, float))]
    return []


@AtomRegistry.register("metrics", "sum")
def metrics_sum(ctx: PipelineContext, field: str = None, **params) -> float:
    """Calculate sum"""
    field = field or params.get('_arg0')
    data = ctx.get_data()
    values = _extract_values(data, field)
    return sum(values)


@AtomRegistry.register("metrics", "avg")
def metrics_avg(ctx: PipelineContext, field: str = None, **params) -> float:
    """Calculate average"""
    field = field or params.get('_arg0')
    data = ctx.get_data()
    values = _extract_values(data, field)
    return sum(values) / len(values) if values else 0


@AtomRegistry.register("metrics", "count")
def metrics_count(ctx: PipelineContext, **params) -> int:
    """Count items"""
    data = ctx.get_data()
    if isinstance(data, list):
        return len(data)
    return 1 if data else 0


@AtomRegistry.register("metrics", "variance")
def metrics_variance(ctx: PipelineContext, field: str, **params) -> Dict:
    """Calculate variance between planned and actual"""
    data = ctx.get_data()
    ctx.log(f"Calculating variance for: {field}")
    return {"_type": "variance", "_field": field, "_data": data}


@AtomRegistry.register("metrics", "percentile")
def metrics_percentile(ctx: PipelineContext, field: str, p: int = 50, **params) -> float:
    """Calculate percentile"""
    data = ctx.get_data()
    values = sorted(_extract_values(data, field))
    
    if not values:
        return 0
    
    idx = int(len(values) * p / 100)
    return values[min(idx, len(values) - 1)]


# ============================================================
# REPORT ATOMS
# ============================================================

@AtomRegistry.register("report", "generate")
def report_generate(ctx: PipelineContext, format: str = "pdf", template: str = None, **params) -> Dict:
    """Generate report"""
    data = ctx.get_data()
    format = format or params.get('_arg0', 'pdf')
    
    ctx.log(f"Generating {format} report with template: {template}")
    
    report_id = f"rpt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "report_id": report_id,
        "format": format,
        "template": template,
        "status": "generated",
        "data_summary": _summarize_data(data),
        "created_at": datetime.now().isoformat()
    }


def _summarize_data(data: Any) -> Dict:
    """Create summary of data for report"""
    if isinstance(data, list):
        return {"type": "list", "count": len(data)}
    elif isinstance(data, dict):
        return {"type": "dict", "keys": list(data.keys())[:10]}
    return {"type": type(data).__name__}


@AtomRegistry.register("report", "schedule")
def report_schedule(ctx: PipelineContext, cron: str, recipients: List[str] = None, **params) -> Dict:
    """Schedule report generation"""
    ctx.log(f"Scheduling report: {cron}")
    return {
        "schedule_id": f"sch_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "cron": cron,
        "recipients": recipients or [],
        "status": "scheduled"
    }


@AtomRegistry.register("report", "send")
def report_send(ctx: PipelineContext, to: List[str], **params) -> Dict:
    """Send report to recipients"""
    data = ctx.get_data()
    ctx.log(f"Sending report to: {to}")
    return {
        "sent_to": to,
        "status": "sent",
        "sent_at": datetime.now().isoformat()
    }


# ============================================================
# ALERT ATOMS
# ============================================================

@AtomRegistry.register("alert", "when")
def alert_when(ctx: PipelineContext, condition: str, **params) -> Dict:
    """Define alert condition"""
    data = ctx.get_data()
    ctx.log(f"Alert condition: {condition}")
    
    # Evaluate condition
    triggered = _evaluate_condition(data, condition)
    
    return {
        "condition": condition,
        "triggered": triggered,
        "data": data
    }


def _evaluate_condition(data: Any, condition: str) -> bool:
    """Evaluate alert condition"""
    # Simple evaluation - in production would be more sophisticated
    if isinstance(data, dict):
        # Try to evaluate condition against data
        try:
            # Safe subset of built-ins
            safe_dict = {**data, 'sum': sum, 'len': len, 'abs': abs}
            return bool(eval(condition, {"__builtins__": {}}, safe_dict))
        except:
            return False
    return False


@AtomRegistry.register("alert", "send")
def alert_send(ctx: PipelineContext, channel: str, message: str = None, **params) -> Dict:
    """Send alert notification"""
    data = ctx.get_data()
    ctx.log(f"Sending alert via {channel}")
    
    return {
        "channel": channel,
        "message": message or f"Alert triggered: {data}",
        "status": "sent",
        "sent_at": datetime.now().isoformat()
    }


@AtomRegistry.register("alert", "threshold")
def alert_threshold(ctx: PipelineContext, field: str, operator: str, value: float, **params) -> Dict:
    """Check threshold condition"""
    data = ctx.get_data()
    
    # Get current value
    if isinstance(data, dict):
        current = data.get(field, 0)
    elif isinstance(data, list) and data:
        current = data[0].get(field, 0) if isinstance(data[0], dict) else 0
    else:
        current = 0
    
    # Check condition
    ops = {
        'gt': lambda a, b: a > b,
        '>': lambda a, b: a > b,
        'lt': lambda a, b: a < b,
        '<': lambda a, b: a < b,
        'eq': lambda a, b: a == b,
        '==': lambda a, b: a == b,
        'gte': lambda a, b: a >= b,
        '>=': lambda a, b: a >= b,
        'lte': lambda a, b: a <= b,
        '<=': lambda a, b: a <= b,
    }
    
    op_func = ops.get(operator, lambda a, b: False)
    triggered = op_func(float(current), float(value))
    
    return {
        "field": field,
        "operator": operator,
        "threshold": value,
        "current_value": current,
        "triggered": triggered
    }


# ============================================================
# BUDGET ATOMS
# ============================================================

@AtomRegistry.register("budget", "create")
def budget_create(ctx: PipelineContext, name: str, **params) -> Dict:
    """Create new budget"""
    ctx.log(f"Creating budget: {name}")
    
    budget_id = f"bdgt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "budget_id": budget_id,
        "name": name,
        "status": "created",
        "created_at": datetime.now().isoformat(),
        **params
    }


@AtomRegistry.register("budget", "load")
def budget_load(ctx: PipelineContext, budget_id: str, **params) -> Dict:
    """Load existing budget"""
    ctx.log(f"Loading budget: {budget_id}")
    return {
        "budget_id": budget_id,
        "status": "loaded",
        "_type": "budget"
    }


@AtomRegistry.register("budget", "compare")
def budget_compare(ctx: PipelineContext, scenario: str = "actual", **params) -> Dict:
    """Compare budget scenarios"""
    data = ctx.get_data()
    ctx.log(f"Comparing budget with scenario: {scenario}")
    
    return {
        "comparison": scenario,
        "base": data,
        "variance": {},
        "_type": "budget_comparison"
    }


@AtomRegistry.register("budget", "variance")
def budget_variance(ctx: PipelineContext, **params) -> Dict:
    """Calculate budget variance"""
    data = ctx.get_data()
    ctx.log("Calculating budget variance")
    
    # Mock variance calculation
    return {
        "total_planned": 100000,
        "total_actual": 95000,
        "variance": 5000,
        "variance_pct": 5.0,
        "status": "under_budget"
    }


@AtomRegistry.register("budget", "categorize")
def budget_categorize(ctx: PipelineContext, by: str, **params) -> Dict:
    """Categorize budget items"""
    data = ctx.get_data()
    ctx.log(f"Categorizing by: {by}")
    
    return {
        "categorized_by": by,
        "categories": {},
        "_type": "categorized_budget"
    }


# ============================================================
# INVESTMENT ATOMS
# ============================================================

@AtomRegistry.register("investment", "analyze")
def investment_analyze(ctx: PipelineContext, **params) -> Dict:
    """Full investment analysis"""
    ctx.log("Running investment analysis")
    
    initial = float(params.get('initial_investment', 0))
    cash_flows = params.get('cash_flows', [])
    rate = float(params.get('discount_rate', 0.1))
    
    # Calculate NPV
    npv = -initial
    for i, cf in enumerate(cash_flows):
        amount = cf.get('amount', cf) if isinstance(cf, dict) else cf
        npv += float(amount) / ((1 + rate) ** (i + 1))
    
    # Calculate ROI
    total_return = sum(
        cf.get('amount', cf) if isinstance(cf, dict) else cf 
        for cf in cash_flows
    )
    roi = ((total_return - initial) / initial * 100) if initial else 0
    
    return {
        "initial_investment": initial,
        "npv": round(npv, 2),
        "roi": round(roi, 2),
        "discount_rate": rate,
        "periods": len(cash_flows)
    }


@AtomRegistry.register("investment", "roi")
def investment_roi(ctx: PipelineContext, **params) -> Dict:
    """Calculate ROI"""
    data = ctx.get_data()
    ctx.log("Calculating ROI")
    
    if isinstance(data, dict):
        initial = float(data.get('initial_investment', 0))
        total_return = float(data.get('total_return', 0))
        roi = ((total_return - initial) / initial * 100) if initial else 0
        return {"roi": round(roi, 2), "roi_formatted": f"{round(roi, 2)}%"}
    
    return {"roi": 0, "roi_formatted": "0%"}


@AtomRegistry.register("investment", "npv")
def investment_npv(ctx: PipelineContext, rate: float = 0.1, **params) -> Dict:
    """Calculate NPV"""
    data = ctx.get_data()
    ctx.log(f"Calculating NPV with rate: {rate}")
    
    if isinstance(data, dict):
        initial = float(data.get('initial_investment', 0))
        cash_flows = data.get('cash_flows', [])
        
        npv = -initial
        for i, cf in enumerate(cash_flows):
            amount = cf.get('amount', cf) if isinstance(cf, dict) else cf
            npv += float(amount) / ((1 + rate) ** (i + 1))
        
        return {"npv": round(npv, 2), "discount_rate": rate}
    
    return {"npv": 0, "discount_rate": rate}


@AtomRegistry.register("investment", "irr")
def investment_irr(ctx: PipelineContext, **params) -> Dict:
    """Calculate IRR (simplified)"""
    ctx.log("Calculating IRR")
    # Simplified - in production use scipy or numpy
    return {"irr": None, "note": "IRR calculation requires scipy"}


@AtomRegistry.register("investment", "payback")
def investment_payback(ctx: PipelineContext, **params) -> Dict:
    """Calculate payback period"""
    data = ctx.get_data()
    ctx.log("Calculating payback period")
    
    if isinstance(data, dict):
        initial = float(data.get('initial_investment', 0))
        cash_flows = data.get('cash_flows', [])
        
        cumulative = 0
        for i, cf in enumerate(cash_flows):
            amount = cf.get('amount', cf) if isinstance(cf, dict) else cf
            cumulative += float(amount)
            if cumulative >= initial:
                # Interpolate
                prev_cumulative = cumulative - float(amount)
                fraction = (initial - prev_cumulative) / float(amount)
                return {"payback_period": round(i + fraction, 2), "unit": "periods"}
        
        return {"payback_period": None, "note": "Investment not recovered"}
    
    return {"payback_period": None}


@AtomRegistry.register("investment", "scenario")
def investment_scenario(ctx: PipelineContext, name: str, multiplier: float = 1.0, **params) -> Dict:
    """Apply scenario multiplier to investment"""
    data = ctx.get_data()
    ctx.log(f"Applying scenario: {name} with multiplier: {multiplier}")
    
    return {
        "scenario": name,
        "multiplier": multiplier,
        "base_data": data,
        "_type": "investment_scenario"
    }


# ============================================================
# FORECAST ATOMS
# ============================================================

@AtomRegistry.register("forecast", "predict")
def forecast_predict(ctx: PipelineContext, periods: int = 30, model: str = "prophet", **params) -> Dict:
    """Generate forecast predictions"""
    data = ctx.get_data()
    ctx.log(f"Predicting {periods} periods with {model}")
    
    return {
        "forecast_id": f"fcst_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "model": model,
        "periods": periods,
        "status": "completed",
        "predictions": [],  # Would contain actual predictions
        "_type": "forecast"
    }


@AtomRegistry.register("forecast", "trend")
def forecast_trend(ctx: PipelineContext, **params) -> Dict:
    """Analyze trend"""
    ctx.log("Analyzing trend")
    return {"trend": "increasing", "slope": 0.05, "_type": "trend_analysis"}


@AtomRegistry.register("forecast", "seasonality")
def forecast_seasonality(ctx: PipelineContext, **params) -> Dict:
    """Analyze seasonality"""
    ctx.log("Analyzing seasonality")
    return {"seasonal_periods": [7, 30, 365], "_type": "seasonality_analysis"}


@AtomRegistry.register("forecast", "confidence")
def forecast_confidence(ctx: PipelineContext, level: float = 0.95, **params) -> Dict:
    """Add confidence intervals"""
    data = ctx.get_data()
    ctx.log(f"Adding confidence intervals at {level}")
    return {"confidence_level": level, "data": data}


# ============================================================
# EXPORT ATOMS
# ============================================================

@AtomRegistry.register("export", "to_csv")
def export_to_csv(ctx: PipelineContext, path: str = None, **params) -> Dict:
    """Export to CSV"""
    data = ctx.get_data()
    ctx.log(f"Exporting to CSV: {path}")
    
    if isinstance(data, list) and data:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if isinstance(data[0], dict) else [])
        writer.writeheader()
        for row in data:
            if isinstance(row, dict):
                writer.writerow(row)
        csv_content = output.getvalue()
        return {"format": "csv", "path": path, "content": csv_content[:1000]}
    
    return {"format": "csv", "path": path, "status": "exported"}


@AtomRegistry.register("export", "to_json")
def export_to_json(ctx: PipelineContext, path: str = None, **params) -> Dict:
    """Export to JSON"""
    data = ctx.get_data()
    ctx.log(f"Exporting to JSON: {path}")
    
    return {
        "format": "json",
        "path": path,
        "content": json.dumps(data, default=str)[:1000] if data else "{}",
        "status": "exported"
    }


@AtomRegistry.register("export", "to_excel")
def export_to_excel(ctx: PipelineContext, path: str = None, **params) -> Dict:
    """Export to Excel"""
    ctx.log(f"Exporting to Excel: {path}")
    return {"format": "xlsx", "path": path, "status": "exported"}


@AtomRegistry.register("export", "to_api")
def export_to_api(ctx: PipelineContext, url: str, method: str = "POST", **params) -> Dict:
    """Send data to API endpoint"""
    data = ctx.get_data()
    ctx.log(f"Sending to API: {method} {url}")
    
    return {
        "url": url,
        "method": method,
        "status": "sent",
        "payload_size": len(json.dumps(data, default=str)) if data else 0
    }


# ============================================================
# VIEW ATOMS - Generate view specifications for frontend rendering
# ============================================================

_view_counter = 0

def _generate_view_id(prefix: str) -> str:
    global _view_counter
    _view_counter += 1
    return f"{prefix}_{_view_counter}"


def _wrap_view_result(data: Any, view_spec: Dict) -> Dict:
    """Wrap data and view spec into result format"""
    if isinstance(data, dict) and "views" in data:
        data["views"].append(view_spec)
        return data
    return {"data": data, "views": [view_spec]}


@AtomRegistry.register("view", "chart")
def view_chart(ctx: PipelineContext, **params) -> Dict:
    """Generate chart view specification"""
    data = ctx.get_data()
    
    chart_type = params.get("type", params.get("_arg0", "bar"))
    x_field = params.get("x", params.get("x_field", ""))
    y_field = params.get("y", params.get("y_field", ""))
    series = params.get("series", [])
    title = params.get("title", "")
    colors = params.get("colors", [])
    show_legend = params.get("legend", True)
    show_grid = params.get("grid", True)
    
    ctx.log(f"Creating chart view: {chart_type}")
    
    spec = {
        "type": "chart",
        "id": _generate_view_id("chart"),
        "title": title,
        "chart_type": chart_type,
        "x_field": x_field,
        "y_field": y_field,
        "series": series if isinstance(series, list) else [series],
        "colors": colors if isinstance(colors, list) else [colors],
        "show_legend": show_legend,
        "show_grid": show_grid,
    }
    
    return _wrap_view_result(data, spec)


@AtomRegistry.register("view", "table")
def view_table(ctx: PipelineContext, **params) -> Dict:
    """Generate table view specification"""
    data = ctx.get_data()
    
    columns_input = params.get("columns", params.get("_arg0", []))
    title = params.get("title", "")
    sortable = params.get("sortable", True)
    filterable = params.get("filterable", True)
    paginate = params.get("paginate", True)
    page_size = params.get("page_size", 10)
    striped = params.get("striped", True)
    
    # Convert simple column names to column specs
    columns = []
    if isinstance(columns_input, list):
        for col in columns_input:
            if isinstance(col, str):
                columns.append({"field": col, "header": col.replace("_", " ").title()})
            elif isinstance(col, dict):
                columns.append(col)
    
    # Auto-detect columns from data if not specified
    if not columns and isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            columns = [{"field": k, "header": k.replace("_", " ").title()} 
                      for k in data[0].keys()]
    
    ctx.log(f"Creating table view with {len(columns)} columns")
    
    spec = {
        "type": "table",
        "id": _generate_view_id("table"),
        "title": title,
        "columns": columns,
        "sortable": sortable,
        "filterable": filterable,
        "paginate": paginate,
        "page_size": page_size,
        "striped": striped,
    }
    
    return _wrap_view_result(data, spec)


@AtomRegistry.register("view", "card")
def view_card(ctx: PipelineContext, **params) -> Dict:
    """Generate metric card specification"""
    data = ctx.get_data()
    
    value_field = params.get("value", params.get("_arg0", ""))
    title = params.get("title", "")
    format_str = params.get("format", "")
    icon = params.get("icon", "")
    style = params.get("style", "default")
    trend_field = params.get("trend", "")
    
    ctx.log(f"Creating card view: {title}")
    
    spec = {
        "type": "card",
        "id": _generate_view_id("card"),
        "title": title,
        "value_field": value_field,
        "format": format_str,
        "icon": icon,
        "style": style,
        "trend_field": trend_field,
    }
    
    return _wrap_view_result(data, spec)


@AtomRegistry.register("view", "kpi")
def view_kpi(ctx: PipelineContext, **params) -> Dict:
    """Generate KPI widget specification"""
    data = ctx.get_data()
    
    value_field = params.get("value", params.get("_arg0", ""))
    target_field = params.get("target", "")
    title = params.get("title", "")
    format_str = params.get("format", "")
    icon = params.get("icon", "")
    show_progress = params.get("progress", True)
    
    ctx.log(f"Creating KPI view: {title}")
    
    spec = {
        "type": "kpi",
        "id": _generate_view_id("kpi"),
        "title": title,
        "value_field": value_field,
        "target_field": target_field,
        "format": format_str,
        "icon": icon,
        "show_progress": show_progress,
    }
    
    return _wrap_view_result(data, spec)


@AtomRegistry.register("view", "grid")
def view_grid(ctx: PipelineContext, **params) -> Dict:
    """Generate grid layout specification"""
    data = ctx.get_data()
    
    columns = params.get("columns", params.get("_arg0", 2))
    gap = params.get("gap", 16)
    items = params.get("items", [])
    title = params.get("title", "")
    
    ctx.log(f"Creating grid view: {columns} columns")
    
    spec = {
        "type": "grid",
        "id": _generate_view_id("grid"),
        "title": title,
        "columns": columns,
        "gap": gap,
        "items": items,
    }
    
    return _wrap_view_result(data, spec)


@AtomRegistry.register("view", "dashboard")
def view_dashboard(ctx: PipelineContext, **params) -> Dict:
    """Generate dashboard specification"""
    data = ctx.get_data()
    
    layout = params.get("layout", params.get("_arg0", "grid"))
    widgets = params.get("widgets", [])
    title = params.get("title", "")
    refresh = params.get("refresh", 0)
    
    ctx.log(f"Creating dashboard view: {title}")
    
    spec = {
        "type": "dashboard",
        "id": _generate_view_id("dashboard"),
        "title": title,
        "layout": layout,
        "widgets": widgets,
        "refresh_interval": refresh,
    }
    
    return _wrap_view_result(data, spec)


@AtomRegistry.register("view", "text")
def view_text(ctx: PipelineContext, **params) -> Dict:
    """Generate text/markdown view specification"""
    data = ctx.get_data()
    
    content = params.get("content", params.get("_arg0", ""))
    format_type = params.get("format", "text")
    title = params.get("title", "")
    
    ctx.log(f"Creating text view")
    
    spec = {
        "type": "text",
        "id": _generate_view_id("text"),
        "title": title,
        "content": content,
        "format": format_type,
    }
    
    return _wrap_view_result(data, spec)


@AtomRegistry.register("view", "list")
def view_list(ctx: PipelineContext, **params) -> Dict:
    """Generate list view specification"""
    data = ctx.get_data()
    
    title = params.get("title", "")
    primary_field = params.get("primary", params.get("_arg0", ""))
    secondary_field = params.get("secondary", "")
    icon_field = params.get("icon", "")
    
    ctx.log(f"Creating list view")
    
    spec = {
        "type": "list",
        "id": _generate_view_id("list"),
        "title": title,
        "primary_field": primary_field,
        "secondary_field": secondary_field,
        "icon_field": icon_field,
    }
    
    return _wrap_view_result(data, spec)


# ============================================================
# UI ATOMS - Generate UI component specifications for pages
# ============================================================

def _wrap_ui_result(data: Any, ui_spec: Dict) -> Dict:
    """Wrap data and UI spec into result format"""
    if isinstance(data, dict) and "ui" in data:
        data["ui"].append(ui_spec)
        return data
    return {"data": data, "ui": [ui_spec]}


@AtomRegistry.register("ui", "page")
def ui_page(ctx: PipelineContext, **params) -> Dict:
    """Generate page container specification"""
    data = ctx.get_data()
    
    title = params.get("title", params.get("_arg0", "Page"))
    layout = params.get("layout", "default")
    theme = params.get("theme", "light")
    
    ctx.log(f"Creating UI page: {title}")
    
    spec = {
        "type": "page",
        "id": _generate_view_id("page"),
        "title": title,
        "layout": layout,
        "theme": theme,
        "components": [],
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "nav")
def ui_nav(ctx: PipelineContext, **params) -> Dict:
    """Generate navigation bar specification"""
    data = ctx.get_data()
    
    brand = params.get("brand", params.get("_arg0", ""))
    logo = params.get("logo", "")
    links = params.get("links", [])
    cta = params.get("cta", [])
    sticky = params.get("sticky", True)
    
    ctx.log(f"Creating UI nav: {brand}")
    
    spec = {
        "type": "nav",
        "id": _generate_view_id("nav"),
        "brand": brand,
        "logo": logo,
        "links": links,
        "cta": cta,
        "sticky": sticky,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "hero")
def ui_hero(ctx: PipelineContext, **params) -> Dict:
    """Generate hero section specification"""
    data = ctx.get_data()
    
    title = params.get("title", params.get("_arg0", ""))
    subtitle = params.get("subtitle", "")
    badge = params.get("badge", "")
    cta_primary = params.get("cta_primary", {})
    cta_secondary = params.get("cta_secondary", {})
    image = params.get("image", "")
    gradient = params.get("gradient", True)
    
    ctx.log(f"Creating UI hero: {title}")
    
    spec = {
        "type": "hero",
        "id": _generate_view_id("hero"),
        "title": title,
        "subtitle": subtitle,
        "badge": badge,
        "cta_primary": cta_primary,
        "cta_secondary": cta_secondary,
        "image": image,
        "gradient": gradient,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "section")
def ui_section(ctx: PipelineContext, **params) -> Dict:
    """Generate section specification"""
    data = ctx.get_data()
    
    title = params.get("title", params.get("_arg0", ""))
    subtitle = params.get("subtitle", "")
    layout = params.get("layout", "default")
    background = params.get("bg", "white")
    padding = params.get("padding", "lg")
    
    ctx.log(f"Creating UI section: {title}")
    
    spec = {
        "type": "section",
        "id": _generate_view_id("section"),
        "title": title,
        "subtitle": subtitle,
        "layout": layout,
        "background": background,
        "padding": padding,
        "children": [],
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "grid")
def ui_grid(ctx: PipelineContext, **params) -> Dict:
    """Generate grid layout specification"""
    data = ctx.get_data()
    
    columns = params.get("columns", params.get("_arg0", 3))
    gap = params.get("gap", "md")
    items = params.get("items", [])
    
    ctx.log(f"Creating UI grid: {columns} columns")
    
    spec = {
        "type": "grid",
        "id": _generate_view_id("grid"),
        "columns": columns,
        "gap": gap,
        "items": items,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "form")
def ui_form(ctx: PipelineContext, **params) -> Dict:
    """Generate form specification"""
    data = ctx.get_data()
    
    action = params.get("action", params.get("_arg0", ""))
    method = params.get("method", "POST")
    fields = params.get("fields", [])
    submit_text = params.get("submit", "Wyślij")
    layout = params.get("layout", "vertical")
    
    ctx.log(f"Creating UI form: {action}")
    
    spec = {
        "type": "form",
        "id": _generate_view_id("form"),
        "action": action,
        "method": method,
        "fields": fields,
        "submit_text": submit_text,
        "layout": layout,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "input")
def ui_input(ctx: PipelineContext, **params) -> Dict:
    """Generate form input specification"""
    data = ctx.get_data()
    
    name = params.get("name", params.get("_arg0", ""))
    input_type = params.get("type", "text")
    label = params.get("label", name.replace("_", " ").title())
    placeholder = params.get("placeholder", "")
    required = params.get("required", False)
    options = params.get("options", [])
    
    spec = {
        "type": "input",
        "id": _generate_view_id("input"),
        "name": name,
        "input_type": input_type,
        "label": label,
        "placeholder": placeholder,
        "required": required,
        "options": options,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "button")
def ui_button(ctx: PipelineContext, **params) -> Dict:
    """Generate button specification"""
    data = ctx.get_data()
    
    text = params.get("text", params.get("_arg0", "Button"))
    href = params.get("href", "")
    onclick = params.get("onclick", "")
    variant = params.get("variant", "primary")
    icon = params.get("icon", "")
    size = params.get("size", "md")
    
    spec = {
        "type": "button",
        "id": _generate_view_id("button"),
        "text": text,
        "href": href,
        "onclick": onclick,
        "variant": variant,
        "icon": icon,
        "size": size,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "stats")
def ui_stats(ctx: PipelineContext, **params) -> Dict:
    """Generate stats/metrics section specification"""
    data = ctx.get_data()
    
    items = params.get("items", [])
    layout = params.get("layout", "horizontal")
    
    ctx.log(f"Creating UI stats: {len(items)} items")
    
    spec = {
        "type": "stats",
        "id": _generate_view_id("stats"),
        "items": items,
        "layout": layout,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "pricing")
def ui_pricing(ctx: PipelineContext, **params) -> Dict:
    """Generate pricing table specification"""
    data = ctx.get_data()
    
    plans = params.get("plans", [])
    highlight = params.get("highlight", "")
    
    ctx.log(f"Creating UI pricing: {len(plans)} plans")
    
    spec = {
        "type": "pricing",
        "id": _generate_view_id("pricing"),
        "plans": plans,
        "highlight": highlight,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "features")
def ui_features(ctx: PipelineContext, **params) -> Dict:
    """Generate features grid specification"""
    data = ctx.get_data()
    
    items = params.get("items", [])
    columns = params.get("columns", 3)
    
    ctx.log(f"Creating UI features: {len(items)} items")
    
    spec = {
        "type": "features",
        "id": _generate_view_id("features"),
        "items": items,
        "columns": columns,
    }
    
    return _wrap_ui_result(data, spec)


@AtomRegistry.register("ui", "footer")
def ui_footer(ctx: PipelineContext, **params) -> Dict:
    """Generate footer specification"""
    data = ctx.get_data()
    
    brand = params.get("brand", "")
    links = params.get("links", [])
    copyright_text = params.get("copyright", "")
    social = params.get("social", [])
    
    spec = {
        "type": "footer",
        "id": _generate_view_id("footer"),
        "brand": brand,
        "links": links,
        "copyright": copyright_text,
        "social": social,
    }
    
    return _wrap_ui_result(data, spec)
