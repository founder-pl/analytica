"""
ANALYTICA DSL - Atom Registry
==============================
Central registry for all DSL atom implementations.

Provides:
- Decorator-based atom registration
- Atom lookup and listing
- Parameter validation system
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps


# ============================================================
# PARAMETER TYPES FOR VALIDATION
# ============================================================

class ParamType(Enum):
    """Parameter type for validation"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ANY = "any"


@dataclass
class Required:
    """Mark a parameter as required"""
    type: Union[type, ParamType] = ParamType.ANY
    description: str = ""
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        if self.type == ParamType.ANY:
            return True
        if isinstance(self.type, type):
            return isinstance(value, self.type)
        type_map = {
            ParamType.STRING: str,
            ParamType.NUMBER: (int, float),
            ParamType.BOOLEAN: bool,
            ParamType.ARRAY: (list, tuple),
            ParamType.OBJECT: dict,
        }
        return isinstance(value, type_map.get(self.type, object))


@dataclass
class Optional_:
    """Mark a parameter as optional with default value"""
    type: Union[type, ParamType] = ParamType.ANY
    default: Any = None
    description: str = ""
    
    def validate(self, value: Any) -> bool:
        if value is None:
            return True  # Optional can be None
        if self.type == ParamType.ANY:
            return True
        if isinstance(self.type, type):
            return isinstance(value, self.type)
        type_map = {
            ParamType.STRING: str,
            ParamType.NUMBER: (int, float),
            ParamType.BOOLEAN: bool,
            ParamType.ARRAY: (list, tuple),
            ParamType.OBJECT: dict,
        }
        return isinstance(value, type_map.get(self.type, object))


@dataclass
class OneOf:
    """Parameter must be one of the given values"""
    values: List[Any]
    description: str = ""
    
    def validate(self, value: Any) -> bool:
        return value in self.values


@dataclass 
class AtomInfo:
    """Metadata about a registered atom"""
    type: str
    action: str
    handler: Callable
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    examples: List[str] = field(default_factory=list)
    returns: str = ""
    category: str = ""


# ============================================================
# ATOM REGISTRY
# ============================================================

class AtomRegistry:
    """
    Registry of available atoms (operations).
    
    Usage:
        @AtomRegistry.register("data", "load")
        def data_load(ctx, source, **params):
            ...
        
        # With parameter validation
        @AtomRegistry.register("data", "load")
        @atom_params(source=Required(str), format=Optional_(str, default="auto"))
        def data_load(ctx, source: str, format: str = "auto"):
            ...
    """
    
    _atoms: Dict[str, Dict[str, AtomInfo]] = {}
    _handlers: Dict[str, Dict[str, Callable]] = {}
    
    @classmethod
    def register(cls, atom_type: str, action: str, **metadata):
        """
        Decorator to register an atom implementation.
        
        Args:
            atom_type: Category (data, transform, view, etc.)
            action: Action name (load, filter, chart, etc.)
            **metadata: Optional metadata (description, examples, etc.)
        """
        def decorator(func: Callable):
            if atom_type not in cls._atoms:
                cls._atoms[atom_type] = {}
                cls._handlers[atom_type] = {}
            
            # Create atom info
            info = AtomInfo(
                type=atom_type,
                action=action,
                handler=func,
                description=metadata.get("description", func.__doc__ or ""),
                examples=metadata.get("examples", []),
                returns=metadata.get("returns", ""),
                category=metadata.get("category", ""),
            )
            
            # Extract param info from function
            if hasattr(func, '_atom_params'):
                info.params = func._atom_params
            
            cls._atoms[atom_type][action] = info
            cls._handlers[atom_type][action] = func
            return func
        return decorator
    
    @classmethod
    def get(cls, atom_type: str, action: str) -> Optional[Callable]:
        """Get atom handler by type and action"""
        return cls._handlers.get(atom_type, {}).get(action)
    
    @classmethod
    def get_info(cls, atom_type: str, action: str) -> Optional[AtomInfo]:
        """Get atom info by type and action"""
        return cls._atoms.get(atom_type, {}).get(action)
    
    @classmethod
    def list_atoms(cls) -> Dict[str, List[str]]:
        """List all registered atoms grouped by type"""
        return {k: list(v.keys()) for k, v in cls._handlers.items()}
    
    @classmethod
    def list_all(cls) -> List[AtomInfo]:
        """List all atom info objects"""
        result = []
        for type_atoms in cls._atoms.values():
            result.extend(type_atoms.values())
        return result
    
    @classmethod
    def get_docs(cls, atom_type: str = None) -> Dict[str, Any]:
        """Generate documentation for atoms"""
        docs = {}
        atoms = cls._atoms
        
        if atom_type:
            atoms = {atom_type: cls._atoms.get(atom_type, {})}
        
        for atype, actions in atoms.items():
            docs[atype] = {}
            for action, info in actions.items():
                docs[atype][action] = {
                    "description": info.description,
                    "params": {k: _param_to_dict(v) for k, v in info.params.items()},
                    "examples": info.examples,
                    "returns": info.returns,
                }
        return docs
    
    @classmethod
    def clear(cls):
        """Clear all registered atoms (for testing)"""
        cls._atoms.clear()
        cls._handlers.clear()


