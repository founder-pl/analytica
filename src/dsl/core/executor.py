"""
ANALYTICA DSL - Pipeline Executor
==================================
Execute parsed DSL pipelines.

Provides:
- Synchronous execution
- Async execution for I/O operations
- Step-by-step execution with error handling
- Execution hooks and middleware
"""

from typing import Any, Callable, Dict, List, Optional, Union
import asyncio
from datetime import datetime

from .context import PipelineContext
from .registry import AtomRegistry


class ExecutionHook:
    """Base class for execution hooks"""
    
    def before_pipeline(self, pipeline: "PipelineDefinition", ctx: PipelineContext):
        """Called before pipeline execution starts"""
        pass
    
    def after_pipeline(self, pipeline: "PipelineDefinition", ctx: PipelineContext):
        """Called after pipeline execution completes"""
        pass
    
    def before_step(self, step: "PipelineStep", ctx: PipelineContext):
        """Called before each step"""
        pass
    
    def after_step(self, step: "PipelineStep", ctx: PipelineContext, result: Any):
        """Called after each step"""
        pass
    
    def on_error(self, step: "PipelineStep", ctx: PipelineContext, error: Exception):
        """Called when a step raises an error"""
        pass


class LoggingHook(ExecutionHook):
    """Hook that logs execution details"""
    
    def before_pipeline(self, pipeline, ctx: PipelineContext):
        ctx.log(f"Starting pipeline: {pipeline.name}")
    
    def after_pipeline(self, pipeline, ctx: PipelineContext):
        ctx.log(f"Pipeline completed in {ctx.execution_time_ms():.2f}ms")
    
    def before_step(self, step, ctx: PipelineContext):
        ctx.log(f"Executing: {step.atom.to_dsl()}")
    
    def on_error(self, step, ctx: PipelineContext, error: Exception):
        ctx.log(f"Error in {step.atom.to_dsl()}: {error}", level="error")


