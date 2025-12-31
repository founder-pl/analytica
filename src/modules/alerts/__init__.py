"""
ANALYTICA Alerts Module
=======================
Threshold monitoring, notifications, and alerting system.

Features:
- Threshold-based alerts
- Anomaly detection
- Multi-channel notifications (email, webhook, Slack)
- Alert escalation
- Alert history and analytics
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .. import BaseModule


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class ComparisonOperator(Enum):
    """Comparison operators for thresholds"""
    GT = "gt"       # greater than
    GTE = "gte"     # greater than or equal
    LT = "lt"       # less than
    LTE = "lte"     # less than or equal
    EQ = "eq"       # equal
    NEQ = "neq"     # not equal


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    SMS = "sms"
    PUSH = "push"


@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    metric: str
    operator: ComparisonOperator
    threshold: float
    severity: AlertSeverity = AlertSeverity.WARNING
    channels: List[NotificationChannel] = field(default_factory=list)
    cooldown_minutes: int = 15
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """Evaluate if value triggers this rule"""
        if self.operator == ComparisonOperator.GT:
            return value > self.threshold
        elif self.operator == ComparisonOperator.GTE:
            return value >= self.threshold
        elif self.operator == ComparisonOperator.LT:
            return value < self.threshold
        elif self.operator == ComparisonOperator.LTE:
            return value <= self.threshold
        elif self.operator == ComparisonOperator.EQ:
            return value == self.threshold
        elif self.operator == ComparisonOperator.NEQ:
            return value != self.threshold
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "metric": self.metric,
            "operator": self.operator.value,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "channels": [c.value for c in self.channels],
            "cooldown_minutes": self.cooldown_minutes,
            "enabled": self.enabled,
        }


@dataclass
class Alert:
    """Triggered alert"""
    id: str
    rule_id: str
    metric: str
    value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    message: str = ""
    
    def acknowledge(self) -> None:
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self) -> None:
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "status": self.status.value,
            "triggered_at": self.triggered_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "message": self.message,
        }


class AlertEngine:
    """Alert processing engine"""
    
    @staticmethod
    def check_threshold(
        metric: str,
        value: float,
        operator: str,
        threshold: float
    ) -> Dict[str, Any]:
        """Check if value exceeds threshold"""
        op = ComparisonOperator(operator) if operator in [o.value for o in ComparisonOperator] else ComparisonOperator.GT
        
        rule = AlertRule(
            id="check",
            name="Threshold Check",
            metric=metric,
            operator=op,
            threshold=threshold,
        )
        
        triggered = rule.evaluate(value)
        
        return {
            "metric": metric,
            "value": value,
            "operator": operator,
            "threshold": threshold,
            "triggered": triggered,
            "message": f"{metric} ({value}) {'exceeded' if triggered else 'within'} threshold ({threshold})",
        }
    
    @staticmethod
    def detect_anomaly(
        values: List[float],
        current: float,
        std_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """Detect anomaly using standard deviation"""
        if len(values) < 2:
            return {"is_anomaly": False, "reason": "Insufficient data"}
        
        import statistics
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        
        lower_bound = mean - (std_multiplier * std)
        upper_bound = mean + (std_multiplier * std)
        
        is_anomaly = current < lower_bound or current > upper_bound
        
        return {
            "is_anomaly": is_anomaly,
            "current_value": current,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "deviation": round(abs(current - mean) / std, 2) if std > 0 else 0,
        }


class AlertsModule(BaseModule):
    """Alerts module implementation"""
    
    name = "alerts"
    version = "1.0.0"
    
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._last_triggered: Dict[str, datetime] = {}
    
    def get_routes(self) -> List[Any]:
        return []
    
    def get_atoms(self) -> Dict[str, Any]:
        return {
            "alert.threshold": self.check_threshold,
            "alert.create": self.create_rule,
            "alert.send": self.send_alert,
            "alert.anomaly": self.detect_anomaly,
        }
    
    def check_threshold(self, **kwargs) -> Dict[str, Any]:
        """Check threshold and optionally trigger alert"""
        metric = kwargs.get("metric", kwargs.get("_arg0", "value"))
        value = float(kwargs.get("value", kwargs.get("_arg1", 0)))
        operator = kwargs.get("operator", kwargs.get("_arg2", "gt"))
        threshold = float(kwargs.get("threshold", kwargs.get("_arg3", 0)))
        
        result = AlertEngine.check_threshold(metric, value, operator, threshold)
        
        if result["triggered"]:
            # Create alert
            from uuid import uuid4
            alert_id = f"alert_{uuid4().hex[:8]}"
            
            alert = Alert(
                id=alert_id,
                rule_id="manual",
                metric=metric,
                value=value,
                threshold=threshold,
                severity=AlertSeverity.WARNING,
                message=result["message"],
            )
            self._alerts[alert_id] = alert
            result["alert_id"] = alert_id
        
        return result
    
    def create_rule(self, **kwargs) -> Dict[str, Any]:
        """Create an alert rule"""
        from uuid import uuid4
        
        rule_id = f"rule_{uuid4().hex[:8]}"
        rule = AlertRule(
            id=rule_id,
            name=kwargs.get("name", "New Rule"),
            metric=kwargs.get("metric", "value"),
            operator=ComparisonOperator(kwargs.get("operator", "gt")),
            threshold=float(kwargs.get("threshold", 0)),
            severity=AlertSeverity(kwargs.get("severity", "warning")),
            channels=[NotificationChannel(c) for c in kwargs.get("channels", ["email"])],
            cooldown_minutes=kwargs.get("cooldown", 15),
        )
        
        self._rules[rule_id] = rule
        return rule.to_dict()
    
    def send_alert(self, **kwargs) -> Dict[str, Any]:
        """Send alert notification (mock)"""
        channel = kwargs.get("channel", kwargs.get("_arg0", "email"))
        recipient = kwargs.get("recipient", kwargs.get("_arg1", ""))
        message = kwargs.get("message", kwargs.get("_arg2", "Alert triggered"))
        severity = kwargs.get("severity", "warning")
        
        return {
            "status": "sent",
            "channel": channel,
            "recipient": recipient,
            "message": message,
            "severity": severity,
            "sent_at": datetime.utcnow().isoformat(),
        }
    
    def detect_anomaly(self, **kwargs) -> Dict[str, Any]:
        """Detect anomaly in data"""
        values = kwargs.get("values", kwargs.get("data", []))
        current = kwargs.get("current", kwargs.get("_arg0"))
        std_multiplier = kwargs.get("std_multiplier", 2.0)
        
        if current is None and values:
            current = values[-1]
            values = values[:-1]
        
        float_values = [float(v) for v in values] if values else []
        current_float = float(current) if current is not None else 0
        
        return AlertEngine.detect_anomaly(float_values, current_float, std_multiplier)


# Module instance
alerts_module = AlertsModule()

__all__ = [
    "AlertsModule",
    "Alert",
    "AlertRule",
    "AlertSeverity",
    "AlertStatus",
    "ComparisonOperator",
    "NotificationChannel",
    "AlertEngine",
    "alerts_module",
]
