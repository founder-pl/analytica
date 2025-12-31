"""
ANALYTICA DSL - Python SDK
===========================

Fluent API for building and executing analytics pipelines
Works as standalone library or with API server

Usage:
    from analytica import Pipeline, Analytica
    
    # Fluent builder
    result = (Pipeline()
        .data.load('sales.csv')
        .transform.filter(year=2024)
        .metrics.sum('amount')
        .execute())
    
    # DSL string
    result = Analytica.run('data.load("sales") | metrics.sum("amount")')
    
    # Async
    result = await Pipeline()
        .data.load('sales')
        .metrics.calculate(['sum', 'avg'])
        .execute_async()
"""

from __future__ import annotations
import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
import httpx
from pathlib import Path
import sys

# Add parent to path for internal imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import core DSL components
try:
    from dsl.core.parser import (
        Pipeline as CorePipeline,
        PipelineBuilder as CorePipelineBuilder,
        PipelineDefinition,
        PipelineContext,
        PipelineExecutor,
        DSLParser,
        AtomRegistry,
        parse,
        execute as core_execute
    )
    from dsl.atoms.implementations import *  # Register atoms
    HAS_LOCAL_DSL = True
except ImportError:
    HAS_LOCAL_DSL = False


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class SDKConfig:
    """SDK configuration"""
    api_url: str = "http://localhost:8080"
    timeout: float = 30.0
    domain: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    local_execution: bool = True  # Use local DSL if available


_config = SDKConfig()


def configure(**kwargs):
    """Configure SDK settings"""
    global _config
    for key, value in kwargs.items():
        if hasattr(_config, key):
            setattr(_config, key, value)


# ============================================================
# ATOM CLASS
# ============================================================

@dataclass
class Atom:
    """Single atomic operation"""
    type: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "action": self.action,
            "params": self.params
        }
    
    def to_dsl(self) -> str:
        params = []
        for k, v in self.params.items():
            if k.startswith('_'):
                continue
            if isinstance(v, str):
                params.append(f'{k}="{v}"')
            else:
                params.append(f'{k}={json.dumps(v)}')
        
        return f"{self.type}.{self.action}({', '.join(params)})"


# ============================================================
# ATOM BUILDERS
# ============================================================

class AtomBuilder:
    """Base class for atom builders"""
    
    def __init__(self, pipeline: "PipelineBuilder", atom_type: str):
        self._pipeline = pipeline
        self._atom_type = atom_type
    
    def _add(self, action: str, **params) -> "PipelineBuilder":
        self._pipeline._steps.append(Atom(self._atom_type, action, params))
        return self._pipeline


class DataBuilder(AtomBuilder):
    """Builder for data operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "data")
    
    def load(self, source: str, **params) -> "PipelineBuilder":
        """Load data from source"""
        return self._add("load", source=source, **params)
    
    def query(self, sql: str, **params) -> "PipelineBuilder":
        """Execute SQL query"""
        return self._add("query", sql=sql, **params)
    
    def fetch(self, url: str, **params) -> "PipelineBuilder":
        """Fetch from URL"""
        return self._add("fetch", url=url, **params)
    
    def from_input(self, data: Any = None) -> "PipelineBuilder":
        """Use provided data"""
        return self._add("from_input", data=data)


class TransformBuilder(AtomBuilder):
    """Builder for transform operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "transform")
    
    def filter(self, **conditions) -> "PipelineBuilder":
        """Filter data by conditions"""
        return self._add("filter", **conditions)
    
    def map(self, func: str, field: str = None) -> "PipelineBuilder":
        """Map function over data"""
        return self._add("map", func=func, field=field)
    
    def sort(self, by: str, order: str = "asc") -> "PipelineBuilder":
        """Sort by field"""
        return self._add("sort", by=by, order=order)
    
    def limit(self, n: int) -> "PipelineBuilder":
        """Limit results"""
        return self._add("limit", n=n)
    
    def group_by(self, *fields) -> "PipelineBuilder":
        """Group by fields"""
        return self._add("group_by", fields=list(fields))
    
    def aggregate(self, by: str, func: str = "sum") -> "PipelineBuilder":
        """Aggregate data"""
        return self._add("aggregate", by=by, func=func)
    
    def select(self, *fields) -> "PipelineBuilder":
        """Select fields"""
        return self._add("select", fields=list(fields))
    
    def rename(self, **mapping) -> "PipelineBuilder":
        """Rename fields"""
        return self._add("rename", **mapping)