class PipelineExecutor:
    """
    Execute parsed pipelines.
    
    Usage:
        executor = PipelineExecutor()
        result = executor.execute("data.load('file.csv') | transform.filter(x>0)")
        
        # With context
        ctx = PipelineContext(variables={"threshold": 100})
        result = executor.execute(pipeline, ctx)
        
        # Async execution
        result = await executor.execute_async(pipeline)
    """
    
    def __init__(self, 
                 context: PipelineContext = None,
                 hooks: List[ExecutionHook] = None):
        self.context = context or PipelineContext()
        self.hooks = hooks or [LoggingHook()]
        self._parser = None
    
    @property
    def parser(self):
        """Lazy-load parser to avoid circular imports"""
        if self._parser is None:
            from .parser import DSLParser
            self._parser = DSLParser()
        return self._parser
    
    def execute(self, pipeline: Union[str, "PipelineDefinition"], 
                context: PipelineContext = None) -> PipelineContext:
        """
        Execute a pipeline synchronously.
        
        Args:
            pipeline: DSL string or parsed PipelineDefinition
            context: Optional execution context
            
        Returns:
            PipelineContext with results
        """
        from .parser import PipelineDefinition
        
        ctx = context or self.context
        
        # Parse if string
        if isinstance(pipeline, str):
            pipeline = self.parser.parse(pipeline)
        
        # Merge variables
        ctx.variables.update(pipeline.variables)
        
        # Before pipeline hooks
        for hook in self.hooks:
            hook.before_pipeline(pipeline, ctx)
        
        try:
            # Execute each step
            for step in pipeline.steps:
                self._execute_step(step, ctx)
        finally:
            # After pipeline hooks
            for hook in self.hooks:
                hook.after_pipeline(pipeline, ctx)
        
        return ctx
    
    def _execute_step(self, step: "PipelineStep", ctx: PipelineContext):
        """Execute a single step"""
        from .parser import PipelineStep
        
        ctx.increment_step()
        
        atom = step.atom
        handler = AtomRegistry.get(atom.type.value, atom.action)
        
        if not handler:
            raise ValueError(f"Unknown atom: {atom.type.value}.{atom.action}")
        
        # Before step hooks
        for hook in self.hooks:
            hook.before_step(step, ctx)
        
        # Resolve parameters
        params = ctx.resolve_params(atom.params)
        
        try:
            # Execute handler
            result = handler(ctx, **params)
            if result is not None:
                ctx.set_data(result)
            
            # After step hooks
            for hook in self.hooks:
                hook.after_step(step, ctx, result)
                
        except Exception as e:
            # Error hooks
            for hook in self.hooks:
                hook.on_error(step, ctx, e)
            
            ctx.error(str(e), exception=e, step=atom.to_dsl())
            
            if step.on_error == "stop":
                raise
            elif step.on_error == "retry":
                # Simple retry logic
                try:
                    result = handler(ctx, **params)
                    if result is not None:
                        ctx.set_data(result)
                except Exception:
                    if step.on_error != "skip":
                        raise
    
    async def execute_async(self, pipeline: Union[str, "PipelineDefinition"],
                           context: PipelineContext = None) -> PipelineContext:
        """
        Execute a pipeline asynchronously.
        
        Args:
            pipeline: DSL string or parsed PipelineDefinition
            context: Optional execution context
            
        Returns:
            PipelineContext with results
        """
        from .parser import PipelineDefinition
        
        ctx = context or self.context
        
        if isinstance(pipeline, str):
            pipeline = self.parser.parse(pipeline)
        
        ctx.variables.update(pipeline.variables)
        
        for hook in self.hooks:
            hook.before_pipeline(pipeline, ctx)
        
        try:
            for step in pipeline.steps:
                await self._execute_step_async(step, ctx)
        finally:
            for hook in self.hooks:
                hook.after_pipeline(pipeline, ctx)
        
        return ctx
    
    async def _execute_step_async(self, step: "PipelineStep", ctx: PipelineContext):
        """Execute step asynchronously"""
        ctx.increment_step()
        
        atom = step.atom
        handler = AtomRegistry.get(atom.type.value, atom.action)
        
        if not handler:
            raise ValueError(f"Unknown atom: {atom.type.value}.{atom.action}")
        
        for hook in self.hooks:
            hook.before_step(step, ctx)
        
        params = ctx.resolve_params(atom.params)
        
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(ctx, **params)
            else:
                result = handler(ctx, **params)
            
            if result is not None:
                ctx.set_data(result)
            
            for hook in self.hooks:
                hook.after_step(step, ctx, result)
                
        except Exception as e:
            for hook in self.hooks:
                hook.on_error(step, ctx, e)
            
            ctx.error(str(e), exception=e, step=atom.to_dsl())
            
            if step.on_error == "stop":
                raise


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def execute(dsl: str, 
            variables: Dict[str, Any] = None,
            data: Any = None,
            domain: str = None) -> PipelineContext:
    """
    Execute a DSL pipeline.
    
    Args:
        dsl: DSL string to execute
        variables: Optional variables dict
        data: Optional input data
        domain: Optional domain context
        
    Returns:
        PipelineContext with results
    """
    ctx = PipelineContext(
        variables=variables or {},
        domain=domain
    )
    if data is not None:
        ctx.set_data(data)
    
    executor = PipelineExecutor(context=ctx)
    return executor.execute(dsl)


async def execute_async(dsl: str,
                       variables: Dict[str, Any] = None,
                       data: Any = None,
                       domain: str = None) -> PipelineContext:
    """Execute a DSL pipeline asynchronously."""
    ctx = PipelineContext(
        variables=variables or {},
        domain=domain
    )
    if data is not None:
        ctx.set_data(data)
    
    executor = PipelineExecutor(context=ctx)
    return await executor.execute_async(dsl)


# Alias for backwards compatibility
dsl_execute = execute
