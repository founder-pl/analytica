"""
ANALYTICA Investment Module
===========================
Investment analysis, ROI calculations, and portfolio management.

Features:
- ROI (Return on Investment) calculation
- NPV (Net Present Value) analysis
- IRR (Internal Rate of Return)
- Payback period calculation
- Scenario comparison
- Risk assessment
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import math

from .. import BaseModule


class InvestmentType(Enum):
    """Types of investments"""
    CAPEX = "capex"
    OPEX = "opex"
    PROJECT = "project"
    ACQUISITION = "acquisition"
    RND = "rnd"


class RiskLevel(Enum):
    """Investment risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class CashFlow:
    """Single cash flow entry"""
    period: int
    amount: Decimal
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "amount": float(self.amount),
            "description": self.description,
        }


@dataclass
class Investment:
    """Investment definition"""
    id: str
    name: str
    initial_investment: Decimal
    discount_rate: Decimal
    investment_type: InvestmentType = InvestmentType.PROJECT
    cash_flows: List[CashFlow] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "initial_investment": float(self.initial_investment),
            "discount_rate": float(self.discount_rate),
            "investment_type": self.investment_type.value,
            "cash_flows": [cf.to_dict() for cf in self.cash_flows],
            "created_at": self.created_at.isoformat(),
        }


class InvestmentCalculator:
    """Investment calculation utilities"""
    
    @staticmethod
    def calculate_roi(
        initial_investment: Decimal,
        total_returns: Decimal
    ) -> Dict[str, Any]:
        """Calculate Return on Investment"""
        if initial_investment == 0:
            return {"roi": 0, "roi_percent": 0}
        
        net_profit = total_returns - initial_investment
        roi = (net_profit / initial_investment) * 100
        
        return {
            "initial_investment": float(initial_investment),
            "total_returns": float(total_returns),
            "net_profit": float(net_profit),
            "roi_percent": round(float(roi), 2),
        }
    
    @staticmethod
    def calculate_npv(
        initial_investment: Decimal,
        cash_flows: List[Decimal],
        discount_rate: Decimal
    ) -> Dict[str, Any]:
        """Calculate Net Present Value"""
        npv = -float(initial_investment)
        rate = float(discount_rate)
        
        discounted_flows = []
        for i, cf in enumerate(cash_flows, 1):
            pv = float(cf) / ((1 + rate) ** i)
            npv += pv
            discounted_flows.append({
                "period": i,
                "cash_flow": float(cf),
                "present_value": round(pv, 2),
            })
        
        return {
            "initial_investment": float(initial_investment),
            "discount_rate": rate,
            "npv": round(npv, 2),
            "discounted_flows": discounted_flows,
            "is_profitable": npv > 0,
        }
    
    @staticmethod
    def calculate_irr(
        initial_investment: Decimal,
        cash_flows: List[Decimal],
        max_iterations: int = 1000,
        tolerance: float = 0.0001
    ) -> Optional[float]:
        """Calculate Internal Rate of Return using Newton-Raphson method"""
        flows = [-float(initial_investment)] + [float(cf) for cf in cash_flows]
        
        def npv_at_rate(rate: float) -> float:
            return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(flows))
        
        def npv_derivative(rate: float) -> float:
            return sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(flows))
        
        rate = 0.1  # Initial guess
        
        for _ in range(max_iterations):
            npv = npv_at_rate(rate)
            if abs(npv) < tolerance:
                return round(rate * 100, 2)
            
            derivative = npv_derivative(rate)
            if derivative == 0:
                return None
            
            rate = rate - npv / derivative
            
            if rate < -1:
                return None
        
        return None
    
    @staticmethod
    def calculate_payback_period(
        initial_investment: Decimal,
        cash_flows: List[Decimal]
    ) -> Dict[str, Any]:
        """Calculate payback period"""
        cumulative = Decimal("0")
        payback_period = None
        cumulative_by_period = []
        
        for i, cf in enumerate(cash_flows, 1):
            cumulative += cf
            cumulative_by_period.append({
                "period": i,
                "cash_flow": float(cf),
                "cumulative": float(cumulative),
            })
            
            if cumulative >= initial_investment and payback_period is None:
                # Interpolate for exact period
                prev_cumulative = cumulative - cf
                remaining = initial_investment - prev_cumulative
                fraction = float(remaining / cf) if cf != 0 else 0
                payback_period = i - 1 + fraction
        
        return {
            "initial_investment": float(initial_investment),
            "payback_period": round(payback_period, 2) if payback_period else None,
            "cumulative_by_period": cumulative_by_period,
            "recovered": cumulative >= initial_investment,
        }
    
    @staticmethod
    def calculate_profitability_index(
        initial_investment: Decimal,
        npv: Decimal
    ) -> float:
        """Calculate profitability index (PI)"""
        if initial_investment == 0:
            return 0
        pv_future = float(initial_investment) + float(npv)
        return round(pv_future / float(initial_investment), 2)
    
    @staticmethod
    def assess_risk(
        npv: float,
        irr: Optional[float],
        payback_period: Optional[float],
        investment_type: InvestmentType
    ) -> RiskLevel:
        """Assess investment risk level"""
        score = 0
        
        # NPV scoring
        if npv > 0:
            score += 2
        elif npv < 0:
            score -= 2
        
        # IRR scoring
        if irr:
            if irr > 20:
                score += 2
            elif irr > 10:
                score += 1
            elif irr < 5:
                score -= 1
        
        # Payback scoring
        if payback_period:
            if payback_period < 2:
                score += 2
            elif payback_period < 4:
                score += 1
            elif payback_period > 6:
                score -= 1
        
        # Type adjustment
        if investment_type in [InvestmentType.RND, InvestmentType.ACQUISITION]:
            score -= 1
        
        if score >= 4:
            return RiskLevel.LOW
        elif score >= 2:
            return RiskLevel.MEDIUM
        elif score >= 0:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH


