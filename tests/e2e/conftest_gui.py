"""
ANALYTICA E2E Tests - GUI Test Configuration
=============================================

Pytest configuration for Playwright GUI tests.
"""

import pytest
import os


def pytest_configure(config):
    """Configure pytest markers for GUI tests"""
    config.addinivalue_line("markers", "gui: GUI/Browser tests with Playwright")


@pytest.fixture(scope="session")
def api_base_url():
    """API base URL for GUI tests"""
    return os.getenv("API_BASE_URL", "http://localhost:18080")
