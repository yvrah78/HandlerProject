"""
Integration tests for Stripe client.

These tests use mocking to avoid actual API calls during testing.
For real integration testing with Stripe test credentials, set:
- STRIPE_SECRET_KEY to your test secret key (starts with sk_test_)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.integrations.stripe_client import StripeClient
from src.core.exceptions import IntegrationError, ConfigurationError


class TestStripeClient:
    """Test suite for Stripe client."""

    @pytest.fixture
    def mock_stripe_settings(self):
        """Mock settings with Stripe credentials."""
        with patch('src.integrations.stripe_client.settings') as mock_settings:
            mock_settings.stripe_secret_key = "sk_test_abc123"
            yield mock_settings

    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe module."""
        with patch('src.integrations.stripe_client.stripe') as mock_stripe:
            # Mock successful account retrieval for initialization
            mock_stripe.Account.retrieve.return_value = Mock()
            yield mock_stripe

    @pytest.mark.asyncio
    async def test_init_success(self, mock_stripe_settings, mock_stripe):
        """Test successful Stripe client initialization."""
        client = StripeClient()

        assert client.api_key == "sk_test_abc123"
        assert mock_stripe.api_key == "sk_test_abc123"
        mock_stripe.Account.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_missing_credentials(self):
        """Test initialization fails with missing credentials."""
        with patch('src.integrations.stripe_client.settings') as mock_settings:
            mock_settings.stripe_secret_key = ""

            with pytest.raises(ConfigurationError) as exc_info:
                StripeClient()

            assert "STRIPE_SECRET_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self, mock_stripe_settings, mock_stripe):
        """Test successful payment intent creation."""
        # Setup mock payment intent
        mock_pi = Mock()
        mock_pi.id = "pi_test123"
        mock_pi.amount = 10000  # $100.00 in cents
        mock_pi.currency = "usd"
        mock_pi.status = "requires_payment_method"
        mock_pi.client_secret = "pi_test123_secret_abc"
        mock_pi.customer = None
        mock_pi.description = "Test payment"
        mock_pi.created = 1234567890

        mock_stripe.PaymentIntent.create.return_value = mock_pi

        # Create client and payment intent
        client = StripeClient()
        result = await client.create_payment_intent(
            amount=100.00,
            currency="usd",
            description="Test payment"
        )

        # Assertions
        assert result["id"] == "pi_test123"
        assert result["amount"] == 100.00
        assert result["amount_cents"] == 10000
        assert result["currency"] == "usd"
        assert result["status"] == "requires_payment_method"
        assert result["client_secret"] == "pi_test123_secret_abc"

        mock_stripe.PaymentIntent.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_intent_with_customer(self, mock_stripe_settings, mock_stripe):
        """Test payment intent creation with customer."""
        mock_pi = Mock()
        mock_pi.id = "pi_test123"
        mock_pi.amount = 5000
        mock_pi.currency = "usd"
        mock_pi.status = "requires_payment_method"
        mock_pi.client_secret = "pi_test123_secret"
        mock_pi.customer = "cus_test123"
        mock_pi.description = "Booking payment"
        mock_pi.created = 1234567890

        mock_stripe.PaymentIntent.create.return_value = mock_pi

        client = StripeClient()
        result = await client.create_payment_intent(
            amount=50.00,
            customer_id="cus_test123",
            description="Booking payment"
        )

        assert result["customer"] == "cus_test123"

    @pytest.mark.asyncio
    async def test_create_payment_intent_card_error(self, mock_stripe_settings, mock_stripe):
        """Test payment intent creation with card error."""
        from stripe.error import CardError

        # Setup mock card error
        card_error = CardError(
            message="Your card was declined",
            param="card",
            code="card_declined"
        )
        card_error.user_message = "Your card was declined"
        card_error.decline_code = "generic_decline"

        mock_stripe.PaymentIntent.create.side_effect = card_error

        client = StripeClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.create_payment_intent(amount=100.00)

        assert "Card error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_customer_success(self, mock_stripe_settings, mock_stripe):
        """Test successful customer creation."""
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        mock_customer.email = "customer@example.com"
        mock_customer.name = "John Doe"
        mock_customer.phone = "+15555551234"
        mock_customer.created = 1234567890

        mock_stripe.Customer.create.return_value = mock_customer

        client = StripeClient()
        result = await client.create_customer(
            email="customer@example.com",
            name="John Doe",
            phone="+15555551234"
        )

        assert result["id"] == "cus_test123"
        assert result["email"] == "customer@example.com"
        assert result["name"] == "John Doe"
        assert result["phone"] == "+15555551234"

    @pytest.mark.asyncio
    async def test_retrieve_customer_success(self, mock_stripe_settings, mock_stripe):
        """Test successful customer retrieval."""
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        mock_customer.email = "customer@example.com"
        mock_customer.name = "John Doe"
        mock_customer.phone = "+15555551234"
        mock_customer.created = 1234567890
        mock_customer.balance = 0

        mock_stripe.Customer.retrieve.return_value = mock_customer

        client = StripeClient()
        result = await client.retrieve_customer("cus_test123")

        assert result["id"] == "cus_test123"
        assert result["balance"] == 0

    @pytest.mark.asyncio
    async def test_create_invoice_success(self, mock_stripe_settings, mock_stripe):
        """Test successful invoice creation."""
        mock_invoice = Mock()
        mock_invoice.id = "in_test123"
        mock_invoice.customer = "cus_test123"
        mock_invoice.status = "draft"
        mock_invoice.amount_due = 10000  # $100.00 in cents
        mock_invoice.currency = "usd"
        mock_invoice.hosted_invoice_url = "https://invoice.stripe.com/i/test123"
        mock_invoice.invoice_pdf = "https://invoice.stripe.com/i/test123/pdf"

        mock_stripe.Invoice.create.return_value = mock_invoice

        client = StripeClient()
        result = await client.create_invoice(
            customer_id="cus_test123",
            description="Monthly invoice"
        )

        assert result["id"] == "in_test123"
        assert result["customer"] == "cus_test123"
        assert result["amount_due"] == 100.00  # Converted to dollars
        assert result["currency"] == "usd"

    @pytest.mark.asyncio
    async def test_process_refund_full_success(self, mock_stripe_settings, mock_stripe):
        """Test successful full refund."""
        mock_refund = Mock()
        mock_refund.id = "re_test123"
        mock_refund.payment_intent = "pi_test123"
        mock_refund.amount = 10000  # $100.00 in cents
        mock_refund.currency = "usd"
        mock_refund.status = "succeeded"
        mock_refund.reason = None
        mock_refund.created = 1234567890

        mock_stripe.Refund.create.return_value = mock_refund

        client = StripeClient()
        result = await client.process_refund(payment_intent_id="pi_test123")

        assert result["id"] == "re_test123"
        assert result["payment_intent"] == "pi_test123"
        assert result["amount"] == 100.00
        assert result["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_process_refund_partial_success(self, mock_stripe_settings, mock_stripe):
        """Test successful partial refund."""
        mock_refund = Mock()
        mock_refund.id = "re_test123"
        mock_refund.payment_intent = "pi_test123"
        mock_refund.amount = 5000  # $50.00 in cents
        mock_refund.currency = "usd"
        mock_refund.status = "succeeded"
        mock_refund.reason = "requested_by_customer"
        mock_refund.created = 1234567890

        mock_stripe.Refund.create.return_value = mock_refund

        client = StripeClient()
        result = await client.process_refund(
            payment_intent_id="pi_test123",
            amount=50.00,
            reason="requested_by_customer"
        )

        assert result["amount"] == 50.00
        assert result["reason"] == "requested_by_customer"

    @pytest.mark.asyncio
    async def test_retrieve_payment_intent_success(self, mock_stripe_settings, mock_stripe):
        """Test successful payment intent retrieval."""
        mock_pi = Mock()
        mock_pi.id = "pi_test123"
        mock_pi.amount = 10000
        mock_pi.currency = "usd"
        mock_pi.status = "succeeded"
        mock_pi.customer = "cus_test123"
        mock_pi.description = "Test payment"
        mock_pi.created = 1234567890

        mock_stripe.PaymentIntent.retrieve.return_value = mock_pi

        client = StripeClient()
        result = await client.retrieve_payment_intent("pi_test123")

        assert result["id"] == "pi_test123"
        assert result["amount"] == 100.00
        assert result["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_list_customer_payments_success(self, mock_stripe_settings, mock_stripe):
        """Test successful listing of customer payments."""
        mock_pi1 = Mock()
        mock_pi1.id = "pi_test1"
        mock_pi1.amount = 10000
        mock_pi1.currency = "usd"
        mock_pi1.status = "succeeded"
        mock_pi1.created = 1234567890

        mock_pi2 = Mock()
        mock_pi2.id = "pi_test2"
        mock_pi2.amount = 5000
        mock_pi2.currency = "usd"
        mock_pi2.status = "requires_payment_method"
        mock_pi2.created = 1234567891

        mock_list = Mock()
        mock_list.data = [mock_pi1, mock_pi2]

        mock_stripe.PaymentIntent.list.return_value = mock_list

        client = StripeClient()
        result = await client.list_customer_payments("cus_test123", limit=10)

        assert len(result) == 2
        assert result[0]["id"] == "pi_test1"
        assert result[0]["amount"] == 100.00
        assert result[1]["id"] == "pi_test2"
        assert result[1]["amount"] == 50.00

    @pytest.mark.asyncio
    async def test_stripe_api_error(self, mock_stripe_settings, mock_stripe):
        """Test handling of Stripe API errors."""
        from stripe.error import StripeError

        mock_stripe.PaymentIntent.create.side_effect = StripeError("API Error")

        client = StripeClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.create_payment_intent(amount=100.00)

        assert "Stripe API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_stripe_settings, mock_stripe):
        """Test retry logic on transient failures."""
        from stripe.error import StripeError

        # Setup mock to fail twice then succeed
        mock_pi = Mock()
        mock_pi.id = "pi_test123"
        mock_pi.amount = 10000
        mock_pi.currency = "usd"
        mock_pi.status = "requires_payment_method"
        mock_pi.client_secret = "pi_test123_secret"
        mock_pi.customer = None
        mock_pi.description = None
        mock_pi.created = 1234567890

        mock_stripe.PaymentIntent.create.side_effect = [
            StripeError("Service unavailable"),
            StripeError("Service unavailable"),
            mock_pi
        ]

        client = StripeClient()

        # Should succeed after retries
        result = await client.create_payment_intent(amount=100.00)

        assert result["id"] == "pi_test123"
        # Should have been called 3 times (initial + 2 retries)
        assert mock_stripe.PaymentIntent.create.call_count == 3
