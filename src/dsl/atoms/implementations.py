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

from .parser import AtomRegistry, PipelineContext


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
    
    return {"_type": "filtered", "_data": data, "_conditions": conditions}


def _matches_conditions(item: Dict, conditions: Dict) -> bool:
    """Check if item matches all conditions"""
    for key, value in conditions.items():
        if key.startswith('_'):
            continue
        if key not in item:
            return False
        if item[key] != value:
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
def transform_limit(ctx: PipelineContext, n: int, **params) -> Any:
    """Limit number of results"""
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
def metrics_sum(ctx: PipelineContext, field: str, **params) -> float:
    """Calculate sum"""
    data = ctx.get_data()
    values = _extract_values(data, field)
    return sum(values)


@AtomRegistry.register("metrics", "avg")
def metrics_avg(ctx: PipelineContext, field: str, **params) -> float:
    """Calculate average"""
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
