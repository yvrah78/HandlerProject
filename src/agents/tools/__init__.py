"""
LangChain tools for Project Handler agents.

This package provides custom LangChain tools that agents can use
to interact with the system's database, external services, and
internal operations.
"""
from src.agents.tools.base_tools import (
    DatabaseQueryTool,
    ValidationTool,
    LoggingTool,
)
from src.agents.tools.communication_tools import (
    SendSMSTool,
    SendEmailTool,
    MakePhonecallTool,
)
from src.agents.tools.financial_tools import (
    CreateQuoteTool,
    GenerateInvoiceTool,
    ProcessPaymentTool,
    CreateRefundTool,
)
from src.agents.tools.operations_tools import (
    PlanRouteTool,
    AssignVehicleTool,
    AssignDriverTool,
    TrackVehicleTool,
)
from src.agents.tools.analytics_tools import (
    GenerateReportTool,
    CalculateMetricsTool,
    PredictDemandTool,
)

__all__ = [
    # Base tools
    "DatabaseQueryTool",
    "ValidationTool",
    "LoggingTool",
    # Communication tools
    "SendSMSTool",
    "SendEmailTool",
    "MakePhonecallTool",
    # Financial tools
    "CreateQuoteTool",
    "GenerateInvoiceTool",
    "ProcessPaymentTool",
    "CreateRefundTool",
    # Operations tools
    "PlanRouteTool",
    "AssignVehicleTool",
    "AssignDriverTool",
    "TrackVehicleTool",
    # Analytics tools
    "GenerateReportTool",
    "CalculateMetricsTool",
    "PredictDemandTool",
]
