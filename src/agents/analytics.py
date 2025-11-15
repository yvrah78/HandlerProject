"""
Analytics Agent for Project Handler.
Handles metrics collection, reporting, and business intelligence using LangChain and Claude AI.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_anthropic import ChatAnthropic
from langchain.memory import ConversationBufferMemory

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, AgentError
from src.core.config import get_settings


class AnalyticsAgent(BaseAgent):
    """
    Advanced Analytics Agent powered by LangChain and Claude AI.

    Manages:
    - Real-time metrics collection and KPI tracking
    - Business intelligence reports with AI-powered insights
    - Performance dashboards and trend analysis
    - Predictive analytics and forecasting
    - Automated recommendations and action items
    """

    def __init__(self):
        super().__init__(
            name="analytics",
            description="AI-powered analytics, reporting, and business intelligence"
        )

        # Get configuration
        self.settings = get_settings()

        # Initialize Claude AI model
        self._initialize_ai_model()

        # Initialize LangChain components
        self._initialize_langchain_components()

        # Metrics storage (in-memory for now, will be DB later)
        self.metrics_cache = {}

        self.logger.info("Analytics Agent initialized with AI capabilities")

    def _initialize_ai_model(self):
        """Initialize Claude AI model for analytics."""
        try:
            if self.settings.anthropic_api_key:
                self.llm = ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    anthropic_api_key=self.settings.anthropic_api_key,
                    temperature=0.3,  # Lower temperature for more focused analytics
                    max_tokens=2048
                )
                self.ai_enabled = True
                self.logger.info("Claude AI model initialized successfully")
            else:
                self.llm = None
                self.ai_enabled = False
                self.logger.warning("No Anthropic API key found - AI features disabled")
        except Exception as e:
            self.llm = None
            self.ai_enabled = False
            self.logger.error(f"Failed to initialize AI model: {str(e)}")

    def _initialize_langchain_components(self):
        """Initialize LangChain chains and memory."""
        # Conversation memory for context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Prompt templates for different report types
        self.prompts = {
            "performance": self._create_performance_prompt(),
            "financial": self._create_financial_prompt(),
            "operations": self._create_operations_prompt(),
            "customer": self._create_customer_prompt(),
            "predictive": self._create_predictive_prompt()
        }

        # Create chains for each report type
        self.chains = {}
        if self.ai_enabled:
            for report_type, prompt in self.prompts.items():
                self.chains[report_type] = LLMChain(
                    llm=self.llm,
                    prompt=prompt,
                    memory=self.memory
                )

    def _create_performance_prompt(self) -> PromptTemplate:
        """Create prompt template for performance analytics."""
        template = """You are an expert business analyst for a transportation management system.

Analyze the following performance metrics and provide insights:

Metrics Data:
{metrics_data}

Time Period: {time_period}

Please provide:
1. Summary of key performance indicators
2. Notable trends and patterns
3. Areas of concern or underperformance
4. Actionable recommendations
5. Comparison with previous periods (if available)

Format your response as a structured business report."""

        return PromptTemplate(
            input_variables=["metrics_data", "time_period"],
            template=template
        )

    def _create_financial_prompt(self) -> PromptTemplate:
        """Create prompt template for financial analytics."""
        template = """You are a financial analyst for a transportation business.

Analyze the following financial metrics:

Financial Data:
{metrics_data}

Time Period: {time_period}

Provide analysis including:
1. Revenue and profit analysis
2. Cost structure and efficiency
3. Payment trends and cash flow
4. Financial health indicators
5. Revenue optimization recommendations

Be specific with numbers and percentages."""

        return PromptTemplate(
            input_variables=["metrics_data", "time_period"],
            template=template
        )

    def _create_operations_prompt(self) -> PromptTemplate:
        """Create prompt template for operations analytics."""
        template = """You are an operations analyst for a transportation fleet.

Analyze the following operational metrics:

Operations Data:
{metrics_data}

Time Period: {time_period}

Provide insights on:
1. Fleet utilization and efficiency
2. Route optimization opportunities
3. Driver performance
4. Booking completion rates
5. Operational bottlenecks and solutions

Focus on actionable operational improvements."""

        return PromptTemplate(
            input_variables=["metrics_data", "time_period"],
            template=template
        )

    def _create_customer_prompt(self) -> PromptTemplate:
        """Create prompt template for customer analytics."""
        template = """You are a customer success analyst for a transportation service.

Analyze the following customer metrics:

Customer Data:
{metrics_data}

Time Period: {time_period}

