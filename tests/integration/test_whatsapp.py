"""
Integration tests for WhatsApp Business API client.

These tests use mocking to avoid actual API calls during testing.
For real integration testing with WhatsApp credentials, set:
- WHATSAPP_API_TOKEN to your access token
- WHATSAPP_PHONE_NUMBER_ID to your phone number ID
- WHATSAPP_BUSINESS_ACCOUNT_ID to your business account ID
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from src.integrations.whatsapp_client import WhatsAppClient
from src.core.exceptions import IntegrationError, ConfigurationError


class TestWhatsAppClient:
    """Test suite for WhatsApp Business API client."""

    @pytest.fixture
    def mock_whatsapp_settings(self):
        """Mock settings with WhatsApp credentials."""
        with patch('src.integrations.whatsapp_client.settings') as mock_settings:
            mock_settings.whatsapp_api_token = "EAAtest123"
            mock_settings.whatsapp_phone_number_id = "123456789"
            mock_settings.whatsapp_business_account_id = "987654321"
            yield mock_settings

    @pytest.mark.asyncio
    async def test_init_success(self, mock_whatsapp_settings):
        """Test successful WhatsApp client initialization."""
        client = WhatsAppClient()

        assert client.api_token == "EAAtest123"
        assert client.phone_number_id == "123456789"
        assert client.business_account_id == "987654321"
        assert "123456789" in client.base_url

    @pytest.mark.asyncio
    async def test_init_missing_credentials(self):
        """Test initialization fails with missing credentials."""
        with patch('src.integrations.whatsapp_client.settings') as mock_settings:
            mock_settings.whatsapp_api_token = ""
            mock_settings.whatsapp_phone_number_id = ""
            mock_settings.whatsapp_business_account_id = ""

            with pytest.raises(ConfigurationError) as exc_info:
                WhatsAppClient()

            assert "WHATSAPP_API_TOKEN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_text_message_success(self, mock_whatsapp_settings):
        """Test successful text message sending."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"wa_id": "1234567890", "input": "+1234567890"}],
            "messages": [{"id": "wamid.test123"}]
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create client and send message
            client = WhatsAppClient()
            result = await client.send_text_message(
                to="+1234567890",
                message="Test message"
            )

            # Assertions
            assert result["message_id"] == "wamid.test123"
            assert result["to"] == "+11234567890"  # Sanitized
            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_text_message_with_preview(self, mock_whatsapp_settings):
        """Test text message with URL preview."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "contacts": [{"wa_id": "1234567890"}],
            "messages": [{"id": "wamid.test123"}]
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()
            result = await client.send_text_message(
                to="+1234567890",
                message="Check this out: https://example.com",
                preview_url=True
            )

            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_template_message_success(self, mock_whatsapp_settings):
        """Test successful template message sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "contacts": [{"wa_id": "1234567890"}],
            "messages": [{"id": "wamid.test456"}]
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()
            result = await client.send_template_message(
                to="+1234567890",
                template_name="booking_confirmation",
                language_code="en_US",
                parameters=[
                    {"type": "text", "text": "John"},
                    {"type": "text", "text": "12345"}
                ]
            )

            assert result["message_id"] == "wamid.test456"
            assert result["template"] == "booking_confirmation"
            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_media_message_image_success(self, mock_whatsapp_settings):
        """Test successful image message sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "contacts": [{"wa_id": "1234567890"}],
            "messages": [{"id": "wamid.test789"}]
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()
            result = await client.send_media_message(
                to="+1234567890",
                media_type="image",
                media_url="https://example.com/image.jpg",
                caption="Check out this image!"
            )

            assert result["message_id"] == "wamid.test789"
            assert result["media_type"] == "image"
            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_media_message_document_success(self, mock_whatsapp_settings):
        """Test successful document message sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "contacts": [{"wa_id": "1234567890"}],
            "messages": [{"id": "wamid.test999"}]
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()
            result = await client.send_media_message(
                to="+1234567890",
                media_type="document",
                media_url="https://example.com/invoice.pdf",
                filename="invoice.pdf"
            )

            assert result["message_id"] == "wamid.test999"
            assert result["media_type"] == "document"

    @pytest.mark.asyncio
    async def test_send_media_message_no_media(self, mock_whatsapp_settings):
        """Test media message fails without media URL or ID."""
        client = WhatsAppClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_media_message(
                to="+1234567890",
                media_type="image"
            )

        assert "media_url or media_id must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_mark_message_as_read_success(self, mock_whatsapp_settings):
        """Test marking message as read."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()
            result = await client.mark_message_as_read("wamid.test123")

            assert result["success"] is True
            assert result["message_id"] == "wamid.test123"

    @pytest.mark.asyncio
    async def test_get_media_url_success(self, mock_whatsapp_settings):
        """Test getting media URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "url": "https://example.com/media/12345.jpg",
            "mime_type": "image/jpeg",
            "sha256": "abc123",
            "file_size": 123456
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()
            result = await client.get_media_url("media123")

            assert result == "https://example.com/media/12345.jpg"

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_whatsapp_settings):
        """Test handling of WhatsApp API errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": {"message": "Invalid phone number"}}'
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid phone number",
                "code": 100
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.post.return_value.raise_for_status = Mock(
                side_effect=httpx.HTTPStatusError(
                    "Bad Request",
                    request=Mock(),
                    response=mock_response
                )
            )
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()

            with pytest.raises(IntegrationError) as exc_info:
                await client.send_text_message(
                    to="invalid",
                    message="Test"
                )

            # The error should be caught during phone number sanitization
            assert "Invalid phone number" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_whatsapp_settings):
        """Test retry logic on transient failures."""
        # Setup mock to fail twice then succeed
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "contacts": [{"wa_id": "1234567890"}],
            "messages": [{"id": "wamid.test123"}]
        }
        mock_success_response.raise_for_status = Mock()

        mock_error_response = Mock()
        mock_error_response.status_code = 503
        mock_error_response.content = b'{"error": {"message": "Service unavailable"}}'
        mock_error_response.json.return_value = {
            "error": {"message": "Service unavailable"}
        }

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                error_response = Mock()
                error_response.status_code = 503
                error_response.content = b'Service unavailable'
                error_response.json.return_value = {"error": {"message": "Service unavailable"}}
                error_response.raise_for_status = Mock(
                    side_effect=httpx.HTTPStatusError(
                        "Service Unavailable",
                        request=Mock(),
                        response=error_response
                    )
                )
                return error_response
            return mock_success_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            client = WhatsAppClient()

            # Should succeed after retries
            result = await client.send_text_message(
                to="+1234567890",
                message="Test"
            )

            assert result["message_id"] == "wamid.test123"
            # Should have been called 3 times (initial + 2 retries)
            assert call_count == 3
