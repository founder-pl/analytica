"""
ANALYTICA DSL - REST API Server
================================

Endpoints:
    POST /api/v1/pipeline/execute     Execute pipeline
    POST /api/v1/pipeline/parse       Parse pipeline to AST
    POST /api/v1/pipeline/validate    Validate pipeline syntax
    GET  /api/v1/atoms                List available atoms
    POST /api/v1/atoms/{type}/{action} Execute single atom
    
    # Stored pipelines
    GET  /api/v1/pipelines            List stored pipelines
    POST /api/v1/pipelines            Store new pipeline
    GET  /api/v1/pipelines/{id}       Get pipeline by ID
    POST /api/v1/pipelines/{id}/run   Execute stored pipeline
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio
import uuid
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dsl.core.parser import (
    Pipeline, PipelineBuilder, PipelineDefinition, PipelineContext,
    PipelineExecutor, DSLParser, AtomRegistry, parse, execute
)
from dsl.atoms.implementations import *  # Register atoms
from dsl.atoms.deploy import *  # Register deploy atoms
from dsl.atoms.data import *  # Register data definition atoms

# Create FastAPI app
app = FastAPI(
    title="ANALYTICA DSL API",
    description="REST API for executing analytics pipelines",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for pipelines (use Redis/DB in production)
PIPELINE_STORE: Dict[str, Dict] = {}
EXECUTION_HISTORY: List[Dict] = []


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class PipelineExecuteRequest(BaseModel):
    """Request to execute a pipeline"""
    dsl: str = Field(..., description="DSL pipeline string")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Pipeline variables")
    input_data: Optional[Any] = Field(None, description="Input data for pipeline")
    domain: Optional[str] = Field(None, description="Domain context")
    async_exec: bool = Field(False, description="Execute asynchronously")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dsl": 'data.load("sales.csv") | transform.filter(year=2024) | metrics.sum("amount")',
                "variables": {"year": 2024},
                "domain": "planbudzetu.pl"
            }
        }


class PipelineExecuteResponse(BaseModel):
    """Response from pipeline execution"""
    execution_id: str
    status: str  # success, error, pending
    result: Optional[Any] = None
    logs: List[Dict] = []
    errors: List[Dict] = []
    execution_time_ms: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec_20241230120000",
                "status": "success",
                "result": {"sum": 150000},
                "logs": [{"level": "info", "message": "Executing: data.load()"}],
                "errors": [],
                "execution_time_ms": 45.2
            }
        }


class PipelineParseRequest(BaseModel):
    """Request to parse a pipeline"""
    dsl: str = Field(..., description="DSL pipeline string")


class PipelineParseResponse(BaseModel):
    """Response from pipeline parsing"""
    name: str
    steps: List[Dict]
    variables: Dict[str, Any]
    dsl_normalized: str
    json_representation: Dict


class PipelineValidateRequest(BaseModel):
    """Request to validate a pipeline"""
    dsl: str


class PipelineValidateResponse(BaseModel):
    """Response from pipeline validation"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class AtomExecuteRequest(BaseModel):
    """Request to execute a single atom"""
    params: Dict[str, Any] = Field(default_factory=dict)
    input_data: Optional[Any] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class StoredPipeline(BaseModel):
    """Stored pipeline definition"""
    id: Optional[str] = None
    name: str
    description: str = ""
    dsl: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    domain: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[str] = []


class AtomInfo(BaseModel):
    """Information about an atom"""
    type: str
    action: str
    description: str = ""
    parameters: List[Dict] = []
    example: str = ""


# ============================================================
# PIPELINE ENDPOINTS
# ============================================================

