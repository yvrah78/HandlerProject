"""
Analytics API endpoints - AI-powered business intelligence and reporting.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from src.agents.analytics import AnalyticsAgent
from src.core.security import get_current_user
from src.models.user import User
from src.schemas.analytics import (
    AnalyticsRequest,
    AnalyticsReport,
    KPIResponse,
    InsightsRequest,
    InsightsResponse,
    AgentStatusResponse,
    ReportType,
    TimePeriod
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Initialize Analytics Agent (singleton pattern)
_analytics_agent = None


def get_analytics_agent() -> AnalyticsAgent:
    """Get or create the Analytics Agent instance."""
    global _analytics_agent
    if _analytics_agent is None:
        _analytics_agent = AnalyticsAgent()
    return _analytics_agent


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get Analytics Agent status and configuration.

    Returns:
        AgentStatusResponse: Current status of the Analytics Agent
    """
    agent = get_analytics_agent()
    status_data = agent.get_status()

    return {
        **status_data,
        "ai_enabled": agent.ai_enabled
    }


@router.post("/reports", response_model=AnalyticsReport)
async def generate_report(
    request: AnalyticsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate an analytics report with AI-powered insights.

    Args:
        request: Analytics request with report type and parameters
        current_user: Current authenticated user

    Returns:
        AnalyticsReport: Generated report with metrics and insights

    Raises:
        HTTPException: If report generation fails
    """
    agent = get_analytics_agent()

    try:
        # Prepare input data for agent
        input_data = {
            "report_type": request.report_type.value,
            "time_period": request.time_period.value,
            "use_ai": request.use_ai
        }

        # Execute agent
        result = await agent.execute(input_data)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate analytics report"
            )

        return result["result"]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/metrics", response_model=dict)
async def get_metrics(
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time metrics for the specified time period.

    Args:
        time_period: Time period for metrics (daily, weekly, monthly, yearly)
        current_user: Current authenticated user

    Returns:
        dict: Current metrics data
    """
    agent = get_analytics_agent()

    try:
        metrics = await agent.collect_metrics(time_period.value)
        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error collecting metrics: {str(e)}"
        )


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    current_user: User = Depends(get_current_user)
):
    """
    Get key performance indicators (KPIs).

    Args:
        time_period: Time period for KPIs
        current_user: Current authenticated user

    Returns:
        KPIResponse: Calculated KPIs
    """
    agent = get_analytics_agent()

    try:
        kpis = await agent.get_kpis(time_period.value)
        return kpis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating KPIs: {str(e)}"
        )


@router.post("/insights", response_model=InsightsResponse)
async def get_ai_insights(
    request: InsightsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered strategic insights and recommendations.

    Args:
        request: Insights request with optional context
        current_user: Current authenticated user

    Returns:
        InsightsResponse: AI-generated insights

    Raises:
        HTTPException: If insights generation fails
    """
    agent = get_analytics_agent()

    try:
        insights = await agent.get_insights(context=request.context or "")
        return insights

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating insights: {str(e)}"
        )


@router.get("/reports/{report_type}", response_model=AnalyticsReport)
async def get_quick_report(
    report_type: ReportType,
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    use_ai: bool = Query(True),
    current_user: User = Depends(get_current_user)
):
    """
    Quick endpoint to generate a specific report type.

    Args:
        report_type: Type of report to generate
        time_period: Time period for analysis
        use_ai: Whether to use AI for insights
        current_user: Current authenticated user

    Returns:
        AnalyticsReport: Generated report
    """
    agent = get_analytics_agent()

    try:
        input_data = {
            "report_type": report_type.value,
            "time_period": time_period.value,
            "use_ai": use_ai
        }

        result = await agent.execute(input_data)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate report"
            )

        return result["result"]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/performance", response_model=AnalyticsReport)
async def get_performance_report(
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    current_user: User = Depends(get_current_user)
):
    """Shortcut endpoint for performance reports."""
    return await get_quick_report(ReportType.PERFORMANCE, time_period, True, current_user)


@router.get("/financial", response_model=AnalyticsReport)
async def get_financial_report(
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    current_user: User = Depends(get_current_user)
):
    """Shortcut endpoint for financial reports."""
    return await get_quick_report(ReportType.FINANCIAL, time_period, True, current_user)


@router.get("/operations", response_model=AnalyticsReport)
async def get_operations_report(
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    current_user: User = Depends(get_current_user)
):
    """Shortcut endpoint for operations reports."""
    return await get_quick_report(ReportType.OPERATIONS, time_period, True, current_user)


@router.get("/customer", response_model=AnalyticsReport)
async def get_customer_report(
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    current_user: User = Depends(get_current_user)
):
    """Shortcut endpoint for customer analytics reports."""
    return await get_quick_report(ReportType.CUSTOMER, time_period, True, current_user)


@router.get("/predictive", response_model=AnalyticsReport)
async def get_predictive_report(
    time_period: TimePeriod = Query(TimePeriod.DAILY),
    current_user: User = Depends(get_current_user)
):
    """Shortcut endpoint for predictive analytics reports."""
    return await get_quick_report(ReportType.PREDICTIVE, time_period, True, current_user)
