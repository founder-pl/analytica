"""
ANALYTICA DSL - Domain Specific Language for Analytics Pipelines
================================================================

DSL Syntax:
-----------
# Basic pipe syntax (Unix-like)
data.load("sales.csv") | transform.filter(year=2024) | report.generate("pdf")

# Named pipeline
@pipeline monthly_report:
    data.load($source)
    | transform.aggregate(by="month")
    | metrics.calculate(["sum", "avg"])
    | report.generate($format)

# Conditionals
data.load("sales") | when(total > 1000).then(alert.send("high_sales"))

# Parallel execution
parallel:
    - data.load("sales") | metrics.revenue()
    - data.load("costs") | metrics.expenses()
| merge() | report.generate("comparison")

# Variables and context
$year = 2024
$threshold = 10000
data.load("invoices") | filter(amount > $threshold, year = $year)

Example Usage:
--------------
>>> from dsl import Pipeline
>>> p = Pipeline('data.load("sales.csv") | transform.sum("amount")')
>>> result = p.execute()

>>> # Or with builder
>>> result = (Pipeline()
...     .data.load("sales.csv")
...     .transform.filter(year=2024)
...     .metrics.calculate("revenue")
...     .execute())
"""

from __future__ import annotations
import re
import json
import yaml
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
from functools import reduce


class AtomType(Enum):
    """Types of atomic operations in DSL"""
    DATA = "data"
    TRANSFORM = "transform"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    METRICS = "metrics"
    REPORT = "report"
    ALERT = "alert"
    BUDGET = "budget"
    INVESTMENT = "investment"
    FORECAST = "forecast"
    EXPORT = "export"
    VALIDATE = "validate"
    MERGE = "merge"
    SPLIT = "split"
    CACHE = "cache"


@dataclass
class Atom:
    """Single atomic operation in pipeline"""
    type: AtomType
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "action": self.action,
            "params": self.params
        }
    
    def to_dsl(self) -> str:
        params_str = ", ".join(
            f'{k}={repr(v)}' if isinstance(v, str) else f'{k}={v}'
            for k, v in self.params.items()
        )
        return f"{self.type.value}.{self.action}({params_str})"
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Atom":
        return cls(
            type=AtomType(data["type"]),
            action=data["action"],
            params=data.get("params", {})
        )


@dataclass
class PipelineStep:
    """A step in the pipeline with metadata"""
    atom: Atom
    condition: Optional[str] = None
    on_error: str = "stop"  # stop, skip, retry
    timeout: Optional[int] = None
    cache_key: Optional[str] = None


@dataclass
class PipelineDefinition:
    """Complete pipeline definition"""
    name: str
    steps: List[PipelineStep]
    variables: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    version: str = "1.0"
    domain: Optional[str] = None
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access for backwards compatibility"""
        return self.to_dict()[key]
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator"""
        return key in self.to_dict()
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "domain": self.domain,
            "variables": self.variables,
            "steps": [
                {
                    "atom": step.atom.to_dict(),
                    "condition": step.condition,
                    "on_error": step.on_error,
                    "timeout": step.timeout,
                    "cache_key": step.cache_key
                }
                for step in self.steps
            ]
        }
    
    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    def to_dsl(self) -> str:
        lines = [f"@pipeline {self.name}:"]
        if self.description:
            lines.append(f'  # {self.description}')
        for var, val in self.variables.items():
            lines.append(f"  ${var} = {repr(val)}")
        
        dsl_steps = " | ".join(step.atom.to_dsl() for step in self.steps)
        lines.append(f"  {dsl_steps}")
        return "\n".join(lines)