@app.post("/api/v1/pipeline/execute", response_model=PipelineExecuteResponse)
async def execute_pipeline(request: PipelineExecuteRequest):
    """Execute a DSL pipeline"""
    execution_id = f"exec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    start_time = datetime.now()
    
    try:
        # Parse pipeline
        pipeline = parse(request.dsl)
        
        # Merge variables
        variables = {**pipeline.variables, **request.variables}
        
        # Create context
        ctx = PipelineContext(
            variables=variables,
            domain=request.domain
        )
        
        # Set input data if provided
        if request.input_data is not None:
            ctx.set_data(request.input_data)
        
        # Execute
        if request.async_exec:
            # Return pending status for async execution
            asyncio.create_task(_execute_async(execution_id, pipeline, ctx))
            return PipelineExecuteResponse(
                execution_id=execution_id,
                status="pending",
                result=None,
                logs=[],
                errors=[]
            )
        
        result = execute(pipeline, ctx)
        
        # Calculate execution time
        exec_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Store in history
        EXECUTION_HISTORY.append({
            "execution_id": execution_id,
            "dsl": request.dsl,
            "status": "success",
            "executed_at": datetime.now().isoformat()
        })
        
        return PipelineExecuteResponse(
            execution_id=execution_id,
            status="success",
            result=result.get_data(),
            logs=result.logs,
            errors=result.errors,
            execution_time_ms=round(exec_time, 2)
        )
        
    except SyntaxError as e:
        return PipelineExecuteResponse(
            execution_id=execution_id,
            status="error",
            result=None,
            logs=[],
            errors=[{"type": "SyntaxError", "message": str(e)}]
        )
    except Exception as e:
        return PipelineExecuteResponse(
            execution_id=execution_id,
            status="error",
            result=None,
            logs=[],
            errors=[{"type": type(e).__name__, "message": str(e)}]
        )


async def _execute_async(execution_id: str, pipeline: PipelineDefinition, ctx: PipelineContext):
    """Execute pipeline asynchronously"""
    try:
        executor = PipelineExecutor(ctx)
        await executor.execute_async(pipeline)
        # Store result (would use Redis/DB in production)
    except Exception as e:
        pass  # Log error


@app.post("/api/v1/pipeline/parse", response_model=PipelineParseResponse)
async def parse_pipeline(request: PipelineParseRequest):
    """Parse DSL pipeline to AST"""
    try:
        pipeline = parse(request.dsl)
        
        return PipelineParseResponse(
            name=pipeline.name,
            steps=[
                {
                    "atom": step.atom.to_dict(),
                    "condition": step.condition,
                    "on_error": step.on_error
                }
                for step in pipeline.steps
            ],
            variables=pipeline.variables,
            dsl_normalized=pipeline.to_dsl(),
            json_representation=pipeline.to_dict()
        )
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Syntax error: {e}")


@app.post("/api/v1/pipeline/validate", response_model=PipelineValidateResponse)
async def validate_pipeline(request: PipelineValidateRequest):
    """Validate DSL pipeline syntax"""
    errors = []
    warnings = []
    
    try:
        pipeline = parse(request.dsl)
        
        # Check if atoms exist
        for step in pipeline.steps:
            atom = step.atom
            handler = AtomRegistry.get(atom.type.value, atom.action)
            if not handler:
                errors.append(f"Unknown atom: {atom.type.value}.{atom.action}")
        
        # Check for unresolved variables
        for step in pipeline.steps:
            for key, value in step.atom.params.items():
                if isinstance(value, str) and value.startswith('$'):
                    var_name = value[1:]
                    if var_name not in pipeline.variables:
                        warnings.append(f"Unresolved variable: {value}")
        
        return PipelineValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    except SyntaxError as e:
        return PipelineValidateResponse(
            valid=False,
            errors=[str(e)],
            warnings=[]
        )


# ============================================================
# ATOMS ENDPOINTS
# ============================================================

@app.get("/api/v1/atoms", response_model=Dict[str, List[str]])
async def list_atoms():
    """List all available atoms"""
    return AtomRegistry.list_atoms()


@app.get("/api/v1/atoms/{atom_type}", response_model=List[str])
async def list_atom_actions(atom_type: str):
    """List actions for a specific atom type"""
    atoms = AtomRegistry.list_atoms()
    if atom_type not in atoms:
        raise HTTPException(status_code=404, detail=f"Unknown atom type: {atom_type}")
    return atoms[atom_type]


