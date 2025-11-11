"""
Stripe integration client for Project Handler.
Handles payment processing via Stripe API.

Rate Limits:
- Default: 100 requests per second in live mode
- Test mode: 25 requests per second
- Handles automatic retry with exponential backoff

Documentation: https://stripe.com/docs/api
"""
from typing import Optional, Dict, Any, List
import stripe
from stripe.error import StripeError, CardError, RateLimitError, InvalidRequestError, AuthenticationError

from src.core.config import get_settings
from src.core.exceptions import IntegrationError
from src.integrations.base import BaseIntegration

settings = get_settings()


class StripeClient(BaseIntegration):
    """
    Client for Stripe API integration.

    Provides payment processing functionality including:
    - Payment intents (one-time payments)
    - Customers management
    - Subscriptions
    - Invoices
    - Refunds
    """

    def __init__(self):
        """Initialize Stripe client with API key from settings."""
        super().__init__("stripe")

        self.api_key = settings.stripe_secret_key

        # Validate configuration
        self._validate_config()

        # Initialize Stripe
        try:
            stripe.api_key = self.api_key
            # Test the API key by making a simple request
            stripe.Account.retrieve()
            self.logger.info("Stripe client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Stripe client: {str(e)}")
            raise IntegrationError(
                f"Failed to initialize Stripe client: {str(e)}",
                integration_name=self.integration_name,
                details={"error": str(e)}
            )

    def _validate_config(self) -> None:
        """Validate that all required Stripe configuration is present."""
        self._check_config_value(self.api_key, "STRIPE_SECRET_KEY")

    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        automatic_payment_methods: bool = True
    ) -> Dict[str, Any]:
        """
        Create a payment intent for one-time payment.

        Args:
            amount: Payment amount in dollars (will be converted to cents)
            currency: Currency code (default: "usd")
            customer_id: Optional Stripe customer ID
            payment_method: Optional payment method ID
            description: Optional payment description
            metadata: Optional metadata dictionary
            automatic_payment_methods: Enable automatic payment methods

        Returns:
            dict: Payment intent information

        Raises:
            IntegrationError: If payment intent creation fails

        Example:
            >>> client = StripeClient()
            >>> result = await client.create_payment_intent(
            ...     amount=100.50,
            ...     currency="usd",
            ...     description="Booking payment"
            ... )
        """
        # Convert amount to cents (smallest currency unit)
        amount_cents = self._format_currency_amount(amount, currency)

        self.logger.info(f"Creating payment intent for {amount} {currency}")

        async def _create():
            try:
                params = {
                    "amount": amount_cents,
                    "currency": currency.lower(),
                }

                if description:
                    params["description"] = description

                if customer_id:
                    params["customer"] = customer_id

                if payment_method:
                    params["payment_method"] = payment_method
                    params["confirm"] = True

                if metadata:
                    params["metadata"] = metadata

                if automatic_payment_methods:
                    params["automatic_payment_methods"] = {"enabled": True}

                payment_intent = stripe.PaymentIntent.create(**params)

                result = {
                    "id": payment_intent.id,
                    "amount": amount,
                    "amount_cents": payment_intent.amount,
                    "currency": payment_intent.currency,
                    "status": payment_intent.status,
                    "client_secret": payment_intent.client_secret,
                    "customer": payment_intent.customer,
                    "description": payment_intent.description,
                    "created": payment_intent.created
                }

                self._log_api_call(
                    "create_payment_intent",
                    {"amount": amount, "currency": currency, "status": payment_intent.status}
                )
                return result

            except CardError as e:
                # Card-specific errors
                self._log_api_call(
                    "create_payment_intent",
                    {"amount": amount, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Card error: {e.user_message}",
                    integration_name=self.integration_name,
                    details={
                        "code": e.code,
                        "decline_code": e.decline_code,
                        "param": e.param
                    }
                )
            except (RateLimitError, InvalidRequestError, AuthenticationError, StripeError) as e:
                self._log_api_call(
                    "create_payment_intent",
                    {"amount": amount, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Stripe API error: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e), "type": type(e).__name__}
                )

        return await self._retry_on_failure(_create, max_retries=3)

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
            metadata: Optional metadata dictionary

        Returns:
            dict: Customer information

        Raises:
            IntegrationError: If customer creation fails

        Example:
            >>> client = StripeClient()
            >>> result = await client.create_customer(
            ...     email="customer@example.com",
            ...     name="John Doe"
            ... )
        """
        email = self._sanitize_email(email)

        self.logger.info(f"Creating Stripe customer for {email}")

        async def _create():
            try:
                params = {"email": email}

                if name:
                    params["name"] = name

                if phone:
                    params["phone"] = self._sanitize_phone_number(phone)

                if metadata:
                    params["metadata"] = metadata

                customer = stripe.Customer.create(**params)

                result = {
                    "id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                    "phone": customer.phone,
                    "created": customer.created
                }

                self._log_api_call("create_customer", {"email": email})
                return result

            except StripeError as e:
                self._log_api_call("create_customer", {"email": email, "error": str(e)}, success=False)
                raise IntegrationError(
                    f"Failed to create customer: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e)}
                )

        return await self._retry_on_failure(_create, max_retries=3)

    async def retrieve_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve a Stripe customer by ID.

        Args:
            customer_id: Stripe customer ID

        Returns:
            dict: Customer information

        Raises:
            IntegrationError: If customer retrieval fails
        """
        self.logger.info(f"Retrieving customer {customer_id}")

        async def _retrieve():
            try:
                customer = stripe.Customer.retrieve(customer_id)

                return {
                    "id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                    "phone": customer.phone,
                    "created": customer.created,
                    "balance": customer.balance
                }

            except StripeError as e:
                raise IntegrationError(
                    f"Failed to retrieve customer: {str(e)}",
                    integration_name=self.integration_name,
                    details={"customer_id": customer_id, "error": str(e)}
                )

        return await self._retry_on_failure(_retrieve, max_retries=2)

    async def create_invoice(
        self,
        customer_id: str,
        description: Optional[str] = None,
        auto_advance: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe invoice.

        Args:
            customer_id: Stripe customer ID
            description: Invoice description
            auto_advance: Automatically finalize and attempt payment
            metadata: Optional metadata dictionary

        Returns:
            dict: Invoice information

        Raises:
            IntegrationError: If invoice creation fails
        """
        self.logger.info(f"Creating invoice for customer {customer_id}")

        async def _create():
            try:
                params = {
                    "customer": customer_id,
                    "auto_advance": auto_advance
                }

                if description:
                    params["description"] = description

                if metadata:
                    params["metadata"] = metadata

                invoice = stripe.Invoice.create(**params)

                result = {
                    "id": invoice.id,
                    "customer": invoice.customer,
                    "status": invoice.status,
                    "amount_due": invoice.amount_due / 100,  # Convert to dollars
                    "currency": invoice.currency,
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                    "invoice_pdf": invoice.invoice_pdf
                }

                self._log_api_call("create_invoice", {"customer_id": customer_id})
                return result

            except StripeError as e:
                self._log_api_call(
                    "create_invoice",
                    {"customer_id": customer_id, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Failed to create invoice: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e)}
                )

        return await self._retry_on_failure(_create, max_retries=3)

    async def process_refund(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a refund for a payment.

        Args:
            payment_intent_id: Payment intent ID to refund
            amount: Optional partial refund amount in dollars (full refund if not specified)
            reason: Optional reason for refund ("duplicate", "fraudulent", "requested_by_customer")
            metadata: Optional metadata dictionary

        Returns:
            dict: Refund information

        Raises:
            IntegrationError: If refund processing fails
        """
        self.logger.info(f"Processing refund for payment {payment_intent_id}")

        async def _refund():
            try:
                params = {"payment_intent": payment_intent_id}

                if amount:
                    # Convert to cents
                    params["amount"] = int(amount * 100)

                if reason:
                    params["reason"] = reason

                if metadata:
                    params["metadata"] = metadata

                refund = stripe.Refund.create(**params)

                result = {
                    "id": refund.id,
                    "payment_intent": refund.payment_intent,
                    "amount": refund.amount / 100,  # Convert to dollars
                    "currency": refund.currency,
                    "status": refund.status,
                    "reason": refund.reason,
                    "created": refund.created
                }

                self._log_api_call(
                    "process_refund",
                    {"payment_intent_id": payment_intent_id, "status": refund.status}
                )
                return result

            except StripeError as e:
                self._log_api_call(
                    "process_refund",
                    {"payment_intent_id": payment_intent_id, "error": str(e)},
                    success=False
                )
                raise IntegrationError(
                    f"Failed to process refund: {str(e)}",
                    integration_name=self.integration_name,
                    details={"error": str(e)}
                )

        return await self._retry_on_failure(_refund, max_retries=3)

    async def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent by ID.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            dict: Payment intent information

        Raises:
            IntegrationError: If retrieval fails
        """
        self.logger.info(f"Retrieving payment intent {payment_intent_id}")

        async def _retrieve():
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

                return {
                    "id": payment_intent.id,
                    "amount": payment_intent.amount / 100,
                    "currency": payment_intent.currency,
                    "status": payment_intent.status,
                    "customer": payment_intent.customer,
                    "description": payment_intent.description,
                    "created": payment_intent.created
                }

            except StripeError as e:
                raise IntegrationError(
                    f"Failed to retrieve payment intent: {str(e)}",
                    integration_name=self.integration_name,
                    details={"payment_intent_id": payment_intent_id, "error": str(e)}
                )

        return await self._retry_on_failure(_retrieve, max_retries=2)

    async def list_customer_payments(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List payment intents for a customer.

        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of payments to return

        Returns:
            list: List of payment intent dictionaries

        Raises:
            IntegrationError: If listing fails
        """
        self.logger.info(f"Listing payments for customer {customer_id}")

        async def _list():
            try:
                payment_intents = stripe.PaymentIntent.list(
                    customer=customer_id,
                    limit=limit
                )

                results = []
                for pi in payment_intents.data:
                    results.append({
                        "id": pi.id,
                        "amount": pi.amount / 100,
                        "currency": pi.currency,
                        "status": pi.status,
                        "created": pi.created
                    })

                return results

            except StripeError as e:
                raise IntegrationError(
                    f"Failed to list customer payments: {str(e)}",
                    integration_name=self.integration_name,
                    details={"customer_id": customer_id, "error": str(e)}
                )

        return await self._retry_on_failure(_list, max_retries=2)
