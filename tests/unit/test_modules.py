"""
ANALYTICA Unit Tests - Modules
==============================

Unit tests for business modules: budget, investment, forecast, reports, alerts, voice
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# ============================================================
# BUDGET MODULE TESTS
# ============================================================

class TestBudgetModule:
    """Tests for budget module"""
    
    def test_budget_line_variance(self):
        """Test budget line variance calculation"""
        from modules.budget import BudgetLine
        
        line = BudgetLine(
            category="marketing",
            name="Digital Ads",
            planned=Decimal("50000"),
            actual=Decimal("48000"),
        )
        
        assert line.variance == Decimal("-2000")
        assert line.variance_percent == -4.0
    
    def test_budget_line_to_dict(self):
        """Test budget line serialization"""
        from modules.budget import BudgetLine
        
        line = BudgetLine(
            category="it",
            name="Software",
            planned=Decimal("10000"),
            actual=Decimal("12000"),
        )
        
        d = line.to_dict()
        assert d["category"] == "it"
        assert d["planned"] == 10000.0
        assert d["actual"] == 12000.0
        assert d["variance"] == 2000.0
        assert d["variance_percent"] == 20.0
    
    def test_budget_calculator_variance(self):
        """Test variance calculation"""
        from modules.budget import BudgetCalculator
        
        result = BudgetCalculator.calculate_variance(
            planned=Decimal("100000"),
            actual=Decimal("95000")
        )
        
        assert result["variance"] == -5000.0
        assert result["variance_percent"] == -5.0
        assert result["status"] == "under"
    
    def test_budget_calculator_over_budget(self):
        """Test over budget status"""
        from modules.budget import BudgetCalculator
        
        result = BudgetCalculator.calculate_variance(
            planned=Decimal("100000"),
            actual=Decimal("120000")
        )
        
        assert result["status"] == "over"
        assert result["variance"] == 20000.0
    
    def test_budget_categorize_expenses(self):
        """Test expense categorization"""
        from modules.budget import BudgetCalculator
        
        expenses = [
            {"description": "Google Ads campaign", "amount": 5000},
            {"description": "Developer salary", "amount": 10000},
            {"description": "Cloud hosting AWS", "amount": 2000},
            {"description": "Office supplies", "amount": 500},
        ]
        
        result = BudgetCalculator.categorize_expenses(expenses)
        
        assert len(result["marketing"]) == 1
        assert len(result["personnel"]) == 1
        assert len(result["it"]) == 1
        assert len(result["other"]) == 1
    
    def test_budget_project_spending(self):
        """Test spending projection"""
        from modules.budget import BudgetCalculator
        
        result = BudgetCalculator.project_spending(
            current_spent=Decimal("30000"),
            days_elapsed=15,
            total_days=30
        )
        
        assert result["daily_rate"] == 2000.0
        assert result["projected_total"] == 60000.0


# ============================================================
# INVESTMENT MODULE TESTS
# ============================================================

class TestInvestmentModule:
    """Tests for investment module"""
    
    def test_roi_calculation(self):
        """Test ROI calculation"""
        from modules.investment import InvestmentCalculator
        
        result = InvestmentCalculator.calculate_roi(
            initial_investment=Decimal("100000"),
            total_returns=Decimal("150000")
        )
        
        assert result["roi_percent"] == 50.0
        assert result["net_profit"] == 50000.0
    
    def test_roi_zero_investment(self):
        """Test ROI with zero investment"""
        from modules.investment import InvestmentCalculator
        
        result = InvestmentCalculator.calculate_roi(
            initial_investment=Decimal("0"),
            total_returns=Decimal("10000")
        )
        
        assert result["roi"] == 0
    
    def test_npv_calculation(self):
        """Test NPV calculation"""
        from modules.investment import InvestmentCalculator
        
        result = InvestmentCalculator.calculate_npv(
            initial_investment=Decimal("100000"),
            cash_flows=[Decimal("40000"), Decimal("50000"), Decimal("60000")],
            discount_rate=Decimal("0.1")
        )
        
        assert result["npv"] > 0
        assert result["is_profitable"] == True
        assert len(result["discounted_flows"]) == 3
    
    def test_npv_negative(self):
        """Test negative NPV"""
        from modules.investment import InvestmentCalculator
        
        result = InvestmentCalculator.calculate_npv(
            initial_investment=Decimal("100000"),
            cash_flows=[Decimal("10000"), Decimal("10000"), Decimal("10000")],
            discount_rate=Decimal("0.1")
        )
        
        assert result["npv"] < 0
        assert result["is_profitable"] == False
    
    def test_irr_calculation(self):
        """Test IRR calculation"""
        from modules.investment import InvestmentCalculator
        
        irr = InvestmentCalculator.calculate_irr(
            initial_investment=Decimal("100000"),
            cash_flows=[Decimal("40000"), Decimal("50000"), Decimal("60000")]
        )
        
        assert irr is not None
        assert irr > 0
    
    def test_payback_period(self):
        """Test payback period calculation"""
        from modules.investment import InvestmentCalculator
        
        result = InvestmentCalculator.calculate_payback_period(
            initial_investment=Decimal("100000"),
            cash_flows=[Decimal("40000"), Decimal("40000"), Decimal("40000")]
        )
        
        assert result["payback_period"] == 2.5
        assert result["recovered"] == True
    
    def test_payback_not_recovered(self):
        """Test payback when investment not recovered"""
        from modules.investment import InvestmentCalculator
        
        result = InvestmentCalculator.calculate_payback_period(
            initial_investment=Decimal("100000"),
            cash_flows=[Decimal("10000"), Decimal("10000")]
        )
        
        assert result["payback_period"] is None
        assert result["recovered"] == False
    
    def test_profitability_index(self):
        """Test profitability index calculation"""
        from modules.investment import InvestmentCalculator
        
        pi = InvestmentCalculator.calculate_profitability_index(
            initial_investment=Decimal("100000"),
            npv=Decimal("20000")
        )
        
        assert pi == 1.2
    
    def test_risk_assessment_low(self):
        """Test low risk assessment"""
        from modules.investment import InvestmentCalculator, InvestmentType, RiskLevel
        
        risk = InvestmentCalculator.assess_risk(
            npv=50000,
            irr=25.0,
            payback_period=1.5,
            investment_type=InvestmentType.PROJECT
        )
        
        assert risk == RiskLevel.LOW
    
    def test_risk_assessment_high(self):
        """Test high risk assessment"""
        from modules.investment import InvestmentCalculator, InvestmentType, RiskLevel
        
        risk = InvestmentCalculator.assess_risk(
            npv=-10000,
            irr=3.0,
            payback_period=7.0,
            investment_type=InvestmentType.RND
        )
        
        assert risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]


# ============================================================
# FORECAST MODULE TESTS
# ============================================================

class TestForecastModule:
    """Tests for forecast module"""
    
    def test_moving_average(self):
        """Test moving average calculation"""
        from modules.forecast import ForecastCalculator
        
        data = [100.0, 110.0, 120.0, 130.0, 140.0]
        result = ForecastCalculator.moving_average(data, window=3)
        
        assert len(result) == 3
        assert result[0] == 110.0  # (100+110+120)/3
        assert result[1] == 120.0  # (110+120+130)/3
        assert result[2] == 130.0  # (120+130+140)/3
    
    def test_exponential_smoothing(self):
        """Test exponential smoothing"""
        from modules.forecast import ForecastCalculator
        
        data = [100.0, 110.0, 120.0, 130.0]
        result = ForecastCalculator.exponential_smoothing(data, alpha=0.5)
        
        assert len(result) == 4
        assert result[0] == 100.0  # First value unchanged
    
    def test_linear_trend(self):
        """Test linear trend detection"""
        from modules.forecast import ForecastCalculator
        
        data = [100.0, 110.0, 120.0, 130.0]
        trend = ForecastCalculator.linear_trend(data)
        
        assert trend["slope"] == 10.0
        assert trend["intercept"] == 100.0
    
    def test_detect_trend_up(self):
        """Test upward trend detection"""
        from modules.forecast import ForecastCalculator, TrendDirection
        
        data = [100.0, 110.0, 120.0, 130.0, 140.0]
        trend = ForecastCalculator.detect_trend(data)
        
        assert trend == TrendDirection.UP
    
    def test_detect_trend_down(self):
        """Test downward trend detection"""
        from modules.forecast import ForecastCalculator, TrendDirection
        
        data = [140.0, 130.0, 120.0, 110.0, 100.0]
        trend = ForecastCalculator.detect_trend(data)
        
        assert trend == TrendDirection.DOWN
    
    def test_detect_trend_stable(self):
        """Test stable trend detection"""
        from modules.forecast import ForecastCalculator, TrendDirection
        
        data = [100.0, 100.0, 100.0, 100.0]
        trend = ForecastCalculator.detect_trend(data)
        
        assert trend == TrendDirection.STABLE
    
    def test_forecast_next_linear(self):
        """Test linear forecasting"""
        from modules.forecast import ForecastCalculator, ForecastMethod
        
        data = [100.0, 110.0, 120.0, 130.0]
        predictions = ForecastCalculator.forecast_next(data, periods=3, method=ForecastMethod.LINEAR)
        
        assert len(predictions) == 3
        assert predictions[0].period == 5
        assert predictions[0].value == 140.0  # Linear continuation
    
    def test_forecast_accuracy_metrics(self):
        """Test forecast accuracy calculation"""
        from modules.forecast import ForecastCalculator
        
        actual = [100.0, 110.0, 120.0]
        predicted = [95.0, 112.0, 118.0]
        
        metrics = ForecastCalculator.calculate_accuracy(actual, predicted)
        
        assert "mae" in metrics
        assert "mape" in metrics
        assert "rmse" in metrics
        assert metrics["mae"] > 0


# ============================================================
# REPORTS MODULE TESTS
# ============================================================

class TestReportsModule:
    """Tests for reports module"""
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        from modules.reports import ReportGenerator
        
        html = ReportGenerator.generate_html(
            title="Test Report",
            data={"summary": {"total": 1000, "count": 10}},
            sections=["summary"]
        )
        
        assert "<html>" in html
        assert "Test Report" in html
        assert "summary" in html.lower()
    
    def test_generate_json_report(self):
        """Test JSON report generation"""
        from modules.reports import ReportGenerator
        import json
        
        result = ReportGenerator.generate_json(
            title="Test Report",
            data={"value": 123}
        )
        
        parsed = json.loads(result)
        assert parsed["title"] == "Test Report"
        assert parsed["data"]["value"] == 123
    
    def test_generate_csv_report(self):
        """Test CSV report generation"""
        from modules.reports import ReportGenerator
        
        data = [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200},
        ]
        
        csv = ReportGenerator.generate_csv(data)
        lines = csv.split("\n")
        
        assert len(lines) == 3  # header + 2 rows
        assert "name,value" in lines[0]


# ============================================================
# ALERTS MODULE TESTS
# ============================================================

class TestAlertsModule:
    """Tests for alerts module"""
    
    def test_alert_rule_evaluate_gt(self):
        """Test greater than evaluation"""
        from modules.alerts import AlertRule, ComparisonOperator, AlertSeverity
        
        rule = AlertRule(
            id="test",
            name="Test Rule",
            metric="value",
            operator=ComparisonOperator.GT,
            threshold=100.0,
            severity=AlertSeverity.WARNING,
        )
        
        assert rule.evaluate(150.0) == True
        assert rule.evaluate(100.0) == False
        assert rule.evaluate(50.0) == False
    
    def test_alert_rule_evaluate_lt(self):
        """Test less than evaluation"""
        from modules.alerts import AlertRule, ComparisonOperator, AlertSeverity
        
        rule = AlertRule(
            id="test",
            name="Test Rule",
            metric="value",
            operator=ComparisonOperator.LT,
            threshold=100.0,
            severity=AlertSeverity.WARNING,
        )
        
        assert rule.evaluate(50.0) == True
        assert rule.evaluate(100.0) == False
        assert rule.evaluate(150.0) == False
    
    def test_check_threshold(self):
        """Test threshold checking"""
        from modules.alerts import AlertEngine
        
        result = AlertEngine.check_threshold(
            metric="budget",
            value=150000,
            operator="gt",
            threshold=100000
        )
        
        assert result["triggered"] == True
        assert "exceeded" in result["message"]
    
    def test_detect_anomaly(self):
        """Test anomaly detection"""
        from modules.alerts import AlertEngine
        
        result = AlertEngine.detect_anomaly(
            values=[100.0, 102.0, 98.0, 101.0, 99.0],
            current=150.0,
            std_multiplier=2.0
        )
        
        assert result["is_anomaly"] == True
        assert result["current_value"] == 150.0
    
    def test_detect_normal_value(self):
        """Test normal value detection"""
        from modules.alerts import AlertEngine
        
        result = AlertEngine.detect_anomaly(
            values=[100.0, 102.0, 98.0, 101.0, 99.0],
            current=100.0,
            std_multiplier=2.0
        )
        
        assert result["is_anomaly"] == False


# ============================================================
# VOICE MODULE TESTS
# ============================================================

class TestVoiceModule:
    """Tests for voice module"""
    
    def test_parse_calculate_command_pl(self):
        """Test Polish calculate command parsing"""
        from modules.voice import VoiceCommandParser
        
        command = VoiceCommandParser.parse("oblicz sumę sprzedaży")
        
        assert command.intent == "calculate"
        assert command.dsl is not None
        assert "metrics.sum" in command.dsl
    
    def test_parse_load_command_pl(self):
        """Test Polish load command parsing"""
        from modules.voice import VoiceCommandParser
        
        command = VoiceCommandParser.parse("załaduj dane sales.csv")
        
        assert command.intent == "load_data"
        assert command.dsl is not None
        assert "data.load" in command.dsl
    
    def test_parse_report_command_pl(self):
        """Test Polish report command parsing"""
        from modules.voice import VoiceCommandParser
        
        command = VoiceCommandParser.parse("wygeneruj raport miesięczny")
        
        assert command.intent == "report"
        assert command.dsl is not None
        assert "report.generate" in command.dsl
    
    def test_parse_unknown_command(self):
        """Test unknown command handling"""
        from modules.voice import VoiceCommandParser
        
        command = VoiceCommandParser.parse("random text that doesn't match")
        
        assert command.intent == "unknown"
        assert command.dsl is None
        assert command.confidence == 0.0
    
    def test_parse_forecast_command(self):
        """Test forecast command parsing"""
        from modules.voice import VoiceCommandParser
        
        command = VoiceCommandParser.parse("prognozuj sprzedaż na 30 dni")
        
        assert command.intent == "forecast"
        assert command.dsl is not None
        assert "forecast.predict" in command.dsl
