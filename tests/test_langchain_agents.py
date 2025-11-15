"""
Tests for LangChain-enabled agents.

Tests the LangChain integration including:
- Agent creation and initialization
- Tool usage
- LLM interaction (mocked)
- Memory management
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.agents.langchain_agents import (
    LangChainCommunicationsAgent,
    LangChainFinancialAgent,
    LangChainOperationsAgent,
    LangChainAnalyticsAgent,
    create_langchain_agent,
)
from src.core.langchain_config import LLMProvider


class TestLangChainAgentCreation:
    """Test LangChain agent creation and initialization."""

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_create_communications_agent(self, mock_config):
        """Test creating a communications agent."""
        # Mock LangChain config
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = LangChainCommunicationsAgent()

        assert agent.name == "langchain_communications"
        assert len(agent.tools) == 6  # 3 comm tools + 3 base tools
        assert agent.llm_provider == LLMProvider.CLAUDE

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_create_financial_agent(self, mock_config):
        """Test creating a financial agent."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = LangChainFinancialAgent()

        assert agent.name == "langchain_financial"
        assert len(agent.tools) == 7  # 4 financial tools + 3 base tools
        assert agent.temperature == 0.5  # Lower temp for financial ops

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_create_operations_agent(self, mock_config):
        """Test creating an operations agent."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = LangChainOperationsAgent()

        assert agent.name == "langchain_operations"
        assert len(agent.tools) == 7  # 4 ops tools + 3 base tools

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_create_analytics_agent(self, mock_config):
        """Test creating an analytics agent."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = LangChainAnalyticsAgent()

        assert agent.name == "langchain_analytics"
        assert len(agent.tools) == 6  # 3 analytics tools + 3 base tools
        assert agent.temperature == 0.4  # Lower temp for analytical precision

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_factory_function(self, mock_config):
        """Test agent factory function."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = create_langchain_agent("communications")
        assert isinstance(agent, LangChainCommunicationsAgent)

        agent = create_langchain_agent("financial")
        assert isinstance(agent, LangChainFinancialAgent)

        agent = create_langchain_agent("operations")
        assert isinstance(agent, LangChainOperationsAgent)

        agent = create_langchain_agent("analytics")
        assert isinstance(agent, LangChainAnalyticsAgent)

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_factory_function_invalid_type(self, mock_config):
        """Test factory function with invalid agent type."""
        with pytest.raises(ValueError, match="Unknown agent type"):
            create_langchain_agent("invalid_type")


class TestLangChainAgentTools:
    """Test LangChain agent tool management."""

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_agent_has_correct_tools(self, mock_config):
        """Test that agents have the correct tools."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        # Communications agent
        comm_agent = LangChainCommunicationsAgent()
        tool_names = [t.name for t in comm_agent.tools]
        assert "send_sms" in tool_names
        assert "send_email" in tool_names
        assert "make_phonecall" in tool_names
        assert "database_query" in tool_names

        # Financial agent
        fin_agent = LangChainFinancialAgent()
        tool_names = [t.name for t in fin_agent.tools]
        assert "create_quote" in tool_names
        assert "generate_invoice" in tool_names
        assert "process_payment" in tool_names
        assert "create_refund" in tool_names

        # Operations agent
        ops_agent = LangChainOperationsAgent()
        tool_names = [t.name for t in ops_agent.tools]
        assert "plan_route" in tool_names
        assert "assign_vehicle" in tool_names
        assert "assign_driver" in tool_names
        assert "track_vehicle" in tool_names

        # Analytics agent
        analytics_agent = LangChainAnalyticsAgent()
        tool_names = [t.name for t in analytics_agent.tools]
        assert "generate_report" in tool_names
        assert "calculate_metrics" in tool_names
        assert "predict_demand" in tool_names

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_add_tool(self, mock_config):
        """Test adding a tool to an agent."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = LangChainCommunicationsAgent()
        initial_count = len(agent.tools)

        # Create a mock tool
        mock_tool = Mock()
        mock_tool.name = "custom_tool"

        agent.add_tool(mock_tool)

        assert len(agent.tools) == initial_count + 1
        assert any(t.name == "custom_tool" for t in agent.tools)

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_remove_tool(self, mock_config):
        """Test removing a tool from an agent."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = LangChainCommunicationsAgent()
        initial_count = len(agent.tools)

        agent.remove_tool("send_sms")

        assert len(agent.tools) == initial_count - 1
        assert not any(t.name == "send_sms" for t in agent.tools)


