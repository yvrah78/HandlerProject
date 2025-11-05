"""
Integration tests for Project Handler API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Project Handler API" in data["message"]
    assert data["version"] == "0.1.0"
    assert data["status"] == "operational"


def test_info_endpoint(client: TestClient):
    """Test info endpoint returns system information."""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Project Handler"
    assert "agents" in data
    assert len(data["agents"]) == 5  # Should have 5 agents


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "project-handler-api"


def test_readiness_check(client: TestClient):
    """Test readiness check endpoint."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data


def test_liveness_check(client: TestClient):
    """Test liveness check endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_nonexistent_endpoint(client: TestClient):
    """Test that nonexistent endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