class InvestmentModule(BaseModule):
    """Investment module implementation"""
    
    name = "investment"
    version = "1.0.0"
    
    def __init__(self):
        self._investments: Dict[str, Investment] = {}
    
    def get_routes(self) -> List[Any]:
        return []
    
    def get_atoms(self) -> Dict[str, Any]:
        return {
            "investment.analyze": self.analyze,
            "investment.roi": self.calculate_roi,
            "investment.npv": self.calculate_npv,
            "investment.irr": self.calculate_irr,
            "investment.payback": self.calculate_payback,
        }
    
    def analyze(self, **kwargs) -> Dict[str, Any]:
        """Full investment analysis"""
        from uuid import uuid4
        
        initial = Decimal(str(kwargs.get("initial_investment", 0)))
        rate = Decimal(str(kwargs.get("discount_rate", 0.1)))
        cash_flows = [Decimal(str(cf.get("amount", cf) if isinstance(cf, dict) else cf)) 
                      for cf in kwargs.get("cash_flows", [])]
        inv_type = InvestmentType(kwargs.get("investment_type", "project"))
        
        # Calculate all metrics
        total_returns = sum(cash_flows)
        roi = InvestmentCalculator.calculate_roi(initial, total_returns)
        npv = InvestmentCalculator.calculate_npv(initial, cash_flows, rate)
        irr = InvestmentCalculator.calculate_irr(initial, cash_flows)
        payback = InvestmentCalculator.calculate_payback_period(initial, cash_flows)
        pi = InvestmentCalculator.calculate_profitability_index(initial, Decimal(str(npv["npv"])))
        risk = InvestmentCalculator.assess_risk(npv["npv"], irr, payback["payback_period"], inv_type)
        
        return {
            "investment_id": f"inv_{uuid4().hex[:8]}",
            "name": kwargs.get("name", "Investment Analysis"),
            "roi": roi["roi_percent"],
            "npv": npv["npv"],
            "irr": irr,
            "payback_period": payback["payback_period"],
            "profitability_index": pi,
            "risk_level": risk.value,
            "recommendation": "proceed" if npv["npv"] > 0 and (irr is None or irr > float(rate) * 100) else "review",
        }
    
    def calculate_roi(self, **kwargs) -> Dict[str, Any]:
        initial = Decimal(str(kwargs.get("initial_investment", kwargs.get("_arg0", 0))))
        returns = Decimal(str(kwargs.get("total_returns", kwargs.get("_arg1", 0))))
        return InvestmentCalculator.calculate_roi(initial, returns)
    
    def calculate_npv(self, **kwargs) -> Dict[str, Any]:
        initial = Decimal(str(kwargs.get("initial_investment", 0)))
        rate = Decimal(str(kwargs.get("discount_rate", 0.1)))
        cash_flows = [Decimal(str(cf)) for cf in kwargs.get("cash_flows", [])]
        return InvestmentCalculator.calculate_npv(initial, cash_flows, rate)
    
    def calculate_irr(self, **kwargs) -> Dict[str, Any]:
        initial = Decimal(str(kwargs.get("initial_investment", 0)))
        cash_flows = [Decimal(str(cf)) for cf in kwargs.get("cash_flows", [])]
        irr = InvestmentCalculator.calculate_irr(initial, cash_flows)
        return {"irr": irr, "irr_percent": f"{irr}%" if irr else None}
    
    def calculate_payback(self, **kwargs) -> Dict[str, Any]:
        initial = Decimal(str(kwargs.get("initial_investment", 0)))
        cash_flows = [Decimal(str(cf)) for cf in kwargs.get("cash_flows", [])]
        return InvestmentCalculator.calculate_payback_period(initial, cash_flows)


# Module instance
investment_module = InvestmentModule()

__all__ = [
    "InvestmentModule",
    "Investment",
    "CashFlow",
    "InvestmentType",
    "RiskLevel",
    "InvestmentCalculator",
    "investment_module",
]
