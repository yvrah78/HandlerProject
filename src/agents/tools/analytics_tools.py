"""
Analytics tools for Analytics Agent.
Tools for metrics, reporting, and business intelligence.
"""
from typing import Dict, Any, Optional
from pydantic import Field
from datetime import datetime, timedelta

from src.agents.tools.base_tool import BaseTool, ToolInput, ToolOutput
from src.core.logging import get_logger
from src.core.database import get_db
from src.models.booking import Booking, BookingStatus
from src.models.invoice import Invoice, InvoiceStatus
from src.models.payment import Payment, PaymentStatus

logger = get_logger(__name__)


class GetRevenueMetricsInput(ToolInput):
    """Input for get_revenue_metrics tool."""

    period: str = Field("today", description="Period: today, week, month, year")
    group_by: Optional[str] = Field(None, description="Group by: service_type, customer")


class GetOperationalMetricsInput(ToolInput):
    """Input for get_operational_metrics tool."""

    metric_type: str = Field(
        "overview", description="Metric type: overview, vehicles, drivers, bookings"
    )


class GenerateReportInput(ToolInput):
    """Input for generate_report tool."""

    report_type: str = Field(..., description="Report type: daily, weekly, monthly")
    include_sections: Optional[list] = Field(
        None, description="Sections to include in report"
    )


class GetRevenueMetricsTool(BaseTool):
    """Tool for getting revenue metrics."""

    def __init__(self):
        super().__init__(
            name="get_revenue_metrics",
            description="Get revenue metrics and financial analytics",
            input_schema=GetRevenueMetricsInput,
            required_permissions=["read:analytics", "read:invoices"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute get revenue metrics."""
        try:
            period = input_data.get("period", "today")

            db = get_db()

            # Calculate date range
            now = datetime.utcnow()
            if period == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_date = now - timedelta(days=7)
            elif period == "month":
                start_date = now - timedelta(days=30)
            elif period == "year":
                start_date = now - timedelta(days=365)
            else:
                start_date = now - timedelta(days=1)

            # Get invoices for period
            invoices = (
                db.query(Invoice)
                .filter(Invoice.created_at >= start_date)
                .all()
            )

            # Calculate metrics
            total_revenue = sum(float(inv.total_amount) for inv in invoices)
            total_invoices = len(invoices)
            paid_invoices = len(
                [inv for inv in invoices if inv.status == InvoiceStatus.PAID]
            )
            unpaid_invoices = len(
                [inv for inv in invoices if inv.status != InvoiceStatus.PAID]
            )

            metrics = {
                "period": period,
                "total_revenue": round(total_revenue, 2),
                "invoice_count": total_invoices,
                "paid_invoices": paid_invoices,
                "unpaid_invoices": unpaid_invoices,
                "collection_rate": (
                    (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
                ),
            }

            return ToolOutput(
                success=True,
                data=metrics,
            )

        except Exception as e:
            logger.error(f"Error getting revenue metrics: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class GetOperationalMetricsTool(BaseTool):
    """Tool for getting operational metrics."""

    def __init__(self):
        super().__init__(
            name="get_operational_metrics",
            description="Get operational metrics and performance indicators",
            input_schema=GetOperationalMetricsInput,
            required_permissions=["read:analytics"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute get operational metrics."""
        try:
            metric_type = input_data.get("metric_type", "overview")

            db = get_db()

            # Get bookings
            all_bookings = db.query(Booking).all()
            today_bookings = [
                b
                for b in all_bookings
                if b.created_at.date() == datetime.utcnow().date()
            ]

            metrics = {
                "metric_type": metric_type,
                "total_bookings": len(all_bookings),
                "today_bookings": len(today_bookings),
                "completed_bookings": len(
                    [b for b in all_bookings if b.status == BookingStatus.COMPLETED]
                ),
                "pending_bookings": len(
                    [b for b in all_bookings if b.status == BookingStatus.PENDING]
                ),
                "cancelled_bookings": len(
                    [b for b in all_bookings if b.status == BookingStatus.CANCELLED]
                ),
            }

            return ToolOutput(
                success=True,
                data=metrics,
            )

        except Exception as e:
            logger.error(f"Error getting operational metrics: {str(e)}")
            return ToolOutput(success=False, error=str(e))


class GenerateReportTool(BaseTool):
    """Tool for generating analytics reports."""

    def __init__(self):
        super().__init__(
            name="generate_report",
            description="Generate analytics and performance report",
            input_schema=GenerateReportInput,
            required_permissions=["read:analytics", "write:reports"],
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute generate report."""
        try:
            report_type = input_data.get("report_type")
            include_sections = input_data.get(
                "include_sections",
                ["revenue", "operations", "fleet", "drivers"],
            )

            db = get_db()

            # Build report
            report = {
                "type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "sections": {},
            }

            # Revenue section
            if "revenue" in include_sections:
                invoices = db.query(Invoice).all()
                report["sections"]["revenue"] = {
                    "total_invoices": len(invoices),
                    "total_amount": sum(float(inv.total_amount) for inv in invoices),
                }

            # Operations section
            if "operations" in include_sections:
                bookings = db.query(Booking).all()
                report["sections"]["operations"] = {
                    "total_bookings": len(bookings),
                    "completed": len(
                        [b for b in bookings if b.status == BookingStatus.COMPLETED]
                    ),
                }

            report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            logger.info(f"Report generated: {report_id}")

            return ToolOutput(
                success=True,
                data={
                    "report_id": report_id,
                    "report": report,
                    "format": "json",
                },
            )

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return ToolOutput(success=False, error=str(e))


def register_analytics_tools(registry) -> None:
    """
    Register all analytics tools in the registry.

    Args:
        registry: ToolRegistry instance
    """
    registry.register(GetRevenueMetricsTool(), category="analytics")
    registry.register(GetOperationalMetricsTool(), category="analytics")
    registry.register(GenerateReportTool(), category="analytics")
    logger.info("Analytics tools registered")