class MetricsBuilder(AtomBuilder):
    """Builder for metrics operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "metrics")
    
    def calculate(self, metrics: List[str], field: str = None) -> "PipelineBuilder":
        """Calculate multiple metrics"""
        return self._add("calculate", metrics=metrics, field=field)
    
    def sum(self, field: str) -> "PipelineBuilder":
        """Calculate sum"""
        return self._add("sum", field=field)
    
    def avg(self, field: str) -> "PipelineBuilder":
        """Calculate average"""
        return self._add("avg", field=field)
    
    def count(self) -> "PipelineBuilder":
        """Count items"""
        return self._add("count")
    
    def variance(self, field: str) -> "PipelineBuilder":
        """Calculate variance"""
        return self._add("variance", field=field)
    
    def percentile(self, field: str, p: int = 50) -> "PipelineBuilder":
        """Calculate percentile"""
        return self._add("percentile", field=field, p=p)


class ReportBuilder(AtomBuilder):
    """Builder for report operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "report")
    
    def generate(self, format: str = "pdf", template: str = None) -> "PipelineBuilder":
        """Generate report"""
        return self._add("generate", format=format, template=template)
    
    def schedule(self, cron: str, recipients: List[str] = None) -> "PipelineBuilder":
        """Schedule report"""
        return self._add("schedule", cron=cron, recipients=recipients or [])
    
    def send(self, to: List[str], **params) -> "PipelineBuilder":
        """Send report"""
        return self._add("send", to=to, **params)


class AlertBuilder(AtomBuilder):
    """Builder for alert operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "alert")
    
    def when(self, condition: str) -> "PipelineBuilder":
        """Define alert condition"""
        return self._add("when", condition=condition)
    
    def send(self, channel: str, message: str = None) -> "PipelineBuilder":
        """Send alert"""
        return self._add("send", channel=channel, message=message)
    
    def threshold(self, field: str, operator: str, value: float) -> "PipelineBuilder":
        """Check threshold"""
        return self._add("threshold", field=field, operator=operator, value=value)


class BudgetBuilder(AtomBuilder):
    """Builder for budget operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "budget")
    
    def create(self, name: str, **params) -> "PipelineBuilder":
        """Create budget"""
        return self._add("create", name=name, **params)
    
    def load(self, budget_id: str) -> "PipelineBuilder":
        """Load budget"""
        return self._add("load", budget_id=budget_id)
    
    def compare(self, scenario: str = "actual") -> "PipelineBuilder":
        """Compare scenarios"""
        return self._add("compare", scenario=scenario)
    
    def variance(self) -> "PipelineBuilder":
        """Calculate variance"""
        return self._add("variance")
    
    def categorize(self, by: str) -> "PipelineBuilder":
        """Categorize items"""
        return self._add("categorize", by=by)


class InvestmentBuilder(AtomBuilder):
    """Builder for investment operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "investment")
    
    def analyze(self, **params) -> "PipelineBuilder":
        """Full investment analysis"""
        return self._add("analyze", **params)
    
    def roi(self) -> "PipelineBuilder":
        """Calculate ROI"""
        return self._add("roi")
    
    def npv(self, rate: float = 0.1) -> "PipelineBuilder":
        """Calculate NPV"""
        return self._add("npv", rate=rate)
    
    def irr(self) -> "PipelineBuilder":
        """Calculate IRR"""
        return self._add("irr")
    
    def payback(self) -> "PipelineBuilder":
        """Calculate payback period"""
        return self._add("payback")
    
    def scenario(self, name: str, multiplier: float = 1.0) -> "PipelineBuilder":
        """Apply scenario"""
        return self._add("scenario", name=name, multiplier=multiplier)


class ForecastBuilder(AtomBuilder):
    """Builder for forecast operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "forecast")
    
    def predict(self, periods: int = 30, model: str = "prophet") -> "PipelineBuilder":
        """Generate predictions"""
        return self._add("predict", periods=periods, model=model)
    
    def trend(self) -> "PipelineBuilder":
        """Analyze trend"""
        return self._add("trend")
    
    def seasonality(self) -> "PipelineBuilder":
        """Analyze seasonality"""
        return self._add("seasonality")
    
    def confidence(self, level: float = 0.95) -> "PipelineBuilder":
        """Add confidence intervals"""
        return self._add("confidence", level=level)


class ExportBuilder(AtomBuilder):
    """Builder for export operations"""
    
    def __init__(self, pipeline: "PipelineBuilder"):
        super().__init__(pipeline, "export")
    
    def to_csv(self, path: str = None) -> "PipelineBuilder":
        """Export to CSV"""
        return self._add("to_csv", path=path)
    
    def to_json(self, path: str = None) -> "PipelineBuilder":
        """Export to JSON"""
        return self._add("to_json", path=path)
    
    def to_excel(self, path: str = None) -> "PipelineBuilder":
        """Export to Excel"""
        return self._add("to_excel", path=path)
    
    def to_api(self, url: str, method: str = "POST") -> "PipelineBuilder":
        """Send to API"""
        return self._add("to_api", url=url, method=method)


