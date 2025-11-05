"""
Operations Agent for Project Handler.
Handles route planning, fleet management, and logistics operations.
"""
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError


class OperationsAgent(BaseAgent):
    """
    Agent responsible for operational logistics.

    Manages:
    - Route planning and optimization
    - Fleet management
    - Driver assignment
    - Real-time tracking
    """

    def __init__(self):
        super().__init__(
            name="operations",
            description="Handles route planning, fleet management, and logistics"
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process operations request.

        Args:
            input_data: Must contain 'operation_type' and relevant data

        Returns:
            Dict[str, Any]: Operations result
        """
        operation = input_data.get("operation_type")
        origin = input_data.get("origin")
        destination = input_data.get("destination")

        self.logger.info(f"Processing {operation} from {origin} to {destination}")

        # Placeholder implementation - will be enhanced with Google Maps API
        return {
            "operation_type": operation,
            "origin": origin,
            "destination": destination,
            "status": "planned",
            "message": f"{operation} operation planned successfully"
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate operations input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ["operation_type"]

        for field in required_fields:
            if field not in input_data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    details={"received_keys": list(input_data.keys())}
                )

        valid_operations = ["route_planning", "fleet_assignment", "tracking", "optimization"]
        if input_data["operation_type"] not in valid_operations:
            raise ValidationError(
                f"Invalid operation type. Must be one of: {valid_operations}",
                details={"received": input_data["operation_type"]}
            )

        return True
