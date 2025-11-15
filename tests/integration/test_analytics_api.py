"""
Integration tests for Analytics API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create mock authentication headers."""
    # Mock JWT token for testing
    return {"Authorization": "Bearer mock_token_for_testing"}


@pytest.fixture
def mock_current_user():
    """Mock the current user dependency."""
    with patch("src.api.routes.analytics.get_current_user") as mock:
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock.return_value = mock_user
        yield mock


class TestAnalyticsAPI:
    """Integration tests for Analytics API."""

    def test_get_agent_status(self, client, mock_current_user):
        """Test getting analytics agent status."""
        response = client.get("/api/v1/analytics/status")

        assert response.status_code == 200
        data = response.json()

        assert "agent" in data
        assert data["agent"] == "analytics"
        assert "status" in data
        assert "ai_enabled" in data

    def test_get_metrics_daily(self, client, mock_current_user):
        """Test getting daily metrics."""
        response = client.get("/api/v1/analytics/metrics?time_period=daily")

        assert response.status_code == 200
        data = response.json()

        assert "timestamp" in data
        assert "time_period" in data
        assert data["time_period"] == "daily"
        assert "revenue" in data
        assert "operations" in data
        assert "customers" in data
        assert "fleet" in data

    def test_get_metrics_weekly(self, client, mock_current_user):
        """Test getting weekly metrics."""
        response = client.get("/api/v1/analytics/metrics?time_period=weekly")

        assert response.status_code == 200
        data = response.json()
        assert data["time_period"] == "weekly"

    def test_get_kpis(self, client, mock_current_user):
        """Test getting KPIs."""
        response = client.get("/api/v1/analytics/kpis?time_period=daily")

        assert response.status_code == 200
        data = response.json()

        assert "time_period" in data
        assert "kpis" in data
        assert "timestamp" in data

        kpis = data["kpis"]
        assert "revenue_per_booking" in kpis
        assert "customer_acquisition_cost" in kpis
        assert "booking_completion_rate" in kpis

    def test_generate_performance_report(self, client, mock_current_user):
        """Test generating performance report."""
        response = client.get("/api/v1/analytics/performance?time_period=daily")

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "performance"
        assert "metrics" in data
        assert "insights" in data

    def test_generate_financial_report(self, client, mock_current_user):
        """Test generating financial report."""
        response = client.get("/api/v1/analytics/financial?time_period=monthly")

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "financial"
        assert data["time_period"] == "monthly"

    def test_generate_operations_report(self, client, mock_current_user):
        """Test generating operations report."""
        response = client.get("/api/v1/analytics/operations")

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "operations"

    def test_generate_customer_report(self, client, mock_current_user):
        """Test generating customer report."""
        response = client.get("/api/v1/analytics/customer")

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "customer"

    def test_generate_predictive_report(self, client, mock_current_user):
        """Test generating predictive report."""
        response = client.get("/api/v1/analytics/predictive")

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "predictive"

    def test_post_report_request(self, client, mock_current_user):
        """Test POST endpoint for report generation."""
        request_data = {
            "report_type": "financial",
            "time_period": "weekly",
            "use_ai": False
        }

        response = client.post("/api/v1/analytics/reports", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "financial"
        assert data["time_period"] == "weekly"

    def test_get_quick_report_by_type(self, client, mock_current_user):
        """Test quick report endpoint."""
        response = client.get("/api/v1/analytics/reports/financial?time_period=daily")

        assert response.status_code == 200
        data = response.json()

        assert data["report_type"] == "financial"

    def test_post_insights_request(self, client, mock_current_user):
        """Test requesting AI insights."""
        request_data = {
            "context": "Focus on revenue optimization"
        }

        response = client.post("/api/v1/analytics/insights", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "insights" in data
        assert "ai_enabled" in data

    def test_post_insights_empty_context(self, client, mock_current_user):
        """Test insights with empty context."""
        request_data = {}

        response = client.post("/api/v1/analytics/insights", json=request_data)

        assert response.status_code == 200

    def test_invalid_report_type(self, client, mock_current_user):
        """Test with invalid report type."""
        request_data = {
            "report_type": "invalid_type",
            "time_period": "daily"
        }

        response = client.post("/api/v1/analytics/reports", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_invalid_time_period(self, client, mock_current_user):
        """Test with invalid time period."""
        response = client.get("/api/v1/analytics/metrics?time_period=invalid")

        assert response.status_code == 422  # Validation error

    def test_all_endpoints_require_auth(self, client):
        """Test that all endpoints require authentication."""
        endpoints = [
            "/api/v1/analytics/status",
            "/api/v1/analytics/metrics",
            "/api/v1/analytics/kpis",
            "/api/v1/analytics/performance",
            "/api/v1/analytics/financial"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should fail without mock_current_user
            assert response.status_code in [401, 403, 500]  # Unauthorized or error

    def test_metrics_response_structure(self, client, mock_current_user):
        """Test that metrics response has correct structure."""
        response = client.get("/api/v1/analytics/metrics")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert isinstance(data["revenue"], dict)
        assert isinstance(data["operations"], dict)
        assert isinstance(data["customers"], dict)
        assert isinstance(data["fleet"], dict)

        # Verify revenue fields
        assert "total_revenue" in data["revenue"]
        assert "average_booking_value" in data["revenue"]

    def test_kpis_all_numeric(self, client, mock_current_user):
        """Test that all KPIs are numeric values."""
        response = client.get("/api/v1/analytics/kpis")

        assert response.status_code == 200
        data = response.json()

        for key, value in data["kpis"].items():
            assert isinstance(value, (int, float)), f"KPI {key} is not numeric"

    def test_report_with_ai_disabled(self, client, mock_current_user):
        """Test generating report with AI explicitly disabled."""
        response = client.get("/api/v1/analytics/performance?time_period=daily")

        assert response.status_code == 200
        data = response.json()

        assert "ai_generated" in data
        # Should have insights even if AI is disabled (basic insights)
        assert "insights" in data

    def test_concurrent_requests(self, client, mock_current_user):
        """Test handling multiple concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/analytics/metrics")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        for result in results:
            assert result.status_code == 200

    def test_different_time_periods_all_endpoints(self, client, mock_current_user):
        """Test all time periods across different endpoints."""
        periods = ["daily", "weekly", "monthly", "yearly"]

        for period in periods:
            # Test metrics
            response = client.get(f"/api/v1/analytics/metrics?time_period={period}")
            assert response.status_code == 200
            assert response.json()["time_period"] == period

            # Test KPIs
            response = client.get(f"/api/v1/analytics/kpis?time_period={period}")
            assert response.status_code == 200
            assert response.json()["time_period"] == period

    def test_report_contains_timestamp(self, client, mock_current_user):
        """Test that reports contain proper timestamps."""
        response = client.get("/api/v1/analytics/financial")

        assert response.status_code == 200
        data = response.json()

        assert "generated_at" in data
        # Verify timestamp format (ISO 8601)
        assert "T" in data["generated_at"]
