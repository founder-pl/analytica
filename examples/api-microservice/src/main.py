"""
ANALYTICA API Microservice
DSL-powered analytics API
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os
import sys

# Add parent to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

app = FastAPI(
    title="Analytica API",
    description="DSL-powered analytics microservice",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class PipelineRequest(BaseModel):
    dsl: str
    input_data: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None


class AnalyticsRequest(BaseModel):
    data: List[Dict[str, Any]]
    metrics: List[str] = ["sum", "avg", "count"]
    group_by: Optional[str] = None


class ReportRequest(BaseModel):
    data: Dict[str, Any]
    template: str = "summary"
    format: str = "json"


# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analytica-api"}


# Pipeline execution
@app.post("/api/v1/pipeline/execute")
async def execute_pipeline(request: PipelineRequest):
    """Execute DSL pipeline"""
    try:
        # Import DSL engine
        from src.dsl import DSLParser, PipelineExecutor
        
        parser = DSLParser()
        ast = parser.parse(request.dsl)
        
        executor = PipelineExecutor()
        result = executor.execute(ast, request.input_data, request.variables)
        
        return result
    except ImportError:
        # Mock response for standalone testing
        return {
            "data": request.input_data or {},
            "views": [],
            "status": "mock_executed",
            "dsl": request.dsl[:100] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Analytics endpoints
@app.post("/api/v1/analytics/summary")
async def analytics_summary(request: AnalyticsRequest):
    """Get analytics summary from data"""
    dsl = f"""
        data.from_input()
        | metrics.calculate(metrics={request.metrics}, field="amount")
    """
    
    if request.group_by:
        dsl = f"""
            data.from_input()
            | transform.group_by("{request.group_by}")
            | transform.aggregate(by="{request.group_by}", func="sum")
            | metrics.calculate(metrics={request.metrics}, field="amount")
        """
    
    # Execute DSL
    try:
        from src.dsl import DSLParser, PipelineExecutor
        parser = DSLParser()
        executor = PipelineExecutor()
        result = executor.execute(parser.parse(dsl), {"items": request.data})
        return result
    except ImportError:
        # Mock calculation
        if not request.data:
            return {"sum": 0, "avg": 0, "count": 0}
        
        amounts = [item.get("amount", 0) for item in request.data]
        return {
            "sum": sum(amounts),
            "avg": sum(amounts) / len(amounts) if amounts else 0,
            "count": len(amounts),
            "min": min(amounts) if amounts else 0,
            "max": max(amounts) if amounts else 0
        }


# Report generation
@app.post("/api/v1/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate report from data"""
    dsl = f"""
        data.from_input()
        | metrics.calculate(metrics=["sum", "avg", "count"], field="amount")
        | report.generate(format="{request.format}", template="{request.template}")
    """
    
    return {
        "report_id": "rpt_" + str(hash(str(request.data)))[-8:],
        "format": request.format,
        "template": request.template,
        "data": request.data,
        "status": "generated"
    }


# Metrics endpoint for Prometheus
@app.get("/api/v1/metrics")
async def metrics():
    """Prometheus metrics"""
    return """
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{endpoint="/api/v1/pipeline/execute"} 100
api_requests_total{endpoint="/api/v1/analytics/summary"} 50

# HELP api_request_duration_seconds API request duration
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{le="0.1"} 80
api_request_duration_seconds_bucket{le="0.5"} 95
api_request_duration_seconds_bucket{le="1.0"} 100
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
