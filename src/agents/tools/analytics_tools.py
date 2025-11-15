"""
LangChain tools for analytics and reporting.

These tools allow the AnalyticsAgent to generate reports, calculate metrics,
and make predictions based on historical data.
"""
from typing import Optional, Type, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from src.core.logging import get_logger
from src.core.database import get_db


logger = get_logger(__name__)


class GenerateReportInput(BaseModel):
    """Input schema for report generation."""
    report_type: str = Field(description="Type of report (e.g., 'revenue', 'bookings', 'performance')")
    start_date: str = Field(description="Report start date (ISO format)")
    end_date: str = Field(description="Report end date (ISO format)")
    format: str = Field(default="json", description="Report format: 'json', 'csv', or 'pdf'")


class GenerateReportTool(BaseTool):
    """
    Tool for generating business reports.

    Creates reports on revenue, bookings, performance, and other metrics
    for specified time periods.
    """
    name = "generate_report"
    description = """
    Generate a business report for a specific time period. Use this to
    create revenue reports, booking summaries, or performance analyses.
    Input should include report type, start date, and end date.
    """
    args_schema: Type[BaseModel] = GenerateReportInput

    def _run(
        self,
        report_type: str,
        start_date: str,
        end_date: str,
        format: str = "json",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Generate report.

        Args:
            report_type: Type of report to generate
            start_date: Report start date
            end_date: Report end date
            format: Output format
            run_manager: Callback manager

        Returns:
            str: JSON response with report data
        """
        try:
            from dateutil import parser

            start = parser.parse(start_date)
            end = parser.parse(end_date)

            db = next(get_db())

            if report_type == "revenue":
                report_data = self._generate_revenue_report(db, start, end)
            elif report_type == "bookings":
                report_data = self._generate_bookings_report(db, start, end)
            elif report_type == "performance":
                report_data = self._generate_performance_report(db, start, end)
            else:
                raise ValueError(f"Unknown report type: {report_type}")

            logger.info(f"Generated {report_type} report from {start_date} to {end_date}")

            import json
            return json.dumps({
                "success": True,
                "report_type": report_type,
                "period": {
                    "start": start.isoformat(),
                    "end": end.isoformat()
                },
                "format": format,
                "data": report_data,
                "generated_at": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def _generate_revenue_report(self, db, start: datetime, end: datetime) -> Dict[str, Any]:
        """Generate revenue report."""
        from src.models.payment import Payment

        payments = db.query(Payment).filter(
            Payment.payment_date >= start,
            Payment.payment_date <= end,
            Payment.status == "completed"
        ).all()

        total_revenue = sum(p.amount for p in payments)
        payment_count = len(payments)
        average_payment = total_revenue / payment_count if payment_count > 0 else 0

        return {
            "total_revenue": float(total_revenue),
            "payment_count": payment_count,
            "average_payment": float(average_payment),
            "currency": "USD"
        }

    def _generate_bookings_report(self, db, start: datetime, end: datetime) -> Dict[str, Any]:
        """Generate bookings report."""
        from src.models.booking import Booking

        bookings = db.query(Booking).filter(
            Booking.created_at >= start,
            Booking.created_at <= end
        ).all()

        total_bookings = len(bookings)
        by_status = {}
        for booking in bookings:
            status = booking.status or "unknown"
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_bookings": total_bookings,
            "by_status": by_status,
        }

    def _generate_performance_report(self, db, start: datetime, end: datetime) -> Dict[str, Any]:
        """Generate performance report."""
        from src.models.booking import Booking

        bookings = db.query(Booking).filter(
            Booking.created_at >= start,
            Booking.created_at <= end
        ).all()

        completed = sum(1 for b in bookings if b.status == "completed")
        cancelled = sum(1 for b in bookings if b.status == "cancelled")
        total = len(bookings)

        completion_rate = (completed / total * 100) if total > 0 else 0
        cancellation_rate = (cancelled / total * 100) if total > 0 else 0

        return {
            "total_bookings": total,
            "completed": completed,
            "cancelled": cancelled,
            "completion_rate": round(completion_rate, 2),
            "cancellation_rate": round(cancellation_rate, 2)
        }

    async def _arun(
        self,
        report_type: str,
        start_date: str,
        end_date: str,
        format: str = "json",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(report_type, start_date, end_date, format, run_manager)


class CalculateMetricsInput(BaseModel):
    """Input schema for metrics calculation."""
    metric_name: str = Field(description="Name of metric to calculate (e.g., 'avg_revenue', 'conversion_rate')")
    time_period: str = Field(default="30d", description="Time period: '7d', '30d', '90d', or '1y'")


class CalculateMetricsTool(BaseTool):
    """
    Tool for calculating business metrics.

    Computes KPIs and metrics like average revenue, conversion rates,
    customer lifetime value, etc.
    """
    name = "calculate_metrics"
    description = """
    Calculate a business metric or KPI for a time period. Use this to
    compute metrics like average revenue, conversion rates, or customer
    lifetime value. Input should include metric name and time period.
    """
    args_schema: Type[BaseModel] = CalculateMetricsInput

    def _run(
        self,
        metric_name: str,
        time_period: str = "30d",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Calculate metric.

        Args:
            metric_name: Name of metric to calculate
            time_period: Time period for calculation
            run_manager: Callback manager

        Returns:
            str: JSON response with metric value
        """
        try:
            # Parse time period
            days = self._parse_time_period(time_period)
            start_date = datetime.utcnow() - timedelta(days=days)
            end_date = datetime.utcnow()

            db = next(get_db())

            # Calculate requested metric
            if metric_name == "avg_revenue":
                value = self._calc_avg_revenue(db, start_date, end_date)
            elif metric_name == "conversion_rate":
                value = self._calc_conversion_rate(db, start_date, end_date)
            elif metric_name == "customer_lifetime_value":
                value = self._calc_customer_ltv(db, start_date, end_date)
            elif metric_name == "avg_booking_value":
                value = self._calc_avg_booking_value(db, start_date, end_date)
            else:
                raise ValueError(f"Unknown metric: {metric_name}")

            logger.info(f"Calculated metric '{metric_name}' for {time_period}: {value}")

            import json
            return json.dumps({
                "success": True,
                "metric_name": metric_name,
                "value": value,
                "time_period": time_period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            })

        except Exception as e:
            logger.error(f"Failed to calculate metric: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    def _parse_time_period(self, period: str) -> int:
        """Parse time period string to days."""
        mappings = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365,
        }
        return mappings.get(period, 30)

    def _calc_avg_revenue(self, db, start: datetime, end: datetime) -> float:
        """Calculate average revenue per day."""
        from src.models.payment import Payment

        payments = db.query(Payment).filter(
            Payment.payment_date >= start,
            Payment.payment_date <= end,
            Payment.status == "completed"
        ).all()

        total_revenue = sum(p.amount for p in payments)
        days = (end - start).days or 1

        return round(total_revenue / days, 2)

    def _calc_conversion_rate(self, db, start: datetime, end: datetime) -> float:
        """Calculate quote to booking conversion rate."""
        from src.models.quote import Quote
        from src.models.booking import Booking

        quotes = db.query(Quote).filter(
            Quote.created_at >= start,
            Quote.created_at <= end
        ).count()

        bookings = db.query(Booking).filter(
            Booking.created_at >= start,
            Booking.created_at <= end
        ).count()

        return round((bookings / quotes * 100) if quotes > 0 else 0, 2)

    def _calc_customer_ltv(self, db, start: datetime, end: datetime) -> float:
        """Calculate customer lifetime value."""
        from src.models.payment import Payment
        from src.models.customer import Customer

        customers = db.query(Customer).filter(
            Customer.created_at >= start,
            Customer.created_at <= end
        ).count()

        payments = db.query(Payment).filter(
            Payment.payment_date >= start,
            Payment.payment_date <= end,
            Payment.status == "completed"
        ).all()

        total_revenue = sum(p.amount for p in payments)

        return round(total_revenue / customers if customers > 0 else 0, 2)

    def _calc_avg_booking_value(self, db, start: datetime, end: datetime) -> float:
        """Calculate average booking value."""
        from src.models.booking import Booking
        from src.models.invoice import Invoice

        invoices = db.query(Invoice).join(Booking).filter(
            Booking.created_at >= start,
            Booking.created_at <= end
        ).all()

        total_value = sum(i.amount for i in invoices)
        count = len(invoices)

        return round(total_value / count if count > 0 else 0, 2)

    async def _arun(
        self,
        metric_name: str,
        time_period: str = "30d",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(metric_name, time_period, run_manager)


class PredictDemandInput(BaseModel):
    """Input schema for demand prediction."""
    service_type: str = Field(description="Service type to predict demand for")
    forecast_days: int = Field(default=7, description="Number of days to forecast")


class PredictDemandTool(BaseTool):
    """
    Tool for predicting future demand.

    Uses historical data to forecast demand for services, helping with
    resource allocation and planning.
    """
    name = "predict_demand"
    description = """
    Predict future demand for a service type. Use this to forecast
    booking volumes for capacity planning. Input should include
    service type and number of days to forecast.
    """
    args_schema: Type[BaseModel] = PredictDemandInput

    def _run(
        self,
        service_type: str,
        forecast_days: int = 7,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Predict demand.

        Args:
            service_type: Service type to forecast
            forecast_days: Days to forecast
            run_manager: Callback manager

        Returns:
            str: JSON response with prediction
        """
        try:
            from src.models.booking import Booking

            db = next(get_db())

            # Get historical data (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            historical_bookings = db.query(Booking).filter(
                Booking.service_type == service_type,
                Booking.created_at >= start_date
            ).count()

            # Simple prediction: average daily bookings * forecast days
            avg_daily_bookings = historical_bookings / 30
            predicted_bookings = int(avg_daily_bookings * forecast_days)

            # Calculate confidence based on data availability
            confidence = min(100, int((historical_bookings / 30) * 10))

            forecast_data = []
            for day in range(forecast_days):
                forecast_date = datetime.utcnow() + timedelta(days=day + 1)
                forecast_data.append({
                    "date": forecast_date.isoformat()[:10],
                    "predicted_bookings": int(avg_daily_bookings),
                    "confidence": confidence
                })

            logger.info(f"Predicted {predicted_bookings} bookings for {service_type} over {forecast_days} days")

            import json
            return json.dumps({
                "success": True,
                "service_type": service_type,
                "forecast_days": forecast_days,
                "total_predicted_bookings": predicted_bookings,
                "avg_daily_bookings": round(avg_daily_bookings, 2),
                "confidence_score": confidence,
                "daily_forecast": forecast_data,
                "historical_data_points": historical_bookings
            })

        except Exception as e:
            logger.error(f"Failed to predict demand: {str(e)}")
            import json
            return json.dumps({
                "success": False,
                "error": str(e)
            })

    async def _arun(
        self,
        service_type: str,
        forecast_days: int = 7,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(service_type, forecast_days, run_manager)
