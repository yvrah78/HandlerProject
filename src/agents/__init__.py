"""
Agent package for Project Handler.

Provides both standard agents and LangChain-enabled intelligent agents.
"""
from src.agents.base_agent import BaseAgent
from src.agents.communications import CommunicationsAgent
from src.agents.financial import FinancialAgent
from src.agents.operations import OperationsAgent
from src.agents.analytics import AnalyticsAgent
from src.agents.coordinator import CoordinatorAgent

# LangChain-enabled agents
from src.agents.langchain_agent import LangChainAgent
from src.agents.langchain_agents import (
    LangChainCommunicationsAgent,
    LangChainFinancialAgent,
    LangChainOperationsAgent,
    LangChainAnalyticsAgent,
    create_langchain_agent,
)

# Workflows
from src.agents.workflows import (
    create_booking_workflow,
    create_payment_workflow,
    create_communication_workflow,
)

__all__ = [
    # Base classes
    "BaseAgent",
    # Standard agents
    "CommunicationsAgent",
    "FinancialAgent",
    "OperationsAgent",
    "AnalyticsAgent",
    "CoordinatorAgent",
    # LangChain agents
    "LangChainAgent",
    "LangChainCommunicationsAgent",
    "LangChainFinancialAgent",
    "LangChainOperationsAgent",
    "LangChainAnalyticsAgent",
    "create_langchain_agent",
    # Workflows
    "create_booking_workflow",
    "create_payment_workflow",
    "create_communication_workflow",
]
