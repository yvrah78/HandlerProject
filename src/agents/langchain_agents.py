"""
Specialized LangChain-enabled agents for Project Handler.

This module provides concrete LangChain agent implementations for:
- Communications (SMS, email, calls)
- Financial (quotes, invoices, payments)
- Operations (routing, fleet, drivers)
- Analytics (reports, metrics, predictions)
"""
from typing import List

from langchain.tools import BaseTool

from src.agents.langchain_agent import LangChainAgent
from src.agents.tools import (
    # Base tools
    DatabaseQueryTool,
    ValidationTool,
    LoggingTool,
    # Communication tools
    SendSMSTool,
    SendEmailTool,
    MakePhonecallTool,
    # Financial tools
    CreateQuoteTool,
    GenerateInvoiceTool,
    ProcessPaymentTool,
    CreateRefundTool,
    # Operations tools
    PlanRouteTool,
    AssignVehicleTool,
    AssignDriverTool,
    TrackVehicleTool,
    # Analytics tools
    GenerateReportTool,
    CalculateMetricsTool,
    PredictDemandTool,
)
from src.core.langchain_config import LLMProvider


class LangChainCommunicationsAgent(LangChainAgent):
    """
    LangChain-enabled communications agent.

    Handles all customer communications including SMS, email, and phone calls.
    Uses Claude to intelligently decide which communication channel to use
    and how to craft messages.
    """

    def __init__(
        self,
        llm_provider: LLMProvider = LLMProvider.CLAUDE,
        model: str = None,
        temperature: float = 0.7
    ):
        """
        Initialize communications agent.

        Args:
            llm_provider: LLM provider to use
            model: Specific model name
            temperature: LLM temperature
        """
        # Define tools for communications
        tools: List[BaseTool] = [
            # Communication tools
            SendSMSTool(),
            SendEmailTool(),
            MakePhonecallTool(),
            # Base tools
            DatabaseQueryTool(),
            ValidationTool(),
            LoggingTool(),
        ]

        description = """
        Communications agent specialized in customer interactions.
        Capabilities:
        - Send SMS notifications and alerts
        - Send formatted emails with booking details
        - Make automated phone calls for urgent matters
        - Query customer contact information
        - Validate phone numbers and email addresses
        - Log communication events

        You intelligently choose the best communication channel based on:
        - Urgency of the message
        - Customer preferences
        - Content type (simple alert vs detailed information)
        - Time of day
        """

        super().__init__(
            name="langchain_communications",
            description=description,
            tools=tools,
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
            max_iterations=8
        )


class LangChainFinancialAgent(LangChainAgent):
    """
    LangChain-enabled financial agent.

    Handles all financial operations including quotes, invoices, payments,
    and refunds. Uses Claude to make intelligent pricing decisions and
    handle payment processing.
    """

    def __init__(
        self,
        llm_provider: LLMProvider = LLMProvider.CLAUDE,
        model: str = None,
        temperature: float = 0.5  # Lower temp for financial operations
    ):
        """
        Initialize financial agent.

        Args:
            llm_provider: LLM provider to use
            model: Specific model name
            temperature: LLM temperature (lower for precision)
        """
        # Define tools for financial operations
        tools: List[BaseTool] = [
            # Financial tools
            CreateQuoteTool(),
            GenerateInvoiceTool(),
            ProcessPaymentTool(),
            CreateRefundTool(),
            # Base tools
            DatabaseQueryTool(),
            ValidationTool(),
            LoggingTool(),
        ]

        description = """
        Financial agent specialized in monetary operations.
        Capabilities:
        - Create accurate price quotes based on service type and distance
        - Generate professional invoices for bookings
        - Process payments securely via Stripe
        - Handle refund requests with proper validation
        - Query payment history and invoice records
        - Validate amounts and payment information

        You ensure financial accuracy and compliance by:
        - Verifying all amounts and calculations
        - Checking customer payment methods
        - Following refund policies
        - Logging all financial transactions
        """

        super().__init__(
            name="langchain_financial",
            description=description,
            tools=tools,
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
            max_iterations=10
        )


