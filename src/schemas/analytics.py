"""
Pydantic schemas for Analytics API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    """Valid report types."""
    PERFORMANCE = "performance"
    FINANCIAL = "financial"
    OPERATIONS = "operations"
    CUSTOMER = "customer"
    PREDICTIVE = "predictive"
    KPIS = "kpis"
    METRICS = "metrics"


class TimePeriod(str, Enum):
    """Valid time periods for analytics."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AnalyticsRequest(BaseModel):
    """Request schema for analytics reports."""
    report_type: ReportType = Field(..., description="Type of report to generate")
    time_period: TimePeriod = Field(TimePeriod.DAILY, description="Time period for analysis")
    use_ai: bool = Field(True, description="Whether to use AI for generating insights")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for data")

    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "financial",
                "time_period": "monthly",
                "use_ai": True,
                "filters": {"customer_id": 123}
            }
        }


class MetricsData(BaseModel):
    """Metrics data schema."""
    timestamp: str
    time_period: str
    revenue: Dict[str, Any]
    operations: Dict[str, Any]
    customers: Dict[str, Any]
    fleet: Dict[str, Any]


class AnalyticsReport(BaseModel):
    """Analytics report response schema."""
    report_type: str
    time_period: str
    generated_at: str
    metrics: MetricsData
    insights: Optional[str]
    ai_generated: bool
    recommendations: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "financial",
                "time_period": "daily",
                "generated_at": "2025-11-15T10:00:00Z",
                "metrics": {
                    "timestamp": "2025-11-15T10:00:00Z",
                    "time_period": "daily",
                    "revenue": {
                        "total_revenue": 45000.00,
                        "average_booking_value": 150.00,
                        "revenue_growth": 12.5,
                        "payment_success_rate": 98.5
                    },
                    "operations": {},
                    "customers": {},
                    "fleet": {}
                },
                "insights": "Revenue is performing well with 12.5% growth...",
                "ai_generated": True,
                "recommendations": ["Increase fleet capacity", "Optimize pricing"]
            }
        }


class KPIResponse(BaseModel):
    """KPI response schema."""
    time_period: str
    kpis: Dict[str, float]
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "time_period": "daily",
                "kpis": {
                    "revenue_per_booking": 150.00,
                    "customer_acquisition_cost": 1000.00,
                    "booking_completion_rate": 95.0,
                    "fleet_efficiency": 82.0,
                    "customer_satisfaction": 4.6,
                    "revenue_growth": 12.5
                },
                "timestamp": "2025-11-15T10:00:00Z"
            }
        }


class InsightsRequest(BaseModel):
    """Request schema for AI insights."""
    context: Optional[str] = Field(None, description="Context for generating insights")

    class Config:
        json_schema_extra = {
            "example": {
                "context": "Focus on revenue optimization strategies"
            }
        }


class InsightsResponse(BaseModel):
    """AI insights response schema."""
    insights: str
    ai_enabled: bool
    generated_at: Optional[str] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "insights": "Based on current data, recommend increasing fleet by 20%...",
                "ai_enabled": True,
                "generated_at": "2025-11-15T10:00:00Z"
            }
        }


class AgentStatusResponse(BaseModel):
    """Agent status response schema."""
    agent: str
    description: str
    status: str
    ai_enabled: bool
    created_at: str
    last_execution: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "agent": "analytics",
                "description": "AI-powered analytics, reporting, and business intelligence",
                "status": "initialized",
                "ai_enabled": True,
                "created_at": "2025-11-15T09:00:00Z",
                "last_execution": "2025-11-15T10:00:00Z"
            }
        }
