"""
Communications Agent for Project Handler.
Handles phone calls, SMS, and email communications via Twilio and SendGrid.
"""
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError


class CommunicationsAgent(BaseAgent):
    """
    Agent responsible for all external communications.

    Manages:
    - Automated phone calls
    - SMS notifications
    - Email communications
    - Customer follow-ups
    """

    def __init__(self):
        super().__init__(
            name="communications",
            description="Handles phone calls, SMS, and email communications"
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process communication request.

        Args:
            input_data: Must contain 'communication_type' and relevant data

        Returns:
            Dict[str, Any]: Communication result
        """
        comm_type = input_data.get("communication_type")
        recipient = input_data.get("recipient")
        message = input_data.get("message", "")

        self.logger.info(f"Processing {comm_type} communication to {recipient}")

        # Placeholder implementation - will be enhanced with Twilio/SendGrid
        return {
            "communication_type": comm_type,
            "recipient": recipient,
            "status": "sent",
            "message": f"{comm_type} communication queued for delivery"
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate communication input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ["communication_type", "recipient"]

        for field in required_fields:
            if field not in input_data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    details={"received_keys": list(input_data.keys())}
                )

        valid_types = ["phone", "sms", "email"]
        if input_data["communication_type"] not in valid_types:
            raise ValidationError(
                f"Invalid communication type. Must be one of: {valid_types}",
                details={"received": input_data["communication_type"]}
            )

        return True