class DSLTokenizer:
    """Tokenize DSL string into components"""
    
    PATTERNS = {
        'PIPE': r'\|',
        'DOT': r'\.',
        'LPAREN': r'\(',
        'RPAREN': r'\)',
        'LBRACE': r'\{',
        'RBRACE': r'\}',
        'LBRACKET': r'\[',
        'RBRACKET': r'\]',
        'COMMA': r',',
        'EQUALS': r'=',
        'COLON': r':',
        'AT': r'@',
        'DOLLAR': r'\$',
        'STRING': r'"[^"]*"|\'[^\']*\'',
        'NUMBER': r'-?\d+\.?\d*',
        'BOOL': r'\b(true|false|True|False)\b',
        'IDENTIFIER': r'[a-zA-Z_][a-zA-Z0-9_]*',
        'WHITESPACE': r'\s+',
        'NEWLINE': r'\n',
        'COMMENT': r'#[^\n]*',
    }
    
    def __init__(self):
        self.pattern = '|'.join(
            f'(?P<{name}>{pattern})' 
            for name, pattern in self.PATTERNS.items()
        )
        self.regex = re.compile(self.pattern)
    
    def tokenize(self, code: str) -> List[tuple]:
        tokens = []
        for match in self.regex.finditer(code):
            token_type = match.lastgroup
            token_value = match.group()
            
            if token_type in ('WHITESPACE', 'COMMENT'):
                continue
            
            # Clean string tokens
            if token_type == 'STRING':
                token_value = token_value[1:-1]
            elif token_type == 'NUMBER':
                token_value = float(token_value) if '.' in token_value else int(token_value)
            elif token_type == 'BOOL':
                token_value = token_value.lower() == 'true'
            
            tokens.append((token_type, token_value))
        
        return tokens


class DSLParser:
    """Parse tokenized DSL into pipeline definition"""
    
    def __init__(self):
        self.tokenizer = DSLTokenizer()
        self.tokens = []
        self.pos = 0
    
    def parse(self, code: str) -> PipelineDefinition:
        """Parse DSL code into pipeline definition"""
        self.tokens = self.tokenizer.tokenize(code)
        self.pos = 0
        
        name = "anonymous"
        variables = {}
        steps = []
        
        # Check for pipeline declaration
        if self._check('AT'):
            self._advance()
            if self._check('IDENTIFIER') and self._current()[1] == 'pipeline':
                self._advance()
                name = self._expect('IDENTIFIER')[1]
                self._expect('COLON')
        
        # Parse variables
        while self._check('DOLLAR'):
            var_name, var_value = self._parse_variable()
            variables[var_name] = var_value
        
        # Parse steps
        while not self._is_at_end():
            step = self._parse_step()
            if step:
                steps.append(step)
            
            # Handle pipe operator
            if self._check('PIPE'):
                self._advance()
        
        return PipelineDefinition(
            name=name,
            steps=steps,
            variables=variables
        )
    
    def _parse_variable(self) -> tuple:
        """Parse $variable = value"""
        self._expect('DOLLAR')
        name = self._expect('IDENTIFIER')[1]
        self._expect('EQUALS')
        value = self._parse_value()
        return name, value
    
    def _parse_step(self) -> Optional[PipelineStep]:
        """Parse single pipeline step: module.action(params)"""
        if not self._check('IDENTIFIER'):
            return None
        
        module = self._expect('IDENTIFIER')[1]
        self._expect('DOT')
        action = self._expect('IDENTIFIER')[1]
        
        params = {}
        if self._check('LPAREN'):
            params = self._parse_params()
        
        try:
            atom_type = AtomType(module)
        except ValueError:
            atom_type = AtomType.DATA  # Default
        
        return PipelineStep(
            atom=Atom(type=atom_type, action=action, params=params)
        )
    
    def _parse_params(self) -> Dict[str, Any]:
        """Parse function parameters"""
        params = {}
        self._expect('LPAREN')
        
        # Handle positional arguments and named arguments
        if not self._check('RPAREN'):
            arg_index = 0
            while not self._check('RPAREN') and not self._is_at_end():
                # Check if this is a named argument (IDENTIFIER followed by EQUALS)
                if self._check('IDENTIFIER'):
                    # Peek ahead to see if next token is EQUALS
                    saved_pos = self.pos
                    self._advance()
                    if self._check('EQUALS'):
                        # Named argument: rewind and parse normally
                        self.pos = saved_pos
                        name = self._expect('IDENTIFIER')[1]
                        self._expect('EQUALS')
                        value = self._parse_value()
                        params[name] = value
                    else:
                        # Positional identifier argument: rewind and parse as value
                        self.pos = saved_pos
                        value = self._parse_value()
                        params[f'_arg{arg_index}'] = value
                        arg_index += 1
                else:
                    # Positional argument (string, number, array, object, etc.)
                    value = self._parse_value()
                    params[f'_arg{arg_index}'] = value
                    arg_index += 1
                
                if self._check('COMMA'):
                    self._advance()
        
        self._expect('RPAREN')
        return params
    
    def _parse_value(self) -> Any:
        """Parse a value (string, number, bool, list, variable)"""
        if self._check('STRING'):
            return self._advance()[1]
        elif self._check('NUMBER'):
            return self._advance()[1]
        elif self._check('BOOL'):
            return self._advance()[1]
        elif self._check('DOLLAR'):
            self._advance()
            return f"${self._expect('IDENTIFIER')[1]}"
        elif self._check('LBRACE'):
            return self._parse_object()
        elif self._check('LBRACKET'):
            return self._parse_list()
        elif self._check('IDENTIFIER'):
            ident = self._advance()[1]
            if ident in ('null', 'None'):
                return None
            return ident
        else:
            raise SyntaxError(f"Unexpected token: {self._current()}")

    def _parse_object(self) -> Dict[str, Any]:
        """Parse {key: value, ...} (JSON-like object)"""
        obj: Dict[str, Any] = {}
        self._expect('LBRACE')

        while not self._check('RBRACE'):
            # Keys can be identifiers or strings
            if self._check('STRING'):
                key = self._advance()[1]
            else:
                key = self._expect('IDENTIFIER')[1]

            self._expect('COLON')
            obj[key] = self._parse_value()

            if self._check('COMMA'):
                self._advance()
            elif self._check('RBRACE'):
                break
            else:
                raise SyntaxError(f"Expected ',' or '}}', got {self._current()}")

        self._expect('RBRACE')
        return obj
    
    def _parse_list(self) -> List:
        """Parse [item, item, ...]"""
        items = []
        self._expect('LBRACKET')
        
        while not self._check('RBRACKET'):
            items.append(self._parse_value())
            if self._check('COMMA'):
                self._advance()
        
        self._expect('RBRACKET')
        return items
    
    def _current(self) -> tuple:
        if self._is_at_end():
            return ('EOF', None)
        return self.tokens[self.pos]
    
    def _check(self, token_type: str) -> bool:
        return not self._is_at_end() and self._current()[0] == token_type
    
    def _advance(self) -> tuple:
        token = self._current()
        self.pos += 1
        return token
    
    def _expect(self, token_type: str) -> tuple:
        if not self._check(token_type):
            raise SyntaxError(f"Expected {token_type}, got {self._current()}")
        return self._advance()
    
    def _is_at_end(self) -> bool:
        return self.pos >= len(self.tokens)


