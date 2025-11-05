"""
Pytest configuration and fixtures for Project Handler tests.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """
    Fixture providing TestClient for API testing.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
def sample_customer_data():
    """
    Fixture providing sample customer data for tests.

    Returns:
        dict: Sample customer data
    """
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "company": "Test Company"
    }


@pytest.fixture
def sample_booking_data():
    """
    Fixture providing sample booking data for tests.

    Returns:
        dict: Sample booking data
    """
    return {
        "customer_id": 1,
        "origin": "123 Main St, City A",
        "destination": "456 Oak Ave, City B",
        "pickup_datetime": "2025-11-10T10:00:00",
        "cargo_description": "Test cargo",
        "cargo_weight": 500.0
    }
