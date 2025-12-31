"""
ANALYTICA Framework - Domain Router & Configuration Manager
Handles multi-domain routing, module access control, and port mapping
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml
import os


class ModuleAccess(Enum):
    FULL = "full"
    BASIC = "basic"
    LIMITED = "limited"
    DISABLED = "disabled"


class DomainType(Enum):
    HUB = "hub"
    SPECIALIZED = "specialized"
    WHITE_LABEL = "white_label"
    GENERAL = "general"


@dataclass
class PortConfig:
    frontend: int
    api: int


@dataclass
class ThemeConfig:
    primary: str
    accent: str
    secondary: str = "#1F2937"
    mode: str = "light"
    logo: str = ""
    gradient: str = ""


@dataclass
class DomainConfig:
    domain: str
    type: DomainType
    display_name: str
    tagline: str
    ports: PortConfig
    modules: Dict[str, Any]
    theme: ThemeConfig
    features: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    pricing_plans: List[str] = field(default_factory=list)
    seo: Dict[str, Any] = field(default_factory=dict)


# Domain registry with all configurations
DOMAIN_REGISTRY: Dict[str, DomainConfig] = {}


def load_domain_config(yaml_path: Path) -> Optional[DomainConfig]:
    """Load domain configuration from YAML file"""
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        
        ports_data = data.get("ports", {})
        ports = PortConfig(
            frontend=ports_data.get("frontend", 3000),
            api=ports_data.get("api", 8000)
        )
        
        theme_data = data.get("theme", {})
        theme = ThemeConfig(
            primary=theme_data.get("primary", "#6366F1"),
            accent=theme_data.get("accent", "#8B5CF6"),
            secondary=theme_data.get("secondary", "#1F2937"),
            mode=theme_data.get("mode", "light"),
            logo=theme_data.get("logo", ""),
            gradient=theme_data.get("gradient", "")
        )
        
        return DomainConfig(
            domain=data["domain"],
            type=DomainType(data.get("type", "general")),
            display_name=data.get("display_name", data["domain"]),
            tagline=data.get("tagline", ""),
            ports=ports,
            modules=data.get("modules", {}),
            theme=theme,
            features=data.get("features", []),
            integrations=data.get("integrations", {}).get("priority", []),
            pricing_plans=data.get("pricing", {}).get("plans", ["free"]),
            seo=data.get("seo", {})
        )
    except Exception as e:
        print(f"Error loading {yaml_path}: {e}")
        return None


def init_domain_registry(config_dir: str = "config/domains"):
    """Initialize domain registry from YAML files"""
    global DOMAIN_REGISTRY
    config_path = Path(config_dir)
    
    if not config_path.exists():
        print(f"Config directory not found: {config_dir}")
        return
    
    for yaml_file in config_path.glob("*.yaml"):
        config = load_domain_config(yaml_file)
        if config:
            DOMAIN_REGISTRY[config.domain] = config
            # Also register without .pl
            domain_key = config.domain.replace(".pl", "")
            DOMAIN_REGISTRY[domain_key] = config


def get_domain_config(domain: str) -> Optional[DomainConfig]:
    """Get domain configuration by name"""
    domain = domain.lower().strip()
    if not domain.endswith(".pl"):
        domain_key = domain
    else:
        domain_key = domain
    
    return DOMAIN_REGISTRY.get(domain_key) or DOMAIN_REGISTRY.get(domain_key.replace(".pl", ""))


def get_domain_by_port(port: int) -> Optional[DomainConfig]:
    """Get domain configuration by port number"""
    for config in DOMAIN_REGISTRY.values():
        if config.ports.api == port or config.ports.frontend == port:
            return config
    return None


def check_module_access(domain: str, module: str) -> ModuleAccess:
    """Check module access level for a domain"""
    config = get_domain_config(domain)
    if not config:
        return ModuleAccess.DISABLED
    
    module_config = config.modules.get(module, {})
    if isinstance(module_config, dict):
        access = module_config.get("access", "disabled")
    else:
        access = module_config if module_config else "disabled"
    
    try:
        return ModuleAccess(access)
    except ValueError:
        return ModuleAccess.DISABLED


def get_enabled_modules(domain: str) -> List[str]:
    """Get list of enabled modules for a domain"""
    config = get_domain_config(domain)
    if not config:
        return []
    
    enabled = []
    for module, access in config.modules.items():
        if isinstance(access, dict):
            level = access.get("access", "disabled")
        else:
            level = access if access else "disabled"
        
        if level != "disabled":
            enabled.append(module)
    
    return enabled


# Port mappings for all domains
DOMAIN_PORTS = {
    # Hub
    "repox.pl": {"frontend": 3000, "api": 8000},
    
    # Analytics
    "analizowanie.pl": {"frontend": 3001, "api": 8001},
    "przeanalizuj.pl": {"frontend": 3002, "api": 8002},
    
    # Monitoring
    "alerts.pl": {"frontend": 3003, "api": 8003},
    
    # Forecasting
    "estymacja.pl": {"frontend": 3004, "api": 8004},
    
    # Historical
    "retrospektywa.pl": {"frontend": 3005, "api": 8005},
    
    # Marketing
    "persony.pl": {"frontend": 3006, "api": 8006},
    
    # Documentation
    "specyfikacja.pl": {"frontend": 3007, "api": 8007},
    
    # White-label
    "nisza.pl": {"frontend": 3008, "api": 8008},
    
    # === FINANCIAL DOMAINS ===
    "multiplan.pl": {"frontend": 3010, "api": 8010},
    "planbudzetu.pl": {"frontend": 3011, "api": 8011},
    "planinwestycji.pl": {"frontend": 3012, "api": 8012},
}


def get_all_domains() -> List[Dict[str, Any]]:
    """Get all registered domains with their configurations"""
    domains = []
    seen = set()
    
    for domain, config in DOMAIN_REGISTRY.items():
        if config.domain not in seen:
            seen.add(config.domain)
            domains.append({
                "domain": config.domain,
                "display_name": config.display_name,
                "type": config.type.value,
                "ports": {
                    "frontend": config.ports.frontend,
                    "api": config.ports.api
                },
                "modules": get_enabled_modules(config.domain)
            })
    
    return domains


def get_port_mapping() -> Dict[str, Dict[str, int]]:
    """Get port mapping for all domains"""
    return DOMAIN_PORTS.copy()


# Module definitions with their capabilities
MODULE_DEFINITIONS = {
    "reports": {
        "name": "Reports Engine",
        "description": "Generate PDF, DOCX, XLSX reports",
        "capabilities": ["generate", "schedule", "distribute", "templates"]
    },
    "alerts": {
        "name": "Alerts Engine", 
        "description": "Real-time KPI monitoring and notifications",
        "capabilities": ["threshold", "anomaly", "trend", "channels"]
    },
    "voice": {
        "name": "Voice/AI Engine",
        "description": "Natural language queries and voice interface",
        "capabilities": ["stt", "nlu", "tts", "conversation"]
    },
    "forecast": {
        "name": "Forecast Engine",
        "description": "ML-powered predictions and projections",
        "capabilities": ["prophet", "arima", "scenarios", "confidence"]
    },
    "budget": {
        "name": "Budget Module",
        "description": "Budget planning and tracking",
        "capabilities": ["planning", "tracking", "comparison", "categories"]
    },
    "investment": {
        "name": "Investment Module",
        "description": "Investment analysis and ROI calculations",
        "capabilities": ["roi", "npv", "irr", "risk", "portfolio"]
    },
    "integrations": {
        "name": "Integrations Hub",
        "description": "Connect external data sources",
        "capabilities": ["api", "import", "sync", "webhooks"]
    }
}


if __name__ == "__main__":
    # Initialize registry
    init_domain_registry()
    
    print("=== ANALYTICA Domain Registry ===\n")
    
    for domain_info in get_all_domains():
        print(f"{domain_info['domain']}:")
        print(f"  Display: {domain_info['display_name']}")
        print(f"  Type: {domain_info['type']}")
        print(f"  Ports: API={domain_info['ports']['api']}, Frontend={domain_info['ports']['frontend']}")
        print(f"  Modules: {', '.join(domain_info['modules'])}")
        print()
