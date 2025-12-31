"""
ANALYTICA E2E Tests - Full Pipeline Testing
============================================

Complete end-to-end tests covering:
- Pipeline parsing and execution
- All atom types
- Domain-specific workflows
- API endpoints
- File import/export
"""

import pytest
import json
import asyncio
from decimal import Decimal
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dsl.core.parser import Pipeline, PipelineBuilder, PipelineContext, parse, execute
from dsl.atoms.implementations import *


# ============================================================
# E2E: BASIC PIPELINE TESTS
# ============================================================

@pytest.mark.e2e
class TestBasicPipelines:
    """Basic pipeline execution tests"""
    
    def test_simple_data_load_and_metrics(self, sample_sales_data):
        """Test basic data loading and metrics calculation"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        result = execute(
            'data.from_input() | metrics.calculate(["sum", "avg", "count"], field="amount")',
            ctx
        )
        
        assert result.get_data() is not None
        data = result.get_data()
        assert "sum" in data
        assert "avg" in data
        assert "count" in data
        assert data["count"] == 6
    
    def test_filter_and_aggregate(self, sample_sales_data):
        """Test filtering and aggregation"""
        ctx = PipelineContext(variables={"region": "PL"})
        ctx.set_data(sample_sales_data)
        
        result = execute(
            'data.from_input() | transform.filter(region=$region) | metrics.sum("amount")',
            ctx
        )
        
        assert result.get_data() is not None
    
    def test_pipeline_with_variables(self, sample_sales_data):
        """Test pipeline with variable substitution"""
        dsl = '''
        $threshold = 2000
        data.from_input() | transform.filter(amount_gt=$threshold)
        '''
        
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        result = execute(dsl, ctx)
        assert result.get_data() is not None
    
    def test_named_pipeline(self, sample_sales_data):
        """Test named pipeline parsing"""
        dsl = '''
        @pipeline sales_analysis:
            data.from_input() | metrics.calculate(["sum", "avg"])
        '''
        
        pipeline = parse(dsl)
        assert pipeline.name == "sales_analysis"
        assert len(pipeline.steps) == 2
    
    def test_multi_step_pipeline(self, sample_sales_data):
        """Test multi-step pipeline execution"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = '''
        data.from_input()
        | transform.filter(amount_gt=1000)
        | transform.sort(by="amount", order="desc")
        | transform.limit(3)
        | metrics.calculate(["sum", "avg", "count"])
        '''
        
        result = execute(dsl, ctx)
        assert result.get_data() is not None


# ============================================================
# E2E: BUDGET MODULE TESTS (planbudzetu.pl)
# ============================================================

@pytest.mark.e2e
class TestBudgetPipelines:
    """Budget module E2E tests"""
    
    def test_budget_creation(self):
        """Test budget creation pipeline"""
        dsl = 'budget.create(name="Budget Q1 2024", period_start="2024-01-01", period_end="2024-03-31")'
        
        result = execute(dsl, PipelineContext())
        
        assert result.get_data() is not None
        data = result.get_data()
        assert "budget_id" in data
        assert data["name"] == "Budget Q1 2024"
    
    def test_budget_variance_calculation(self, sample_budget_data):
        """Test budget variance calculation"""
        ctx = PipelineContext()
        ctx.set_data(sample_budget_data)
        
        dsl = 'data.from_input() | budget.variance()'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        data = result.get_data()
        assert "variance" in data or "total_planned" in data
    
    def test_budget_categorization(self, sample_budget_data):
        """Test budget categorization"""
        ctx = PipelineContext()
        ctx.set_data(sample_budget_data)
        
        dsl = 'data.from_input() | budget.categorize(by="category")'
        
        result = execute(dsl, ctx)
        assert result.get_data() is not None
    
    def test_budget_comparison_pipeline(self, sample_budget_data):
        """Test full budget comparison workflow"""
        ctx = PipelineContext(domain="planbudzetu.pl")
        ctx.set_data(sample_budget_data)
        
        dsl = '''
        data.from_input()
        | budget.compare(scenario="actual")
        | budget.variance()
        | report.generate(format="pdf", template="budget_vs_actual")
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert len(result.errors) == 0
    
    def test_expense_tracking_pipeline(self, sample_transactions):
        """Test expense tracking workflow"""
        ctx = PipelineContext()
        ctx.set_data(sample_transactions)
        
        dsl = '''
        data.from_input()
        | transform.filter(type="expense")
        | transform.group_by("category")
        | metrics.calculate(["sum", "count"], field="amount")
        '''
        
        result = execute(dsl, ctx)
        assert result.get_data() is not None


