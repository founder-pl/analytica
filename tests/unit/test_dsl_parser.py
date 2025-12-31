"""
ANALYTICA Unit Tests - DSL Parser
=================================

Unit tests for the DSL tokenizer, parser, and pipeline builder
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dsl.core.parser import (
    DSLTokenizer, DSLParser, Pipeline, PipelineBuilder,
    PipelineDefinition, PipelineContext, Atom, AtomType,
    parse, execute
)
from dsl.atoms.implementations import *


# ============================================================
# TOKENIZER TESTS
# ============================================================

@pytest.mark.unit
class TestDSLTokenizer:
    """Tests for DSL tokenizer"""
    
    def test_tokenize_simple_atom(self):
        """Test tokenizing simple atom"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('data.load("file.csv")')
        
        # Should have: IDENTIFIER, DOT, IDENTIFIER, LPAREN, STRING, RPAREN
        assert len(tokens) >= 5
        assert tokens[0] == ('IDENTIFIER', 'data')
        assert tokens[1] == ('DOT', '.')
        assert tokens[2] == ('IDENTIFIER', 'load')
    
    def test_tokenize_pipe_operator(self):
        """Test tokenizing pipe operator"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('data.load("x") | metrics.sum("y")')
        
        # Should contain PIPE token
        token_types = [t[0] for t in tokens]
        assert 'PIPE' in token_types
    
    def test_tokenize_numbers(self):
        """Test tokenizing numbers"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('transform.filter(year=2024, amount=1500.50)')
        
        # Find number tokens
        numbers = [t for t in tokens if t[0] == 'NUMBER']
        assert len(numbers) == 2
        assert 2024 in [t[1] for t in numbers]
        assert 1500.50 in [t[1] for t in numbers]
    
    def test_tokenize_string_values(self):
        """Test tokenizing string values"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('data.load("sales.csv")')
        
        strings = [t for t in tokens if t[0] == 'STRING']
        assert len(strings) == 1
        assert strings[0][1] == 'sales.csv'
    
    def test_tokenize_variables(self):
        """Test tokenizing variables"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('$year = 2024')
        
        token_types = [t[0] for t in tokens]
        assert 'DOLLAR' in token_types
        assert 'EQUALS' in token_types
    
    def test_tokenize_array(self):
        """Test tokenizing array"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('metrics.calculate(["sum", "avg"])')
        
        token_types = [t[0] for t in tokens]
        assert 'LBRACKET' in token_types
        assert 'RBRACKET' in token_types
    
    def test_tokenize_boolean(self):
        """Test tokenizing booleans"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('transform.filter(active=true)')
        
        bools = [t for t in tokens if t[0] == 'BOOL']
        assert len(bools) == 1
        assert bools[0][1] == True
    
    def test_tokenize_ignores_comments(self):
        """Test that comments are ignored"""
        tokenizer = DSLTokenizer()
        tokens = tokenizer.tokenize('data.load("x") # This is a comment')
        
        # Comments should not appear in tokens
        assert all('comment' not in str(t).lower() for t in tokens)


# ============================================================
# PARSER TESTS
# ============================================================

@pytest.mark.unit
class TestDSLParser:
    """Tests for DSL parser"""
    
    def test_parse_simple_pipeline(self):
        """Test parsing simple pipeline"""
        dsl = 'data.load("sales.csv")'
        pipeline = parse(dsl)
        
        assert pipeline is not None
        assert len(pipeline.steps) == 1
        assert pipeline.steps[0].atom.type == AtomType.DATA
        assert pipeline.steps[0].atom.action == "load"
    
    def test_parse_piped_pipeline(self):
        """Test parsing piped pipeline"""
        dsl = 'data.load("sales") | metrics.sum("amount")'
        pipeline = parse(dsl)
        
        assert len(pipeline.steps) == 2
        assert pipeline.steps[0].atom.action == "load"
        assert pipeline.steps[1].atom.action == "sum"
    
    def test_parse_named_pipeline(self):
        """Test parsing named pipeline"""
        dsl = '''
        @pipeline my_analysis:
            data.load("sales") | metrics.sum("amount")
        '''
        pipeline = parse(dsl)
        
        assert pipeline.name == "my_analysis"
    
    def test_parse_with_variables(self):
        """Test parsing with variables"""
        dsl = '''
        $year = 2024
        data.load("sales") | transform.filter(year=$year)
        '''
        pipeline = parse(dsl)
        
        assert "year" in pipeline.variables
        assert pipeline.variables["year"] == 2024
    
    def test_parse_multiple_variables(self):
        """Test parsing multiple variables"""
        dsl = '''
        $year = 2024
        $threshold = 1000
        $format = "pdf"
        data.load("sales")
        '''
        pipeline = parse(dsl)
        
        assert len(pipeline.variables) == 3
        assert pipeline.variables["year"] == 2024
        assert pipeline.variables["threshold"] == 1000
        assert pipeline.variables["format"] == "pdf"
    
    def test_parse_array_parameter(self):
        """Test parsing array parameters"""
        dsl = 'metrics.calculate(["sum", "avg", "count"])'
        pipeline = parse(dsl)
        
        # Check that metrics param is a list
        params = pipeline.steps[0].atom.params
        # Should have array parameter
        assert any(isinstance(v, list) for v in params.values())
    
    def test_parse_named_parameters(self):
        """Test parsing named parameters"""
        dsl = 'transform.filter(year=2024, status="active")'
        pipeline = parse(dsl)
        
        params = pipeline.steps[0].atom.params
        assert params.get("year") == 2024
        assert params.get("status") == "active"
    
    def test_parse_complex_pipeline(self):
        """Test parsing complex multi-step pipeline"""
        dsl = '''
        @pipeline complex_analysis:
            $year = 2024
            data.load("sales")
            | transform.filter(year=$year)
            | transform.group_by("category")
            | metrics.calculate(["sum", "avg"])
            | report.generate(format="pdf")
        '''
        pipeline = parse(dsl)
        
        assert pipeline.name == "complex_analysis"
        assert len(pipeline.steps) == 5
        assert "year" in pipeline.variables
    
    def test_parse_invalid_syntax_raises_error(self):
        """Test that invalid syntax raises SyntaxError"""
        with pytest.raises(SyntaxError):
            parse('data.load(')  # Missing closing paren
    
    def test_parse_empty_string(self):
        """Test parsing empty string"""
        pipeline = parse('')
        assert len(pipeline.steps) == 0


