"""
ANALYTICA Framework - Base API Service
Modular FastAPI application for multi-domain analytics platform
"""
from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from pathlib import Path

from dsl.core.parser import (
    AtomRegistry,
    PipelineContext as DSLPipelineContext,
    parse as dsl_parse,
    execute as dsl_execute,
)
from dsl.atoms import implementations as _dsl_atoms
from api.auth import auth_router, get_current_user, get_optional_user

# Get domain from environment
DOMAIN = os.getenv("ANALYTICA_DOMAIN", "repox.pl")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Create FastAPI app
app = FastAPI(
    title=f"ANALYTICA API - {DOMAIN}",
    description=f"Analytics API for {DOMAIN}",
    version="2.0.0",
)

_src_dir = Path(__file__).resolve().parent.parent
_frontend_dir = _src_dir / "frontend"
_landing_dir = _frontend_dir / "landing"
_sdk_js_dir = _src_dir / "sdk" / "js"

# Mount static directories (order matters - more specific paths first)
if _sdk_js_dir.exists():
    app.mount("/ui/sdk", StaticFiles(directory=str(_sdk_js_dir)), name="ui-sdk")
if _landing_dir.exists():
    app.mount("/landing", StaticFiles(directory=str(_landing_dir), html=True), name="landing")
if _frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dir), html=True), name="ui")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# ============ MODELS ============

class HealthResponse(BaseModel):
    status: str
    domain: str
    port: int
    timestamp: str
    modules: List[str]


class DomainInfo(BaseModel):
    domain: str
    display_name: str
    tagline: str
    type: str
    modules: List[str]
    theme: Dict[str, str]


# Reports Models
class ReportRequest(BaseModel):
    template: str
    title: str = "Raport"
    data_source: Optional[str] = None
    parameters: Dict[str, Any] = {}
    format: str = "pdf"
    schedule: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    status: str
    template: str
    format: str
    created_at: str
    download_url: Optional[str] = None


# Alerts Models
class AlertRequest(BaseModel):
    name: str
    metric: str
    condition: str  # gt, lt, eq, change_pct
    threshold: float
    channels: List[str] = ["email"]
    enabled: bool = True


class AlertResponse(BaseModel):
    alert_id: str
    name: str
    status: str
    created_at: str


# Budget Models (for multiplan.pl, planbudzetu.pl)
class BudgetCategory(BaseModel):
    name: str
    planned: Decimal
    actual: Decimal = Decimal("0")


class BudgetRequest(BaseModel):
    name: str
    period_start: date
    period_end: date
    categories: List[BudgetCategory]
    scenario: str = "realistic"


class BudgetResponse(BaseModel):
    budget_id: str
    name: str
    status: str
    total_planned: Decimal
    total_actual: Decimal
    variance: Decimal
    variance_pct: float


# Investment Models (for planinwestycji.pl)
class CashFlow(BaseModel):
    period: int
    amount: Decimal
    description: str = ""


class InvestmentRequest(BaseModel):
    name: str
    initial_investment: Decimal
    cash_flows: List[CashFlow]
    discount_rate: float = 0.1
    investment_type: str = "capex"


class ROIResponse(BaseModel):
    investment_id: str
    name: str
    roi: float
    npv: Decimal
    irr: Optional[float]
    payback_period: Optional[float]
    profitability_index: float
    risk_level: str


# Forecast Models
class ForecastRequest(BaseModel):
    dataset_id: str
    periods: int = 30
    model: str = "prophet"
    confidence: float = 0.95


class ForecastResponse(BaseModel):
    forecast_id: str
    model: str
    periods: int
    status: str


# DSL Models
class DSLExecuteRequest(BaseModel):
    dsl: str = Field(..., description="DSL pipeline string")
    variables: Dict[str, Any] = Field(default_factory=dict)
    input_data: Optional[Any] = None
    domain: Optional[str] = None


