"""
Financial Agent for Project Handler.
Handles quotations, invoicing, payments, and financial operations.
"""
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError


class FinancialAgent(BaseAgent):
    """
    Agent responsible for all financial operations.

    Manages:
    - Price quotations
    - Invoice generation
    - Payment processing via Stripe
    - Financial reporting
    """

    def __init__(self):
        super().__init__(
            name="financial",
            description="Handles quotations, invoicing, and payment processing"
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process financial operation.

        Args:
            input_data: Must contain 'operation_type' and relevant data

        Returns:
            Dict[str, Any]: Financial operation result
        """
        operation = input_data.get("operation_type")
        amount = input_data.get("amount", 0)
        customer_id = input_data.get("customer_id")

        self.logger.info(f"Processing {operation} operation for customer {customer_id}")

        # Placeholder implementation - will be enhanced with Stripe
        return {
            "operation_type": operation,
            "customer_id": customer_id,
            "amount": amount,
            "status": "processed",
            "message": f"{operation} operation completed successfully"
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate financial operation input.

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

        valid_operations = ["quotation", "invoice", "payment", "refund"]
        if input_data["operation_type"] not in valid_operations:
            raise ValidationError(
                f"Invalid operation type. Must be one of: {valid_operations}",
                details={"received": input_data["operation_type"]}
            )

        return True
