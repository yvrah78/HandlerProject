"""
Integration tests for Twilio client.

These tests use mocking to avoid actual API calls during testing.
For real integration testing with Twilio test credentials, set:
- TWILIO_ACCOUNT_SID to your test account SID
- TWILIO_AUTH_TOKEN to your test auth token
- TWILIO_PHONE_NUMBER to your Twilio test number
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.integrations.twilio_client import TwilioClient
from src.core.exceptions import IntegrationError, ConfigurationError


class TestTwilioClient:
    """Test suite for Twilio client."""

    @pytest.fixture
    def mock_twilio_settings(self):
        """Mock settings with Twilio credentials."""
        with patch('src.integrations.twilio_client.settings') as mock_settings:
            mock_settings.twilio_account_sid = "ACtest123"
            mock_settings.twilio_auth_token = "test_token_123"
            mock_settings.twilio_phone_number = "+15555551234"
            yield mock_settings

    @pytest.fixture
    def mock_twilio_client(self):
        """Mock Twilio Client."""
        with patch('src.integrations.twilio_client.Client') as mock_client:
            yield mock_client

    @pytest.mark.asyncio
    async def test_init_success(self, mock_twilio_settings, mock_twilio_client):
        """Test successful Twilio client initialization."""
        client = TwilioClient()

        assert client.account_sid == "ACtest123"
        assert client.auth_token == "test_token_123"
        assert client.from_number == "+15555551234"
        mock_twilio_client.assert_called_once_with("ACtest123", "test_token_123")

    @pytest.mark.asyncio
    async def test_init_missing_credentials(self):
        """Test initialization fails with missing credentials."""
        with patch('src.integrations.twilio_client.settings') as mock_settings:
            mock_settings.twilio_account_sid = ""
            mock_settings.twilio_auth_token = ""

            with pytest.raises(ConfigurationError) as exc_info:
                TwilioClient()

            assert "TWILIO_ACCOUNT_SID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_sms_success(self, mock_twilio_settings, mock_twilio_client):
        """Test successful SMS sending."""
        # Setup mock message response
        mock_message = Mock()
        mock_message.sid = "SMtest123"
        mock_message.status = "queued"
        mock_message.to = "+15555555678"
        mock_message.from_ = "+15555551234"
        mock_message.date_created = datetime.now()
        mock_message.num_segments = 1

        mock_client_instance = Mock()
        mock_client_instance.messages.create.return_value = mock_message
        mock_twilio_client.return_value = mock_client_instance

        # Create client and send SMS
        client = TwilioClient()
        result = await client.send_sms(
            to="+15555555678",
            message="Test message"
        )

        # Assertions
        assert result["sid"] == "SMtest123"
        assert result["status"] == "queued"
        assert result["to"] == "+15555555678"
        assert result["from"] == "+15555551234"
        assert result["num_segments"] == 1

        mock_client_instance.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sms_with_media(self, mock_twilio_settings, mock_twilio_client):
        """Test SMS sending with media URLs (MMS)."""
        # Setup mock message response
        mock_message = Mock()
        mock_message.sid = "MMtest123"
        mock_message.status = "queued"
        mock_message.to = "+15555555678"
        mock_message.from_ = "+15555551234"
        mock_message.date_created = datetime.now()
        mock_message.num_segments = 1

        mock_client_instance = Mock()
        mock_client_instance.messages.create.return_value = mock_message
        mock_twilio_client.return_value = mock_client_instance

        # Create client and send MMS
        client = TwilioClient()
        result = await client.send_sms(
            to="+15555555678",
            message="Test message with image",
            media_urls=["https://example.com/image.jpg"]
        )

        # Assertions
        assert result["sid"] == "MMtest123"
        call_kwargs = mock_client_instance.messages.create.call_args[1]
        assert "media_url" in call_kwargs
        assert call_kwargs["media_url"] == ["https://example.com/image.jpg"]

    @pytest.mark.asyncio
    async def test_send_sms_sanitizes_phone(self, mock_twilio_settings, mock_twilio_client):
        """Test that phone numbers are sanitized."""
        mock_message = Mock()
        mock_message.sid = "SMtest123"
        mock_message.status = "queued"
        mock_message.to = "+15555555678"
        mock_message.from_ = "+15555551234"
        mock_message.date_created = datetime.now()
        mock_message.num_segments = 1

        mock_client_instance = Mock()
        mock_client_instance.messages.create.return_value = mock_message
        mock_twilio_client.return_value = mock_client_instance

        client = TwilioClient()

        # Test with various phone formats
        result = await client.send_sms(
            to="(555) 555-5678",  # US format with formatting
            message="Test"
        )

        # Should be converted to E.164 format
        call_kwargs = mock_client_instance.messages.create.call_args[1]
        assert call_kwargs["to"] == "+15555555678"

    @pytest.mark.asyncio
    async def test_send_sms_invalid_phone(self, mock_twilio_settings, mock_twilio_client):
        """Test SMS sending with invalid phone number."""
        mock_client_instance = Mock()
        mock_twilio_client.return_value = mock_client_instance

        client = TwilioClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_sms(to="invalid", message="Test")

        assert "Invalid phone number" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_call_success(self, mock_twilio_settings, mock_twilio_client):
        """Test successful call initiation."""
        # Setup mock call response
        mock_call = Mock()
        mock_call.sid = "CAtest123"
        mock_call.status = "queued"
        mock_call.to = "+15555555678"
        mock_call.from_ = "+15555551234"
        mock_call.date_created = datetime.now()

        mock_client_instance = Mock()
        mock_client_instance.calls.create.return_value = mock_call
        mock_twilio_client.return_value = mock_client_instance

        # Create client and make call
        client = TwilioClient()
        result = await client.make_call(
            to="+15555555678",
            message="Test call message"
        )

        # Assertions
        assert result["sid"] == "CAtest123"
        assert result["status"] == "queued"
        assert result["to"] == "+15555555678"

        mock_client_instance.calls.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_call_with_twiml_url(self, mock_twilio_settings, mock_twilio_client):
        """Test call with custom TwiML URL."""
        mock_call = Mock()
        mock_call.sid = "CAtest123"
        mock_call.status = "queued"
        mock_call.to = "+15555555678"
        mock_call.from_ = "+15555551234"
        mock_call.date_created = datetime.now()

        mock_client_instance = Mock()
        mock_client_instance.calls.create.return_value = mock_call
        mock_twilio_client.return_value = mock_client_instance

        client = TwilioClient()
        result = await client.make_call(
            to="+15555555678",
            twiml_url="https://example.com/twiml"
        )

        # Should use URL instead of inline TwiML
        call_kwargs = mock_client_instance.calls.create.call_args[1]
        assert "url" in call_kwargs
        assert call_kwargs["url"] == "https://example.com/twiml"

    @pytest.mark.asyncio
    async def test_make_call_no_message_or_url(self, mock_twilio_settings, mock_twilio_client):
        """Test call fails without message or TwiML URL."""
        mock_client_instance = Mock()
        mock_twilio_client.return_value = mock_client_instance

        client = TwilioClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.make_call(to="+15555555678")

        assert "message or twiml_url must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_message_status_success(self, mock_twilio_settings, mock_twilio_client):
        """Test retrieving message status."""
        mock_message = Mock()
        mock_message.sid = "SMtest123"
        mock_message.status = "delivered"
        mock_message.to = "+15555555678"
        mock_message.from_ = "+15555551234"
        mock_message.error_code = None
        mock_message.error_message = None
        mock_message.date_sent = datetime.now()
        mock_message.date_updated = datetime.now()

        mock_messages = Mock()
        mock_messages.return_value.fetch.return_value = mock_message

        mock_client_instance = Mock()
        mock_client_instance.messages = mock_messages
        mock_twilio_client.return_value = mock_client_instance

        client = TwilioClient()
        result = await client.get_message_status("SMtest123")

        assert result["sid"] == "SMtest123"
        assert result["status"] == "delivered"
        assert result["error_code"] is None

    @pytest.mark.asyncio
    async def test_get_call_status_success(self, mock_twilio_settings, mock_twilio_client):
        """Test retrieving call status."""
        mock_call = Mock()
        mock_call.sid = "CAtest123"
        mock_call.status = "completed"
        mock_call.to = "+15555555678"
        mock_call.from_ = "+15555551234"
        mock_call.duration = "45"
        mock_call.date_created = datetime.now()
        mock_call.date_updated = datetime.now()

        mock_calls = Mock()
        mock_calls.return_value.fetch.return_value = mock_call

        mock_client_instance = Mock()
        mock_client_instance.calls = mock_calls
        mock_twilio_client.return_value = mock_client_instance

        client = TwilioClient()
        result = await client.get_call_status("CAtest123")

        assert result["sid"] == "CAtest123"
        assert result["status"] == "completed"
        assert result["duration"] == "45"

    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_twilio_settings, mock_twilio_client):
        """Test retry logic on transient failures."""
        from twilio.base.exceptions import TwilioRestException

        # Setup mock to fail twice then succeed
        mock_message = Mock()
        mock_message.sid = "SMtest123"
        mock_message.status = "queued"
        mock_message.to = "+15555555678"
        mock_message.from_ = "+15555551234"
        mock_message.date_created = datetime.now()
        mock_message.num_segments = 1

        mock_client_instance = Mock()
        mock_client_instance.messages.create.side_effect = [
            TwilioRestException(500, "https://api.twilio.com", msg="Service unavailable"),
            TwilioRestException(500, "https://api.twilio.com", msg="Service unavailable"),
            mock_message
        ]
        mock_twilio_client.return_value = mock_client_instance

        client = TwilioClient()

        # Should succeed after retries
        result = await client.send_sms(to="+15555555678", message="Test")

        assert result["sid"] == "SMtest123"
        # Should have been called 3 times (initial + 2 retries)
        assert mock_client_instance.messages.create.call_count == 3
