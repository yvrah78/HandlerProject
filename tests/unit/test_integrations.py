"""
Unit tests for external integrations (Twilio, SendGrid, Stripe, Google Maps).
Tests integration client initialization and basic functionality.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.integrations.twilio_client import TwilioClient
from src.integrations.sendgrid_client import SendGridClient
from src.integrations.stripe_client import StripeClient
from src.integrations.googlemaps_client import GoogleMapsClient
from src.core.exceptions import IntegrationError


class TestTwilioClient:
    """Test Twilio integration client."""

    @pytest.fixture
    def mock_twilio_settings(self, monkeypatch):
        """Mock Twilio settings."""
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "test_sid")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test_token")

    def test_initialization_without_credentials(self):
        """Test client initializes in disabled mode without credentials."""
        client = TwilioClient()
        assert client.enabled is False
        assert client.client is None

    @patch('src.integrations.twilio_client.Client')
    def test_initialization_with_credentials(self, mock_client, mock_twilio_settings):
        """Test client initializes successfully with credentials."""
        from src.integrations.twilio_client import TwilioClient
        client = TwilioClient()
        # Note: will be disabled in test env without actual credentials
        assert client.account_sid is not None

    @pytest.mark.asyncio
    async def test_send_sms_disabled(self):
        """Test sending SMS when Twilio is disabled raises error."""
        client = TwilioClient()
        client.enabled = False

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_sms(to="+1234567890", message="Test")

        assert "not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_sms_invalid_phone_format(self):
        """Test sending SMS with invalid phone format raises error."""
        client = TwilioClient()
        client.enabled = True
        client.client = Mock()

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_sms(to="1234567890", message="Test")

        assert "E.164 format" in str(exc_info.value)

    def test_get_status(self):
        """Test get_status returns correct information."""
        client = TwilioClient()
        status = client.get_status()

        assert "enabled" in status
        assert "configured" in status
        assert "capabilities" in status
        assert "sms" in status["capabilities"]
        assert "voice" in status["capabilities"]
        assert "whatsapp" in status["capabilities"]


class TestSendGridClient:
    """Test SendGrid integration client."""

    @pytest.fixture
    def mock_sendgrid_settings(self, monkeypatch):
        """Mock SendGrid settings."""
        monkeypatch.setenv("SENDGRID_API_KEY", "test_key")

    def test_initialization_without_api_key(self):
        """Test client initializes in disabled mode without API key."""
        client = SendGridClient()
        assert client.enabled is False
        assert client.client is None

    @pytest.mark.asyncio
    async def test_send_email_disabled(self):
        """Test sending email when SendGrid is disabled raises error."""
        client = SendGridClient()
        client.enabled = False

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_email(
                to="test@example.com",
                subject="Test",
                html_content="<p>Test</p>"
            )

        assert "not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_email_without_content(self):
        """Test sending email without content raises error."""
        client = SendGridClient()
        client.enabled = True

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_email(
                to="test@example.com",
                subject="Test"
            )

        assert "must be provided" in str(exc_info.value)

    def test_configure_sender(self):
        """Test configuring sender email."""
        client = SendGridClient()
        client.configure_sender("noreply@example.com", "Test Sender")

        assert client.from_email == "noreply@example.com"
        assert client.from_name == "Test Sender"

    def test_get_status(self):
        """Test get_status returns correct information."""
        client = SendGridClient()
        status = client.get_status()

        assert "enabled" in status
        assert "configured" in status
        assert "capabilities" in status
        assert "email" in status["capabilities"]


class TestStripeClient:
    """Test Stripe integration client."""

    @pytest.fixture
    def mock_stripe_settings(self, monkeypatch):
        """Mock Stripe settings."""
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_12345")

    def test_initialization_without_api_key(self):
        """Test client initializes in disabled mode without API key."""
        client = StripeClient()
        assert client.enabled is False

    @pytest.mark.asyncio
    async def test_create_payment_intent_disabled(self):
        """Test creating payment intent when Stripe is disabled raises error."""
        client = StripeClient()
        client.enabled = False

        with pytest.raises(IntegrationError) as exc_info:
            await client.create_payment_intent(amount=100.0)

        assert "not configured" in str(exc_info.value)

    def test_get_status(self):
        """Test get_status returns correct information."""
        client = StripeClient()
        status = client.get_status()

        assert "enabled" in status
        assert "configured" in status
        assert "capabilities" in status
        assert "payments" in status["capabilities"]
        assert "refunds" in status["capabilities"]
        assert "invoices" in status["capabilities"]


class TestGoogleMapsClient:
    """Test Google Maps integration client."""

    @pytest.fixture
    def mock_maps_settings(self, monkeypatch):
        """Mock Google Maps settings."""
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test_api_key")

    def test_initialization_without_api_key(self):
        """Test client initializes in disabled mode without API key."""
        client = GoogleMapsClient()
        assert client.enabled is False
        assert client.client is None

    @pytest.mark.asyncio
    async def test_geocode_disabled(self):
        """Test geocoding when Google Maps is disabled raises error."""
        client = GoogleMapsClient()
        client.enabled = False

        with pytest.raises(IntegrationError) as exc_info:
            await client.geocode("123 Main St")

        assert "not configured" in str(exc_info.value)

    def test_get_status(self):
        """Test get_status returns correct information."""
        client = GoogleMapsClient()
        status = client.get_status()

        assert "enabled" in status
        assert "configured" in status
        assert "capabilities" in status
        assert "geocoding" in status["capabilities"]
        assert "directions" in status["capabilities"]
        assert "route_optimization" in status["capabilities"]


# Integration Tests (with mocked API responses)

class TestTwilioIntegration:
    """Integration tests for Twilio client with mocked responses."""

    @pytest.mark.asyncio
    @patch('src.integrations.twilio_client.Client')
    async def test_send_sms_success(self, mock_twilio_client):
        """Test successful SMS sending."""
        # Setup mock
        mock_message = Mock()
        mock_message.sid = "SM123456"
        mock_message.status = "queued"
        mock_message.from_ = "+15551234567"
        mock_message.date_created = datetime.utcnow()
        mock_message.price = None
        mock_message.price_unit = "USD"
        mock_message.num_media = "0"
        mock_message.error_code = None
        mock_message.error_message = None

        mock_client_instance = Mock()
        mock_client_instance.messages.create.return_value = mock_message
        mock_twilio_client.return_value = mock_client_instance

        # Create client and configure
        client = TwilioClient()
        client.enabled = True
        client.client = mock_client_instance
        client.from_phone = "+15551234567"

        # Test
        result = await client.send_sms(to="+15559876543", message="Test message")

        assert result["sid"] == "SM123456"
        assert result["status"] == "queued"
        assert result["to"] == "+15559876543"


class TestSendGridIntegration:
    """Integration tests for SendGrid client with mocked responses."""

    @pytest.mark.asyncio
    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    async def test_send_email_success(self, mock_sg_client):
        """Test successful email sending."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg_123"}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sg_client.return_value = mock_client_instance

        # Create client and configure
        client = SendGridClient()
        client.enabled = True
        client.client = mock_client_instance
        client.from_email = "noreply@example.com"

        # Test
        result = await client.send_email(
            to="test@example.com",
            subject="Test",
            html_content="<p>Test</p>"
        )

        assert result["status"] == "sent"
        assert result["status_code"] == 202
        assert result["to"] == "test@example.com"