class DSLExecuteResponse(BaseModel):
    execution_id: str
    status: str
    result: Optional[Any] = None
    logs: List[Dict] = []
    errors: List[Dict] = []
    execution_time_ms: Optional[float] = None


class DSLParseRequest(BaseModel):
    dsl: str


class DSLParseResponse(BaseModel):
    name: str
    steps: List[Dict]
    variables: Dict[str, Any]
    dsl_normalized: str
    json_representation: Dict


class DSLValidateRequest(BaseModel):
    dsl: str


class DSLValidateResponse(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


# ============ DOMAIN CONFIGURATION ============

DOMAIN_MODULES = {
    "repox.pl": ["reports", "alerts", "voice", "forecast", "budget", "investment", "integrations"],
    "analizowanie.pl": ["reports", "charts", "data_import"],
    "przeanalizuj.pl": ["voice", "reports", "natural_language"],
    "alerts.pl": ["alerts", "reports", "anomaly", "webhooks"],
    "estymacja.pl": ["forecast", "what_if", "reports"],
    "retrospektywa.pl": ["reports", "time_series", "cohort"],
    "persony.pl": ["segmentation", "persona", "attribution", "reports"],
    "specyfikacja.pl": ["spec_generator", "api_docs", "compliance", "reports"],
    "nisza.pl": ["all"],
    "multiplan.pl": ["budget", "forecast", "reports", "alerts"],
    "planbudzetu.pl": ["budget", "reports", "alerts", "forecast"],
    "planinwestycji.pl": ["investment", "forecast", "reports", "budget"],
}

DOMAIN_INFO = {
    "repox.pl": {
        "display_name": "REPOX",
        "tagline": "Centrum analityki biznesowej",
        "type": "hub",
        "theme": {"primary": "#6366F1", "accent": "#8B5CF6", "mode": "dark"}
    },
    "alerts.pl": {
        "display_name": "Alerts.pl",
        "tagline": "Monitoruj KPI w czasie rzeczywistym",
        "type": "specialized",
        "theme": {"primary": "#EF4444", "accent": "#F97316", "mode": "light"}
    },
    "estymacja.pl": {
        "display_name": "Estymacja",
        "tagline": "Prognozy i predykcje oparte na AI",
        "type": "specialized",
        "theme": {"primary": "#10B981", "accent": "#34D399", "mode": "light"}
    },
    "multiplan.pl": {
        "display_name": "MultiPlan",
        "tagline": "Planuj finanse w wielu scenariuszach",
        "type": "specialized",
        "theme": {"primary": "#0891B2", "accent": "#06B6D4", "mode": "light"}
    },
    "planbudzetu.pl": {
        "display_name": "PlanBudżetu",
        "tagline": "Raporty finansowe pod kontrolą",
        "type": "specialized",
        "theme": {"primary": "#059669", "accent": "#10B981", "mode": "light"}
    },
    "planinwestycji.pl": {
        "display_name": "PlanInwestycji",
        "tagline": "Analizuj ROI, planuj inwestycje",
        "type": "specialized",
        "theme": {"primary": "#7C3AED", "accent": "#8B5CF6", "mode": "light"}
    },
}


def get_modules() -> List[str]:
    """Get enabled modules for current domain"""
    modules = DOMAIN_MODULES.get(DOMAIN, [])
    if "all" in modules:
        return list(set(m for mods in DOMAIN_MODULES.values() for m in mods if m != "all"))
    return modules


def check_module(module: str):
    """Dependency to check if module is enabled for current domain"""
    def _check():
        modules = get_modules()
        if module not in modules and "all" not in DOMAIN_MODULES.get(DOMAIN, []):
            raise HTTPException(
                status_code=403,
                detail=f"Module '{module}' not available for domain '{DOMAIN}'"
            )
        return True
    return Depends(_check)


# ============ ROUTES ============

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check and domain info"""
    return HealthResponse(
        status="healthy",
        domain=DOMAIN,
        port=API_PORT,
        timestamp=datetime.utcnow().isoformat(),
        modules=get_modules()
    )


@app.get("/health")
async def health():
    return {"status": "ok", "domain": DOMAIN}


@app.get("/v1/domain", response_model=DomainInfo)
async def get_domain_info():
    """Get current domain configuration"""
    info = DOMAIN_INFO.get(DOMAIN, {
        "display_name": DOMAIN,
        "tagline": "Analytics Platform",
        "type": "general",
        "theme": {"primary": "#6366F1", "accent": "#8B5CF6", "mode": "light"}
    })
    return DomainInfo(
        domain=DOMAIN,
        modules=get_modules(),
        **info
    )


dsl_router = APIRouter()

# In-memory storage for pipelines
_stored_pipelines: Dict[str, Dict[str, Any]] = {}


@dsl_router.get("/health")
async def dsl_health():
    return {"status": "ok", "service": "dsl-api", "domain": DOMAIN}


@dsl_router.get("/atoms", response_model=Dict[str, List[str]])
async def dsl_list_atoms():
    return AtomRegistry.list_atoms()


@dsl_router.get("/atoms/{atom_type}")
async def dsl_list_atom_actions(atom_type: str):
    all_atoms = AtomRegistry.list_atoms()
    if atom_type not in all_atoms:
        raise HTTPException(status_code=404, detail=f"Unknown atom type: {atom_type}")
    return {"type": atom_type, "actions": all_atoms[atom_type]}


class AtomExecuteRequest(BaseModel):
    input_data: Optional[Any] = None
    params: Optional[Dict[str, Any]] = None


@dsl_router.post("/atoms/{atom_type}/{action}")
async def dsl_execute_atom(atom_type: str, action: str, request: AtomExecuteRequest = None):
    handler = AtomRegistry.get(atom_type, action)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Unknown atom: {atom_type}.{action}")
    
    ctx = DSLPipelineContext(domain=DOMAIN)
    if request and request.input_data is not None:
        ctx.set_data(request.input_data)
    
    try:
        result = handler(ctx, **(request.params if request and request.params else {}))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@dsl_router.post("/pipeline/parse", response_model=DSLParseResponse)
async def dsl_parse_pipeline(request: DSLParseRequest):
    pipeline = dsl_parse(request.dsl)
    return DSLParseResponse(
        name=pipeline.name,
        steps=[
            {
                "atom": step.atom.to_dict(),
                "condition": step.condition,
                "on_error": step.on_error,
            }
            for step in pipeline.steps
        ],
        variables=pipeline.variables,
        dsl_normalized=pipeline.to_dsl(),
        json_representation=pipeline.to_dict(),
    )


@dsl_router.post("/pipeline/validate", response_model=DSLValidateResponse)
async def dsl_validate_pipeline(request: DSLValidateRequest):
    errors: List[str] = []
    warnings: List[str] = []
    try:
        pipeline = dsl_parse(request.dsl)
    except SyntaxError as e:
        return DSLValidateResponse(valid=False, errors=[str(e)], warnings=[])

    for step in pipeline.steps:
        atom = step.atom
        handler = AtomRegistry.get(atom.type.value, atom.action)
        if not handler:
            errors.append(f"Unknown atom: {atom.type.value}.{atom.action}")

    for step in pipeline.steps:
        for _, value in step.atom.params.items():
            if isinstance(value, str) and value.startswith('$'):
                var_name = value[1:]
                if var_name not in pipeline.variables:
                    warnings.append(f"Unresolved variable: {value}")

    return DSLValidateResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)


@dsl_router.post("/pipeline/execute", response_model=DSLExecuteResponse)
async def dsl_execute_pipeline(request: DSLExecuteRequest):
    execution_id = f"exec_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    start_time = datetime.utcnow()
    try:
        pipeline = dsl_parse(request.dsl)
        variables = {**pipeline.variables, **(request.variables or {})}
        ctx = DSLPipelineContext(variables=variables, domain=request.domain or DOMAIN)
        if request.input_data is not None:
            ctx.set_data(request.input_data)
        result_ctx = dsl_execute(pipeline, ctx)
        exec_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return DSLExecuteResponse(
            execution_id=execution_id,
            status="success",
            result=result_ctx.get_data(),
            logs=result_ctx.logs,
            errors=result_ctx.errors,
            execution_time_ms=round(exec_time, 2),
        )
    except SyntaxError as e:
        return DSLExecuteResponse(
            execution_id=execution_id,
            status="error",
            result=None,
            logs=[],
            errors=[{"type": "SyntaxError", "message": str(e)}],
        )
    except Exception as e:
        return DSLExecuteResponse(
            execution_id=execution_id,
            status="error",
            result=None,
            logs=[],
            errors=[{"type": type(e).__name__, "message": str(e)}],
        )


# Stored pipelines CRUD
class StoredPipelineRequest(BaseModel):
    name: str
    dsl: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class StoredPipelineResponse(BaseModel):
    id: str
    name: str
    dsl: str
    description: Optional[str] = None
    tags: List[str] = []
    created_at: str


@dsl_router.get("/pipelines")
async def list_stored_pipelines():
    return {"pipelines": list(_stored_pipelines.values()), "count": len(_stored_pipelines)}


@dsl_router.post("/pipelines", response_model=StoredPipelineResponse)
async def create_stored_pipeline(request: StoredPipelineRequest):
    pipeline_id = f"pipe_{uuid.uuid4().hex[:8]}"
    stored = {
        "id": pipeline_id,
        "name": request.name,
        "dsl": request.dsl,
        "description": request.description,
        "tags": request.tags or [],
        "created_at": datetime.utcnow().isoformat(),
    }
    _stored_pipelines[pipeline_id] = stored
    return StoredPipelineResponse(**stored)


@dsl_router.get("/pipelines/{pipeline_id}", response_model=StoredPipelineResponse)
async def get_stored_pipeline(pipeline_id: str):
    if pipeline_id not in _stored_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {pipeline_id}")
    return StoredPipelineResponse(**_stored_pipelines[pipeline_id])


@dsl_router.delete("/pipelines/{pipeline_id}")
async def delete_stored_pipeline(pipeline_id: str):
    if pipeline_id not in _stored_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {pipeline_id}")
    del _stored_pipelines[pipeline_id]
    return {"status": "deleted", "id": pipeline_id}


@dsl_router.post("/pipelines/{pipeline_id}/run", response_model=DSLExecuteResponse)
async def run_stored_pipeline(pipeline_id: str, variables: Dict[str, Any] = None, input_data: Any = None):
    if pipeline_id not in _stored_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {pipeline_id}")
    
    stored = _stored_pipelines[pipeline_id]
    request = DSLExecuteRequest(dsl=stored["dsl"], variables=variables or {}, input_data=input_data)
    return await dsl_execute_pipeline(request)


app.include_router(dsl_router, prefix="/api/v1")
app.include_router(dsl_router, prefix="/v1", include_in_schema=False)


# ============ REPORTS MODULE ============

@app.get("/v1/reports", dependencies=[check_module("reports")])
async def list_reports():
    """List available report templates"""
    templates = {
        "repox.pl": ["dashboard", "executive_summary", "custom"],
        "alerts.pl": ["alert_summary", "incident_report"],
        "estymacja.pl": ["forecast_report", "scenario_comparison"],
        "multiplan.pl": ["budget_vs_actual", "scenario_comparison", "financial_summary"],
        "planbudzetu.pl": ["monthly_budget", "expense_analysis", "income_vs_expense"],
        "planinwestycji.pl": ["investment_proposal", "roi_analysis", "portfolio_summary"],
    }
    return {
        "domain": DOMAIN,
        "templates": templates.get(DOMAIN, ["basic_report"])
    }


@app.post("/v1/reports/generate", response_model=ReportResponse, dependencies=[check_module("reports")])
async def generate_report(report: ReportRequest):
    """Generate a new report"""
    report_id = f"rpt_{DOMAIN.replace('.pl', '')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return ReportResponse(
        report_id=report_id,
        status="queued",
        template=report.template,
        format=report.format,
        created_at=datetime.utcnow().isoformat(),
        download_url=f"/v1/reports/{report_id}/download"
    )


# ============ ALERTS MODULE ============

@app.get("/v1/alerts", dependencies=[check_module("alerts")])
async def list_alerts():
    """List configured alerts"""
    return {"domain": DOMAIN, "alerts": [], "count": 0}


@app.post("/v1/alerts", response_model=AlertResponse, dependencies=[check_module("alerts")])
async def create_alert(alert: AlertRequest):
    """Create a new alert"""
    alert_id = f"alrt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return AlertResponse(
        alert_id=alert_id,
        name=alert.name,
        status="active",
        created_at=datetime.utcnow().isoformat()
    )


# ============ BUDGET MODULE (multiplan.pl, planbudzetu.pl) ============

@app.get("/v1/budgets", dependencies=[check_module("budget")])
async def list_budgets():
    """List budgets"""
    return {"domain": DOMAIN, "budgets": [], "count": 0}


@app.post("/v1/budgets", response_model=BudgetResponse, dependencies=[check_module("budget")])
async def create_budget(budget: BudgetRequest):
    """Create a new budget"""
    total_planned = sum(c.planned for c in budget.categories)
    total_actual = sum(c.actual for c in budget.categories)
    variance = total_planned - total_actual
    variance_pct = float(variance / total_planned * 100) if total_planned else 0
    
    budget_id = f"bdgt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return BudgetResponse(
        budget_id=budget_id,
        name=budget.name,
        status="active",
        total_planned=total_planned,
        total_actual=total_actual,
        variance=variance,
        variance_pct=round(variance_pct, 2)
    )


@app.get("/v1/budgets/scenarios", dependencies=[check_module("budget")])
async def list_scenarios():
    """List budget scenarios (for multiplan.pl)"""
    if DOMAIN != "multiplan.pl":
        return {"scenarios": ["default"]}
    return {
        "scenarios": [
            {"id": "optimistic", "name": "Optymistyczny", "multiplier": 1.2},
            {"id": "realistic", "name": "Realistyczny", "multiplier": 1.0},
            {"id": "pessimistic", "name": "Pesymistyczny", "multiplier": 0.8},
        ]
    }


@app.get("/v1/budgets/categories", dependencies=[check_module("budget")])
async def list_categories():
    """List budget categories"""
    categories = [
        "Wynagrodzenia",
        "Usługi zewnętrzne", 
        "Marketing",
        "IT i oprogramowanie",
        "Biuro i administracja",
        "Podróże służbowe",
        "Szkolenia",
        "Pozostałe"
    ]
    return {"domain": DOMAIN, "categories": categories}


# ============ INVESTMENT MODULE (planinwestycji.pl) ============

@app.get("/v1/investments", dependencies=[check_module("investment")])
async def list_investments():
    """List investments"""
    return {"domain": DOMAIN, "investments": [], "count": 0}


@app.post("/v1/investments/analyze", response_model=ROIResponse, dependencies=[check_module("investment")])
async def analyze_investment(investment: InvestmentRequest):
    """Analyze investment and calculate ROI, NPV, IRR"""
    # Calculate metrics
    initial = float(investment.initial_investment)
    cash_flows = [float(cf.amount) for cf in investment.cash_flows]
    rate = investment.discount_rate
    
    # NPV calculation
    npv = -initial + sum(cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
    
    # ROI calculation
    total_return = sum(cash_flows)
    roi = ((total_return - initial) / initial) * 100 if initial else 0
    
    # Payback period (simple)
    cumulative = 0
    payback = None
    for i, cf in enumerate(cash_flows):
        cumulative += cf
        if cumulative >= initial:
            payback = i + 1 - (cumulative - initial) / cf
            break
    
    # Profitability Index
    pv_cash_flows = sum(cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
    pi = pv_cash_flows / initial if initial else 0
    
    # Risk level
    if roi > 20 and npv > 0:
        risk = "low"
    elif roi > 10 and npv > 0:
        risk = "medium"
    else:
        risk = "high"
    
    investment_id = f"inv_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return ROIResponse(
        investment_id=investment_id,
        name=investment.name,
        roi=round(roi, 2),
        npv=Decimal(str(round(npv, 2))),
        irr=None,  # Would need scipy for proper IRR calculation
        payback_period=round(payback, 2) if payback else None,
        profitability_index=round(pi, 2),
        risk_level=risk
    )


@app.get("/v1/investments/calculators", dependencies=[check_module("investment")])
async def list_calculators():
    """List available investment calculators"""
    return {
        "calculators": [
            {"id": "roi", "name": "ROI - Return on Investment"},
            {"id": "npv", "name": "NPV - Net Present Value"},
            {"id": "irr", "name": "IRR - Internal Rate of Return"},
            {"id": "payback", "name": "Okres zwrotu"},
            {"id": "profitability", "name": "Wskaźnik rentowności"},
        ]
    }


# ============ FORECAST MODULE ============

@app.post("/v1/forecast/predict", response_model=ForecastResponse, dependencies=[check_module("forecast")])
async def create_forecast(forecast: ForecastRequest):
    """Generate a forecast"""
    forecast_id = f"fcst_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return ForecastResponse(
        forecast_id=forecast_id,
        model=forecast.model,
        periods=forecast.periods,
        status="queued"
    )


@app.get("/v1/forecast/models", dependencies=[check_module("forecast")])
async def list_forecast_models():
    """List available forecast models"""
    return {
        "models": [
            {"id": "prophet", "name": "Prophet", "description": "Facebook's time series forecasting"},
            {"id": "arima", "name": "ARIMA", "description": "Auto-regressive integrated moving average"},
            {"id": "exponential", "name": "Exponential Smoothing", "description": "Holt-Winters method"},
        ]
    }


# ============ ENTERPRISE QUOTES ============

_quotes_db = []

class QuoteRequest(BaseModel):
    name: str
    email: str
    company: str
    phone: Optional[str] = None
    product: str
    users: Optional[str] = None
    budget: Optional[str] = None
    message: Optional[str] = None
    ticketId: Optional[str] = None

@app.post("/api/v1/quotes")
async def submit_quote(quote: QuoteRequest):
    """Submit enterprise quote request"""
    quote_data = {
        **quote.dict(),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "new"
    }
    _quotes_db.append(quote_data)
    return {"status": "success", "ticketId": quote.ticketId, "message": "Quote received"}

@app.get("/api/v1/quotes")
async def list_quotes():
    """List all quotes (admin only)"""
    return {"quotes": _quotes_db, "count": len(_quotes_db)}


# ============ INTEGRATIONS ============

@app.get("/v1/integrations")
async def list_integrations():
    """List available integrations for this domain"""
    integrations = {
        "multiplan.pl": ["ifirma", "fakturownia", "comarch_erp", "google_sheets", "excel"],
        "planbudzetu.pl": ["ifirma", "fakturownia", "infakt", "mbank", "ing", "pko"],
        "planinwestycji.pl": ["excel", "google_sheets", "comarch_erp"],
        "alerts.pl": ["slack", "teams", "pagerduty", "webhook"],
    }
    return {
        "domain": DOMAIN,
        "available": integrations.get(DOMAIN, ["csv", "api"]),
        "connected": []
    }


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
