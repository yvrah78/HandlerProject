"""
Analytics Agent for Project Handler.
Handles metrics collection, reporting, and business intelligence.
"""
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError


class AnalyticsAgent(BaseAgent):
    """
    Agent responsible for analytics and reporting.

    Manages:
    - Metrics collection and analysis
    - Business intelligence reports
    - Performance dashboards
    - Predictive analytics
    """

    def __init__(self):
        super().__init__(
            name="analytics",
            description="Handles metrics collection, reporting, and business intelligence"
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process analytics request.

        Args:
            input_data: Must contain 'report_type' and relevant parameters

        Returns:
            Dict[str, Any]: Analytics result
        """
        report_type = input_data.get("report_type")
        time_period = input_data.get("time_period", "daily")
        metrics = input_data.get("metrics", [])

        self.logger.info(f"Generating {report_type} report for {time_period}")

        # Placeholder implementation - will be enhanced with actual analytics
        return {
            "report_type": report_type,
            "time_period": time_period,
            "metrics": metrics,
            "status": "generated",
            "message": f"{report_type} report generated successfully"
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate analytics input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ["report_type"]

        for field in required_fields:
            if field not in input_data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    details={"received_keys": list(input_data.keys())}
                )

        valid_reports = ["performance", "financial", "operations", "customer", "predictive"]
        if input_data["report_type"] not in valid_reports:
            raise ValidationError(
                f"Invalid report type. Must be one of: {valid_reports}",
                details={"received": input_data["report_type"]}
            )

        return True