class TestLangChainAgentExecution:
    """Test LangChain agent execution (mocked)."""

    @pytest.mark.asyncio
    @patch('src.agents.langchain_agent.get_langchain_config')
    async def test_process_task(self, mock_config):
        """Test processing a task (mocked LLM)."""
        # Mock LangChain components
        mock_lc = MagicMock()
        mock_llm = Mock()
        mock_memory = Mock()
        mock_memory.buffer = ""
        mock_callback = Mock()
        mock_callback.call_count = 0
        mock_callback.total_tokens = 0

        mock_lc.get_llm.return_value = mock_llm
        mock_lc.get_memory.return_value = mock_memory
        mock_lc.get_callback_handler.return_value = mock_callback
        mock_config.return_value = mock_lc

        agent = LangChainCommunicationsAgent()

        # Mock the agent executor
        mock_executor = Mock()
        mock_executor.invoke = Mock(return_value={
            "output": "SMS sent successfully",
            "intermediate_steps": []
        })
        agent.agent_executor = mock_executor

        # Process task
        result = await agent.process({
            "task": "Send an SMS to customer 123 confirming their booking"
        })

        assert result["status"] == "success"
        assert "SMS sent successfully" in result["output"]
        mock_executor.invoke.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.agents.langchain_agent.get_langchain_config')
    async def test_validate_input(self, mock_config):
        """Test input validation."""
        mock_lc = MagicMock()
        mock_lc.get_llm.return_value = Mock()
        mock_lc.get_memory.return_value = Mock()
        mock_lc.get_callback_handler.return_value = Mock()
        mock_config.return_value = mock_lc

        agent = LangChainCommunicationsAgent()

        # Valid input
        assert await agent.validate_input({"task": "send sms"}) == True
        assert await agent.validate_input({"query": "what is the status?"}) == True

        # Invalid input (not a dict)
        assert await agent.validate_input("not a dict") == False
        assert await agent.validate_input(None) == False


class TestLangChainAgentStats:
    """Test LangChain agent statistics."""

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_get_stats(self, mock_config):
        """Test getting agent statistics."""
        mock_lc = MagicMock()
        mock_llm = Mock()
        mock_memory = Mock()
        mock_callback = Mock()
        mock_callback.call_count = 5
        mock_callback.total_tokens = 1000

        mock_lc.get_llm.return_value = mock_llm
        mock_lc.get_memory.return_value = mock_memory
        mock_lc.get_callback_handler.return_value = mock_callback
        mock_config.return_value = mock_lc

        agent = LangChainCommunicationsAgent()

        stats = agent.get_stats()

        assert stats["langchain_enabled"] == True
        assert stats["llm_provider"] == LLMProvider.CLAUDE
        assert stats["tool_count"] == 6
        assert "send_sms" in stats["tools"]
        assert stats["has_memory"] == True
        assert stats["llm_calls"] == 5
        assert stats["total_tokens"] == 1000

    @patch('src.agents.langchain_agent.get_langchain_config')
    def test_clear_memory(self, mock_config):
        """Test clearing agent memory."""
        mock_lc = MagicMock()
        mock_llm = Mock()
        mock_memory = Mock()
        mock_callback = Mock()

        mock_lc.get_llm.return_value = mock_llm
        mock_lc.get_memory.return_value = mock_memory
        mock_lc.get_callback_handler.return_value = mock_callback
        mock_config.return_value = mock_lc

        agent = LangChainCommunicationsAgent()

        agent.clear_memory()

        mock_memory.clear.assert_called_once()
