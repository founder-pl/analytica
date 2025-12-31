"""
ANALYTICA Budget Module
=======================
Budget management, variance analysis, and expense tracking.

Features:
- Budget creation and management
- Variance analysis (planned vs actual)
- Expense categorization
- Budget alerts
- Multi-scenario budgeting
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from .. import BaseModule


class BudgetCategory(Enum):
    """Standard budget categories"""
    PERSONNEL = "personnel"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    IT = "it"
    FACILITIES = "facilities"
    TRAVEL = "travel"
    SUPPLIES = "supplies"
    SERVICES = "services"
    OTHER = "other"


class BudgetScenario(Enum):
    """Budget scenario types"""
    OPTIMISTIC = "optimistic"
    REALISTIC = "realistic"
    PESSIMISTIC = "pessimistic"


@dataclass
class BudgetLine:
    """Single budget line item"""
    category: str
    name: str
    planned: Decimal
    actual: Decimal = Decimal("0")
    notes: str = ""
    
    @property
    def variance(self) -> Decimal:
        """Calculate variance (actual - planned)"""
        return self.actual - self.planned
    
    @property
    def variance_percent(self) -> float:
        """Calculate variance as percentage"""
        if self.planned == 0:
            return 0.0
        return float((self.variance / self.planned) * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "name": self.name,
            "planned": float(self.planned),
            "actual": float(self.actual),
            "variance": float(self.variance),
            "variance_percent": round(self.variance_percent, 2),
            "notes": self.notes,
        }


@dataclass
class Budget:
    """Budget definition"""
    id: str
    name: str
    period_start: date
    period_end: date
    scenario: BudgetScenario = BudgetScenario.REALISTIC
    lines: List[BudgetLine] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_planned(self) -> Decimal:
        return sum(line.planned for line in self.lines)
    
    @property
    def total_actual(self) -> Decimal:
        return sum(line.actual for line in self.lines)
    
    @property
    def total_variance(self) -> Decimal:
        return self.total_actual - self.total_planned
    
    def add_line(self, line: BudgetLine) -> None:
        self.lines.append(line)
    
    def get_by_category(self, category: str) -> List[BudgetLine]:
        return [l for l in self.lines if l.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "scenario": self.scenario.value,
            "lines": [l.to_dict() for l in self.lines],
            "totals": {
                "planned": float(self.total_planned),
                "actual": float(self.total_actual),
                "variance": float(self.total_variance),
            },
            "created_at": self.created_at.isoformat(),
        }


class BudgetCalculator:
    """Budget calculation utilities"""
    
    @staticmethod
    def calculate_variance(planned: Decimal, actual: Decimal) -> Dict[str, Any]:
        """Calculate variance metrics"""
        variance = actual - planned
        variance_pct = (variance / planned * 100) if planned != 0 else Decimal("0")
        
        return {
            "planned": float(planned),
            "actual": float(actual),
            "variance": float(variance),
            "variance_percent": round(float(variance_pct), 2),
            "status": "over" if variance > 0 else "under" if variance < 0 else "on_target",
        }
    
    @staticmethod
    def categorize_expenses(
        expenses: List[Dict[str, Any]], 
        rules: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize expenses based on rules"""
        rules = rules or {
            "personnel": ["salary", "wages", "bonus", "benefits"],
            "marketing": ["ads", "advertising", "promotion", "campaign"],
            "it": ["software", "hardware", "cloud", "hosting"],
            "travel": ["flight", "hotel", "transport", "travel"],
        }
        
        categorized: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in rules}
        categorized["other"] = []
        
        for expense in expenses:
            desc = expense.get("description", "").lower()
            matched = False
            
            for category, keywords in rules.items():
                if any(kw in desc for kw in keywords):
                    categorized[category].append(expense)
                    matched = True
                    break
            
            if not matched:
                categorized["other"].append(expense)
        
        return categorized
    
    @staticmethod
    def project_spending(
        current_spent: Decimal,
        days_elapsed: int,
        total_days: int
    ) -> Dict[str, Any]:
        """Project end-of-period spending based on current rate"""
        if days_elapsed <= 0:
            return {"projected": 0, "daily_rate": 0}
        
        daily_rate = current_spent / days_elapsed
        projected = daily_rate * total_days
        
        return {
            "current_spent": float(current_spent),
            "days_elapsed": days_elapsed,
            "total_days": total_days,
            "daily_rate": round(float(daily_rate), 2),
            "projected_total": round(float(projected), 2),
        }


class BudgetModule(BaseModule):
    """Budget module implementation"""
    
    name = "budget"
    version = "1.0.0"
    
    def __init__(self):
        self._budgets: Dict[str, Budget] = {}
    
    def get_routes(self) -> List[Any]:
        """Return FastAPI routes"""
        return []  # Routes defined in API
    
    def get_atoms(self) -> Dict[str, Any]:
        """Return DSL atoms"""
        return {
            "budget.create": self.create_budget,
            "budget.variance": self.calculate_variance,
            "budget.categorize": self.categorize_expenses,
        }
    
    def create_budget(self, **kwargs) -> Dict[str, Any]:
        """Create a new budget"""
        from uuid import uuid4
        budget_id = f"budget_{uuid4().hex[:8]}"
        
        budget = Budget(
            id=budget_id,
            name=kwargs.get("name", "New Budget"),
            period_start=date.fromisoformat(kwargs.get("period_start", date.today().isoformat())),
            period_end=date.fromisoformat(kwargs.get("period_end", date.today().isoformat())),
            scenario=BudgetScenario(kwargs.get("scenario", "realistic")),
        )
        
        for line_data in kwargs.get("lines", []):
            budget.add_line(BudgetLine(
                category=line_data.get("category", "other"),
                name=line_data.get("name", ""),
                planned=Decimal(str(line_data.get("planned", 0))),
                actual=Decimal(str(line_data.get("actual", 0))),
            ))
        
        self._budgets[budget_id] = budget
        return budget.to_dict()
    
    def calculate_variance(self, budget_id: str = None, **kwargs) -> Dict[str, Any]:
        """Calculate budget variance"""
        if budget_id and budget_id in self._budgets:
            budget = self._budgets[budget_id]
            return {
                "budget_id": budget_id,
                "total_variance": BudgetCalculator.calculate_variance(
                    budget.total_planned, budget.total_actual
                ),
                "by_line": [l.to_dict() for l in budget.lines],
            }
        
        # Direct calculation
        planned = Decimal(str(kwargs.get("planned", 0)))
        actual = Decimal(str(kwargs.get("actual", 0)))
        return BudgetCalculator.calculate_variance(planned, actual)
    
    def categorize_expenses(self, expenses: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Categorize expenses"""
        expenses = expenses or kwargs.get("data", [])
        return BudgetCalculator.categorize_expenses(expenses)


# Module instance
budget_module = BudgetModule()

__all__ = [
    "BudgetModule",
    "Budget",
    "BudgetLine",
    "BudgetCategory",
    "BudgetScenario",
    "BudgetCalculator",
    "budget_module",
]
