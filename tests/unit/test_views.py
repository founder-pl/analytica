"""
Tests for DSL View Atoms
========================

Tests for view.chart, view.table, view.card, view.kpi, etc.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from dsl.core.parser import DSLParser, PipelineExecutor, AtomRegistry, PipelineContext
from dsl.atoms import implementations


class TestViewChart:
    """Tests for view.chart atom"""
    
    def test_chart_basic(self):
        """Test basic chart creation"""
        ctx = PipelineContext()
        ctx.set_data([
            {"month": "Jan", "sales": 100},
            {"month": "Feb", "sales": 150},
            {"month": "Mar", "sales": 200},
        ])
        
        result = implementations.view_chart(ctx, type="bar", x="month", y="sales", title="Sales Chart")
        
        assert "views" in result
        assert len(result["views"]) == 1
        assert result["views"][0]["type"] == "chart"
        assert result["views"][0]["chart_type"] == "bar"
        assert result["views"][0]["x_field"] == "month"
        assert result["views"][0]["y_field"] == "sales"
        assert result["views"][0]["title"] == "Sales Chart"
    
    def test_chart_line(self):
        """Test line chart"""
        ctx = PipelineContext()
        ctx.set_data([1, 2, 3, 4, 5])
        
        result = implementations.view_chart(ctx, type="line", title="Trend")
        
        assert result["views"][0]["chart_type"] == "line"
    
    def test_chart_pie(self):
        """Test pie chart"""
        ctx = PipelineContext()
        ctx.set_data({"a": 30, "b": 50, "c": 20})
        
        result = implementations.view_chart(ctx, type="pie")
        
        assert result["views"][0]["chart_type"] == "pie"
    
    def test_chart_with_series(self):
        """Test chart with multiple series"""
        ctx = PipelineContext()
        ctx.set_data([
            {"month": "Jan", "sales": 100, "costs": 80},
            {"month": "Feb", "sales": 150, "costs": 100},
        ])
        
        result = implementations.view_chart(ctx, type="bar", x="month", series=["sales", "costs"])
        
        assert result["views"][0]["series"] == ["sales", "costs"]


class TestViewTable:
    """Tests for view.table atom"""
    
    def test_table_basic(self):
        """Test basic table creation"""
        ctx = PipelineContext()
        ctx.set_data([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ])
        
        result = implementations.view_table(ctx, columns=["name", "age"], title="Users")
        
        assert "views" in result
        assert len(result["views"]) == 1
        assert result["views"][0]["type"] == "table"
        assert result["views"][0]["title"] == "Users"
        assert len(result["views"][0]["columns"]) == 2
    
    def test_table_auto_columns(self):
        """Test table auto-detects columns from data"""
        ctx = PipelineContext()
        ctx.set_data([
            {"id": 1, "name": "Test", "value": 100},
        ])
        
        result = implementations.view_table(ctx)
        
        assert len(result["views"][0]["columns"]) == 3
        assert result["views"][0]["columns"][0]["field"] == "id"
    
    def test_table_with_options(self):
        """Test table with sorting and pagination options"""
        ctx = PipelineContext()
        ctx.set_data([{"x": 1}])
        
        result = implementations.view_table(ctx, sortable=True, paginate=True, page_size=20)
        
        assert result["views"][0]["sortable"] == True
        assert result["views"][0]["paginate"] == True
        assert result["views"][0]["page_size"] == 20


class TestViewCard:
    """Tests for view.card atom"""
    
    def test_card_basic(self):
        """Test basic card creation"""
        ctx = PipelineContext()
        ctx.set_data({"total": 12345, "change": 5.2})
        
        result = implementations.view_card(ctx, value="total", title="Total Sales", icon="📊")
        
        assert "views" in result
        assert result["views"][0]["type"] == "card"
        assert result["views"][0]["title"] == "Total Sales"
        assert result["views"][0]["value_field"] == "total"
        assert result["views"][0]["icon"] == "📊"
    
    def test_card_with_trend(self):
        """Test card with trend indicator"""
        ctx = PipelineContext()
        ctx.set_data({"value": 100, "trend": 10})
        
        result = implementations.view_card(ctx, value="value", trend="trend", style="success")
        
        assert result["views"][0]["trend_field"] == "trend"
        assert result["views"][0]["style"] == "success"
    
    def test_card_with_format(self):
        """Test card with value format"""
        ctx = PipelineContext()
        ctx.set_data({"amount": 1234.56})
        
        result = implementations.view_card(ctx, value="amount", format="currency")
        
        assert result["views"][0]["format"] == "currency"


class TestViewKPI:
    """Tests for view.kpi atom"""
    
    def test_kpi_basic(self):
        """Test basic KPI creation"""
        ctx = PipelineContext()
        ctx.set_data({"current": 75, "target": 100})
        
        result = implementations.view_kpi(ctx, value="current", target="target", title="Progress")
        
        assert "views" in result
        assert result["views"][0]["type"] == "kpi"
        assert result["views"][0]["value_field"] == "current"
        assert result["views"][0]["target_field"] == "target"
        assert result["views"][0]["title"] == "Progress"
    
    def test_kpi_with_progress(self):
        """Test KPI with progress bar"""
        ctx = PipelineContext()
        ctx.set_data({"value": 50})
        
        result = implementations.view_kpi(ctx, value="value", progress=True)
        
        assert result["views"][0]["show_progress"] == True


class TestViewGrid:
    """Tests for view.grid atom"""
    
    def test_grid_basic(self):
        """Test basic grid creation"""
        ctx = PipelineContext()
        ctx.set_data({"test": 1})
        
        result = implementations.view_grid(ctx, columns=3, gap=20)
        
        assert "views" in result
        assert result["views"][0]["type"] == "grid"
        assert result["views"][0]["columns"] == 3
        assert result["views"][0]["gap"] == 20


class TestViewDashboard:
    """Tests for view.dashboard atom"""
    
    def test_dashboard_basic(self):
        """Test basic dashboard creation"""
        ctx = PipelineContext()
        ctx.set_data({"metric": 100})
        
        result = implementations.view_dashboard(ctx, layout="grid", title="My Dashboard")
        
        assert "views" in result
        assert result["views"][0]["type"] == "dashboard"
        assert result["views"][0]["layout"] == "grid"
        assert result["views"][0]["title"] == "My Dashboard"
    
    def test_dashboard_with_refresh(self):
        """Test dashboard with auto-refresh"""
        ctx = PipelineContext()
        ctx.set_data({})
        
        result = implementations.view_dashboard(ctx, refresh=30)
        
        assert result["views"][0]["refresh_interval"] == 30


class TestViewText:
    """Tests for view.text atom"""
    
    def test_text_basic(self):
        """Test basic text view"""
        ctx = PipelineContext()
        ctx.set_data(None)
        
        result = implementations.view_text(ctx, content="Hello World", title="Message")
        
        assert "views" in result
        assert result["views"][0]["type"] == "text"
        assert result["views"][0]["content"] == "Hello World"
    
    def test_text_markdown(self):
        """Test markdown text"""
        ctx = PipelineContext()
        ctx.set_data(None)
        
        result = implementations.view_text(ctx, content="**Bold** text", format="markdown")
        
        assert result["views"][0]["format"] == "markdown"


class TestViewList:
    """Tests for view.list atom"""
    
    def test_list_basic(self):
        """Test basic list view"""
        ctx = PipelineContext()
        ctx.set_data([
            {"name": "Item 1", "desc": "Description 1"},
            {"name": "Item 2", "desc": "Description 2"},
        ])
        
        result = implementations.view_list(ctx, primary="name", secondary="desc")
        
        assert "views" in result
        assert result["views"][0]["type"] == "list"
        assert result["views"][0]["primary_field"] == "name"
        assert result["views"][0]["secondary_field"] == "desc"


class TestMultipleViews:
    """Tests for multiple views in single pipeline"""
    
    def test_chain_multiple_views(self):
        """Test chaining multiple view atoms"""
        ctx = PipelineContext()
        data = [{"x": 1, "y": 10}, {"x": 2, "y": 20}]
        ctx.set_data(data)
        
        # First view
        result1 = implementations.view_chart(ctx, type="bar", x="x", y="y")
        
        # Update context with result containing first view
        ctx.set_data(result1)
        
        # Second view - should append to existing views
        result2 = implementations.view_table(ctx, columns=["x", "y"])
        
        assert "views" in result2
        assert len(result2["views"]) == 2
        assert result2["views"][0]["type"] == "chart"
        assert result2["views"][1]["type"] == "table"
    
    def test_view_preserves_data(self):
        """Test that view atoms preserve original data"""
        ctx = PipelineContext()
        original_data = [{"a": 1}, {"a": 2}]
        ctx.set_data(original_data)
        
        result = implementations.view_table(ctx)
        
        assert result["data"] == original_data


class TestViewDSLPipeline:
    """Tests for view atoms in DSL pipeline execution"""
    
    def test_execute_view_pipeline(self):
        """Test executing a pipeline with view atoms"""
        parser = DSLParser()
        
        # Create context with input data
        ctx = PipelineContext()
        input_data = [
            {"name": "A", "value": 10},
            {"name": "B", "value": 20},
        ]
        ctx.set_data(input_data)
        
        executor = PipelineExecutor(ctx)
        
        dsl = '''
        data.from_input()
        | view.chart(type="bar", x="name", y="value", title="Test Chart")
        '''
        
        pipeline = parser.parse(dsl)
        result_ctx = executor.execute(pipeline)
        
        result = result_ctx.get_data()
        assert "views" in result
        assert result["views"][0]["type"] == "chart"
    
    def test_execute_table_pipeline(self):
        """Test executing a pipeline with table view"""
        parser = DSLParser()
        
        ctx = PipelineContext()
        input_data = [{"id": 1, "name": "Test"}]
        ctx.set_data(input_data)
        
        executor = PipelineExecutor(ctx)
        
        dsl = '''
        data.from_input()
        | view.table(title="Data Table")
        '''
        
        pipeline = parser.parse(dsl)
        result_ctx = executor.execute(pipeline)
        
        result = result_ctx.get_data()
        assert "views" in result
        assert result["views"][0]["type"] == "table"
    
    def test_execute_card_pipeline(self):
        """Test executing a pipeline with card view"""
        parser = DSLParser()
        
        ctx = PipelineContext()
        input_data = {"total": 12345}
        ctx.set_data(input_data)
        
        executor = PipelineExecutor(ctx)
        
        dsl = '''
        data.from_input()
        | view.card(value="total", title="Total", icon="💰")
        '''
        
        pipeline = parser.parse(dsl)
        result_ctx = executor.execute(pipeline)
        
        result = result_ctx.get_data()
        assert "views" in result
        assert result["views"][0]["type"] == "card"
        assert result["views"][0]["icon"] == "💰"


class TestViewAtomRegistration:
    """Tests for view atom registration"""
    
    def test_view_atoms_registered(self):
        """Test that all view atoms are registered"""
        # Check that view atoms can be retrieved
        chart_atom = AtomRegistry.get("view", "chart")
        table_atom = AtomRegistry.get("view", "table")
        card_atom = AtomRegistry.get("view", "card")
        kpi_atom = AtomRegistry.get("view", "kpi")
        grid_atom = AtomRegistry.get("view", "grid")
        dashboard_atom = AtomRegistry.get("view", "dashboard")
        text_atom = AtomRegistry.get("view", "text")
        list_atom = AtomRegistry.get("view", "list")
        
        assert chart_atom is not None
        assert table_atom is not None
        assert card_atom is not None
        assert kpi_atom is not None
        assert grid_atom is not None
        assert dashboard_atom is not None
        assert text_atom is not None
        assert list_atom is not None
