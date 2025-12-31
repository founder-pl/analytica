"""
ANALYTICA Modules
=================
Reusable business modules for domain-specific functionality.

Available modules:
- budget: Budget management and variance analysis
- investment: ROI, NPV, IRR calculations
- forecast: Time series forecasting
- reports: Report generation and scheduling
- alerts: Threshold monitoring and notifications
- voice: Voice input processing
"""

from typing import Dict, List, Any, Protocol, runtime_checkable
from abc import ABC, abstractmethod


@runtime_checkable
class Module(Protocol):
    """Protocol for ANALYTICA modules"""
    
    name: str
    version: str
    
    def get_routes(self) -> List[Any]:
        """Return FastAPI routes for this module"""
        ...
    
    def get_atoms(self) -> Dict[str, Any]:
        """Return DSL atoms provided by this module"""
        ...


class BaseModule(ABC):
    """Base class for ANALYTICA modules"""
    
    name: str = "base"
    version: str = "1.0.0"
    
    @abstractmethod
    def get_routes(self) -> List[Any]:
        """Return FastAPI routes for this module"""
        pass
    
    @abstractmethod
    def get_atoms(self) -> Dict[str, Any]:
        """Return DSL atoms provided by this module"""
        pass
    
    def __repr__(self) -> str:
        return f"<Module {self.name} v{self.version}>"


# Module registry
_modules: Dict[str, BaseModule] = {}


def register_module(module: BaseModule) -> None:
    """Register a module"""
    _modules[module.name] = module


def get_module(name: str) -> BaseModule:
    """Get a registered module by name"""
    if name not in _modules:
        raise KeyError(f"Module not found: {name}")
    return _modules[name]


def list_modules() -> List[str]:
    """List all registered module names"""
    return list(_modules.keys())


__all__ = [
    "Module",
    "BaseModule", 
    "register_module",
    "get_module",
    "list_modules",
]
