"""
Integration tests for SendGrid client.

These tests use mocking to avoid actual API calls during testing.
For real integration testing with SendGrid test credentials, set:
- SENDGRID_API_KEY to your test API key
- SENDGRID_FROM_EMAIL to your verified sender email
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.integrations.sendgrid_client import SendGridClient
from src.core.exceptions import IntegrationError, ConfigurationError


class TestSendGridClient:
    """Test suite for SendGrid client."""

    @pytest.fixture
    def mock_sendgrid_settings(self):
        """Mock settings with SendGrid credentials."""
        with patch('src.integrations.sendgrid_client.settings') as mock_settings:
            mock_settings.sendgrid_api_key = "SG.test_api_key_123"
            mock_settings.sendgrid_from_email = "noreply@projecthandler.com"
            yield mock_settings

    @pytest.fixture
    def mock_sendgrid_client(self):
        """Mock SendGrid API Client."""
        with patch('src.integrations.sendgrid_client.SendGridAPIClient') as mock_client:
            yield mock_client

    @pytest.mark.asyncio
    async def test_init_success(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test successful SendGrid client initialization."""
        client = SendGridClient()

        assert client.api_key == "SG.test_api_key_123"
        assert client.from_email == "noreply@projecthandler.com"
        mock_sendgrid_client.assert_called_once_with("SG.test_api_key_123")

    @pytest.mark.asyncio
    async def test_init_missing_credentials(self):
        """Test initialization fails with missing credentials."""
        with patch('src.integrations.sendgrid_client.settings') as mock_settings:
            mock_settings.sendgrid_api_key = ""
            mock_settings.sendgrid_from_email = ""

            with pytest.raises(ConfigurationError) as exc_info:
                SendGridClient()

            assert "SENDGRID_API_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test successful email sending."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance

        # Create client and send email
        client = SendGridClient()
        result = await client.send_email(
            to="customer@example.com",
            subject="Test Email",
            html_content="<h1>Test Content</h1>"
        )

        # Assertions
        assert result["status_code"] == 202
        assert result["message_id"] == "test_message_id_123"
        assert result["to"] == "customer@example.com"
        assert result["success"] is True

        mock_client_instance.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_plain_text(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test email sending with plain text content."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()
        result = await client.send_email(
            to="customer@example.com",
            subject="Test Email",
            plain_text_content="Test plain text content"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_no_content(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test email sending fails without content."""
        mock_client_instance = Mock()
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_email(
                to="customer@example.com",
                subject="Test Email"
            )

        assert "html_content or plain_text_content must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test email sending with attachments."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()
        result = await client.send_email(
            to="customer@example.com",
            subject="Test Email with Attachment",
            html_content="<h1>Please see attached</h1>",
            attachments=[{
                'content': 'base64_encoded_content',
                'filename': 'invoice.pdf',
                'type': 'application/pdf'
            }]
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test email sending with CC and BCC recipients."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()
        result = await client.send_email(
            to="customer@example.com",
            subject="Test Email",
            html_content="<h1>Test</h1>",
            cc=["manager@example.com"],
            bcc=["admin@example.com"]
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_sanitizes_email(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test that email addresses are sanitized."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()

        # Test with email that needs sanitization
        result = await client.send_email(
            to=" Customer@Example.COM ",  # With spaces and mixed case
            subject="Test",
            html_content="<h1>Test</h1>"
        )

        # Should be converted to lowercase and trimmed
        assert result["to"] == "customer@example.com"

    @pytest.mark.asyncio
    async def test_send_email_invalid_email(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test email sending with invalid email address."""
        mock_client_instance = Mock()
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_email(
                to="invalid-email",
                subject="Test",
                html_content="<h1>Test</h1>"
            )

        assert "Invalid email address" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_template_email_success(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test successful template email sending."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()
        result = await client.send_template_email(
            to="customer@example.com",
            template_id="d-abc123def456",
            dynamic_data={"name": "John Doe", "booking_id": "12345"}
        )

        assert result["status_code"] == 202
        assert result["template_id"] == "d-abc123def456"
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_bulk_emails_success(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test successful bulk email sending."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        mock_client_instance = Mock()
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()
        result = await client.send_bulk_emails(
            recipients=[
                {"email": "user1@example.com", "name": "User 1"},
                {"email": "user2@example.com", "name": "User 2"},
                {"email": "user3@example.com", "name": "User 3"}
            ],
            subject="Bulk Newsletter",
            html_content="<h1>Newsletter Content</h1>"
        )

        assert result["status_code"] == 202
        assert result["recipient_count"] == 3
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_api_error(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test email sending with API error."""
        from python_http_client.exceptions import HTTPError

        # Setup mock to raise HTTPError
        http_error = HTTPError(
            Mock(status_code=400, body=b'{"errors": [{"message": "Invalid email"}]}'),
            "Bad Request"
        )

        mock_client_instance = Mock()
        mock_client_instance.send.side_effect = http_error
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()

        with pytest.raises(IntegrationError) as exc_info:
            await client.send_email(
                to="customer@example.com",
                subject="Test",
                html_content="<h1>Test</h1>"
            )

        assert "SendGrid API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_sendgrid_settings, mock_sendgrid_client):
        """Test retry logic on transient failures."""
        from python_http_client.exceptions import HTTPError

        # Setup mock to fail twice then succeed
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_message_id_123'}

        http_error = HTTPError(
            Mock(status_code=503, body=b'Service unavailable'),
            "Service Unavailable"
        )

        mock_client_instance = Mock()
        mock_client_instance.send.side_effect = [
            http_error,
            http_error,
            mock_response
        ]
        mock_sendgrid_client.return_value = mock_client_instance

        client = SendGridClient()

        # Should succeed after retries
        result = await client.send_email(
            to="customer@example.com",
            subject="Test",
            html_content="<h1>Test</h1>"
        )

        assert result["success"] is True
        # Should have been called 3 times (initial + 2 retries)
        assert mock_client_instance.send.call_count == 3