class AtomRegistry:
    """Registry of available atoms (operations)"""
    
    _atoms: Dict[str, Dict[str, Callable]] = {}
    
    @classmethod
    def register(cls, atom_type: str, action: str):
        """Decorator to register an atom implementation"""
        def decorator(func: Callable):
            if atom_type not in cls._atoms:
                cls._atoms[atom_type] = {}
            cls._atoms[atom_type][action] = func
            return func
        return decorator
    
    @classmethod
    def get(cls, atom_type: str, action: str) -> Optional[Callable]:
        return cls._atoms.get(atom_type, {}).get(action)
    
    @classmethod
    def list_atoms(cls) -> Dict[str, List[str]]:
        return {k: list(v.keys()) for k, v in cls._atoms.items()}


class PipelineContext:
    """Context passed through pipeline execution"""
    
    def __init__(self, 
                 variables: Dict[str, Any] = None,
                 domain: str = None,
                 user_id: str = None,
                 org_id: str = None):
        self.variables = variables or {}
        self.domain = domain
        self.user_id = user_id
        self.org_id = org_id
        self.data = None
        self.metadata = {}
        self.errors = []
        self.logs = []
    
    def resolve_variable(self, value: Any) -> Any:
        """Resolve $variable references"""
        if isinstance(value, str) and value.startswith('$'):
            var_name = value[1:]
            if var_name in self.variables:
                return self.variables[var_name]
            raise ValueError(f"Undefined variable: {value}")
        return value
    
    def resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve all variables in params"""
        return {k: self.resolve_variable(v) for k, v in params.items()}
    
    def log(self, message: str, level: str = "info"):
        self.logs.append({"level": level, "message": message})
    
    def set_data(self, data: Any):
        self.data = data
        return self
    
    def get_data(self) -> Any:
        return self.data


class PipelineExecutor:
    """Execute parsed pipelines"""
    
    def __init__(self, context: PipelineContext = None):
        self.context = context or PipelineContext()
        self.parser = DSLParser()
    
    def execute(self, pipeline: Union[str, PipelineDefinition]) -> PipelineContext:
        """Execute a pipeline"""
        if isinstance(pipeline, str):
            pipeline = self.parser.parse(pipeline)
        
        # Merge variables
        self.context.variables.update(pipeline.variables)
        
        # Execute each step
        for step in pipeline.steps:
            self._execute_step(step)
        
        return self.context
    
    def _execute_step(self, step: PipelineStep):
        """Execute a single step"""
        atom = step.atom
        handler = AtomRegistry.get(atom.type.value, atom.action)
        
        if not handler:
            raise ValueError(f"Unknown atom: {atom.type.value}.{atom.action}")
        
        # Resolve parameters
        params = self.context.resolve_params(atom.params)
        
        # Log execution
        self.context.log(f"Executing: {atom.to_dsl()}")
        
        try:
            # Execute handler
            result = handler(self.context, **params)
            if result is not None:
                self.context.set_data(result)
        except Exception as e:
            self.context.errors.append({
                "step": atom.to_dsl(),
                "error": str(e)
            })
            if step.on_error == "stop":
                raise
    
    async def execute_async(self, pipeline: Union[str, PipelineDefinition]) -> PipelineContext:
        """Async execution for I/O bound operations"""
        if isinstance(pipeline, str):
            pipeline = self.parser.parse(pipeline)
        
        self.context.variables.update(pipeline.variables)
        
        for step in pipeline.steps:
            await self._execute_step_async(step)
        
        return self.context
    
    async def _execute_step_async(self, step: PipelineStep):
        """Execute step asynchronously"""
        atom = step.atom
        handler = AtomRegistry.get(atom.type.value, atom.action)
        
        if not handler:
            raise ValueError(f"Unknown atom: {atom.type.value}.{atom.action}")
        
        params = self.context.resolve_params(atom.params)
        self.context.log(f"Executing async: {atom.to_dsl()}")
        
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(self.context, **params)
            else:
                result = handler(self.context, **params)
            
            if result is not None:
                self.context.set_data(result)
        except Exception as e:
            self.context.errors.append({
                "step": atom.to_dsl(),
                "error": str(e)
            })
            if step.on_error == "stop":
                raise


# ============================================================
# FLUENT PIPELINE BUILDER
# ============================================================

class PipelineBuilder:
    """Fluent API for building pipelines"""
    
    def __init__(self, domain: str = None):
        self.steps: List[PipelineStep] = []
        self.variables: Dict[str, Any] = {}
        self.domain = domain
        self._name = "pipeline"
    
    def name(self, name: str) -> "PipelineBuilder":
        self._name = name
        return self
    
    def var(self, name: str, value: Any) -> "PipelineBuilder":
        self.variables[name] = value
        return self
    
    def _add_step(self, atom_type: AtomType, action: str, **params) -> "PipelineBuilder":
        self.steps.append(PipelineStep(
            atom=Atom(type=atom_type, action=action, params=params)
        ))
        return self
    
    # Data operations
    @property
    def data(self) -> "_DataBuilder":
        return _DataBuilder(self)
    
    # Transform operations
    @property
    def transform(self) -> "_TransformBuilder":
        return _TransformBuilder(self)
    
    # Metrics operations
    @property
    def metrics(self) -> "_MetricsBuilder":
        return _MetricsBuilder(self)
    
    # Report operations
    @property
    def report(self) -> "_ReportBuilder":
        return _ReportBuilder(self)
    
    # Alert operations
    @property
    def alert(self) -> "_AlertBuilder":
        return _AlertBuilder(self)
    
    # Budget operations
    @property
    def budget(self) -> "_BudgetBuilder":
        return _BudgetBuilder(self)
    
    # Investment operations
    @property
    def investment(self) -> "_InvestmentBuilder":
        return _InvestmentBuilder(self)
    
    # Forecast operations
    @property
    def forecast(self) -> "_ForecastBuilder":
        return _ForecastBuilder(self)
    
    # Export operations
    @property
    def export(self) -> "_ExportBuilder":
        return _ExportBuilder(self)
    
    def build(self) -> PipelineDefinition:
        return PipelineDefinition(
            name=self._name,
            steps=self.steps,
            variables=self.variables,
            domain=self.domain
        )
    
    def to_dsl(self) -> str:
        return self.build().to_dsl()
    
    def to_dict(self) -> Dict:
        return self.build().to_dict()
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def execute(self, context: PipelineContext = None) -> PipelineContext:
        executor = PipelineExecutor(context or PipelineContext(domain=self.domain))
        return executor.execute(self.build())


class _AtomBuilder:
    """Base class for atom builders"""
    
    def __init__(self, pipeline: PipelineBuilder, atom_type: AtomType):
        self.pipeline = pipeline
        self.atom_type = atom_type
    
    def _add(self, action: str, **params) -> PipelineBuilder:
        return self.pipeline._add_step(self.atom_type, action, **params)


class _DataBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.DATA)
    
    def load(self, source: str, **params) -> PipelineBuilder:
        return self._add("load", source=source, **params)
    
    def query(self, sql: str, **params) -> PipelineBuilder:
        return self._add("query", sql=sql, **params)
    
    def fetch(self, url: str, **params) -> PipelineBuilder:
        return self._add("fetch", url=url, **params)
    
    def from_input(self, data: Any = None) -> PipelineBuilder:
        return self._add("from_input", data=data)


class _TransformBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.TRANSFORM)
    
    def filter(self, **conditions) -> PipelineBuilder:
        return self._add("filter", **conditions)
    
    def map(self, func: str, field: str = None) -> PipelineBuilder:
        return self._add("map", func=func, field=field)
    
    def sort(self, by: str, order: str = "asc") -> PipelineBuilder:
        return self._add("sort", by=by, order=order)
    
    def limit(self, n: int) -> PipelineBuilder:
        return self._add("limit", n=n)
    
    def group_by(self, *fields) -> PipelineBuilder:
        return self._add("group_by", fields=list(fields))
    
    def aggregate(self, by: str, func: str = "sum") -> PipelineBuilder:
        return self._add("aggregate", by=by, func=func)
    
    def rename(self, **mapping) -> PipelineBuilder:
        return self._add("rename", **mapping)
    
    def select(self, *fields) -> PipelineBuilder:
        return self._add("select", fields=list(fields))


class _MetricsBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.METRICS)
    
    def calculate(self, metrics: List[str], field: str = None) -> PipelineBuilder:
        return self._add("calculate", metrics=metrics, field=field)
    
    def sum(self, field: str) -> PipelineBuilder:
        return self._add("sum", field=field)
    
    def avg(self, field: str) -> PipelineBuilder:
        return self._add("avg", field=field)
    
    def count(self) -> PipelineBuilder:
        return self._add("count")
    
    def variance(self, field: str) -> PipelineBuilder:
        return self._add("variance", field=field)
    
    def percentile(self, field: str, p: int = 50) -> PipelineBuilder:
        return self._add("percentile", field=field, p=p)


class _ReportBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.REPORT)
    
    def generate(self, format: str = "pdf", template: str = None) -> PipelineBuilder:
        return self._add("generate", format=format, template=template)
    
    def schedule(self, cron: str, recipients: List[str] = None) -> PipelineBuilder:
        return self._add("schedule", cron=cron, recipients=recipients)
    
    def send(self, to: List[str], **params) -> PipelineBuilder:
        return self._add("send", to=to, **params)


class _AlertBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.ALERT)
    
    def when(self, condition: str) -> PipelineBuilder:
        return self._add("when", condition=condition)
    
    def send(self, channel: str, message: str = None) -> PipelineBuilder:
        return self._add("send", channel=channel, message=message)
    
    def threshold(self, field: str, operator: str, value: float) -> PipelineBuilder:
        return self._add("threshold", field=field, operator=operator, value=value)


class _BudgetBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.BUDGET)
    
    def create(self, name: str, **params) -> PipelineBuilder:
        return self._add("create", name=name, **params)
    
    def load(self, budget_id: str) -> PipelineBuilder:
        return self._add("load", budget_id=budget_id)
    
    def compare(self, scenario: str = "actual") -> PipelineBuilder:
        return self._add("compare", scenario=scenario)
    
    def variance(self) -> PipelineBuilder:
        return self._add("variance")
    
    def categorize(self, by: str) -> PipelineBuilder:
        return self._add("categorize", by=by)


class _InvestmentBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.INVESTMENT)
    
    def analyze(self, **params) -> PipelineBuilder:
        return self._add("analyze", **params)
    
    def roi(self) -> PipelineBuilder:
        return self._add("roi")
    
    def npv(self, rate: float = 0.1) -> PipelineBuilder:
        return self._add("npv", rate=rate)
    
    def irr(self) -> PipelineBuilder:
        return self._add("irr")
    
    def payback(self) -> PipelineBuilder:
        return self._add("payback")
    
    def scenario(self, name: str, multiplier: float = 1.0) -> PipelineBuilder:
        return self._add("scenario", name=name, multiplier=multiplier)


class _ForecastBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.FORECAST)
    
    def predict(self, periods: int = 30, model: str = "prophet") -> PipelineBuilder:
        return self._add("predict", periods=periods, model=model)
    
    def trend(self) -> PipelineBuilder:
        return self._add("trend")
    
    def seasonality(self) -> PipelineBuilder:
        return self._add("seasonality")
    
    def confidence(self, level: float = 0.95) -> PipelineBuilder:
        return self._add("confidence", level=level)


class _ExportBuilder(_AtomBuilder):
    def __init__(self, pipeline: PipelineBuilder):
        super().__init__(pipeline, AtomType.EXPORT)
    
    def to_csv(self, path: str = None) -> PipelineBuilder:
        return self._add("to_csv", path=path)
    
    def to_json(self, path: str = None) -> PipelineBuilder:
        return self._add("to_json", path=path)
    
    def to_excel(self, path: str = None) -> PipelineBuilder:
        return self._add("to_excel", path=path)
    
    def to_api(self, url: str, method: str = "POST") -> PipelineBuilder:
        return self._add("to_api", url=url, method=method)


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def Pipeline(dsl_or_domain: str = None, domain: str = None) -> Union[PipelineBuilder, PipelineDefinition]:
    """Create a pipeline from DSL code or return builder.
    
    Usage:
        Pipeline()                          -> PipelineBuilder
        Pipeline("repox.pl")                -> PipelineBuilder with domain
        Pipeline(domain="repox.pl")         -> PipelineBuilder with domain
        Pipeline('data.load("x") | ...')    -> PipelineDefinition (parsed)
    """
    if dsl_or_domain:
        # Heuristic: if it looks like DSL code (has function calls), parse it
        # Otherwise treat it as a domain name
        is_dsl = '(' in dsl_or_domain or '|' in dsl_or_domain or '@pipeline' in dsl_or_domain
        if is_dsl:
            parser = DSLParser()
            return parser.parse(dsl_or_domain)
        else:
            # Treat as domain name
            return PipelineBuilder(domain=dsl_or_domain)
    return PipelineBuilder(domain=domain)


def execute(pipeline: Union[str, PipelineDefinition, PipelineBuilder], 
            context: PipelineContext = None) -> PipelineContext:
    """Execute a pipeline"""
    if isinstance(pipeline, PipelineBuilder):
        pipeline = pipeline.build()
    
    executor = PipelineExecutor(context)
    return executor.execute(pipeline)


def parse(dsl_code: str) -> PipelineDefinition:
    """Parse DSL code to pipeline definition"""
    return DSLParser().parse(dsl_code)


# Export public API
__all__ = [
    'Pipeline', 'PipelineBuilder', 'PipelineDefinition', 'PipelineContext',
    'PipelineExecutor', 'Atom', 'AtomType', 'AtomRegistry',
    'execute', 'parse', 'DSLParser', 'DSLTokenizer'
]