@app.post("/api/v1/atoms/{atom_type}/{action}")
async def execute_atom(atom_type: str, action: str, request: AtomExecuteRequest):
    """Execute a single atom"""
    handler = AtomRegistry.get(atom_type, action)
    
    if not handler:
        raise HTTPException(
            status_code=404, 
            detail=f"Unknown atom: {atom_type}.{action}"
        )
    
    try:
        ctx = PipelineContext(
            variables=request.context.get('variables', {}),
            domain=request.context.get('domain')
        )
        
        if request.input_data is not None:
            ctx.set_data(request.input_data)
        
        result = handler(ctx, **request.params)
        
        return {
            "status": "success",
            "result": result,
            "logs": ctx.logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# STORED PIPELINES ENDPOINTS
# ============================================================

@app.get("/api/v1/pipelines", response_model=List[StoredPipeline])
async def list_pipelines(domain: Optional[str] = None, tag: Optional[str] = None):
    """List stored pipelines"""
    pipelines = list(PIPELINE_STORE.values())
    
    if domain:
        pipelines = [p for p in pipelines if p.get('domain') == domain]
    
    if tag:
        pipelines = [p for p in pipelines if tag in p.get('tags', [])]
    
    return pipelines


@app.post("/api/v1/pipelines", response_model=StoredPipeline)
async def create_pipeline(pipeline: StoredPipeline):
    """Store a new pipeline"""
    # Validate DSL
    try:
        parse(pipeline.dsl)
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Invalid DSL: {e}")
    
    # Generate ID
    pipeline_id = pipeline.id or f"pipe_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()
    
    stored = {
        "id": pipeline_id,
        "name": pipeline.name,
        "description": pipeline.description,
        "dsl": pipeline.dsl,
        "variables": pipeline.variables,
        "domain": pipeline.domain,
        "tags": pipeline.tags,
        "created_at": now,
        "updated_at": now
    }
    
    PIPELINE_STORE[pipeline_id] = stored
    
    return StoredPipeline(**stored)


@app.get("/api/v1/pipelines/{pipeline_id}", response_model=StoredPipeline)
async def get_pipeline(pipeline_id: str):
    """Get a stored pipeline by ID"""
    if pipeline_id not in PIPELINE_STORE:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return StoredPipeline(**PIPELINE_STORE[pipeline_id])


@app.delete("/api/v1/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: str):
    """Delete a stored pipeline"""
    if pipeline_id not in PIPELINE_STORE:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    del PIPELINE_STORE[pipeline_id]
    return {"status": "deleted", "id": pipeline_id}


@app.post("/api/v1/pipelines/{pipeline_id}/run", response_model=PipelineExecuteResponse)
async def run_stored_pipeline(
    pipeline_id: str, 
    variables: Dict[str, Any] = None,
    input_data: Any = None
):
    """Execute a stored pipeline"""
    if pipeline_id not in PIPELINE_STORE:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    stored = PIPELINE_STORE[pipeline_id]
    
    request = PipelineExecuteRequest(
        dsl=stored['dsl'],
        variables={**stored.get('variables', {}), **(variables or {})},
        input_data=input_data,
        domain=stored.get('domain')
    )
    
    return await execute_pipeline(request)


# ============================================================
# UTILITY ENDPOINTS
# ============================================================

@app.get("/api/v1/history")
async def get_execution_history(limit: int = 100):
    """Get recent execution history"""
    return EXECUTION_HISTORY[-limit:]


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ANALYTICA DSL API",
        "version": "2.0.0",
        "atoms_loaded": sum(len(v) for v in AtomRegistry.list_atoms().values())
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "ANALYTICA DSL API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "execute": "POST /api/v1/pipeline/execute",
            "parse": "POST /api/v1/pipeline/parse",
            "validate": "POST /api/v1/pipeline/validate",
            "atoms": "GET /api/v1/atoms",
            "pipelines": "GET /api/v1/pipelines"
        }
    }


# ============================================================
# WEBSOCKET FOR STREAMING RESULTS
# ============================================================

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    """WebSocket endpoint for streaming pipeline execution"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('action') == 'execute':
                dsl = data.get('dsl', '')
                variables = data.get('variables', {})
                
                try:
                    pipeline = parse(dsl)
                    ctx = PipelineContext(variables=variables)
                    
                    # Stream each step
                    for i, step in enumerate(pipeline.steps):
                        await websocket.send_json({
                            "type": "step_start",
                            "step": i,
                            "atom": step.atom.to_dsl()
                        })
                        
                        # Execute step
                        handler = AtomRegistry.get(step.atom.type.value, step.atom.action)
                        if handler:
                            params = ctx.resolve_params(step.atom.params)
                            result = handler(ctx, **params)
                            if result is not None:
                                ctx.set_data(result)
                        
                        await websocket.send_json({
                            "type": "step_complete",
                            "step": i,
                            "result": ctx.get_data()
                        })
                    
                    await websocket.send_json({
                        "type": "complete",
                        "result": ctx.get_data()
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
    
    except WebSocketDisconnect:
        pass


# Run with: uvicorn dsl.api.server:app --reload --port 8080
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
