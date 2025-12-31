"""
ANALYTICA Integration Tests - API
=================================

Integration tests for REST API endpoints
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# ============================================================
# API CLIENT FIXTURE
# ============================================================

@pytest.fixture
def api_base_url():
    """Base URL for API tests"""
    return "http://localhost:8080"


@pytest.fixture
def api_client(api_base_url):
    """HTTP client for API tests"""
    with httpx.Client(base_url=api_base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
async def async_api_client(api_base_url):
    """Async HTTP client for API tests"""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


# ============================================================
# PIPELINE API TESTS
# ============================================================

@pytest.mark.integration
class TestPipelineExecuteAPI:
    """Tests for /api/v1/pipeline/execute endpoint"""
    
    def test_execute_simple_pipeline(self, api_client):
        """Test executing a simple pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={
                "dsl": 'data.from_input() | metrics.count()',
                "input_data": [1, 2, 3, 4, 5]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "execution_id" in data
    
    def test_execute_with_variables(self, api_client):
        """Test executing pipeline with variables"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={
                "dsl": 'data.from_input() | transform.filter(year=$year)',
                "variables": {"year": 2024},
                "input_data": [
                    {"year": 2023, "amount": 100},
                    {"year": 2024, "amount": 200}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_execute_budget_pipeline(self, api_client):
        """Test executing budget pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={
                "dsl": 'budget.create(name="Test Budget 2024")',
                "domain": "planbudzetu.pl"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_execute_investment_pipeline(self, api_client):
        """Test executing investment analysis pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={
                "dsl": '''
                    data.from_input() 
                    | investment.analyze(discount_rate=0.12)
                    | investment.roi()
                ''',
                "domain": "planinwestycji.pl",
                "input_data": {
                    "initial_investment": 500000,
                    "cash_flows": [150000, 180000, 200000, 220000, 250000]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_execute_invalid_dsl(self, api_client):
        """Test error handling for invalid DSL"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "invalid.syntax((("}
        )
        
        assert response.status_code == 200  # API returns 200 with error in body
        data = response.json()
        assert data["status"] == "error"
        assert len(data["errors"]) > 0
    
    def test_execute_with_report_generation(self, api_client):
        """Test pipeline with report generation"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={
                "dsl": '''
                    data.from_input()
                    | metrics.calculate(["sum", "avg"])
                    | report.generate(format="pdf", template="summary")
                ''',
                "input_data": [
                    {"amount": 100},
                    {"amount": 200},
                    {"amount": 300}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


@pytest.mark.integration
class TestPipelineParseAPI:
    """Tests for /api/v1/pipeline/parse endpoint"""
    
    def test_parse_simple_pipeline(self, api_client):
        """Test parsing simple pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/parse",
            json={"dsl": 'data.load("sales.csv") | metrics.sum("amount")'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "steps" in data
        assert len(data["steps"]) == 2
    
    def test_parse_named_pipeline(self, api_client):
        """Test parsing named pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/parse",
            json={
                "dsl": '''
                    @pipeline my_analysis:
                        $year = 2024
                        data.load("sales") | metrics.sum("amount")
                '''
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "my_analysis"
        assert "year" in data["variables"]


@pytest.mark.integration
class TestPipelineValidateAPI:
    """Tests for /api/v1/pipeline/validate endpoint"""
    
    def test_validate_valid_pipeline(self, api_client):
        """Test validating valid pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/validate",
            json={"dsl": 'data.load("sales") | metrics.sum("amount")'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert len(data["errors"]) == 0
    
    def test_validate_invalid_pipeline(self, api_client):
        """Test validating invalid pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/validate",
            json={"dsl": 'unknown.atom()'}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return warnings about unknown atom
        assert "errors" in data or "warnings" in data


# ============================================================
# ATOMS API TESTS
# ============================================================

@pytest.mark.integration
class TestAtomsAPI:
    """Tests for /api/v1/atoms endpoints"""
    
    def test_list_all_atoms(self, api_client):
        """Test listing all available atoms"""
        response = api_client.get("/api/v1/atoms")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have main atom types
        assert "data" in data
        assert "transform" in data
        assert "metrics" in data
        assert "budget" in data
        assert "investment" in data
    
    def test_list_atom_actions(self, api_client):
        """Test listing actions for specific atom type"""
        response = api_client.get("/api/v1/atoms/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have metric actions
        assert "sum" in data or "calculate" in data
    
    def test_execute_single_atom(self, api_client):
        """Test executing a single atom"""
        response = api_client.post(
            "/api/v1/atoms/metrics/count",
            json={
                "input_data": [1, 2, 3, 4, 5]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


# ============================================================
# STORED PIPELINES API TESTS
# ============================================================

@pytest.mark.integration
class TestStoredPipelinesAPI:
    """Tests for stored pipelines endpoints"""
    
    def test_create_and_list_pipeline(self, api_client):
        """Test creating and listing pipelines"""
        # Create pipeline
        create_response = api_client.post(
            "/api/v1/pipelines",
            json={
                "name": "test_pipeline",
                "dsl": 'data.load("test") | metrics.count()',
                "description": "Test pipeline",
                "tags": ["test", "unit"]
            }
        )
        
        assert create_response.status_code == 200
        created = create_response.json()
        assert "id" in created
        
        # List pipelines
        list_response = api_client.get("/api/v1/pipelines")
        
        assert list_response.status_code == 200
        pipelines = list_response.json()
        assert len(pipelines) > 0
    
    def test_run_stored_pipeline(self, api_client):
        """Test running a stored pipeline"""
        # First create a pipeline
        create_response = api_client.post(
            "/api/v1/pipelines",
            json={
                "name": "runnable_pipeline",
                "dsl": 'data.from_input() | metrics.count()'
            }
        )
        
        pipeline_id = create_response.json()["id"]
        
        # Run it
        run_response = api_client.post(
            f"/api/v1/pipelines/{pipeline_id}/run",
            json={
                "input_data": [1, 2, 3]
            }
        )
        
        assert run_response.status_code == 200
        data = run_response.json()
        assert data["status"] == "success"


# ============================================================
# HEALTH & UTILITY API TESTS
# ============================================================

@pytest.mark.integration
class TestUtilityAPI:
    """Tests for utility endpoints"""
    
    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, api_client):
        """Test root endpoint"""
        response = api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data


# ============================================================
# ASYNC TESTS
# ============================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncAPI:
    """Async API tests"""
    
    async def test_concurrent_pipeline_execution(self, async_api_client):
        """Test concurrent pipeline execution"""
        pipelines = [
            {"dsl": 'data.from_input() | metrics.count()', "input_data": [1, 2, 3]},
            {"dsl": 'data.from_input() | metrics.sum("value")', "input_data": [{"value": 10}]},
            {"dsl": 'budget.create(name="Test")'},
        ]
        
        async def execute_pipeline(pipeline_data):
            response = await async_api_client.post(
                "/api/v1/pipeline/execute",
                json=pipeline_data
            )
            return response.json()
        
        results = await asyncio.gather(
            *[execute_pipeline(p) for p in pipelines]
        )
        
        assert len(results) == 3
        assert all(r["status"] in ["success", "error"] for r in results)


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
