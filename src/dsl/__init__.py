"""
ANALYTICA DSL - Domain Specific Language for Analytics Pipelines
================================================================

A powerful, expressive DSL for building analytics pipelines that can be
executed locally or via REST API.

Quick Start:
------------
    from analytica.dsl import Pipeline, execute, parse
    
    # Fluent API
    result = (Pipeline()
        .data.load('sales.csv')
        .transform.filter(year=2024)
        .metrics.sum('amount')
        .execute())
    
    # DSL String
    result = execute('data.load("sales") | metrics.sum("amount")')

DSL Syntax:
-----------
    # Pipe syntax
    data.load("file") | transform.filter(x=1) | metrics.sum("field")
    
    # Variables
    $year = 2024
    data.load("sales") | transform.filter(year=$year)
    
    # Named pipeline
    @pipeline my_pipeline:
        data.load("data") | metrics.calculate(["sum", "avg"])

Available Atoms:
----------------
    data        - Load and fetch data
    transform   - Filter, sort, group, aggregate
    metrics     - Calculate statistics
    report      - Generate and send reports
    alert       - Define alerts and notifications
    budget      - Budget operations (planbudzetu.pl)
    investment  - Investment analysis (planinwestycji.pl)
    forecast    - ML predictions (estymacja.pl)
    export      - Export to various formats
"""

from .core.parser import (
    # Core classes
    Pipeline,
    PipelineBuilder,
    PipelineDefinition,
    PipelineContext,
    PipelineExecutor,
    
    # Atom classes
    Atom,
    AtomType,
    AtomRegistry,
    
    # Parser
    DSLParser,
    DSLTokenizer,
    
    # Functions
    parse,
    execute
)

# Import atom implementations to register them
from .atoms import implementations as _atoms

__version__ = "2.0.0"
__author__ = "Softreck"

__all__ = [
    # Core
    'Pipeline',
    'PipelineBuilder', 
    'PipelineDefinition',
    'PipelineContext',
    'PipelineExecutor',
    
    # Atoms
    'Atom',
    'AtomType',
    'AtomRegistry',
    
    # Parser
    'DSLParser',
    'DSLTokenizer',
    
    # Functions
    'parse',
    'execute',
    
    # Version
    '__version__'
]