# ============================================================
# PIPELINE BUILDER TESTS
# ============================================================

@pytest.mark.unit
class TestPipelineBuilder:
    """Tests for fluent pipeline builder"""
    
    def test_builder_data_load(self):
        """Test builder data.load()"""
        pipeline = (Pipeline()
            .data.load("sales.csv"))
        
        dsl = pipeline.to_dsl()
        assert "data.load" in dsl
        assert "sales.csv" in dsl
    
    def test_builder_transform_filter(self):
        """Test builder transform.filter()"""
        pipeline = (Pipeline()
            .data.load("sales")
            .transform.filter(year=2024))
        
        dsl = pipeline.to_dsl()
        assert "transform.filter" in dsl
    
    def test_builder_metrics(self):
        """Test builder metrics operations"""
        pipeline = (Pipeline()
            .data.load("sales")
            .metrics.sum("amount"))
        
        dsl = pipeline.to_dsl()
        assert "metrics.sum" in dsl
    
    def test_builder_with_variables(self):
        """Test builder with variables"""
        pipeline = (Pipeline()
            .var("year", 2024)
            .var("format", "pdf")
            .data.load("sales"))
        
        definition = pipeline.build()
        assert definition["variables"]["year"] == 2024
        assert definition["variables"]["format"] == "pdf"
    
    def test_builder_with_name(self):
        """Test builder with pipeline name"""
        pipeline = (Pipeline()
            .name("my_pipeline")
            .data.load("sales"))
        
        dsl = pipeline.to_dsl()
        assert "my_pipeline" in dsl
    
    def test_builder_chain_multiple_steps(self):
        """Test builder chaining multiple steps"""
        pipeline = (Pipeline()
            .data.load("sales")
            .transform.filter(year=2024)
            .transform.sort("amount", "desc")
            .transform.limit(10)
            .metrics.calculate(["sum", "avg"]))
        
        definition = pipeline.build()
        assert len(definition["steps"]) == 5
    
    def test_builder_budget_operations(self):
        """Test builder budget operations"""
        pipeline = (Pipeline("planbudzetu.pl")
            .budget.load("budget_2024")
            .budget.variance())
        
        dsl = pipeline.to_dsl()
        assert "budget.load" in dsl
        assert "budget.variance" in dsl
    
    def test_builder_investment_operations(self):
        """Test builder investment operations"""
        pipeline = (Pipeline("planinwestycji.pl")
            .investment.analyze(discount_rate=0.12)
            .investment.roi()
            .investment.npv(rate=0.1))
        
        dsl = pipeline.to_dsl()
        assert "investment.analyze" in dsl
        assert "investment.roi" in dsl
        assert "investment.npv" in dsl
    
    def test_builder_forecast_operations(self):
        """Test builder forecast operations"""
        pipeline = (Pipeline("estymacja.pl")
            .forecast.predict(periods=30, model="prophet")
            .forecast.confidence(level=0.95))
        
        dsl = pipeline.to_dsl()
        assert "forecast.predict" in dsl
        assert "forecast.confidence" in dsl
    
    def test_builder_export_operations(self):
        """Test builder export operations"""
        pipeline = (Pipeline()
            .data.load("sales")
            .export.to_csv("output.csv"))
        
        dsl = pipeline.to_dsl()
        assert "export.to_csv" in dsl
    
    def test_builder_to_json(self):
        """Test builder JSON serialization"""
        pipeline = (Pipeline()
            .name("test")
            .data.load("sales"))
        
        json_str = pipeline.to_json()
        assert '"name": "test"' in json_str
    
    def test_builder_to_dict(self):
        """Test builder dict conversion"""
        pipeline = (Pipeline()
            .name("test")
            .var("x", 1)
            .data.load("sales"))
        
        d = pipeline.build()
        assert d["name"] == "test"
        assert d["variables"]["x"] == 1
        assert len(d["steps"]) == 1