# ============================================================
# PIPELINE BUILDER
# ============================================================

class PipelineBuilder:
    """Fluent pipeline builder"""
    
    def __init__(self, domain: str = None):
        self._steps: List[Atom] = []
        self._variables: Dict[str, Any] = {}
        self._name: str = "pipeline"
        self._domain: str = domain or _config.domain
    
    def name(self, name: str) -> "PipelineBuilder":
        """Set pipeline name"""
        self._name = name
        return self
    
    def var(self, name: str, value: Any) -> "PipelineBuilder":
        """Set variable"""
        self._variables[name] = value
        return self
    
    def vars(self, **variables) -> "PipelineBuilder":
        """Set multiple variables"""
        self._variables.update(variables)
        return self
    
    # Atom builders
    @property
    def data(self) -> DataBuilder:
        return DataBuilder(self)
    
    @property
    def transform(self) -> TransformBuilder:
        return TransformBuilder(self)
    
    @property
    def metrics(self) -> MetricsBuilder:
        return MetricsBuilder(self)
    
    @property
    def report(self) -> ReportBuilder:
        return ReportBuilder(self)
    
    @property
    def alert(self) -> AlertBuilder:
        return AlertBuilder(self)
    
    @property
    def budget(self) -> BudgetBuilder:
        return BudgetBuilder(self)
    
    @property
    def investment(self) -> InvestmentBuilder:
        return InvestmentBuilder(self)
    
    @property
    def forecast(self) -> ForecastBuilder:
        return ForecastBuilder(self)
    
    @property
    def export(self) -> ExportBuilder:
        return ExportBuilder(self)
    
    # Build methods
    def build(self) -> Dict:
        """Build pipeline definition"""
        return {
            "name": self._name,
            "steps": [s.to_dict() for s in self._steps],
            "variables": self._variables,
            "domain": self._domain
        }
    
    def to_dsl(self) -> str:
        """Convert to DSL string"""
        steps = " | ".join(s.to_dsl() for s in self._steps)
        
        lines = []
        if self._name != "pipeline":
            lines.append(f"@pipeline {self._name}:")
        
        for k, v in self._variables.items():
            lines.append(f"${k} = {json.dumps(v)}")
        
        lines.append(steps)
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.build(), indent=2)
    
    # Execution methods
    def execute(self, input_data: Any = None, **extra_vars) -> Dict:
        """Execute pipeline synchronously"""
        variables = {**self._variables, **extra_vars}
        
        # Try local execution first
        if _config.local_execution and HAS_LOCAL_DSL:
            return self._execute_local(input_data, variables)
        
        # Fall back to API
        return self._execute_api(input_data, variables)
    
    async def execute_async(self, input_data: Any = None, **extra_vars) -> Dict:
        """Execute pipeline asynchronously"""
        variables = {**self._variables, **extra_vars}
        
        if _config.local_execution and HAS_LOCAL_DSL:
            # Run local execution in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                lambda: self._execute_local(input_data, variables)
            )
        
        return await self._execute_api_async(input_data, variables)
    
    def _execute_local(self, input_data: Any, variables: Dict) -> Dict:
        """Execute using local DSL engine"""
        ctx = PipelineContext(variables=variables, domain=self._domain)
        
        if input_data is not None:
            ctx.set_data(input_data)
        
        dsl = self.to_dsl()
        result = core_execute(dsl, ctx)
        
        return {
            "status": "success",
            "result": result.get_data(),
            "logs": result.logs,
            "errors": result.errors
        }
    
    def _execute_api(self, input_data: Any, variables: Dict) -> Dict:
        """Execute via API"""
        with httpx.Client(timeout=_config.timeout) as client:
            response = client.post(
                f"{_config.api_url}/api/v1/pipeline/execute",
                json={
                    "dsl": self.to_dsl(),
                    "variables": variables,
                    "input_data": input_data,
                    "domain": self._domain
                },
                headers=_config.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def _execute_api_async(self, input_data: Any, variables: Dict) -> Dict:
        """Execute via API asynchronously"""
        async with httpx.AsyncClient(timeout=_config.timeout) as client:
            response = await client.post(
                f"{_config.api_url}/api/v1/pipeline/execute",
                json={
                    "dsl": self.to_dsl(),
                    "variables": variables,
                    "input_data": input_data,
                    "domain": self._domain
                },
                headers=_config.headers
            )
            response.raise_for_status()
            return response.json()


# ============================================================
# ANALYTICA CLIENT
# ============================================================

class AnalyticaClient:
    """Client for ANALYTICA API"""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or _config.api_url
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=_config.timeout,
                headers=_config.headers
            )
        return self._client
    
    def run(self, dsl: str, variables: Dict = None, 
            input_data: Any = None, domain: str = None) -> Dict:
        """Run DSL pipeline"""
        # Try local first
        if _config.local_execution and HAS_LOCAL_DSL:
            ctx = PipelineContext(
                variables=variables or {},
                domain=domain
            )
            if input_data is not None:
                ctx.set_data(input_data)
            
            result = core_execute(dsl, ctx)
            return {
                "status": "success",
                "result": result.get_data(),
                "logs": result.logs,
                "errors": result.errors
            }
        
        # API fallback
        response = self._get_client().post(
            f"{self.api_url}/api/v1/pipeline/execute",
            json={
                "dsl": dsl,
                "variables": variables or {},
                "input_data": input_data,
                "domain": domain
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def run_async(self, dsl: str, variables: Dict = None,
                       input_data: Any = None, domain: str = None) -> Dict:
        """Run DSL pipeline asynchronously"""
        async with httpx.AsyncClient(timeout=_config.timeout) as client:
            response = await client.post(
                f"{self.api_url}/api/v1/pipeline/execute",
                json={
                    "dsl": dsl,
                    "variables": variables or {},
                    "input_data": input_data,
                    "domain": domain
                },
                headers=_config.headers
            )
            response.raise_for_status()
            return response.json()
    
    def parse(self, dsl: str) -> Dict:
        """Parse DSL string"""
        if HAS_LOCAL_DSL:
            pipeline = parse(dsl)
            return {
                "name": pipeline.name,
                "steps": [s.atom.to_dict() for s in pipeline.steps],
                "variables": pipeline.variables
            }
        
        response = self._get_client().post(
            f"{self.api_url}/api/v1/pipeline/parse",
            json={"dsl": dsl}
        )
        response.raise_for_status()
        return response.json()
    
    def validate(self, dsl: str) -> Dict:
        """Validate DSL string"""
        response = self._get_client().post(
            f"{self.api_url}/api/v1/pipeline/validate",
            json={"dsl": dsl}
        )
        return response.json()
    
    def atoms(self) -> Dict:
        """List available atoms"""
        if HAS_LOCAL_DSL:
            return AtomRegistry.list_atoms()
        
        response = self._get_client().get(f"{self.api_url}/api/v1/atoms")
        return response.json()
    
    def execute_atom(self, atom_type: str, action: str, 
                     params: Dict = None, input_data: Any = None) -> Dict:
        """Execute single atom"""
        response = self._get_client().post(
            f"{self.api_url}/api/v1/atoms/{atom_type}/{action}",
            json={
                "params": params or {},
                "input_data": input_data
            }
        )
        return response.json()
    
    def list_pipelines(self, domain: str = None, tag: str = None) -> List[Dict]:
        """List stored pipelines"""
        params = {}
        if domain:
            params["domain"] = domain
        if tag:
            params["tag"] = tag
        
        response = self._get_client().get(
            f"{self.api_url}/api/v1/pipelines",
            params=params
        )
        return response.json()
    
    def save_pipeline(self, name: str, dsl: str, 
                     description: str = "", **kwargs) -> Dict:
        """Save a pipeline"""
        response = self._get_client().post(
            f"{self.api_url}/api/v1/pipelines",
            json={
                "name": name,
                "dsl": dsl,
                "description": description,
                **kwargs
            }
        )
        return response.json()
    
    def run_pipeline(self, pipeline_id: str, 
                    variables: Dict = None, input_data: Any = None) -> Dict:
        """Run a stored pipeline"""
        response = self._get_client().post(
            f"{self.api_url}/api/v1/pipelines/{pipeline_id}/run",
            json={
                "variables": variables or {},
                "input_data": input_data
            }
        )
        return response.json()
    
    def close(self):
        """Close client"""
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# ============================================================
# FACTORY FUNCTIONS
# ============================================================

def Pipeline(domain: str = None) -> PipelineBuilder:
    """Create a new pipeline builder"""
    return PipelineBuilder(domain)


def run(dsl: str, **kwargs) -> Dict:
    """Quick run a DSL string"""
    return Analytica.run(dsl, **kwargs)


async def run_async(dsl: str, **kwargs) -> Dict:
    """Quick run a DSL string asynchronously"""
    return await Analytica.run_async(dsl, **kwargs)


# Singleton client
Analytica = AnalyticaClient()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'Pipeline',
    'PipelineBuilder', 
    'Analytica',
    'AnalyticaClient',
    'Atom',
    'configure',
    'run',
    'run_async'
]