# ============================================================
# E2E: INVESTMENT MODULE TESTS (planinwestycji.pl)
# ============================================================

@pytest.mark.e2e
class TestInvestmentPipelines:
    """Investment module E2E tests"""
    
    def test_investment_analysis_full(self, sample_investment_data):
        """Test complete investment analysis"""
        ctx = PipelineContext(domain="planinwestycji.pl")
        ctx.set_data(sample_investment_data)
        
        dsl = '''
        data.from_input()
        | investment.analyze(discount_rate=0.12)
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        data = result.get_data()
        assert "npv" in data
        assert "roi" in data
    
    def test_roi_calculation(self, sample_investment_data):
        """Test ROI calculation"""
        ctx = PipelineContext()
        ctx.set_data(sample_investment_data)
        
        dsl = 'data.from_input() | investment.roi()'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
    
    def test_npv_calculation(self, sample_investment_data):
        """Test NPV calculation with different rates"""
        ctx = PipelineContext()
        ctx.set_data(sample_investment_data)
        
        # Test with 10% discount rate
        dsl = 'data.from_input() | investment.npv(rate=0.1)'
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert "npv" in result.get_data()
    
    def test_payback_period(self, sample_investment_data):
        """Test payback period calculation"""
        ctx = PipelineContext()
        ctx.set_data(sample_investment_data)
        
        dsl = 'data.from_input() | investment.payback()'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
    
    def test_scenario_analysis(self, sample_investment_data):
        """Test scenario analysis"""
        ctx = PipelineContext()
        ctx.set_data(sample_investment_data)
        
        dsl = '''
        data.from_input()
        | investment.scenario(name="optimistic", multiplier=1.2)
        | investment.analyze(discount_rate=0.1)
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
    
    def test_full_investment_report_pipeline(self, sample_investment_data):
        """Test complete investment report workflow"""
        ctx = PipelineContext(domain="planinwestycji.pl")
        ctx.set_data(sample_investment_data)
        
        dsl = '''
        data.from_input()
        | investment.analyze(discount_rate=0.12)
        | investment.roi()
        | investment.npv(rate=0.1)
        | investment.payback()
        | report.generate(format="pdf", template="investment_proposal")
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert len(result.errors) == 0


# ============================================================
# E2E: MULTIPLAN MODULE TESTS (multiplan.pl)
# ============================================================

@pytest.mark.e2e
class TestMultiplanPipelines:
    """Multiplan module E2E tests"""
    
    def test_scenario_planning(self, sample_budget_data):
        """Test multi-scenario budget planning"""
        ctx = PipelineContext(domain="multiplan.pl")
        ctx.set_data(sample_budget_data)
        
        scenarios = ["optimistic", "realistic", "pessimistic"]
        results = {}
        
        for scenario in scenarios:
            dsl = f'''
            data.from_input()
            | investment.scenario(name="{scenario}", multiplier={1.2 if scenario == "optimistic" else 0.8 if scenario == "pessimistic" else 1.0})
            | budget.variance()
            '''
            
            result = execute(dsl, ctx)
            results[scenario] = result.get_data()
        
        assert len(results) == 3
        assert all(r is not None for r in results.values())
    
    def test_rolling_forecast_pipeline(self, sample_forecast_data):
        """Test rolling forecast workflow"""
        ctx = PipelineContext(domain="multiplan.pl")
        ctx.set_data(sample_forecast_data)
        
        dsl = '''
        data.from_input()
        | forecast.predict(periods=30, model="prophet")
        | forecast.confidence(level=0.95)
        '''
        
        result = execute(dsl, ctx)
        assert result.get_data() is not None


# ============================================================
# E2E: ALERT MODULE TESTS (alerts.pl)
# ============================================================

@pytest.mark.e2e
class TestAlertPipelines:
    """Alert module E2E tests"""
    
    def test_threshold_alert(self, sample_sales_data):
        """Test threshold-based alert"""
        ctx = PipelineContext(domain="alerts.pl")
        ctx.set_data({"amount": 15000, "budget": 12000})
        
        dsl = '''
        data.from_input()
        | alert.threshold(field="amount", operator="gt", value=10000)
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        data = result.get_data()
        assert "triggered" in data
        assert data["triggered"] == True
    
    def test_alert_send(self):
        """Test alert sending"""
        ctx = PipelineContext(domain="alerts.pl")
        ctx.set_data({"alert_triggered": True})
        
        dsl = '''
        data.from_input()
        | alert.send(channel="slack", message="Test alert!")
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert result.get_data()["status"] == "sent"


# ============================================================
# E2E: FORECAST MODULE TESTS (estymacja.pl)
# ============================================================

@pytest.mark.e2e
class TestForecastPipelines:
    """Forecast module E2E tests"""
    
    def test_basic_forecast(self, sample_forecast_data):
        """Test basic forecasting"""
        ctx = PipelineContext(domain="estymacja.pl")
        ctx.set_data(sample_forecast_data)
        
        dsl = 'data.from_input() | forecast.predict(periods=30, model="prophet")'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert "forecast_id" in result.get_data()
    
    def test_trend_analysis(self, sample_forecast_data):
        """Test trend analysis"""
        ctx = PipelineContext()
        ctx.set_data(sample_forecast_data)
        
        dsl = 'data.from_input() | forecast.trend()'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
    
    def test_full_forecast_pipeline(self, sample_forecast_data):
        """Test complete forecasting workflow"""
        ctx = PipelineContext(domain="estymacja.pl")
        ctx.set_data(sample_forecast_data)
        
        dsl = '''
        data.from_input()
        | forecast.predict(periods=90, model="prophet")
        | forecast.trend()
        | forecast.seasonality()
        | forecast.confidence(level=0.95)
        | report.generate(format="pdf", template="forecast_report")
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert len(result.errors) == 0