Analyze:
1. Customer acquisition and retention trends
2. Satisfaction scores and feedback patterns
3. Booking behavior and preferences
4. Customer lifetime value indicators
5. Strategies to improve customer experience

Provide customer-centric recommendations."""

        return PromptTemplate(
            input_variables=["metrics_data", "time_period"],
            template=template
        )

    def _create_predictive_prompt(self) -> PromptTemplate:
        """Create prompt template for predictive analytics."""
        template = """You are a data scientist specializing in predictive analytics for transportation.

Analyze the following historical data and trends:

Historical Data:
{metrics_data}

Time Period: {time_period}

Provide predictions and forecasts for:
1. Future demand patterns
2. Revenue projections
3. Resource requirements (fleet, drivers)
4. Potential risks and challenges
5. Growth opportunities

Base predictions on data patterns and industry knowledge."""

        return PromptTemplate(
            input_variables=["metrics_data", "time_period"],
            template=template
        )

    async def collect_metrics(self, time_period: str = "daily") -> Dict[str, Any]:
        """
        Collect real-time metrics from the system.

        Args:
            time_period: Time period for metrics (daily, weekly, monthly)

        Returns:
            Dict containing collected metrics
        """
        # TODO: Integrate with actual database queries
        # For now, return simulated metrics

        now = datetime.utcnow()
        metrics = {
            "timestamp": now.isoformat(),
            "time_period": time_period,

            # Revenue metrics
            "revenue": {
                "total_revenue": 45000.00,
                "average_booking_value": 150.00,
                "revenue_growth": 12.5,  # percentage
                "payment_success_rate": 98.5
            },

            # Operational metrics
            "operations": {
                "total_bookings": 300,
                "completed_bookings": 285,
                "cancelled_bookings": 15,
                "completion_rate": 95.0,
                "average_trip_duration": 45,  # minutes
                "fleet_utilization": 78.5  # percentage
            },

            # Customer metrics
            "customers": {
                "total_customers": 1200,
                "new_customers": 45,
                "returning_customers": 255,
                "customer_satisfaction": 4.6,  # out of 5
                "retention_rate": 85.0
            },

            # Fleet metrics
            "fleet": {
                "total_vehicles": 25,
                "active_vehicles": 20,
                "maintenance_required": 2,
                "average_vehicle_efficiency": 82.0,
                "fuel_cost_per_km": 0.85
            }
        }

        # Cache metrics
        self.metrics_cache[time_period] = metrics

        return metrics

    async def generate_report(
        self,
        report_type: str,
        time_period: str = "daily",
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Generate analytics report with AI insights.

        Args:
            report_type: Type of report (performance, financial, operations, customer, predictive)
            time_period: Time period for analysis
            use_ai: Whether to use AI for generating insights

        Returns:
            Dict containing report data and insights
        """
        # Collect latest metrics
        metrics = await self.collect_metrics(time_period)

        # Base report structure
        report = {
            "report_type": report_type,
            "time_period": time_period,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "insights": None,
            "recommendations": []
        }

        # Generate AI insights if enabled
        if use_ai and self.ai_enabled and report_type in self.chains:
            try:
                # Format metrics for AI analysis
                metrics_summary = self._format_metrics_for_ai(metrics, report_type)

                # Run LangChain chain to generate insights
                chain = self.chains[report_type]
                ai_response = await chain.arun(
                    metrics_data=metrics_summary,
                    time_period=time_period
                )

                report["insights"] = ai_response
                report["ai_generated"] = True

                self.logger.info(f"Generated AI insights for {report_type} report")

            except Exception as e:
                self.logger.error(f"Failed to generate AI insights: {str(e)}")
                report["insights"] = "AI insights unavailable"
                report["ai_generated"] = False
        else:
            # Fallback to basic insights
            report["insights"] = self._generate_basic_insights(metrics, report_type)
            report["ai_generated"] = False

        return report

    def _format_metrics_for_ai(self, metrics: Dict[str, Any], report_type: str) -> str:
        """Format metrics data for AI consumption."""
        # Select relevant metrics based on report type
        if report_type == "financial":
            relevant_data = metrics.get("revenue", {})
        elif report_type == "operations":
            relevant_data = metrics.get("operations", {})
        elif report_type == "customer":
            relevant_data = metrics.get("customers", {})
        else:
            relevant_data = metrics

        # Format as readable text
        formatted = []
        for key, value in relevant_data.items():
            if isinstance(value, dict):
                formatted.append(f"\n{key.upper()}:")
                for sub_key, sub_value in value.items():
                    formatted.append(f"  - {sub_key.replace('_', ' ').title()}: {sub_value}")
            else:
                formatted.append(f"- {key.replace('_', ' ').title()}: {value}")

        return "\n".join(formatted)

    def _generate_basic_insights(self, metrics: Dict[str, Any], report_type: str) -> str:
        """Generate basic insights without AI."""
        insights = []

        if report_type == "performance":
            ops = metrics.get("operations", {})
            insights.append(f"Completion rate: {ops.get('completion_rate', 0)}%")
            insights.append(f"Fleet utilization: {metrics.get('fleet', {}).get('average_vehicle_efficiency', 0)}%")

        elif report_type == "financial":
            rev = metrics.get("revenue", {})
            insights.append(f"Total revenue: ${rev.get('total_revenue', 0):,.2f}")
            insights.append(f"Revenue growth: {rev.get('revenue_growth', 0)}%")

        elif report_type == "customer":
            cust = metrics.get("customers", {})
            insights.append(f"Customer satisfaction: {cust.get('customer_satisfaction', 0)}/5")
            insights.append(f"Retention rate: {cust.get('retention_rate', 0)}%")

        return " | ".join(insights) if insights else "No insights available"

    async def get_kpis(self, time_period: str = "daily") -> Dict[str, Any]:
        """
        Get key performance indicators.

        Args:
            time_period: Time period for KPIs

        Returns:
            Dict containing KPIs
        """
        metrics = await self.collect_metrics(time_period)

        # Calculate KPIs
        kpis = {
            "revenue_per_booking": metrics["revenue"]["total_revenue"] / max(metrics["operations"]["total_bookings"], 1),
            "customer_acquisition_cost": metrics["revenue"]["total_revenue"] / max(metrics["customers"]["new_customers"], 1),
            "booking_completion_rate": metrics["operations"]["completion_rate"],
            "fleet_efficiency": metrics["fleet"]["average_vehicle_efficiency"],
            "customer_satisfaction": metrics["customers"]["customer_satisfaction"],
            "revenue_growth": metrics["revenue"]["revenue_growth"]
        }

        return {
            "time_period": time_period,
            "kpis": kpis,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process analytics request.

        Args:
            input_data: Must contain 'report_type' and optional 'time_period', 'metrics'

        Returns:
            Dict[str, Any]: Analytics result
        """
        report_type = input_data.get("report_type")
        time_period = input_data.get("time_period", "daily")
        use_ai = input_data.get("use_ai", True)

        self.logger.info(f"Processing {report_type} analytics request for {time_period}")

        # Route to appropriate method
        if report_type in ["performance", "financial", "operations", "customer", "predictive"]:
            return await self.generate_report(report_type, time_period, use_ai)
        elif report_type == "kpis":
            return await self.get_kpis(time_period)
        elif report_type == "metrics":
            return await self.collect_metrics(time_period)
        else:
            # Default: return metrics
            return await self.collect_metrics(time_period)

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate analytics input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ["report_type"]

        for field in required_fields:
            if field not in input_data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    details={"received_keys": list(input_data.keys())}
                )

        valid_reports = [
            "performance", "financial", "operations",
            "customer", "predictive", "kpis", "metrics"
        ]

        if input_data["report_type"] not in valid_reports:
            raise ValidationError(
                f"Invalid report type. Must be one of: {valid_reports}",
                details={"received": input_data["report_type"]}
            )

        # Validate time_period if provided
        if "time_period" in input_data:
            valid_periods = ["daily", "weekly", "monthly", "yearly"]
            if input_data["time_period"] not in valid_periods:
                raise ValidationError(
                    f"Invalid time period. Must be one of: {valid_periods}",
                    details={"received": input_data["time_period"]}
                )

        return True

    async def get_insights(self, context: str = "") -> Dict[str, Any]:
        """
        Get AI-powered insights about the business.

        Args:
            context: Optional context for specific insights

        Returns:
            Dict containing AI-generated insights
        """
        if not self.ai_enabled:
            return {
                "insights": "AI insights not available - Anthropic API key not configured",
                "ai_enabled": False
            }

        try:
            # Create a general insights prompt
            prompt = f"""As a business intelligence expert for a transportation management system,
            provide strategic insights and recommendations based on current operations.

            Context: {context if context else 'General business overview'}

            Provide:
            1. Current state assessment
            2. Key opportunities for improvement
            3. Risk factors to monitor
            4. Strategic recommendations
            5. Next steps for management
            """

            response = await self.llm.ainvoke(prompt)

            return {
                "insights": response.content,
                "ai_enabled": True,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to generate insights: {str(e)}")
            return {
                "insights": f"Error generating insights: {str(e)}",
                "ai_enabled": True,
                "error": str(e)
            }
