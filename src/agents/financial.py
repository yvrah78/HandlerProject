"""
Financial Agent for Project Handler.
Handles quotations, invoicing, payments, and financial operations via Stripe.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, IntegrationError
from src.integrations.stripe_client import StripeClient


class FinancialAgent(BaseAgent):
    """
    Agent responsible for all financial operations.

    Integration:
    - Stripe: Payment processing, invoicing, subscriptions

    Capabilities:
    - Price quotations and calculations
    - Invoice generation and management
    - Payment processing (one-time and recurring)
    - Refund processing
    - Subscription management
    - Financial reporting and analytics
    """

    def __init__(self):
        """Initialize Financial Agent with Stripe client."""
        super().__init__(
            name="financial",
            description="Handles quotations, invoicing, and payment processing via Stripe"
        )

        # Initialize Stripe integration
        self.stripe = StripeClient()

        # Track financial statistics
        self.stats = {
            "total_transactions": 0,
            "payments_processed": 0,
            "invoices_created": 0,
            "refunds_processed": 0,
            "total_revenue": 0.0,
            "failed_transactions": 0
        }

        self.logger.info(f"Financial Agent initialized - Stripe: {self.stripe.enabled}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process financial operation.

        Args:
            input_data: Must contain 'operation_type' and relevant data

        Returns:
            Dict[str, Any]: Financial operation result

        Raises:
            ValidationError: If input is invalid
            IntegrationError: If operation fails
        """
        await self.validate_input(input_data)

        operation = input_data.get("operation_type")
        self.logger.info(f"Processing {operation} operation")

        # Route to appropriate handler
        if operation == "quotation":
            result = await self.create_quotation(input_data)
        elif operation == "invoice":
            result = await self.create_invoice(input_data)
        elif operation == "payment":
            result = await self.process_payment(input_data)
        elif operation == "refund":
            result = await self.process_refund(input_data)
        elif operation == "subscription":
            result = await self.create_subscription(input_data)
        else:
            raise ValidationError(
                f"Unknown operation type: {operation}",
                details={"received": operation}
            )

        # Update statistics
        self.stats["total_transactions"] += 1

        return result

    async def create_quotation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate price quotation.

        Args:
            data: Quotation details (service_type, distance, etc.)

        Returns:
            dict: Quotation with calculated price
        """
        service_type = data.get("service_type", "standard")
        distance = data.get("distance", 0)  # in km
        duration = data.get("duration", 0)  # in minutes
        additional_charges = data.get("additional_charges", 0.0)

        self.logger.info(f"Creating quotation for {service_type} service")

        # Calculate base price (simplified pricing model)
        base_rates = {
            "standard": {"base": 10.0, "per_km": 1.5, "per_min": 0.3},
            "premium": {"base": 20.0, "per_km": 2.5, "per_min": 0.5},
            "luxury": {"base": 35.0, "per_km": 4.0, "per_min": 0.8}
        }

        rates = base_rates.get(service_type, base_rates["standard"])
        calculated_price = (
            rates["base"] +
            (distance * rates["per_km"]) +
            (duration * rates["per_min"]) +
            additional_charges
        )

        # Round to 2 decimals
        total_price = round(calculated_price, 2)

        return {
            "operation_type": "quotation",
            "service_type": service_type,
            "distance_km": distance,
            "duration_min": duration,
            "base_price": rates["base"],
            "distance_charge": round(distance * rates["per_km"], 2),
            "time_charge": round(duration * rates["per_min"], 2),
            "additional_charges": additional_charges,
            "total_price": total_price,
            "currency": "USD",
            "valid_until": datetime.utcnow().isoformat(),
            "status": "calculated"
        }

    async def create_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create invoice via Stripe.

        Args:
            data: Invoice details with customer_id and amount

        Returns:
            dict: Invoice creation result
        """
        customer_id = data.get("customer_id")
        amount = data.get("amount")
        description = data.get("description")

        self.logger.info(f"Creating invoice for customer {customer_id}")

        try:
            result = await self.stripe.create_invoice(
                customer_id=customer_id,
                amount=amount,
                description=description
            )

            self.stats["invoices_created"] += 1

            return {
                "operation_type": "invoice",
                "status": "created",
                "invoice_id": result["id"],
                "customer_id": customer_id,
                "amount": result["amount"],
                "invoice_url": result.get("hosted_invoice_url"),
                "pdf_url": result.get("invoice_pdf"),
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to create invoice: {str(e)}")
            self.stats["failed_transactions"] += 1
            return {
                "operation_type": "invoice",
                "status": "failed",
                "customer_id": customer_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def process_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payment via Stripe.

        Args:
            data: Payment details with amount and customer info

        Returns:
            dict: Payment processing result
        """
        amount = data.get("amount")
        customer_id = data.get("customer_id")
        description = data.get("description")
        currency = data.get("currency", "usd")

        self.logger.info(f"Processing payment of ${amount} for customer {customer_id}")

        try:
            result = await self.stripe.create_payment_intent(
                amount=amount,
                currency=currency,
                customer_id=customer_id,
                description=description
            )

            self.stats["payments_processed"] += 1
            self.stats["total_revenue"] += amount

            return {
                "operation_type": "payment",
                "status": "created",
                "payment_id": result["id"],
                "client_secret": result["client_secret"],
                "amount": result["amount"],
                "currency": result["currency"],
                "customer_id": customer_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to process payment: {str(e)}")
            self.stats["failed_transactions"] += 1
            return {
                "operation_type": "payment",
                "status": "failed",
                "customer_id": customer_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def process_refund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process refund via Stripe.

        Args:
            data: Refund details with payment_id

        Returns:
            dict: Refund processing result
        """
        payment_id = data.get("payment_id")
        amount = data.get("amount")
        reason = data.get("reason")

        self.logger.info(f"Processing refund for payment {payment_id}")

        try:
            result = await self.stripe.process_refund(
                payment_intent_id=payment_id,
                amount=amount,
                reason=reason
            )

            self.stats["refunds_processed"] += 1

            return {
                "operation_type": "refund",
                "status": "processed",
                "refund_id": result["id"],
                "payment_id": payment_id,
                "amount": result["amount"],
                "currency": result["currency"],
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to process refund: {str(e)}")
            self.stats["failed_transactions"] += 1
            return {
                "operation_type": "refund",
                "status": "failed",
                "payment_id": payment_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def create_subscription(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create recurring subscription via Stripe.

        Args:
            data: Subscription details with customer_id and price_id

        Returns:
            dict: Subscription creation result
        """
        customer_id = data.get("customer_id")
        price_id = data.get("price_id")
        trial_days = data.get("trial_days")

        self.logger.info(f"Creating subscription for customer {customer_id}")

        try:
            result = await self.stripe.create_subscription(
                customer_id=customer_id,
                price_id=price_id,
                trial_days=trial_days
            )

            return {
                "operation_type": "subscription",
                "status": "created",
                "subscription_id": result["id"],
                "customer_id": customer_id,
                "subscription_status": result["status"],
                "current_period_end": result["current_period_end"],
                "timestamp": datetime.utcnow().isoformat()
            }

        except IntegrationError as e:
            self.logger.error(f"Failed to create subscription: {str(e)}")
            self.stats["failed_transactions"] += 1
            return {
                "operation_type": "subscription",
                "status": "failed",
                "customer_id": customer_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
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

        valid_operations = ["quotation", "invoice", "payment", "refund", "subscription"]
        if input_data["operation_type"] not in valid_operations:
            raise ValidationError(
                f"Invalid operation type. Must be one of: {valid_operations}",
                details={"received": input_data["operation_type"]}
            )

        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status including Stripe integration status.

        Returns:
            dict: Agent and integration status
        """
        return {
            "agent_name": self.name,
            "enabled": True,
            "integrations": {
                "stripe": self.stripe.get_status()
            },
            "statistics": self.stats,
            "capabilities": {
                "quotations": True,
                "invoices": self.stripe.enabled,
                "payments": self.stripe.enabled,
                "refunds": self.stripe.enabled,
                "subscriptions": self.stripe.enabled
            }
        }
