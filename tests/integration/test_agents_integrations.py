"""
Integration tests for agents with external service integrations.
Tests Communications, Financial, and Operations agents.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.agents.communications import CommunicationsAgent
from src.agents.financial import FinancialAgent
from src.agents.operations import OperationsAgent
from src.core.exceptions import ValidationError, IntegrationError


class TestCommunicationsAgent:
    """Test Communications Agent with Twilio and SendGrid integration."""

    @pytest.fixture
    def agent(self):
        """Create Communications Agent instance."""
        return CommunicationsAgent()

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "communications"
        assert hasattr(agent, 'twilio')
        assert hasattr(agent, 'sendgrid')
        assert isinstance(agent.stats, dict)

    @pytest.mark.asyncio
    async def test_validate_input_missing_fields(self, agent):
        """Test validation fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            await agent.validate_input({})

        assert "communication_type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_input_invalid_type(self, agent):
        """Test validation fails with invalid communication type."""
        with pytest.raises(ValidationError) as exc_info:
            await agent.validate_input({
                "communication_type": "invalid",
                "recipient": "test"
            })

        assert "Invalid communication type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_input_success(self, agent):
        """Test validation succeeds with valid input."""
        result = await agent.validate_input({
            "communication_type": "sms",
            "recipient": "+1234567890",
            "message": "Test"
        })

        assert result is True

    @pytest.mark.asyncio
    @patch.object(TwilioClient, 'send_sms')
    async def test_send_sms_success(self, mock_send_sms, agent):
        """Test sending SMS through agent."""
        # Setup mock
        mock_send_sms.return_value = {
            "sid": "SM123",
            "status": "queued",
            "to": "+1234567890"
        }
        agent.twilio.enabled = True

        # Test
        result = await agent.process({
            "communication_type": "sms",
            "recipient": "+1234567890",
            "message": "Test message"
        })

        assert result["communication_type"] == "sms"
        assert result["status"] == "sent"
        assert result["message_sid"] == "SM123"

    @pytest.mark.asyncio
    @patch.object(SendGridClient, 'send_email')
    async def test_send_email_success(self, mock_send_email, agent):
        """Test sending email through agent."""
        # Setup mock
        mock_send_email.return_value = {
            "status_code": 202,
            "status": "sent",
            "message_id": "msg_123"
        }
        agent.sendgrid.enabled = True

        # Test
        result = await agent.process({
            "communication_type": "email",
            "recipient": "test@example.com",
            "subject": "Test",
            "html_content": "<p>Test</p>"
        })

        assert result["communication_type"] == "email"
        assert result["status"] == "sent"

    def test_get_status(self, agent):
        """Test agent status includes integration status."""
        status = agent.get_status()

        assert status["agent_name"] == "communications"
        assert "integrations" in status
        assert "twilio" in status["integrations"]
        assert "sendgrid" in status["integrations"]
        assert "statistics" in status


class TestFinancialAgent:
    """Test Financial Agent with Stripe integration."""

    @pytest.fixture
    def agent(self):
        """Create Financial Agent instance."""
        return FinancialAgent()

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "financial"
        assert hasattr(agent, 'stripe')
        assert isinstance(agent.stats, dict)

    @pytest.mark.asyncio
    async def test_validate_input_missing_fields(self, agent):
        """Test validation fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            await agent.validate_input({})

        assert "operation_type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_input_invalid_operation(self, agent):
        """Test validation fails with invalid operation type."""
        with pytest.raises(ValidationError) as exc_info:
            await agent.validate_input({
                "operation_type": "invalid"
            })

        assert "Invalid operation type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_quotation_success(self, agent):
        """Test creating quotation."""
        result = await agent.process({
            "operation_type": "quotation",
            "service_type": "standard",
            "distance": 10,
            "duration": 30
        })

        assert result["operation_type"] == "quotation"
        assert result["status"] == "calculated"
        assert result["total_price"] > 0
        assert result["currency"] == "USD"

    @pytest.mark.asyncio
    @patch.object(StripeClient, 'create_payment_intent')
    async def test_process_payment_success(self, mock_payment, agent):
        """Test processing payment through agent."""
        # Setup mock
        mock_payment.return_value = {
            "id": "pi_123",
            "client_secret": "secret_123",
            "amount": 100.0,
            "currency": "USD",
            "status": "requires_payment_method"
        }
        agent.stripe.enabled = True

        # Test
        result = await agent.process({
            "operation_type": "payment",
            "amount": 100.0,
            "customer_id": "cus_123"
        })

        assert result["operation_type"] == "payment"
        assert result["status"] == "created"
        assert result["payment_id"] == "pi_123"

    def test_get_status(self, agent):
        """Test agent status includes Stripe integration status."""
        status = agent.get_status()

        assert status["agent_name"] == "financial"
        assert "integrations" in status
        assert "stripe" in status["integrations"]
        assert "statistics" in status


class TestOperationsAgent:
    """Test Operations Agent with Google Maps integration."""

    @pytest.fixture
    def agent(self):
        """Create Operations Agent instance."""
        return OperationsAgent()

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "operations"
        assert hasattr(agent, 'maps')
        assert isinstance(agent.stats, dict)

    @pytest.mark.asyncio
    async def test_validate_input_missing_fields(self, agent):
        """Test validation fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            await agent.validate_input({})

        assert "operation_type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_input_invalid_operation(self, agent):
        """Test validation fails with invalid operation type."""
        with pytest.raises(ValidationError) as exc_info:
            await agent.validate_input({
                "operation_type": "invalid"
            })

        assert "Invalid operation type" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.object(GoogleMapsClient, 'calculate_distance')
    async def test_calculate_distance_success(self, mock_distance, agent):
        """Test calculating distance through agent."""
        # Setup mock
        mock_distance.return_value = {
            "origin": "Location A",
            "destination": "Location B",
            "distance": {"value": 15000, "text": "15 km"},
            "duration": {"value": 1200, "text": "20 mins"}
        }
        agent.maps.enabled = True

        # Test
        result = await agent.process({
            "operation_type": "distance_calculation",
            "origin": "Location A",
            "destination": "Location B"
        })

        assert result["operation_type"] == "distance_calculation"
        assert result["status"] == "success"
        assert "distance" in result

    @pytest.mark.asyncio
    @patch.object(GoogleMapsClient, 'validate_address')
    async def test_validate_address_success(self, mock_validate, agent):
        """Test validating address through agent."""
        # Setup mock
        mock_validate.return_value = {
            "valid": True,
            "original_address": "123 Main St",
            "formatted_address": "123 Main Street, City, ST 12345",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        agent.maps.enabled = True

        # Test
        result = await agent.process({
            "operation_type": "address_validation",
            "address": "123 Main St"
        })

        assert result["operation_type"] == "address_validation"
        assert result["status"] == "success"
        assert result["valid"] is True

    def test_get_status(self, agent):
        """Test agent status includes Google Maps integration status."""
        status = agent.get_status()

        assert status["agent_name"] == "operations"
        assert "integrations" in status
        assert "google_maps" in status["integrations"]
        assert "statistics" in status