class LangChainOperationsAgent(LangChainAgent):
    """
    LangChain-enabled operations agent.

    Handles logistics including route planning, vehicle assignment,
    driver scheduling, and fleet tracking. Uses Claude to optimize
    operations and resource allocation.
    """

    def __init__(
        self,
        llm_provider: LLMProvider = LLMProvider.CLAUDE,
        model: str = None,
        temperature: float = 0.6
    ):
        """
        Initialize operations agent.

        Args:
            llm_provider: LLM provider to use
            model: Specific model name
            temperature: LLM temperature
        """
        # Define tools for operations
        tools: List[BaseTool] = [
            # Operations tools
            PlanRouteTool(),
            AssignVehicleTool(),
            AssignDriverTool(),
            TrackVehicleTool(),
            # Base tools
            DatabaseQueryTool(),
            ValidationTool(),
            LoggingTool(),
        ]

        description = """
        Operations agent specialized in logistics and fleet management.
        Capabilities:
        - Plan optimal routes considering time and distance
        - Assign appropriate vehicles based on passenger count and service type
        - Match qualified drivers to bookings
        - Track vehicle locations in real-time
        - Query fleet availability and status
        - Validate location data and booking details

        You optimize operations by:
        - Choosing the most efficient routes
        - Matching vehicle capacity to passenger needs
        - Considering driver availability and qualifications
        - Minimizing wait times and travel distances
        - Ensuring all assignments are logged
        """

        super().__init__(
            name="langchain_operations",
            description=description,
            tools=tools,
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
            max_iterations=12
        )


class LangChainAnalyticsAgent(LangChainAgent):
    """
    LangChain-enabled analytics agent.

    Handles business intelligence including report generation,
    metrics calculation, and demand forecasting. Uses Claude to
    interpret data and provide insights.
    """

    def __init__(
        self,
        llm_provider: LLMProvider = LLMProvider.CLAUDE,
        model: str = None,
        temperature: float = 0.4  # Lower temp for analytical precision
    ):
        """
        Initialize analytics agent.

        Args:
            llm_provider: LLM provider to use
            model: Specific model name
            temperature: LLM temperature (lower for precision)
        """
        # Define tools for analytics
        tools: List[BaseTool] = [
            # Analytics tools
            GenerateReportTool(),
            CalculateMetricsTool(),
            PredictDemandTool(),
            # Base tools
            DatabaseQueryTool(),
            ValidationTool(),
            LoggingTool(),
        ]

        description = """
        Analytics agent specialized in business intelligence and insights.
        Capabilities:
        - Generate comprehensive business reports (revenue, bookings, performance)
        - Calculate key metrics (conversion rate, LTV, average revenue)
        - Forecast demand for capacity planning
        - Query historical data for trend analysis
        - Validate date ranges and report parameters
        - Log all analytical operations

        You provide valuable insights by:
        - Analyzing data across meaningful time periods
        - Identifying trends and patterns
        - Computing accurate KPIs and metrics
        - Making data-driven predictions
        - Presenting findings in clear, actionable formats
        - Considering seasonality and historical patterns
        """

        super().__init__(
            name="langchain_analytics",
            description=description,
            tools=tools,
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
            max_iterations=10
        )


# Helper function to create agent by type
def create_langchain_agent(
    agent_type: str,
    llm_provider: LLMProvider = LLMProvider.CLAUDE,
    model: str = None,
    **kwargs
) -> LangChainAgent:
    """
    Factory function to create LangChain agents by type.

    Args:
        agent_type: Type of agent ('communications', 'financial', 'operations', 'analytics')
        llm_provider: LLM provider to use
        model: Specific model name
        **kwargs: Additional arguments

    Returns:
        LangChainAgent: Configured agent instance

    Raises:
        ValueError: If agent_type is unknown
    """
    agents = {
        "communications": LangChainCommunicationsAgent,
        "financial": LangChainFinancialAgent,
        "operations": LangChainOperationsAgent,
        "analytics": LangChainAnalyticsAgent,
    }

    agent_class = agents.get(agent_type)
    if not agent_class:
        raise ValueError(
            f"Unknown agent type: {agent_type}. "
            f"Available types: {list(agents.keys())}"
        )

    return agent_class(llm_provider=llm_provider, model=model, **kwargs)
