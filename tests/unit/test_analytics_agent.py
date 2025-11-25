"""
Unit tests for Analytics Agent.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.agents.analytics import AnalyticsAgent
from src.core.exceptions import ValidationError


@pytest.fixture
def analytics_agent():
    """Create an Analytics Agent instance for testing."""
    return AnalyticsAgent()


@pytest.mark.asyncio
class TestAnalyticsAgent:
    """Test suite for Analytics Agent."""

    async def test_agent_initialization(self, analytics_agent):
        """Test that agent initializes correctly."""
        assert analytics_agent.name == "analytics"
        assert "analytics" in analytics_agent.description.lower()
        assert analytics_agent.status == "initialized"
        assert analytics_agent.metrics_cache is not None

    async def test_collect_metrics_daily(self, analytics_agent):
        """Test collecting daily metrics."""
        metrics = await analytics_agent.collect_metrics("daily")

        assert metrics is not None
        assert "timestamp" in metrics
        assert "time_period" in metrics
        assert metrics["time_period"] == "daily"

        # Check all metric categories exist
        assert "revenue" in metrics
        assert "operations" in metrics
        assert "customers" in metrics
        assert "fleet" in metrics

        # Verify revenue metrics
        assert "total_revenue" in metrics["revenue"]
        assert "average_booking_value" in metrics["revenue"]
        assert "revenue_growth" in metrics["revenue"]

    async def test_collect_metrics_weekly(self, analytics_agent):
        """Test collecting weekly metrics."""
        metrics = await analytics_agent.collect_metrics("weekly")

        assert metrics["time_period"] == "weekly"
        assert metrics is not None

    async def test_metrics_caching(self, analytics_agent):
        """Test that metrics are cached correctly."""
        await analytics_agent.collect_metrics("daily")

        assert "daily" in analytics_agent.metrics_cache
        cached = analytics_agent.metrics_cache["daily"]
        assert cached is not None

    async def test_get_kpis(self, analytics_agent):
        """Test KPI calculation."""
        kpis = await analytics_agent.get_kpis("daily")

        assert "time_period" in kpis
        assert "kpis" in kpis
        assert "timestamp" in kpis

        # Check calculated KPIs
        assert "revenue_per_booking" in kpis["kpis"]
        assert "customer_acquisition_cost" in kpis["kpis"]
        assert "booking_completion_rate" in kpis["kpis"]
        assert "fleet_efficiency" in kpis["kpis"]
        assert "customer_satisfaction" in kpis["kpis"]
        assert "revenue_growth" in kpis["kpis"]

        # Verify KPI values are numeric
        for key, value in kpis["kpis"].items():
            assert isinstance(value, (int, float))

    async def test_validate_input_valid_performance(self, analytics_agent):
        """Test input validation with valid performance report request."""
        input_data = {
            "report_type": "performance",
            "time_period": "daily"
        }

        is_valid = await analytics_agent.validate_input(input_data)
        assert is_valid is True

    async def test_validate_input_valid_financial(self, analytics_agent):
        """Test input validation with valid financial report request."""
        input_data = {
            "report_type": "financial",
            "time_period": "monthly"
        }

        is_valid = await analytics_agent.validate_input(input_data)
        assert is_valid is True

    async def test_validate_input_missing_report_type(self, analytics_agent):
        """Test validation fails when report_type is missing."""
        input_data = {
            "time_period": "daily"
        }

        with pytest.raises(ValidationError) as exc_info:
            await analytics_agent.validate_input(input_data)

        assert "report_type" in str(exc_info.value)

    async def test_validate_input_invalid_report_type(self, analytics_agent):
        """Test validation fails with invalid report type."""
        input_data = {
            "report_type": "invalid_type"
        }

        with pytest.raises(ValidationError) as exc_info:
            await analytics_agent.validate_input(input_data)

        assert "Invalid report type" in str(exc_info.value)

    async def test_validate_input_invalid_time_period(self, analytics_agent):
        """Test validation fails with invalid time period."""
        input_data = {
            "report_type": "performance",
            "time_period": "invalid_period"
        }

        with pytest.raises(ValidationError) as exc_info:
            await analytics_agent.validate_input(input_data)

        assert "Invalid time period" in str(exc_info.value)

    async def test_validate_input_all_report_types(self, analytics_agent):
        """Test validation for all valid report types."""
        valid_types = ["performance", "financial", "operations", "customer", "predictive", "kpis", "metrics"]

        for report_type in valid_types:
            input_data = {
                "report_type": report_type,
                "time_period": "daily"
            }

            is_valid = await analytics_agent.validate_input(input_data)
            assert is_valid is True

    async def test_process_metrics_request(self, analytics_agent):
        """Test processing a metrics request."""
        input_data = {
            "report_type": "metrics",
            "time_period": "daily"
        }

        result = await analytics_agent.process(input_data)

        assert result is not None
        assert "timestamp" in result
        assert "revenue" in result

    async def test_process_kpis_request(self, analytics_agent):
        """Test processing a KPIs request."""
        input_data = {
            "report_type": "kpis",
            "time_period": "weekly"
        }

        result = await analytics_agent.process(input_data)

        assert result is not None
        assert "kpis" in result
        assert result["time_period"] == "weekly"

    async def test_generate_report_without_ai(self, analytics_agent):
        """Test generating a report without AI insights."""
        report = await analytics_agent.generate_report(
            report_type="financial",
            time_period="daily",
            use_ai=False
        )

        assert report is not None
        assert report["report_type"] == "financial"
        assert report["time_period"] == "daily"
        assert "metrics" in report
        assert "insights" in report
        assert report["ai_generated"] is False

    async def test_generate_basic_insights_performance(self, analytics_agent):
        """Test basic insights generation for performance report."""
        metrics = await analytics_agent.collect_metrics("daily")
        insights = analytics_agent._generate_basic_insights(metrics, "performance")

        assert insights is not None
        assert isinstance(insights, str)
        assert len(insights) > 0

    async def test_generate_basic_insights_financial(self, analytics_agent):
        """Test basic insights generation for financial report."""
        metrics = await analytics_agent.collect_metrics("daily")
        insights = analytics_agent._generate_basic_insights(metrics, "financial")

        assert insights is not None
        assert "revenue" in insights.lower() or "$" in insights

    async def test_format_metrics_for_ai_financial(self, analytics_agent):
        """Test formatting metrics for AI consumption (financial)."""
        metrics = await analytics_agent.collect_metrics("daily")
        formatted = analytics_agent._format_metrics_for_ai(metrics, "financial")

        assert formatted is not None
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    async def test_format_metrics_for_ai_operations(self, analytics_agent):
        """Test formatting metrics for AI consumption (operations)."""
        metrics = await analytics_agent.collect_metrics("daily")
        formatted = analytics_agent._format_metrics_for_ai(metrics, "operations")

        assert formatted is not None
        assert isinstance(formatted, str)

    async def test_execute_success(self, analytics_agent):
        """Test successful agent execution."""
        input_data = {
            "report_type": "metrics",
            "time_period": "daily"
        }

        result = await analytics_agent.execute(input_data)

        assert result is not None
        assert result["success"] is True
        assert result["agent"] == "analytics"
        assert "result" in result
        assert "timestamp" in result

    async def test_get_status(self, analytics_agent):
        """Test getting agent status."""
        status = analytics_agent.get_status()

        assert status is not None
        assert status["agent"] == "analytics"
        assert "status" in status
        assert "created_at" in status
        assert "description" in status

    async def test_reset_agent(self, analytics_agent):
        """Test resetting agent state."""
        # Execute agent first
        await analytics_agent.execute({
            "report_type": "metrics"
        })

        assert analytics_agent.status == "completed"

        # Reset
        analytics_agent.reset()

        assert analytics_agent.status == "initialized"
        assert analytics_agent.last_execution is None

    @pytest.mark.skipif(
        not pytest.importorskip("langchain", minversion=None),
        reason="LangChain not installed"
    )
    async def test_ai_prompts_initialized(self, analytics_agent):
        """Test that AI prompts are initialized."""
        assert analytics_agent.prompts is not None
        assert "performance" in analytics_agent.prompts
        assert "financial" in analytics_agent.prompts
        assert "operations" in analytics_agent.prompts
        assert "customer" in analytics_agent.prompts
        assert "predictive" in analytics_agent.prompts

    async def test_process_all_report_types(self, analytics_agent):
        """Test processing all report types without AI."""
        report_types = ["performance", "financial", "operations", "customer", "predictive"]

        for report_type in report_types:
            input_data = {
                "report_type": report_type,
                "time_period": "daily",
                "use_ai": False
            }

            result = await analytics_agent.process(input_data)

            assert result is not None
            assert result["report_type"] == report_type

    async def test_insights_without_api_key(self, analytics_agent):
        """Test getting insights when AI is not enabled."""
        # Force disable AI
        analytics_agent.ai_enabled = False

        insights = await analytics_agent.get_insights("test context")

        assert insights is not None
        assert "ai_enabled" in insights
        assert insights["ai_enabled"] is False

    async def test_different_time_periods(self, analytics_agent):
        """Test collecting metrics for different time periods."""
        periods = ["daily", "weekly", "monthly", "yearly"]

        for period in periods:
            metrics = await analytics_agent.collect_metrics(period)

            assert metrics is not None
            assert metrics["time_period"] == period

    async def test_metrics_have_required_fields(self, analytics_agent):
        """Test that metrics contain all required fields."""
        metrics = await analytics_agent.collect_metrics("daily")

        # Revenue metrics
        revenue = metrics["revenue"]
        assert "total_revenue" in revenue
        assert "average_booking_value" in revenue
        assert "revenue_growth" in revenue
        assert "payment_success_rate" in revenue

        # Operations metrics
        ops = metrics["operations"]
        assert "total_bookings" in ops
        assert "completed_bookings" in ops
        assert "cancelled_bookings" in ops
        assert "completion_rate" in ops

        # Customer metrics
        customers = metrics["customers"]
        assert "total_customers" in customers
        assert "new_customers" in customers
        assert "customer_satisfaction" in customers

        # Fleet metrics
        fleet = metrics["fleet"]
        assert "total_vehicles" in fleet
        assert "active_vehicles" in fleet
        assert "average_vehicle_efficiency" in fleet
