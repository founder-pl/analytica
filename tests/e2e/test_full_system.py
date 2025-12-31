"""
ANALYTICA E2E Tests - Full System Testing
==========================================

Complete end-to-end tests running against Docker environment:
- API health and endpoints
- DSL parsing and execution
- Pipeline workflows
- Deploy atoms
- URI launcher
- Authentication
- Frontend static files
"""

import pytest
import httpx
import asyncio
import os
import json
from typing import Dict, Any

# API base URL from environment or default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:18080")


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def api_client():
    """HTTP client for API requests"""
    return httpx.Client(base_url=API_BASE_URL, timeout=30.0)


@pytest.fixture
def async_api_client():
    """Async HTTP client for API requests"""
    return httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)


# ============================================================
# HEALTH & BASIC ENDPOINTS
# ============================================================

@pytest.mark.e2e
class TestHealthEndpoints:
    """Test API health and basic endpoints"""
    
    def test_health_endpoint(self, api_client):
        """API health check"""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_root_endpoint(self, api_client):
        """Root endpoint returns API info"""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "ANALYTICA" in data.get("message", "")
    
    def test_docs_endpoint(self, api_client):
        """OpenAPI docs available"""
        response = api_client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema(self, api_client):
        """OpenAPI schema available"""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


# ============================================================
# DSL API ENDPOINTS
# ============================================================

@pytest.mark.e2e
class TestDSLEndpoints:
    """Test DSL API endpoints"""
    
    def test_pipeline_validate_valid(self, api_client):
        """Validate valid DSL pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/validate",
            json={"dsl": "data.define(x=100) | data.compute(y=\"x * 2\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == True
    
    def test_pipeline_validate_invalid(self, api_client):
        """Validate invalid DSL pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/validate",
            json={"dsl": "invalid.atom.that.does.not.exist()"}
        )
        assert response.status_code == 200
        data = response.json()
        # May be valid syntax but unknown atom
    
    def test_pipeline_execute_simple(self, api_client):
        """Execute simple DSL pipeline"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(revenue=100000, costs=65000) | data.compute(profit=\"revenue - costs\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("result") is not None
        result = data["result"]
        assert result.get("profit") == 35000
    
    def test_pipeline_execute_with_variables(self, api_client):
        """Execute DSL pipeline with variables"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={
                "dsl": "data.define(base=$BASE) | data.compute(total=\"base * 2\")",
                "variables": {"BASE": 500}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        result = data["result"]
        assert result.get("total") == 1000
    
    def test_pipeline_schema(self, api_client):
        """Get pipeline JSON schema"""
        response = api_client.get("/api/v1/pipeline/schema")
        assert response.status_code == 200
        data = response.json()
        assert "type" in data or "$schema" in data
    
    def test_pipeline_parse(self, api_client):
        """Parse DSL to JSON representation"""
        response = api_client.post(
            "/api/v1/pipeline/parse",
            json={"dsl": "data.define(x=1) | data.compute(y=\"x+1\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "json_representation" in data or "steps" in data


# ============================================================
# DEPLOY ATOMS
# ============================================================

@pytest.mark.e2e
class TestDeployAtoms:
    """Test deploy atoms via API"""
    
    def test_deploy_docker(self, api_client):
        """Test deploy.docker atom"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(app=\"test\") | deploy.docker(image=\"myapp\", tag=\"latest\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        result = data.get("result", {})
        # Check for docker config or deployments
        assert "config" in result or "deployments" in result or "type" in result
    
    def test_deploy_kubernetes(self, api_client):
        """Test deploy.kubernetes atom"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(app=\"test\") | deploy.kubernetes(namespace=\"prod\", replicas=3)"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_deploy_web(self, api_client):
        """Test deploy.web atom"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(app=\"test\") | deploy.web(framework=\"react\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_deploy_desktop(self, api_client):
        """Test deploy.desktop atom"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(app=\"test\") | deploy.desktop(framework=\"electron\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_deploy_mobile(self, api_client):
        """Test deploy.mobile atom"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(app=\"test\") | deploy.mobile(framework=\"react-native\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_deploy_github_actions(self, api_client):
        """Test deploy.github_actions atom"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(app=\"test\") | deploy.github_actions(workflow=\"ci\")"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"


# ============================================================
# URI LAUNCHER
# ============================================================

@pytest.mark.e2e
class TestURILauncher:
    """Test URI launcher endpoints"""
    
    def test_launcher_status(self, api_client):
        """Check launcher status"""
        response = api_client.get("/api/v1/launcher/status")
        assert response.status_code == 200
        data = response.json()
        assert "scheme" in data
        assert "registered" in data
    
    def test_launcher_parse(self, api_client):
        """Parse URI"""
        response = api_client.get(
            "/api/v1/launcher/parse",
            params={"uri": "analytica://desktop/run?dir=/tmp&url=http://localhost"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("scheme") == "analytica"
        assert "params" in data


# ============================================================
# AUTHENTICATION
# ============================================================

@pytest.mark.e2e
class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_user(self, api_client):
        """Register new user"""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        response = api_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "testpass123",
                "name": "Test User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data or "user" in data or "id" in data
    
    def test_login_invalid(self, api_client):
        """Login with invalid credentials"""
        response = api_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "wrongpassword"
            }
        )
        # Should return 401 or 400
        assert response.status_code in [400, 401, 404]


# ============================================================
# COMPLEX PIPELINES
# ============================================================

@pytest.mark.e2e
class TestComplexPipelines:
    """Test complex multi-step pipelines"""
    
    def test_financial_pipeline(self, api_client):
        """Financial analysis pipeline"""
        dsl = """
        data.define(revenue=100000, costs=65000, tax_rate=0.19)
        | data.compute(profit="revenue - costs")
        | data.compute(tax="profit * tax_rate")
        | data.compute(net_profit="profit - tax")
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        result = data["result"]
        assert result.get("profit") == 35000
        assert result.get("net_profit") == 35000 - (35000 * 0.19)
    
    def test_data_transform_pipeline(self, api_client):
        """Data transformation pipeline"""
        dsl = """
        data.define(items=[
            {"name": "A", "value": 100},
            {"name": "B", "value": 200},
            {"name": "C", "value": 150}
        ])
        | transform.filter(value=">100")
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_view_pipeline(self, api_client):
        """Pipeline with view atoms"""
        dsl = """
        data.define(revenue=100000, costs=65000)
        | data.compute(profit="revenue - costs")
        | view.card(value="profit", title="Zysk", icon="💰")
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_multi_deploy_pipeline(self, api_client):
        """Pipeline with multiple deploy targets"""
        dsl = """
        data.define(app="analytica", version="1.0")
        | deploy.docker(image="analytica/app", tag="latest")
        | deploy.kubernetes(namespace="prod", replicas=3)
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        result = data.get("result", {})
        # Should have deployments array
        deployments = result.get("deployments", [])
        if deployments:
            assert len(deployments) >= 2


# ============================================================
# STATIC FILES
# ============================================================

@pytest.mark.e2e
class TestStaticFiles:
    """Test static file serving"""
    
    def test_landing_page(self, api_client):
        """Landing page accessible"""
        response = api_client.get("/landing/")
        assert response.status_code == 200
    
    def test_dsl_editor(self, api_client):
        """DSL editor page accessible"""
        response = api_client.get("/landing/dsl-editor.html")
        assert response.status_code == 200
        assert "DSL" in response.text or "Analytica" in response.text


# ============================================================
# ERROR HANDLING
# ============================================================

@pytest.mark.e2e
class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json(self, api_client):
        """Invalid JSON returns proper error"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_dsl(self, api_client):
        """Missing DSL field returns error"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={}
        )
        assert response.status_code in [400, 422]
    
    def test_syntax_error_in_dsl(self, api_client):
        """Syntax error in DSL handled gracefully"""
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(x=)"}  # Invalid syntax
        )
        assert response.status_code == 200
        data = response.json()
        # Should return error status, not crash
        assert data.get("status") == "error" or "errors" in data


