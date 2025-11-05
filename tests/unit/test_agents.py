"""
Unit tests for Project Handler agents.
"""
import pytest
from src.agents.coordinator import CoordinatorAgent
from src.agents.communications import CommunicationsAgent
from src.agents.financial import FinancialAgent
from src.agents.operations import OperationsAgent
from src.agents.analytics import AnalyticsAgent
from src.core.exceptions import ValidationError


@pytest.mark.asyncio
async def test_coordinator_agent_initialization():
    """Test coordinator agent initialization."""
    agent = CoordinatorAgent()
    assert agent.name == "coordinator"
    assert agent.status == "initialized"


@pytest.mark.asyncio
async def test_coordinator_agent_register():
    """Test registering specialized agents."""
    coordinator = CoordinatorAgent()
    comm_agent = CommunicationsAgent()

    coordinator.register_agent("communications", comm_agent)
    registered = coordinator.get_registered_agents()

    assert "communications" in registered
    assert registered["communications"] == "communications"


@pytest.mark.asyncio
async def test_coordinator_validation_error():
    """Test coordinator input validation."""
    agent = CoordinatorAgent()

    with pytest.raises(ValidationError):
        await agent.validate_input({})  # Missing task_type


@pytest.mark.asyncio
async def test_communications_agent():
    """Test communications agent."""
    agent = CommunicationsAgent()
    assert agent.name == "communications"

    input_data = {
        "communication_type": "email",
        "recipient": "test@example.com",
        "message": "Test message"
    }

    result = await agent.execute(input_data)
    assert result["success"] is True
    assert result["agent"] == "communications"


@pytest.mark.asyncio
async def test_communications_agent_validation():
    """Test communications agent validation."""
    agent = CommunicationsAgent()

    # Missing required fields
    with pytest.raises(ValidationError):
        await agent.validate_input({"communication_type": "email"})

    # Invalid communication type
    with pytest.raises(ValidationError):
        await agent.validate_input({
            "communication_type": "invalid",
            "recipient": "test@example.com"
        })


@pytest.mark.asyncio
async def test_financial_agent():
    """Test financial agent."""
    agent = FinancialAgent()
    assert agent.name == "financial"

    input_data = {
        "operation_type": "quotation",
        "customer_id": 1,
        "amount": 500.0
    }

    result = await agent.execute(input_data)
    assert result["success"] is True
    assert result["agent"] == "financial"


@pytest.mark.asyncio
async def test_operations_agent():
    """Test operations agent."""
    agent = OperationsAgent()
    assert agent.name == "operations"

    input_data = {
        "operation_type": "route_planning",
        "origin": "City A",
        "destination": "City B"
    }

    result = await agent.execute(input_data)
    assert result["success"] is True
    assert result["agent"] == "operations"


@pytest.mark.asyncio
async def test_analytics_agent():
    """Test analytics agent."""
    agent = AnalyticsAgent()
    assert agent.name == "analytics"

    input_data = {
        "report_type": "performance",
        "time_period": "monthly"
    }

    result = await agent.execute(input_data)
    assert result["success"] is True
    assert result["agent"] == "analytics"


@pytest.mark.asyncio
async def test_agent_status():
    """Test agent status retrieval."""
    agent = CommunicationsAgent()
    status = agent.get_status()

    assert status["agent"] == "communications"
    assert status["status"] == "initialized"
    assert "created_at" in status


@pytest.mark.asyncio
async def test_agent_reset():
    """Test agent reset functionality."""
    agent = CommunicationsAgent()

    input_data = {
        "communication_type": "email",
        "recipient": "test@example.com"
    }

    await agent.execute(input_data)
    assert agent.status == "completed"

    agent.reset()
    assert agent.status == "initialized"
    assert agent.last_execution is None
