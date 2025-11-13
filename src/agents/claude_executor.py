"""
Claude executor for intelligent agent processing.
Integrates Claude AI into agent workflows with specialized prompts and context.
"""
from typing import Dict, Any, Optional, List
from src.integrations.claude_integration import (
    AsyncClaudeAPIClient,
    ClaudeResponseParser,
    get_claude_client,
)
from src.core.logging import get_logger


logger = get_logger("agents.claude_executor")


class ClaudeExecutor:
    """Executes agent tasks using Claude AI."""

    def __init__(
        self,
        agent_name: str,
        client: Optional[AsyncClaudeAPIClient] = None,
    ):
        """
        Initialize Claude executor.

        Args:
            agent_name: Name of the agent using this executor
            client: Claude API client (uses global if not provided)
        """
        self.agent_name = agent_name
        self.client = client or get_claude_client()
        self.response_parser = ClaudeResponseParser()

    async def execute(
        self,
        task: str,
        context: str,
        input_data: Dict[str, Any],
        tools_info: Optional[str] = None,
        memory_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task using Claude.

        Args:
            task: Task description
            context: Context information
            input_data: Input data for the task
            tools_info: Available tools description
            memory_context: Previous conversation context
            system_prompt: System prompt for Claude

        Returns:
            Execution result from Claude
        """
        # Build the full prompt
        full_prompt = self._build_prompt(
            task, context, input_data, tools_info, memory_context
        )

        # Use provided system prompt or default
        system = system_prompt or self._get_default_system_prompt()

        try:
            # Call Claude
            response = await self.client.send_message(
                system=system,
                user_message=full_prompt,
            )

            if not response.get("success"):
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error"),
                    "agent": self.agent_name,
                }

            # Parse response
            parsed_response = self.response_parser.parse_json(response["content"])

            return {
                "success": True,
                "result": parsed_response,
                "agent": self.agent_name,
                "tokens": response.get("tokens"),
                "model": response.get("model"),
                "raw_content": response["content"],
            }

        except Exception as e:
            logger.error(f"Claude execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
            }

    def _build_prompt(
        self,
        task: str,
        context: str,
        input_data: Dict[str, Any],
        tools_info: Optional[str],
        memory_context: Optional[str],
    ) -> str:
        """Build complete prompt for Claude."""
        parts = [f"TASK: {task}"]

        if memory_context:
            parts.append(f"\nCONTEXT FROM MEMORY:\n{memory_context}")

        if context:
            parts.append(f"\nCONTEXT:\n{context}")

        if tools_info:
            parts.append(f"\nAVAILABLE TOOLS:\n{tools_info}")

        parts.append(f"\nINPUT DATA:\n{self._format_input_data(input_data)}")

        parts.append(
            "\nPlease process this task and respond in JSON format "
            "with the structure: {status: string, result: object, actions: array}"
        )

        return "\n".join(parts)

    @staticmethod
    def _format_input_data(data: Dict[str, Any]) -> str:
        """Format input data for prompt."""
        parts = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                parts.append(f"- {key}: {str(value)[:200]}")
            else:
                parts.append(f"- {key}: {value}")
        return "\n".join(parts) if parts else "No input data"

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for agent."""
        return f"""You are the {self.agent_name} agent in the Project Handler system.

Your role:
- Process incoming requests intelligently
- Use available tools to complete tasks
- Provide clear, structured responses
- Track all actions taken

Guidelines:
1. Analyze requests thoroughly before acting
2. Use tools when needed to complete tasks
3. Provide detailed explanations for decisions
4. Return results in the requested JSON format
5. Handle errors gracefully with clear error messages

Always be professional, efficient, and thorough."""


class CommunicationsClaudeExecutor(ClaudeExecutor):
    """Claude executor specialized for communications agent."""

    def __init__(self, client: Optional[AsyncClaudeAPIClient] = None):
        super().__init__("communications", client)

    def _get_default_system_prompt(self) -> str:
        return """You are the Communications Agent for Project Handler.

Your role:
- Send SMS, emails, and manage voice communications
- Personalize messages for customers
- Track communication history and preferences
- Ensure timely delivery of all communications

When processing requests:
1. Validate customer contact information
2. Select appropriate communication channel (SMS/Email/Voice)
3. Personalize message content
4. Schedule delivery if requested
5. Log communication for audit trail

Respond with JSON: {status, message_id, delivery_status, channel, recipient}"""


class FinancialClaudeExecutor(ClaudeExecutor):
    """Claude executor specialized for financial agent."""

    def __init__(self, client: Optional[AsyncClaudeAPIClient] = None):
        super().__init__("financial", client)

    def _get_default_system_prompt(self) -> str:
        return """You are the Financial Agent for Project Handler.

Your role:
- Generate accurate quotes and pricing
- Create and manage invoices
- Process secure payments
- Generate financial reports

When processing requests:
1. Calculate pricing based on distance, service, and applicable fees
2. Generate invoices with itemization
3. Process payments through Stripe securely
4. Update financial records
5. Provide transaction confirmations

Respond with JSON: {status, amount, currency, transaction_id, receipt_url}"""


class OperationsClaudeExecutor(ClaudeExecutor):
    """Claude executor specialized for operations agent."""

    def __init__(self, client: Optional[AsyncClaudeAPIClient] = None):
        super().__init__("operations", client)

    def _get_default_system_prompt(self) -> str:
        return """You are the Operations Agent for Project Handler.

Your role:
- Optimize routes and logistics
- Manage fleet assignments
- Track vehicle and driver availability
- Ensure on-time service delivery

When processing requests:
1. Calculate optimized routes
2. Check vehicle and driver availability
3. Assign appropriate vehicle to booking
4. Provide time estimates
5. Handle service disruptions

Respond with JSON: {status, route, vehicle_id, driver_id, eta, estimated_distance}"""


class AnalyticsClaudeExecutor(ClaudeExecutor):
    """Claude executor specialized for analytics agent."""

    def __init__(self, client: Optional[AsyncClaudeAPIClient] = None):
        super().__init__("analytics", client)

    def _get_default_system_prompt(self) -> str:
        return """You are the Analytics Agent for Project Handler.

Your role:
- Generate insights from business data
- Create reports and dashboards
- Track KPIs and performance metrics
- Identify trends and opportunities

When processing requests:
1. Query relevant data
2. Aggregate and analyze metrics
3. Identify trends and patterns
4. Generate insights and recommendations
5. Create visualizations

Respond with JSON: {status, report_type, metrics, insights, recommendations}"""