# ============================================================
# PERFORMANCE
# ============================================================

@pytest.mark.e2e
class TestPerformance:
    """Basic performance tests"""
    
    def test_simple_pipeline_response_time(self, api_client):
        """Simple pipeline should respond quickly"""
        import time
        start = time.time()
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": "data.define(x=1)"}
        )
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 5.0  # Should complete in under 5 seconds
    
    def test_concurrent_requests(self, api_client):
        """Handle multiple concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return api_client.post(
                "/api/v1/pipeline/execute",
                json={"dsl": "data.define(x=1)"}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)


# ============================================================
# ASYNC TESTS
# ============================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestAsyncOperations:
    """Async operation tests"""
    
    async def test_async_pipeline_execution(self, async_api_client):
        """Execute pipeline asynchronously"""
        async with async_api_client as client:
            response = await client.post(
                "/api/v1/pipeline/execute",
                json={"dsl": "data.define(x=100) | data.compute(y=\"x * 2\")"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "success"
    
    async def test_multiple_async_requests(self, async_api_client):
        """Multiple async requests"""
        async with async_api_client as client:
            tasks = [
                client.post("/api/v1/pipeline/execute", json={"dsl": f"data.define(x={i})"})
                for i in range(5)
            ]
            responses = await asyncio.gather(*tasks)
            assert all(r.status_code == 200 for r in responses)
