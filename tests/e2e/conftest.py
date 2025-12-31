"""
ANALYTICA E2E Tests - Pytest Configuration
===========================================

Fixtures and configuration for E2E tests.
"""

import pytest
import httpx
import os
import time

# API base URL from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:18080")


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")


@pytest.fixture(scope="session")
def api_base_url():
    """API base URL"""
    return API_BASE_URL


@pytest.fixture(scope="session")
def wait_for_api():
    """Wait for API to be ready"""
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                print(f"API ready after {i * retry_interval} seconds")
                return True
        except Exception as e:
            print(f"Waiting for API... ({i+1}/{max_retries}): {e}")
        time.sleep(retry_interval)
    
    pytest.fail(f"API not ready after {max_retries * retry_interval} seconds")


@pytest.fixture
def api_client(wait_for_api):
    """HTTP client for API requests"""
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
async def async_api_client(wait_for_api):
    """Async HTTP client for API requests"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def sample_sales_data():
    """Sample sales data for testing"""
    return [
        {"id": 1, "region": "PL", "amount": 1000, "product": "A"},
        {"id": 2, "region": "PL", "amount": 1500, "product": "B"},
        {"id": 3, "region": "DE", "amount": 2000, "product": "A"},
        {"id": 4, "region": "DE", "amount": 2500, "product": "C"},
        {"id": 5, "region": "PL", "amount": 800, "product": "B"},
        {"id": 6, "region": "FR", "amount": 3000, "product": "A"},
    ]


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing"""
    return {
        "revenue": 100000,
        "costs": 65000,
        "tax_rate": 0.19,
        "employees": 10,
        "office_rent": 5000
    }


@pytest.fixture
def auth_token(api_client):
    """Get authentication token"""
    import uuid
    unique_email = f"e2e_test_{uuid.uuid4().hex[:8]}@test.com"
    
    # Register user
    response = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "testpass123",
            "name": "E2E Test User"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    
    # Try login if registration failed (user exists)
    response = api_client.post(
        "/api/v1/auth/login",
        json={
            "email": unique_email,
            "password": "testpass123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    
    return None


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """API client with authentication"""
    if auth_token:
        api_client.headers["Authorization"] = f"Bearer {auth_token}"
    return api_client
