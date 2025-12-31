"""
ANALYTICA E2E Tests - Frontend Testing
=======================================

Tests for frontend pages and UI functionality.
Uses httpx to test static file serving and basic page structure.
"""

import pytest
import httpx
import os
import re

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:18080")


@pytest.fixture
def api_client():
    """HTTP client for API requests"""
    return httpx.Client(base_url=API_BASE_URL, timeout=30.0)


# ============================================================
# STATIC FILE TESTS
# ============================================================

@pytest.mark.e2e
class TestStaticFiles:
    """Test static file serving"""
    
    def test_landing_index(self, api_client):
        """Landing index page"""
        response = api_client.get("/landing/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_dsl_editor_page(self, api_client):
        """DSL editor page loads"""
        response = api_client.get("/landing/dsl-editor.html")
        assert response.status_code == 200
        content = response.text
        # Check for key elements
        assert "Analytica" in content or "DSL" in content
        assert "<script" in content
        assert "<style" in content
    
    def test_dsl_editor_has_tabs(self, api_client):
        """DSL editor has output tabs"""
        response = api_client.get("/landing/dsl-editor.html")
        assert response.status_code == 200
        content = response.text
        # Check for output tabs
        assert "output-tab" in content
        assert "JSON" in content
        assert "Preview" in content
        assert "Export" in content
    
    def test_dsl_editor_has_examples(self, api_client):
        """DSL editor has example pipelines"""
        response = api_client.get("/landing/dsl-editor.html")
        assert response.status_code == 200
        content = response.text
        # Check for example references
        assert "example" in content.lower()
    
    def test_app_html(self, api_client):
        """App HTML page"""
        response = api_client.get("/landing/app.html")
        # May or may not exist
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")
    
    def test_dashboard_html(self, api_client):
        """Dashboard HTML page"""
        response = api_client.get("/landing/dashboard.html")
        # May or may not exist
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")


# ============================================================
# API INTEGRATION FROM FRONTEND
# ============================================================

@pytest.mark.e2e
class TestFrontendAPIIntegration:
    """Test API calls that frontend makes"""
    
    def test_execute_endpoint_cors(self, api_client):
        """Execute endpoint accepts CORS requests"""
        response = api_client.options(
            "/api/v1/pipeline/execute",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        # Should allow CORS
        assert response.status_code in [200, 204]
    
    def test_validate_endpoint_cors(self, api_client):
        """Validate endpoint accepts CORS requests"""
        response = api_client.options(
            "/api/v1/pipeline/validate",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code in [200, 204]
    
    def test_launcher_status_cors(self, api_client):
        """Launcher status endpoint accepts CORS"""
        response = api_client.options(
            "/api/v1/launcher/status",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code in [200, 204]


# ============================================================
# DSL EXAMPLES
# ============================================================

@pytest.mark.e2e
class TestDSLExamples:
    """Test DSL examples from frontend"""
    
    EXAMPLES = {
        "iot-sensor": 'data.define(temperature=25.5, humidity=60)',
        "api-dashboard": 'data.define(requests=1000, errors=5)',
        "financial": 'data.define(revenue=100000, costs=65000)',
        "etl-pipeline": 'data.define(source="csv", records=1000)',
        "industrial-plc": 'data.define(sensor_id="PLC001", value=42.5)',
    }
    
    def test_iot_sensor_example(self, api_client):
        """IoT sensor example executes"""
        dsl = self.EXAMPLES.get("iot-sensor", "data.define(x=1)")
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_financial_example(self, api_client):
        """Financial example executes"""
        dsl = """
        data.define(revenue=100000, costs=65000)
        | data.compute(profit="revenue - costs")
        | data.compute(margin="profit / revenue * 100")
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        result = data.get("result", {})
        assert result.get("profit") == 35000
    
    def test_etl_pipeline_example(self, api_client):
        """ETL pipeline example executes"""
        dsl = """
        data.define(records=[
            {"id": 1, "value": 100},
            {"id": 2, "value": 200}
        ])
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"


# ============================================================
# EXPORT FUNCTIONALITY
# ============================================================

@pytest.mark.e2e
class TestExportFunctionality:
    """Test export functionality used by frontend"""
    
    def test_docker_export(self, api_client):
        """Docker export generates config"""
        dsl = """
        data.define(app="test")
        | deploy.docker(image="myapp", tag="latest", port=8000)
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        result = data.get("result", {})
        # Should have docker config
        assert "type" in result or "config" in result or "deployments" in result
    
    def test_kubernetes_export(self, api_client):
        """Kubernetes export generates config"""
        dsl = """
        data.define(app="test")
        | deploy.kubernetes(namespace="prod", replicas=3)
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
    
    def test_desktop_export(self, api_client):
        """Desktop export generates config"""
        dsl = """
        data.define(app="test")
        | deploy.desktop(framework="electron", platforms=["win", "mac", "linux"])
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        result = data.get("result", {})
        # Should have desktop config with commands
        if "commands" in result:
            assert "dev" in result["commands"] or "build" in result["commands"]
    
    def test_github_actions_export(self, api_client):
        """GitHub Actions export generates workflow"""
        dsl = """
        data.define(app="test")
        | deploy.github_actions(workflow="ci", triggers=["push", "pull_request"])
        """
        response = api_client.post(
            "/api/v1/pipeline/execute",
            json={"dsl": dsl}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