def _param_to_dict(param) -> Dict:
    """Convert param spec to dict for documentation"""
    if isinstance(param, Required):
        return {
            "required": True,
            "type": param.type.value if isinstance(param.type, ParamType) else param.type.__name__,
            "description": param.description,
        }
    elif isinstance(param, Optional_):
        return {
            "required": False,
            "type": param.type.value if isinstance(param.type, ParamType) else param.type.__name__,
            "default": param.default,
            "description": param.description,
        }
    elif isinstance(param, OneOf):
        return {
            "required": True,
            "type": "enum",
            "values": param.values,
            "description": param.description,
        }
    return {"type": "any"}


# ============================================================
# PARAMETER VALIDATION DECORATOR
# ============================================================

def atom_params(**param_specs):
    """
    Decorator to define and validate atom parameters.
    
    Usage:
        @AtomRegistry.register("data", "load")
        @atom_params(
            source=Required(str, description="Data source path or URL"),
            format=Optional_(str, default="auto", description="Data format"),
            encoding=Optional_(str, default="utf-8")
        )
        def data_load(ctx, source: str, format: str = "auto", encoding: str = "utf-8"):
            ...
    """
    def decorator(func: Callable):
        # Store param specs on function
        func._atom_params = param_specs
        
        @wraps(func)
        def wrapper(ctx, **kwargs):
            # Map _arg0, _arg1, etc. to named params
            positional_params = sorted(
                [k for k in kwargs if k.startswith('_arg')],
                key=lambda x: int(x[4:])
            )
            required_params = [k for k, v in param_specs.items() if isinstance(v, Required)]
            
            # Map positional args to required params
            for i, arg_key in enumerate(positional_params):
                if i < len(required_params):
                    param_name = required_params[i]
                    if param_name not in kwargs or kwargs.get(param_name) is None:
                        kwargs[param_name] = kwargs.pop(arg_key)
                    else:
                        kwargs.pop(arg_key, None)
            
            # Apply defaults for optional params
            for name, spec in param_specs.items():
                if isinstance(spec, Optional_) and name not in kwargs:
                    kwargs[name] = spec.default
            
            # Validate required params
            errors = []
            for name, spec in param_specs.items():
                value = kwargs.get(name)
                if isinstance(spec, Required) and not spec.validate(value):
                    errors.append(f"Required parameter '{name}' is missing or invalid")
                elif isinstance(spec, OneOf) and not spec.validate(value):
                    errors.append(f"Parameter '{name}' must be one of {spec.values}")
            
            if errors:
                raise ValueError("; ".join(errors))
            
            # Remove any remaining _argN keys
            kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_arg')}
            
            return func(ctx, **kwargs)
        
        return wrapper
    return decorator
