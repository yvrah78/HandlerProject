"""
Financial Agent for Project Handler - AI-powered version.
Handles quotations, invoicing, payments, and refunds via Stripe.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
import os

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, AgentError
from src.core.logging import get_logger

logger = get_logger("agent.financial")


class FinancialAgent(BaseAgent):
    """
    Intelligent agent responsible for all financial operations.

    Capabilities:
    - Payment processing via Stripe
    - Invoice generation and management
    - Refund processing
    - Price quotations with intelligent pricing
    - Financial reporting and tracking
    - Multi-currency support

    Modes:
    - Demo mode: Simulates operations without Stripe API calls
    - Live mode: Uses real Stripe API
    """

    def __init__(self):
        super().__init__(
            name="financial",
            description="AI-powered financial agent handling payments, invoices, and quotations"
        )

        # Initialize integrations (lazy loading)
        self._stripe = None

        # Financial operation history
        self.financial_history: List[Dict[str, Any]] = []

        # Pricing configuration
        self.base_rates = {
            "standard_delivery": 50.0,
            "express_delivery": 100.0,
            "overnight_delivery": 150.0,
            "per_mile": 2.5,
            "per_hour": 45.0
        }

        # Check for API keys
        self.demo_mode = self._check_demo_mode()

    def _check_demo_mode(self) -> bool:
        """Check if we're in demo mode (no Stripe API key)."""
        stripe_key = os.getenv("STRIPE_SECRET_KEY")

        if not stripe_key or stripe_key.startswith("your_"):
            logger.warning("No Stripe API key found - running in demo mode")
            return True

        return False

    @property
    def stripe(self):
        """Lazy load Stripe client."""
        if self._stripe is None and not self.demo_mode:
            try:
                import stripe
                api_key = os.getenv("STRIPE_SECRET_KEY")

                if api_key and not api_key.startswith("your_"):
                    stripe.api_key = api_key
                    self._stripe = stripe
                    logger.info("Stripe client initialized successfully")
                else:
                    logger.warning("Invalid Stripe API key - enabling demo mode")
                    self.demo_mode = True
            except ImportError:
                logger.error("Stripe library not installed - enabling demo mode")
                self.demo_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize Stripe: {e}")
                self.demo_mode = True

        return self._stripe

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process financial operation with intelligence.

        Args:
            input_data: Financial operation request data

        Returns:
            Dict[str, Any]: Operation result
        """
        operation = input_data.get("operation_type", "").lower()

        # Route to appropriate handler
        if operation == "payment":
            return await self._handle_payment(input_data)
        elif operation == "invoice":
            return await self._handle_invoice(input_data)
        elif operation == "refund":
            return await self._handle_refund(input_data)
        elif operation == "quotation" or operation == "quote":
            return await self._handle_quotation(input_data)
        else:
            return await self._handle_generic(input_data)

    async def _handle_payment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment processing via Stripe."""
        amount = float(input_data.get("amount", 0))
        currency = input_data.get("currency", "usd").lower()
        description = input_data.get("description", "Payment for transportation services")
        customer_email = input_data.get("customer_email")
        metadata = input_data.get("metadata", {})

        self.logger.info(f"Processing payment: ${amount} {currency}")

        if self.demo_mode or not self.stripe:
            # Demo mode response
            result = {
                "status": "demo_processed",
                "amount": amount,
                "currency": currency,
                "description": description,
                "payment_intent_id": "pi_demo_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                "note": "Demo mode - no actual charge made. Configure STRIPE_SECRET_KEY to enable.",
                "channel": "payment"
            }
        else:
            try:
                # Convert amount to cents for Stripe
                amount_cents = int(amount * 100)

                # Create payment intent
                payment_intent = self.stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency=currency,
                    description=description,
                    receipt_email=customer_email,
                    metadata=metadata
                )

                result = {
                    "status": "succeeded" if payment_intent.status == "succeeded" else "requires_payment_method",
                    "payment_intent_id": payment_intent.id,
                    "amount": amount,
                    "currency": currency,
                    "client_secret": payment_intent.client_secret,
                    "description": description,
                    "channel": "payment"
                }

                logger.info(f"Payment intent created: {payment_intent.id}")

            except Exception as e:
                logger.error(f"Failed to process payment: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "amount": amount,
                    "currency": currency,
                    "channel": "payment"
                }

        # Save to history
        self._add_to_history("payment", result)

        return result

    async def _handle_invoice(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice generation."""
        customer_email = input_data.get("customer_email")
        customer_name = input_data.get("customer_name", "Customer")
        amount = float(input_data.get("amount", 0))
        currency = input_data.get("currency", "usd").lower()
        description = input_data.get("description", "Transportation services")
        due_date = input_data.get("due_date")  # Unix timestamp or datetime string
        items = input_data.get("items", [])

        self.logger.info(f"Generating invoice for {customer_email}: ${amount}")

        if self.demo_mode or not self.stripe:
            # Demo mode response
            invoice_number = "INV-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            result = {
                "status": "demo_created",
                "invoice_id": "in_demo_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                "invoice_number": invoice_number,
                "customer_email": customer_email,
                "customer_name": customer_name,
                "amount": amount,
                "currency": currency,
                "description": description,
                "items": items,
                "note": "Demo mode - no actual invoice created. Configure STRIPE_SECRET_KEY to enable.",
                "channel": "invoice"
            }
        else:
            try:
                # In production, you'd create a Stripe customer and invoice
                # For now, using a simplified approach
                invoice_number = "INV-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")

                # Create invoice items (simplified)
                metadata = {
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "invoice_number": invoice_number,
                    "description": description
                }

                # Note: Full Stripe invoice creation requires customer object
                # This is a simplified version for demonstration
                result = {
                    "status": "created",
                    "invoice_number": invoice_number,
                    "customer_email": customer_email,
                    "customer_name": customer_name,
                    "amount": amount,
                    "currency": currency,
                    "description": description,
                    "items": items,
                    "due_date": due_date,
                    "channel": "invoice",
                    "note": "Invoice generated. Full Stripe integration requires customer setup."
                }

                logger.info(f"Invoice created: {invoice_number}")

            except Exception as e:
                logger.error(f"Failed to create invoice: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "customer_email": customer_email,
                    "channel": "invoice"
                }

        # Save to history
        self._add_to_history("invoice", result)

        return result

    async def _handle_refund(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund processing."""
        payment_intent_id = input_data.get("payment_intent_id")
        amount = input_data.get("amount")  # Optional - full refund if not specified
        reason = input_data.get("reason", "requested_by_customer")
        metadata = input_data.get("metadata", {})

        self.logger.info(f"Processing refund for payment {payment_intent_id}")

        if self.demo_mode or not self.stripe:
            # Demo mode response
            result = {
                "status": "demo_refunded",
                "refund_id": "re_demo_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                "payment_intent_id": payment_intent_id,
                "amount": amount if amount else "full",
                "reason": reason,
                "note": "Demo mode - no actual refund processed. Configure STRIPE_SECRET_KEY to enable.",
                "channel": "refund"
            }
        else:
            try:
                # Create refund
                refund_params = {
                    "payment_intent": payment_intent_id,
                    "reason": reason,
                    "metadata": metadata
                }

                if amount:
                    # Partial refund (amount in cents)
                    refund_params["amount"] = int(float(amount) * 100)

                refund = self.stripe.Refund.create(**refund_params)

                result = {
                    "status": refund.status,
                    "refund_id": refund.id,
                    "payment_intent_id": payment_intent_id,
                    "amount": refund.amount / 100 if refund.amount else "full",
                    "currency": refund.currency,
                    "reason": reason,
                    "channel": "refund"
                }

                logger.info(f"Refund processed: {refund.id}")

            except Exception as e:
                logger.error(f"Failed to process refund: {e}")
                result = {
                    "status": "failed",
                    "error": str(e),
                    "payment_intent_id": payment_intent_id,
                    "channel": "refund"
                }

        # Save to history
        self._add_to_history("refund", result)

        return result

    async def _handle_quotation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle intelligent price quotation."""
        service_type = input_data.get("service_type", "standard_delivery")
        distance_miles = float(input_data.get("distance_miles", 0))
        estimated_hours = float(input_data.get("estimated_hours", 0))
        special_requirements = input_data.get("special_requirements", [])
        urgency = input_data.get("urgency", "normal")  # normal, urgent, emergency

        self.logger.info(f"Generating quotation for {service_type}")

        # Calculate base price
        base_price = self.base_rates.get(service_type, self.base_rates["standard_delivery"])

        # Add distance charges
        distance_charge = distance_miles * self.base_rates["per_mile"]

        # Add time charges if applicable
        time_charge = estimated_hours * self.base_rates["per_hour"] if estimated_hours > 0 else 0

        # Calculate subtotal
        subtotal = base_price + distance_charge + time_charge

        # Apply urgency multiplier
        urgency_multipliers = {
            "normal": 1.0,
            "urgent": 1.3,
            "emergency": 1.6
        }
        urgency_multiplier = urgency_multipliers.get(urgency, 1.0)
        urgency_surcharge = subtotal * (urgency_multiplier - 1.0)

        # Calculate special requirements surcharge
        special_surcharge = 0.0
        if special_requirements:
            special_surcharge = len(special_requirements) * 25.0  # $25 per special requirement

        # Calculate total
        total = subtotal + urgency_surcharge + special_surcharge

        # Add tax (example: 8%)
        tax_rate = 0.08
        tax = total * tax_rate
        grand_total = total + tax

        # Build breakdown
        breakdown = {
            "base_price": round(base_price, 2),
            "distance_charge": round(distance_charge, 2),
            "time_charge": round(time_charge, 2),
            "subtotal": round(subtotal, 2),
            "urgency_surcharge": round(urgency_surcharge, 2),
            "special_requirements_surcharge": round(special_surcharge, 2),
            "tax": round(tax, 2),
            "grand_total": round(grand_total, 2)
        }

        result = {
            "status": "quote_generated",
            "quote_id": "QT-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S"),
            "service_type": service_type,
            "distance_miles": distance_miles,
            "estimated_hours": estimated_hours,
            "urgency": urgency,
            "special_requirements": special_requirements,
            "breakdown": breakdown,
            "total": round(grand_total, 2),
            "currency": "usd",
            "valid_until": (datetime.utcnow().timestamp() + 86400 * 7),  # Valid for 7 days
            "channel": "quotation"
        }

        # Save to history
        self._add_to_history("quotation", result)

        return result

    async def _handle_generic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic financial request."""
        return {
            "status": "processed",
            "message": "Generic financial handler",
            "data": input_data
        }

    def _add_to_history(self, operation_type: str, result: Dict[str, Any]):
        """Add financial operation to history."""
        self.financial_history.append({
            "operation_type": operation_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last 100 operations
        if len(self.financial_history) > 100:
            self.financial_history = self.financial_history[-100:]

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
        if not isinstance(input_data, dict):
            raise ValidationError(
                "Input must be a dictionary",
                details={"received_type": type(input_data).__name__}
            )

        # Must have operation type
        operation = input_data.get("operation_type")
        if not operation:
            raise ValidationError(
                "Missing required field: operation_type",
                details={"received_keys": list(input_data.keys())}
            )

        valid_operations = ["payment", "invoice", "refund", "quotation", "quote"]
        if operation.lower() not in valid_operations:
            raise ValidationError(
                f"Invalid operation type. Must be one of: {valid_operations}",
                details={"received": operation}
            )

        # Validate operation-specific requirements
        if operation.lower() == "payment":
            if "amount" not in input_data:
                raise ValidationError(
                    "Payment requires 'amount' field",
                    details={"operation": operation}
                )
            if float(input_data["amount"]) <= 0:
                raise ValidationError(
                    "Payment amount must be greater than 0",
                    details={"amount": input_data["amount"]}
                )

        elif operation.lower() == "invoice":
            required_fields = ["amount", "customer_email"]
            for field in required_fields:
                if field not in input_data:
                    raise ValidationError(
                        f"Invoice requires '{field}' field",
                        details={"operation": operation}
                    )

        elif operation.lower() == "refund":
            if "payment_intent_id" not in input_data:
                raise ValidationError(
                    "Refund requires 'payment_intent_id' field",
                    details={"operation": operation}
                )

        return True

    def get_financial_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get financial operation history."""
        if limit:
            return self.financial_history[-limit:]
        return self.financial_history

    def clear_history(self):
        """Clear financial history."""
        self.financial_history = []
        logger.info("Financial history cleared")

    def get_pricing_info(self) -> Dict[str, Any]:
        """Get current pricing configuration."""
        return {
            "base_rates": self.base_rates,
            "tax_rate": 0.08,
            "urgency_multipliers": {
                "normal": 1.0,
                "urgent": 1.3,
                "emergency": 1.6
            },
            "special_requirement_fee": 25.0
        }

    def update_base_rate(self, service_type: str, rate: float):
        """Update a base rate."""
        if service_type in self.base_rates:
            old_rate = self.base_rates[service_type]
            self.base_rates[service_type] = rate
            logger.info(f"Updated {service_type} rate from ${old_rate} to ${rate}")
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced agent status."""
        base_status = super().get_status()
        base_status.update({
            "demo_mode": self.demo_mode,
            "stripe_enabled": self.stripe is not None,
            "total_operations": len(self.financial_history),
            "supported_operations": ["payment", "invoice", "refund", "quotation"],
            "supported_currencies": ["usd", "eur", "gbp"],
            "pricing_configured": bool(self.base_rates)
        })
        return base_status
