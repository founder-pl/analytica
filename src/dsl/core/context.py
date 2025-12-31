"""
ANALYTICA DSL - Pipeline Context
=================================
Execution context for DSL pipelines.

Provides:
- Variable resolution
- Data flow management
- Logging and error tracking
- Metadata storage
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

import re


@dataclass
class PipelineContext:
    """
    Context passed through pipeline execution.
    
    Holds:
    - Current data being processed
    - Variables for substitution
    - Domain/user/org context
    - Execution logs and errors
    - Metadata for tracking
    """
    
    variables: Dict[str, Any] = field(default_factory=dict)
    domain: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    
    # Internal state
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution tracking
    started_at: Optional[datetime] = None
    step_count: int = 0
    
    def __post_init__(self):
        self.started_at = datetime.utcnow()
    
    def resolve_variable(self, value: Any) -> Any:
        """
        Resolve $variable references.
        
        Args:
            value: Value that may contain variable reference
            
        Returns:
            Resolved value or original if not a variable
            
        Raises:
            ValueError: If variable is undefined
        """
        if not isinstance(value, str):
            return value

        # Exact variable reference: $VAR or ${VAR}
        if value.startswith('${') and value.endswith('}') and len(value) > 3:
            var_name = value[2:-1]
            if var_name in self.variables:
                return self.variables[var_name]
            raise ValueError(f"Undefined variable: {value}")

        if value.startswith('$') and len(value) > 1 and value[1:].isidentifier():
            var_name = value[1:]
            if var_name in self.variables:
                return self.variables[var_name]
            raise ValueError(f"Undefined variable: {value}")

        # Interpolation inside string
        pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")

        def repl(m: re.Match) -> str:
            token = m.group(0)
            var_name = m.group(1) or m.group(2)
            if var_name in self.variables:
                return str(self.variables[var_name])
            raise ValueError(f"Undefined variable: {token}")

        if '$' in value and pattern.search(value):
            return pattern.sub(repl, value)

        return value
    
    def resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve all variables in params dict.
        
        Args:
            params: Dict with potential variable references
            
        Returns:
            Dict with all variables resolved
        """
        def resolve_any(v: Any) -> Any:
            if isinstance(v, dict):
                return self.resolve_params(v)
            if isinstance(v, list):
                return [resolve_any(item) for item in v]
            return self.resolve_variable(v)

        resolved: Dict[str, Any] = {}
        for k, v in params.items():
            resolved[k] = resolve_any(v)
        return resolved
    
    def log(self, message: str, level: str = "info"):
        """
        Add a log entry.
        
        Args:
            message: Log message
            level: Log level (debug, info, warn, error)
        """
        self.logs.append({
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "step": self.step_count
        })
    
    def error(self, message: str, exception: Exception = None, step: str = None):
        """
        Record an error.
        
        Args:
            message: Error message
            exception: Optional exception object
            step: Optional step identifier
        """
        self.errors.append({
            "message": message,
            "type": type(exception).__name__ if exception else "Error",
            "step": step or f"step_{self.step_count}",
            "timestamp": datetime.utcnow().isoformat()
        })
        self.log(f"ERROR: {message}", level="error")
    
    def set_data(self, data: Any) -> "PipelineContext":
        """
        Set the current data.
        
        Args:
            data: Data to set
            
        Returns:
            Self for chaining
        """
        self.data = data
        return self
    
    def get_data(self) -> Any:
        """Get current data."""
        return self.data
    
    def set_var(self, name: str, value: Any) -> "PipelineContext":
        """
        Set a variable.
        
        Args:
            name: Variable name
            value: Variable value
            
        Returns:
            Self for chaining
        """
        self.variables[name] = value
        return self
    
    def get_var(self, name: str, default: Any = None) -> Any:
        """
        Get a variable value.
        
        Args:
            name: Variable name
            default: Default value if not found
            
        Returns:
            Variable value or default
        """
        return self.variables.get(name, default)
    
    def set_metadata(self, key: str, value: Any) -> "PipelineContext":
        """Set metadata value."""
        self.metadata[key] = value
        return self
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    def increment_step(self):
        """Increment step counter."""
        self.step_count += 1
    
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.errors) > 0
    
    def execution_time_ms(self) -> float:
        """Get execution time in milliseconds."""
        if self.started_at:
            delta = datetime.utcnow() - self.started_at
            return delta.total_seconds() * 1000
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context state to dict."""
        return {
            "domain": self.domain,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "variables": self.variables,
            "metadata": self.metadata,
            "step_count": self.step_count,
            "execution_time_ms": self.execution_time_ms(),
            "has_errors": self.has_errors(),
            "error_count": len(self.errors),
            "log_count": len(self.logs)
        }
    
    def clone(self) -> "PipelineContext":
        """Create a copy of the context."""
        return PipelineContext(
            variables=dict(self.variables),
            domain=self.domain,
            user_id=self.user_id,
            org_id=self.org_id,
            data=self.data,
            metadata=dict(self.metadata)
        )


# Alias for backwards compatibility
DSLPipelineContext = PipelineContext