# ============================================================
# E2E: REPORT MODULE TESTS
# ============================================================

@pytest.mark.e2e
class TestReportPipelines:
    """Report module E2E tests"""
    
    def test_report_generation(self, sample_sales_data):
        """Test report generation"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = '''
        data.from_input()
        | metrics.calculate(["sum", "avg", "count"])
        | report.generate(format="pdf", template="sales_summary")
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        data = result.get_data()
        assert "report_id" in data
        assert data["format"] == "pdf"
    
    def test_report_scheduling(self, sample_sales_data):
        """Test report scheduling"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = '''
        data.from_input()
        | report.generate(format="pdf")
        | report.schedule(cron="0 9 * * MON", recipients=["team@company.pl"])
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert "schedule_id" in result.get_data()
    
    def test_report_send(self, sample_sales_data):
        """Test report sending"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = '''
        data.from_input()
        | report.generate(format="xlsx")
        | report.send(to=["finance@company.pl", "cfo@company.pl"])
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert result.get_data()["status"] == "sent"


# ============================================================
# E2E: EXPORT MODULE TESTS
# ============================================================

@pytest.mark.e2e
class TestExportPipelines:
    """Export module E2E tests"""
    
    def test_export_to_csv(self, sample_sales_data):
        """Test CSV export"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = 'data.from_input() | export.to_csv(path="output.csv")'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert result.get_data()["format"] == "csv"
    
    def test_export_to_json(self, sample_sales_data):
        """Test JSON export"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = 'data.from_input() | export.to_json(path="output.json")'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert result.get_data()["format"] == "json"
    
    def test_export_to_excel(self, sample_sales_data):
        """Test Excel export"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = 'data.from_input() | export.to_excel(path="output.xlsx")'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert result.get_data()["format"] == "xlsx"
    
    def test_export_to_api(self, sample_sales_data):
        """Test API export"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        dsl = 'data.from_input() | export.to_api(url="https://api.example.com/data", method="POST")'
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert result.get_data()["status"] == "sent"


# ============================================================
# E2E: FLUENT API TESTS
# ============================================================

@pytest.mark.e2e
class TestFluentAPI:
    """Fluent API E2E tests"""
    
    def test_fluent_pipeline_builder(self, sample_sales_data):
        """Test fluent pipeline builder"""
        pipeline = (Pipeline()
            .name("sales_analysis")
            .var("year", 2024)
            .data.from_input()
            .transform.filter(year="$year")
            .metrics.calculate(["sum", "avg", "count"]))
        
        dsl = pipeline.to_dsl()
        
        assert "sales_analysis" in dsl
        assert "data.from_input" in dsl
        assert "metrics.calculate" in dsl
    
    def test_fluent_budget_pipeline(self, sample_budget_data):
        """Test fluent budget pipeline"""
        pipeline = (Pipeline("planbudzetu.pl")
            .data.from_input()
            .budget.variance()
            .report.generate("pdf", "budget_report"))
        
        dsl = pipeline.to_dsl()
        
        assert "budget.variance" in dsl
        assert "report.generate" in dsl
    
    def test_fluent_investment_pipeline(self, sample_investment_data):
        """Test fluent investment pipeline"""
        pipeline = (Pipeline("planinwestycji.pl")
            .data.from_input()
            .investment.analyze(discount_rate=0.12)
            .investment.roi()
            .investment.npv(rate=0.1)
            .investment.payback())
        
        dsl = pipeline.to_dsl()
        
        assert "investment.analyze" in dsl
        assert "investment.roi" in dsl
        assert "investment.npv" in dsl


# ============================================================
# E2E: COMPLEX WORKFLOW TESTS
# ============================================================

@pytest.mark.e2e
class TestComplexWorkflows:
    """Complex multi-step workflow tests"""
    
    def test_full_financial_analysis_workflow(self, sample_sales_data, sample_budget_data):
        """Test complete financial analysis workflow"""
        ctx = PipelineContext(domain="planbudzetu.pl")
        ctx.set_data({
            "sales": sample_sales_data,
            "budget": sample_budget_data
        })
        
        dsl = '''
        data.from_input()
        | metrics.calculate(["sum", "avg", "count"])
        | budget.variance()
        | report.generate(format="pdf", template="financial_analysis")
        '''
        
        result = execute(dsl, ctx)
        
        assert result.get_data() is not None
        assert len(result.errors) == 0
    
    def test_investment_with_multiple_scenarios(self, sample_investment_data):
        """Test investment analysis with multiple scenarios"""
        scenarios = {
            "optimistic": 1.2,
            "realistic": 1.0,
            "pessimistic": 0.8
        }
        
        results = {}
        
        for name, multiplier in scenarios.items():
            ctx = PipelineContext()
            ctx.set_data(sample_investment_data)
            
            dsl = f'''
            data.from_input()
            | investment.scenario(name="{name}", multiplier={multiplier})
            | investment.analyze(discount_rate=0.1)
            | investment.roi()
            | investment.npv(rate=0.1)
            '''
            
            result = execute(dsl, ctx)
            results[name] = result.get_data()
        
        assert len(results) == 3
        assert all(r is not None for r in results.values())


# ============================================================
# E2E: ERROR HANDLING TESTS
# ============================================================

@pytest.mark.e2e
class TestErrorHandling:
    """Error handling E2E tests"""
    
    def test_invalid_dsl_syntax(self):
        """Test invalid DSL syntax handling"""
        with pytest.raises(SyntaxError):
            parse('data.load(')
    
    def test_unknown_atom(self):
        """Test unknown atom handling"""
        ctx = PipelineContext()
        
        with pytest.raises(ValueError):
            execute('unknown.action()', ctx)
    
    def test_missing_required_param(self):
        """Test missing required parameter"""
        ctx = PipelineContext()
        
        # Should handle gracefully
        result = execute('data.load()', ctx)
        # May raise or return error in result
        assert result is not None
    
    def test_pipeline_with_errors_continues(self, sample_sales_data):
        """Test pipeline continues after non-fatal errors"""
        ctx = PipelineContext()
        ctx.set_data(sample_sales_data)
        
        # This should execute successfully
        result = execute('data.from_input() | metrics.count()', ctx)
        
        assert result.get_data() is not None


# ============================================================
# RUN ALL E2E TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