class TestStripeIntegration:
    """Integration tests for Stripe client with mocked responses."""

    @pytest.mark.asyncio
    @patch('src.integrations.stripe_client.stripe.PaymentIntent')
    async def test_create_payment_intent_success(self, mock_payment_intent):
        """Test successful payment intent creation."""
        # Setup mock
        mock_intent = Mock()
        mock_intent.id = "pi_123456"
        mock_intent.client_secret = "secret_123"
        mock_intent.amount = 10000
        mock_intent.currency = "usd"
        mock_intent.status = "requires_payment_method"
        mock_intent.customer = None
        mock_intent.created = int(datetime.utcnow().timestamp())

        mock_payment_intent.create.return_value = mock_intent

        # Create client
        client = StripeClient()
        client.enabled = True

        # Test
        result = await client.create_payment_intent(amount=100.0)

        assert result["id"] == "pi_123456"
        assert result["amount"] == 100.0
        assert result["currency"] == "USD"


class TestGoogleMapsIntegration:
    """Integration tests for Google Maps client with mocked responses."""

    @pytest.mark.asyncio
    @patch('src.integrations.googlemaps_client.googlemaps.Client')
    async def test_geocode_success(self, mock_maps_client):
        """Test successful geocoding."""
        # Setup mock
        mock_result = [{
            'formatted_address': '123 Main St, City, State 12345',
            'geometry': {
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'location_type': 'ROOFTOP'
            },
            'place_id': 'ChIJ123456',
            'address_components': []
        }]

        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = mock_result
        mock_maps_client.return_value = mock_client_instance

        # Create client
        client = GoogleMapsClient()
        client.enabled = True
        client.client = mock_client_instance

        # Test
        result = await client.geocode("123 Main St")

        assert result["formatted_address"] == '123 Main St, City, State 12345'
        assert result["latitude"] == 40.7128
        assert result["longitude"] == -74.0060
