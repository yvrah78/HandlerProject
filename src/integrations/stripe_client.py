"""
Stripe integration client for Project Handler.
Handles payment processing, invoicing, and subscriptions via Stripe API.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

import stripe
from stripe.error import StripeError

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.exceptions import IntegrationError

logger = get_logger(__name__)
settings = get_settings()


class StripeClient:
    """Client for Stripe payment API integration."""

    def __init__(self):
        """Initialize Stripe client with API key."""
        self.api_key = settings.stripe_secret_key
        self.logger = logger
        self.enabled = False

        # Initialize Stripe API key if available
        if self.api_key:
            try:
                stripe.api_key = self.api_key
                self.enabled = True
                self.logger.info("Stripe client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Stripe client: {str(e)}")
                self.enabled = False
        else:
            self.logger.info("Stripe API key not provided - running in disabled mode")

    def _check_enabled(self):
        """Check if Stripe is enabled and raise error if not."""
        if not self.enabled:
            raise IntegrationError(
                "Stripe integration is not configured. Please set STRIPE_SECRET_KEY.",
                integration_name="stripe"
            )

    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        payment_method_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent for processing payments.

        Args:
            amount: Payment amount in dollars (will be converted to cents)
            currency: Currency code (default: USD)
            customer_id: Optional Stripe customer ID
            metadata: Optional metadata to attach
            description: Optional payment description
            payment_method_types: Payment methods to accept (default: ["card"])

        Returns:
            dict: Payment intent information with client_secret

        Raises:
            IntegrationError: If payment intent creation fails
        """
        self._check_enabled()
        amount_cents = int(amount * 100)  # Convert to cents
        self.logger.info(f"Creating payment intent for ${amount} {currency.upper()}")

        try:
            loop = asyncio.get_event_loop()
            payment_intent = await loop.run_in_executor(
                None,
                lambda: stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency=currency.lower(),
                    customer=customer_id,
                    metadata=metadata or {},
                    description=description,
                    payment_method_types=payment_method_types or ["card"]
                )
            )

            return {
                "id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount,
                "amount_cents": amount_cents,
                "currency": currency.upper(),
                "status": payment_intent.status,
                "customer": customer_id,
                "created": datetime.fromtimestamp(payment_intent.created).isoformat(),
                "description": description
            }

        except StripeError as e:
            self.logger.error(f"Stripe payment intent error: {str(e)}")
            raise IntegrationError(
                f"Failed to create payment intent: {str(e)}",
                integration_name="stripe"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error creating payment intent: {str(e)}")
            raise IntegrationError(
                f"Failed to create payment intent: {str(e)}",
                integration_name="stripe"
            )

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer.

        Args:
            email: Customer email address
            name: Customer name
            phone: Customer phone number
            metadata: Optional metadata

        Returns:
            dict: Customer information with Stripe customer ID

        Raises:
            IntegrationError: If customer creation fails
        """
        self._check_enabled()
        self.logger.info(f"Creating Stripe customer for {email}")

        try:
            loop = asyncio.get_event_loop()
            customer = await loop.run_in_executor(
                None,
                lambda: stripe.Customer.create(
                    email=email,
                    name=name,
                    phone=phone,
                    metadata=metadata or {}
                )
            )

            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "phone": customer.phone,
                "created": datetime.fromtimestamp(customer.created).isoformat()
            }

        except StripeError as e:
            self.logger.error(f"Stripe customer creation error: {str(e)}")
            raise IntegrationError(
                f"Failed to create customer: {str(e)}",
                integration_name="stripe"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to create customer: {str(e)}",
                integration_name="stripe"
            )

    async def create_invoice(
        self,
        customer_id: str,
        amount: float,
        description: Optional[str] = None,
        auto_advance: bool = True
    ) -> Dict[str, Any]:
        """
        Create an invoice for a customer.

        Args:
            customer_id: Stripe customer ID
            amount: Invoice amount in dollars
            description: Optional invoice description
            auto_advance: Auto-finalize invoice (default: True)

        Returns:
            dict: Invoice information with payment URL

        Raises:
            IntegrationError: If invoice creation fails
        """
        self._check_enabled()
        amount_cents = int(amount * 100)
        self.logger.info(f"Creating invoice for customer {customer_id}")

        try:
            loop = asyncio.get_event_loop()

            # Create invoice item
            invoice_item = await loop.run_in_executor(
                None,
                lambda: stripe.InvoiceItem.create(
                    customer=customer_id,
                    amount=amount_cents,
                    currency="usd",
                    description=description
                )
            )

            # Create invoice
            invoice = await loop.run_in_executor(
                None,
                lambda: stripe.Invoice.create(
                    customer=customer_id,
                    auto_advance=auto_advance
                )
            )

            # Finalize if auto_advance
            if auto_advance:
                invoice = await loop.run_in_executor(
                    None,
                    lambda: stripe.Invoice.finalize_invoice(invoice.id)
                )

            return {
                "id": invoice.id,
                "customer": customer_id,
                "amount": amount,
                "amount_cents": amount_cents,
                "status": invoice.status,
                "hosted_invoice_url": invoice.hosted_invoice_url,
                "invoice_pdf": invoice.invoice_pdf,
                "created": datetime.fromtimestamp(invoice.created).isoformat()
            }

        except StripeError as e:
            self.logger.error(f"Stripe invoice error: {str(e)}")
            raise IntegrationError(
                f"Failed to create invoice: {str(e)}",
                integration_name="stripe"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to create invoice: {str(e)}",
                integration_name="stripe"
            )

    async def process_refund(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a refund for a payment.

        Args:
            payment_intent_id: Payment intent ID to refund
            amount: Optional partial refund amount in dollars (full refund if not specified)
            reason: Optional refund reason

        Returns:
            dict: Refund information

        Raises:
            IntegrationError: If refund processing fails
        """
        self._check_enabled()
        self.logger.info(f"Processing refund for payment {payment_intent_id}")

        try:
            refund_params = {"payment_intent": payment_intent_id}

            if amount is not None:
                refund_params["amount"] = int(amount * 100)

            if reason:
                refund_params["reason"] = reason

            loop = asyncio.get_event_loop()
            refund = await loop.run_in_executor(
                None,
                lambda: stripe.Refund.create(**refund_params)
            )

            return {
                "id": refund.id,
                "payment_intent": payment_intent_id,
                "amount": refund.amount / 100,
                "amount_cents": refund.amount,
                "currency": refund.currency.upper(),
                "status": refund.status,
                "reason": refund.reason,
                "created": datetime.fromtimestamp(refund.created).isoformat()
            }

        except StripeError as e:
            self.logger.error(f"Stripe refund error: {str(e)}")
            raise IntegrationError(
                f"Failed to process refund: {str(e)}",
                integration_name="stripe"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to process refund: {str(e)}",
                integration_name="stripe"
            )

    async def get_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get status of a payment intent.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            dict: Payment status information

        Raises:
            IntegrationError: If status check fails
        """
        self._check_enabled()
        self.logger.info(f"Checking status for payment {payment_intent_id}")

        try:
            loop = asyncio.get_event_loop()
            payment_intent = await loop.run_in_executor(
                None,
                lambda: stripe.PaymentIntent.retrieve(payment_intent_id)
            )

            return {
                "id": payment_intent.id,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency.upper(),
                "status": payment_intent.status,
                "customer": payment_intent.customer,
                "created": datetime.fromtimestamp(payment_intent.created).isoformat(),
                "charges": len(payment_intent.charges.data) if payment_intent.charges else 0
            }

        except StripeError as e:
            self.logger.error(f"Stripe payment status error: {str(e)}")
            raise IntegrationError(
                f"Failed to get payment status: {str(e)}",
                integration_name="stripe"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to get payment status: {str(e)}",
                integration_name="stripe"
            )

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription for recurring payments.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the subscription
            trial_days: Optional trial period in days

        Returns:
            dict: Subscription information

        Raises:
            IntegrationError: If subscription creation fails
        """
        self._check_enabled()
        self.logger.info(f"Creating subscription for customer {customer_id}")

        try:
            sub_params = {
                "customer": customer_id,
                "items": [{"price": price_id}]
            }

            if trial_days:
                sub_params["trial_period_days"] = trial_days

            loop = asyncio.get_event_loop()
            subscription = await loop.run_in_executor(
                None,
                lambda: stripe.Subscription.create(**sub_params)
            )

            return {
                "id": subscription.id,
                "customer": customer_id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                "trial_end": datetime.fromtimestamp(subscription.trial_end).isoformat() if subscription.trial_end else None
            }

        except StripeError as e:
            self.logger.error(f"Stripe subscription error: {str(e)}")
            raise IntegrationError(
                f"Failed to create subscription: {str(e)}",
                integration_name="stripe"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to create subscription: {str(e)}",
                integration_name="stripe"
            )

    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            dict: Cancelled subscription information

        Raises:
            IntegrationError: If cancellation fails
        """
        self._check_enabled()
        self.logger.info(f"Cancelling subscription {subscription_id}")

        try:
            loop = asyncio.get_event_loop()
            subscription = await loop.run_in_executor(
                None,
                lambda: stripe.Subscription.delete(subscription_id)
            )

            return {
                "id": subscription.id,
                "status": subscription.status,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at).isoformat() if subscription.canceled_at else None
            }

        except StripeError as e:
            self.logger.error(f"Stripe cancellation error: {str(e)}")
            raise IntegrationError(
                f"Failed to cancel subscription: {str(e)}",
                integration_name="stripe"
            )
        except Exception as e:
            raise IntegrationError(
                f"Failed to cancel subscription: {str(e)}",
                integration_name="stripe"
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get Stripe client status.

        Returns:
            dict: Client configuration and status
        """
        return {
            "enabled": self.enabled,
            "configured": bool(self.api_key),
            "api_key": self.api_key[:12] + "..." if self.api_key else None,
            "capabilities": {
                "payments": self.enabled,
                "refunds": self.enabled,
                "invoices": self.enabled,
                "subscriptions": self.enabled,
                "customers": self.enabled
            }
        }
