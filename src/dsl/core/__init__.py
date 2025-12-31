"""
ANALYTICA DSL Core
==================
Core DSL parsing, execution, and registry components.
"""

from .registry import (
    AtomRegistry,
    AtomInfo,
    Required,
    Optional_ as Optional,
    OneOf,
    ParamType,
    atom_params,
)

from .context import (
    PipelineContext,
    DSLPipelineContext,
)

from .executor import (
    PipelineExecutor,
    ExecutionHook,
    LoggingHook,
    execute,
    execute_async,
    dsl_execute,
)

from .parser import (
    AtomType,
    Atom,
    PipelineStep,
    PipelineDefinition,
    DSLTokenizer,
    DSLParser,
    PipelineBuilder,
    dsl_parse,
)

__all__ = [
    # Registry
    "AtomRegistry",
    "AtomInfo", 
    "Required",
    "Optional",
    "OneOf",
    "ParamType",
    "atom_params",
    # Context
    "PipelineContext",
    "DSLPipelineContext",
    # Executor
    "PipelineExecutor",
    "ExecutionHook",
    "LoggingHook",
    "execute",
    "execute_async",
    "dsl_execute",
    # Parser
    "AtomType",
    "Atom",
    "PipelineStep",
    "PipelineDefinition",
    "DSLTokenizer",
    "DSLParser",
    "PipelineBuilder",
    "dsl_parse",
]