# ============================================================
# ATOM TESTS
# ============================================================

@pytest.mark.unit
class TestAtom:
    """Tests for Atom class"""
    
    def test_atom_creation(self):
        """Test atom creation"""
        atom = Atom(
            type=AtomType.DATA,
            action="load",
            params={"source": "file.csv"}
        )
        
        assert atom.type == AtomType.DATA
        assert atom.action == "load"
        assert atom.params["source"] == "file.csv"
    
    def test_atom_to_dsl(self):
        """Test atom DSL conversion"""
        atom = Atom(
            type=AtomType.METRICS,
            action="sum",
            params={"field": "amount"}
        )
        
        dsl = atom.to_dsl()
        assert "metrics.sum" in dsl
        assert "amount" in dsl
    
    def test_atom_to_dict(self):
        """Test atom dict conversion"""
        atom = Atom(
            type=AtomType.TRANSFORM,
            action="filter",
            params={"year": 2024}
        )
        
        d = atom.to_dict()
        assert d["type"] == "transform"
        assert d["action"] == "filter"
        assert d["params"]["year"] == 2024
    
    def test_atom_from_dict(self):
        """Test atom from dict"""
        d = {
            "type": "data",
            "action": "load",
            "params": {"source": "test.csv"}
        }
        
        atom = Atom.from_dict(d)
        assert atom.type == AtomType.DATA
        assert atom.action == "load"


# ============================================================
# PIPELINE CONTEXT TESTS
# ============================================================

@pytest.mark.unit
class TestPipelineContext:
    """Tests for PipelineContext"""
    
    def test_context_creation(self):
        """Test context creation"""
        ctx = PipelineContext(
            variables={"x": 1},
            domain="test.pl"
        )
        
        assert ctx.variables["x"] == 1
        assert ctx.domain == "test.pl"
    
    def test_context_set_get_data(self):
        """Test setting and getting data"""
        ctx = PipelineContext()
        ctx.set_data([1, 2, 3])
        
        assert ctx.get_data() == [1, 2, 3]
    
    def test_context_resolve_variable(self):
        """Test variable resolution"""
        ctx = PipelineContext(variables={"year": 2024})
        
        assert ctx.resolve_variable("$year") == 2024
        assert ctx.resolve_variable("plain") == "plain"
    
    def test_context_resolve_undefined_variable(self):
        """Test undefined variable raises error"""
        ctx = PipelineContext()
        
        with pytest.raises(ValueError):
            ctx.resolve_variable("$undefined")
    
    def test_context_resolve_params(self):
        """Test resolving all params"""
        ctx = PipelineContext(variables={"year": 2024, "name": "test"})
        
        params = {"year": "$year", "name": "$name", "static": 100}
        resolved = ctx.resolve_params(params)
        
        assert resolved["year"] == 2024
        assert resolved["name"] == "test"
        assert resolved["static"] == 100
    
    def test_context_logging(self):
        """Test context logging"""
        ctx = PipelineContext()
        
        ctx.log("Test message", "info")
        ctx.log("Warning!", "warning")
        
        assert len(ctx.logs) == 2
        assert ctx.logs[0]["message"] == "Test message"


# ============================================================
# PIPELINE DEFINITION TESTS
# ============================================================

@pytest.mark.unit
class TestPipelineDefinition:
    """Tests for PipelineDefinition"""
    
    def test_definition_to_dict(self):
        """Test definition dict conversion"""
        steps = [
            Atom(AtomType.DATA, "load", {"source": "x"}),
            Atom(AtomType.METRICS, "sum", {"field": "y"})
        ]
        
        # Create minimal PipelineStep objects
        from dsl.core.parser import PipelineStep
        pipeline_steps = [PipelineStep(atom=a) for a in steps]
        
        definition = PipelineDefinition(
            name="test",
            steps=pipeline_steps,
            variables={"v": 1}
        )
        
        d = definition.to_dict()
        assert d["name"] == "test"
        assert len(d["steps"]) == 2
        assert d["variables"]["v"] == 1
    
    def test_definition_to_yaml(self):
        """Test definition YAML conversion"""
        from dsl.core.parser import PipelineStep
        
        steps = [PipelineStep(atom=Atom(AtomType.DATA, "load", {}))]
        definition = PipelineDefinition(name="test", steps=steps)
        
        yaml_str = definition.to_yaml()
        assert "name: test" in yaml_str
    
    def test_definition_to_dsl(self):
        """Test definition DSL conversion"""
        from dsl.core.parser import PipelineStep
        
        steps = [
            PipelineStep(atom=Atom(AtomType.DATA, "load", {"source": "x"}))
        ]
        definition = PipelineDefinition(name="my_pipe", steps=steps)
        
        dsl = definition.to_dsl()
        assert "@pipeline my_pipe" in dsl
        assert "data.load" in dsl


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
