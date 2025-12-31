"""
ANALYTICA DSL Schema
====================
Multiplatform DSL schema definition with JSON Schema validation.

Supports export to:
- JSON (native)
- YAML
- TOML
- XML
- Protocol Buffers (schema)
- GraphQL (schema)
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


# ============================================================
# DSL SCHEMA VERSION
# ============================================================

DSL_SCHEMA_VERSION = "2.0.0"


# ============================================================
# MULTIPLATFORM FORMATS
# ============================================================

class DSLFormat(Enum):
    """Supported DSL formats"""
    NATIVE = "native"      # pipe syntax: source.http() | transform.filter()
    JSON = "json"          # JSON object format
    YAML = "yaml"          # YAML format
    TOML = "toml"          # TOML format
    XML = "xml"            # XML format
    GRAPHQL = "graphql"    # GraphQL-like syntax


# ============================================================
# JSON SCHEMA DEFINITION
# ============================================================

DSL_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://analytica.pl/dsl/schema/v2",
    "title": "Analytica DSL Schema",
    "description": "Multiplatform DSL for data pipelines, UI generation, and IoT integration",
    "version": DSL_SCHEMA_VERSION,
    
    "definitions": {
        "atom": {
            "type": "object",
            "required": ["type", "action"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "data", "transform", "filter", "aggregate", "metrics",
                        "report", "alert", "budget", "investment", "forecast",
                        "export", "validate", "merge", "split", "cache",
                        "view", "ui", "source", "sink", "stream"
                    ]
                },
                "action": {"type": "string"},
                "params": {"type": "object"},
                "id": {"type": "string"},
                "condition": {"type": "string"},
                "on_error": {"type": "string", "enum": ["stop", "skip", "retry"]}
            }
        },
        
        "source_spec": {
            "type": "object",
            "required": ["protocol"],
            "properties": {
                "protocol": {
                    "type": "string",
                    "enum": [
                        "http", "https", "graphql", "websocket", "sse",
                        "mqtt", "mqtts", "coap", "coaps", "amqp", "amqps",
                        "modbus", "opcua", "serial", "bluetooth", "zigbee",
                        "sql", "mongodb", "redis", "elasticsearch", "influxdb",
                        "s3", "azure", "gcs", "ftp", "sftp",
                        "kafka", "nats", "rabbitmq",
                        "file", "stdin"
                    ]
                },
                "uri": {"type": "string"},
                "auth": {"$ref": "#/definitions/auth_spec"},
                "options": {"type": "object"}
            }
        },
        
        "sink_spec": {
            "type": "object",
            "required": ["protocol"],
            "properties": {
                "protocol": {
                    "type": "string",
                    "enum": [
                        "http", "https", "websocket",
                        "mqtt", "amqp", "modbus",
                        "sql", "mongodb", "redis", "elasticsearch", "influxdb",
                        "s3", "azure", "gcs",
                        "kafka", "nats",
                        "file", "stdout",
                        "email", "sms", "push", "slack", "discord", "telegram",
                        "display", "dashboard"
                    ]
                },
                "uri": {"type": "string"},
                "options": {"type": "object"}
            }
        },
        
        "auth_spec": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["none", "basic", "bearer", "api_key", "oauth2", "cert", "aws_sig"]
                },
                "credentials": {"type": "object"}
            }
        },
        
        "view_spec": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["chart", "table", "card", "kpi", "grid", "dashboard", "text", "list", "map", "gauge"]
                },
                "id": {"type": "string"},
                "title": {"type": "string"},
                "options": {"type": "object"}
            }
        },
        
        "ui_spec": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["page", "nav", "hero", "section", "grid", "form", "input", "button", "stats", "pricing", "features", "footer"]
                },
                "id": {"type": "string"},
                "children": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/ui_spec"}
                },
                "props": {"type": "object"}
            }
        },
        
        "variable": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string", "enum": ["string", "number", "boolean", "array", "object", "date", "secret"]},
                "default": {},
                "required": {"type": "boolean"},
                "description": {"type": "string"}
            }
        },
        
        "trigger": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["manual", "schedule", "webhook", "event", "stream", "change"]
                },
                "config": {"type": "object"}
            }
        }
    },
    
    "type": "object",
    "required": ["version", "pipeline"],
    "properties": {
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "author": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        
        "variables": {
            "type": "array",
            "items": {"$ref": "#/definitions/variable"}
        },
        
        "triggers": {
            "type": "array",
            "items": {"$ref": "#/definitions/trigger"}
        },
        
        "sources": {
            "type": "object",
            "additionalProperties": {"$ref": "#/definitions/source_spec"}
        },
        
        "sinks": {
            "type": "object",
            "additionalProperties": {"$ref": "#/definitions/sink_spec"}
        },
        
        "pipeline": {
            "type": "array",
            "items": {"$ref": "#/definitions/atom"}
        },
        
        "views": {
            "type": "array",
            "items": {"$ref": "#/definitions/view_spec"}
        },
        
        "ui": {
            "type": "array",
            "items": {"$ref": "#/definitions/ui_spec"}
        },
        
        "metadata": {
            "type": "object",
            "properties": {
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
                "platform": {"type": "string"},
                "target": {
                    "type": "string",
                    "enum": ["web", "mobile", "desktop", "iot", "cli", "api"]
                }
            }
        }
    }
}


# ============================================================
# DSL DOCUMENT CLASS
# ============================================================

@dataclass
class DSLDocument:
    """
    Multiplatform DSL document representation.
    Can be serialized to JSON, YAML, TOML, XML.
    """
    version: str = DSL_SCHEMA_VERSION
    name: str = ""
    description: str = ""
    pipeline: List[Dict] = field(default_factory=list)
    variables: List[Dict] = field(default_factory=list)
    triggers: List[Dict] = field(default_factory=list)
    sources: Dict[str, Dict] = field(default_factory=dict)
    sinks: Dict[str, Dict] = field(default_factory=dict)
    views: List[Dict] = field(default_factory=list)
    ui: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_json(self, indent: int = 2) -> str:
        """Export to JSON format"""
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)
    
    def to_yaml(self) -> str:
        """Export to YAML format"""
        try:
            import yaml
            return yaml.dump(asdict(self), allow_unicode=True, default_flow_style=False)
        except ImportError:
            raise ImportError("PyYAML required for YAML export: pip install pyyaml")
    
    def to_toml(self) -> str:
        """Export to TOML format"""
        try:
            import toml
            return toml.dumps(asdict(self))
        except ImportError:
            raise ImportError("toml required for TOML export: pip install toml")
    
    def to_xml(self) -> str:
        """Export to XML format"""
        def dict_to_xml(d, root_name="dsl"):
            def _to_xml(data, parent):
                if isinstance(data, dict):
                    for key, value in data.items():
                        child = f"<{key}>"
                        child += _to_xml(value, key)
                        child += f"</{key}>"
                        parent += child
                elif isinstance(data, list):
                    for item in data:
                        parent += f"<item>{_to_xml(item, 'item')}</item>"
                else:
                    parent = str(data) if data is not None else ""
                return parent
            return f'<?xml version="1.0" encoding="UTF-8"?><{root_name}>{_to_xml(d, root_name)}</{root_name}>'
        return dict_to_xml(asdict(self))
    
    def to_native(self) -> str:
        """Export to native DSL pipe syntax"""
        lines = []
        
        # Variables
        for var in self.variables:
            default = f' = {json.dumps(var.get("default"))}' if "default" in var else ""
            lines.append(f'${var["name"]}: {var.get("type", "any")}{default}')
        
        if self.variables:
            lines.append("")
        
        # Pipeline
        steps = []
        for step in self.pipeline:
            params = step.get("params", {})
            params_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in params.items())
            steps.append(f'{step["type"]}.{step["action"]}({params_str})')
        
        if steps:
            lines.append("\n| ".join(steps))
        
        return "\n".join(lines)
    
    @classmethod
    def from_json(cls, json_str: str) -> "DSLDocument":
        """Parse from JSON"""
        data = json.loads(json_str)
        return cls(**data)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> "DSLDocument":
        """Parse from YAML"""
        try:
            import yaml
            data = yaml.safe_load(yaml_str)
            return cls(**data)
        except ImportError:
            raise ImportError("PyYAML required for YAML import")
    
    @classmethod
    def from_native(cls, dsl_str: str) -> "DSLDocument":
        """Parse from native DSL syntax"""
        from .parser import dsl_parse
        pipeline = dsl_parse(dsl_str)
        
        steps = []
        for step in pipeline.steps:
            steps.append({
                "type": step.atom.type.value,
                "action": step.atom.action,
                "params": step.atom.params
            })
        
        return cls(
            pipeline=steps,
            variables=[{"name": k, "default": v} for k, v in pipeline.variables.items()]
        )
    
    def validate(self) -> List[str]:
        """Validate document against schema"""
        errors = []
        
        # Version check
        if not self.version:
            errors.append("Missing version")
        
        # Pipeline check
        if not self.pipeline:
            errors.append("Empty pipeline")
        
        for i, step in enumerate(self.pipeline):
            if "type" not in step:
                errors.append(f"Step {i}: missing type")
            if "action" not in step:
                errors.append(f"Step {i}: missing action")
        
        return errors


# ============================================================
# FORMAT CONVERTERS
# ============================================================

def convert_dsl(source: str, from_format: DSLFormat, to_format: DSLFormat) -> str:
    """
    Convert DSL between formats.
    
    Usage:
        json_dsl = convert_dsl(native_dsl, DSLFormat.NATIVE, DSLFormat.JSON)
        yaml_dsl = convert_dsl(json_dsl, DSLFormat.JSON, DSLFormat.YAML)
    """
    # Parse source
    if from_format == DSLFormat.NATIVE:
        doc = DSLDocument.from_native(source)
    elif from_format == DSLFormat.JSON:
        doc = DSLDocument.from_json(source)
    elif from_format == DSLFormat.YAML:
        doc = DSLDocument.from_yaml(source)
    else:
        raise ValueError(f"Unsupported source format: {from_format}")
    
    # Export to target
    if to_format == DSLFormat.NATIVE:
        return doc.to_native()
    elif to_format == DSLFormat.JSON:
        return doc.to_json()
    elif to_format == DSLFormat.YAML:
        return doc.to_yaml()
    elif to_format == DSLFormat.TOML:
        return doc.to_toml()
    elif to_format == DSLFormat.XML:
        return doc.to_xml()
    else:
        raise ValueError(f"Unsupported target format: {to_format}")


def get_schema() -> Dict:
    """Get JSON Schema for DSL validation"""
    return DSL_JSON_SCHEMA


def validate_dsl(dsl_dict: Dict) -> List[str]:
    """Validate DSL document against schema"""
    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(DSL_JSON_SCHEMA)
        return [str(e.message) for e in validator.iter_errors(dsl_dict)]
    except ImportError:
        # Fallback to basic validation
        doc = DSLDocument(**dsl_dict)
        return doc.validate()
