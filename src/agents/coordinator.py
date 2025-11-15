"""
Coordinator Agent for Project Handler - Intelligent version with LangChain.
Orchestrates and delegates tasks to specialized agents using AI.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, AgentError
from src.core.logging import get_logger

logger = get_logger("agent.coordinator")


class CoordinatorAgent(BaseAgent):
    """
    Intelligent coordinator agent that orchestrates tasks across specialized agents.

    Uses LangChain and Anthropic Claude to understand natural language requests,
    make intelligent routing decisions, and coordinate complex workflows.
    """

    def __init__(self):
        super().__init__(
            name="coordinator",
            description="AI-powered orchestration agent for intelligent task delegation"
        )
        self.specialized_agents = {}
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize LangChain components
        self._initialize_llm()
        self._initialize_memory()
        self._initialize_prompts()

    def _initialize_llm(self) -> None:
        """Initialize the Language Model (Claude)."""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found, using demo mode")
            self.llm = None
            self.demo_mode = True
        else:
            try:
                self.llm = ChatAnthropic(
                    anthropic_api_key=api_key,
                    model="claude-3-sonnet-20240229",
                    temperature=0.7,
                    max_tokens=2048
                )
                self.demo_mode = False
                logger.info("Initialized Claude-3 Sonnet model successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                self.llm = None
                self.demo_mode = True

    def _initialize_memory(self) -> None:
        """Initialize conversation memory."""
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

    def _initialize_prompts(self) -> None:
        """Initialize system prompts for the coordinator."""
        self.system_prompt = """You are an intelligent coordinator agent for a transportation management system called Project Handler.

Your role is to:
1. Understand natural language requests from users
2. Decide which specialized agent should handle the request
3. Extract relevant information and structure it appropriately
4. Coordinate complex multi-step workflows when needed

Available specialized agents:
- Communications Agent: Handles SMS, emails, phone calls (via Twilio/SendGrid)
- Financial Agent: Manages quotes, invoices, payments (via Stripe)
- Operations Agent: Plans routes, manages fleet, tracks deliveries (via Google Maps)
- Analytics Agent: Generates reports, analyzes data, provides insights

Current system capabilities:
- Customer management (CRUD operations)
- Booking management (create, list, update, cancel)
- User authentication and authorization

When a user makes a request:
1. Analyze the intent and extract key information
2. Determine if it requires a specialized agent or can be handled directly
3. Structure the response clearly and professionally
4. If delegating, specify which agent and what data to pass

Always be helpful, concise, and professional. If you're unsure, ask for clarification.
"""

    def register_agent(self, agent_type: str, agent: BaseAgent) -> None:
        """
        Register a specialized agent.

        Args:
            agent_type: Type identifier for the agent (e.g., 'communications', 'financial')
            agent: Agent instance to register
        """
        self.specialized_agents[agent_type] = agent
        self.logger.info(f"Registered {agent_type} agent: {agent.name}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process coordination request with AI-powered intelligence.

        Args:
            input_data: Request data with 'message' or 'task_type' and 'data'

        Returns:
            Dict[str, Any]: Intelligent coordination result
        """
        # Check if natural language message or structured task
        if "message" in input_data:
            return await self._process_natural_language(input_data)
        elif "task_type" in input_data:
            return await self._process_structured_task(input_data)
        else:
            raise ValidationError(
                "Input must contain either 'message' or 'task_type'",
                details={"received_keys": list(input_data.keys())}
            )

    async def _process_natural_language(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process natural language request using LLM.

        Args:
            input_data: Contains 'message' field with user request

        Returns:
            Dict[str, Any]: AI-generated response and routing decision
        """
        user_message = input_data["message"]
        context = input_data.get("context", {})

        self.logger.info(f"Processing natural language request: {user_message[:100]}...")

        # Demo mode fallback
        if self.demo_mode or not self.llm:
            return await self._demo_mode_response(user_message, context)

        try:
            # Build conversation context
            messages = [SystemMessage(content=self.system_prompt)]

            # Add conversation history
            for msg in self.conversation_history[-5:]:  # Last 5 messages
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

            # Add current message with context
            current_msg = f"User request: {user_message}"
            if context:
                current_msg += f"\n\nContext: {context}"
            messages.append(HumanMessage(content=current_msg))

            # Get AI response
            response = await self.llm.ainvoke(messages)
            ai_response = response.content

            # Save to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Analyze response for routing decisions
            routing = self._analyze_routing(ai_response, user_message)

            return {
                "response": ai_response,
                "routing": routing,
                "conversation_id": id(self),
                "message_count": len(self.conversation_history)
            }

        except Exception as e:
            self.logger.error(f"Error processing with LLM: {e}")
            return await self._demo_mode_response(user_message, context)

    async def _process_structured_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process structured task request (legacy mode).

        Args:
            input_data: Contains 'task_type' and 'data'

        Returns:
            Dict[str, Any]: Task execution result
        """
        task_type = input_data["task_type"]
        task_data = input_data.get("data", {})

        self.logger.info(f"Processing structured task: {task_type}")

        # Route to appropriate specialized agent
        if task_type in self.specialized_agents:
            agent = self.specialized_agents[task_type]
            try:
                result = await agent.execute(task_data)
                return {
                    "task_type": task_type,
                    "delegated_to": agent.name,
                    "status": "delegated",
                    "result": result
                }
            except Exception as e:
                return {
                    "task_type": task_type,
                    "status": "failed",
                    "error": str(e)
                }

        # Handle directly if no specialized agent
        return {
            "task_type": task_type,
            "status": "handled_directly",
            "message": f"Task '{task_type}' processed by coordinator",
            "note": "This is a basic response. Specialized agents not yet implemented."
        }

    def _analyze_routing(self, ai_response: str, user_message: str) -> Dict[str, Any]:
        """
        Analyze AI response to determine routing decisions.

        Args:
            ai_response: The AI's response
            user_message: Original user message

        Returns:
            Dict[str, Any]: Routing decision
        """
        # Simple keyword-based routing analysis
        keywords = {
            "communications": ["email", "sms", "call", "message", "notify", "send"],
            "financial": ["quote", "invoice", "payment", "charge", "bill", "stripe"],
            "operations": ["route", "delivery", "fleet", "driver", "vehicle", "location"],
            "analytics": ["report", "analyze", "metrics", "statistics", "dashboard"]
        }

        detected_agents = []
        message_lower = user_message.lower()
        response_lower = ai_response.lower()

        for agent_type, words in keywords.items():
            if any(word in message_lower or word in response_lower for word in words):
                detected_agents.append(agent_type)

        return {
            "suggested_agents": detected_agents,
            "requires_delegation": len(detected_agents) > 0,
            "complexity": "simple" if len(detected_agents) <= 1 else "complex"
        }

    async def _demo_mode_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate demo response when LLM is not available.

        Args:
            message: User message
            context: Request context

        Returns:
            Dict[str, Any]: Demo response
        """
        self.logger.info("Using demo mode (no API key)")

        # Simple rule-based responses
        message_lower = message.lower()

        if "help" in message_lower or "what can you do" in message_lower:
            response = """I'm the Project Handler Coordinator Agent! I can help you with:

🚚 **Booking Management**: Create, view, and manage transportation bookings
👥 **Customer Management**: Add and manage customer information
📊 **Analytics**: Generate reports and insights (coming soon)
💰 **Financial**: Handle quotes and invoices (coming soon)
📞 **Communications**: Send notifications via email/SMS (coming soon)

I'm currently in demo mode. To enable full AI capabilities, configure the ANTHROPIC_API_KEY environment variable.

How can I assist you today?"""

        elif any(word in message_lower for word in ["booking", "reserve", "transport"]):
            response = """I can help you create a new booking!

To create a booking, I need:
- Customer ID
- Origin address
- Destination address
- Pickup date and time
- Cargo details (weight, description)

Would you like me to guide you through creating a booking?"""

        elif any(word in message_lower for word in ["customer", "client"]):
            response = """I can help with customer management!

You can:
- Create new customers
- View customer list
- Update customer information
- Search for customers

What would you like to do?"""

        else:
            response = f"""I received your message: "{message}"

I'm currently in demo mode. With full AI capabilities enabled, I would:
1. Analyze your request intelligently
2. Route it to the appropriate specialized agent
3. Coordinate complex multi-step workflows
4. Provide natural, contextual responses

To enable full features, please configure the ANTHROPIC_API_KEY.

How else can I help you?"""

        routing = self._analyze_routing(response, message)

        return {
            "response": response,
            "routing": routing,
            "mode": "demo",
            "note": "Configure ANTHROPIC_API_KEY for full AI capabilities"
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate coordinator input.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(input_data, dict):
            raise ValidationError(
                "Input must be a dictionary",
                details={"received_type": type(input_data).__name__}
            )

        # Accept either natural language or structured format
        has_message = "message" in input_data
        has_task_type = "task_type" in input_data

        if not (has_message or has_task_type):
            raise ValidationError(
                "Input must contain either 'message' (for natural language) or 'task_type' (for structured tasks)",
                details={"received_keys": list(input_data.keys())}
            )

        return True

    def get_registered_agents(self) -> Dict[str, str]:
        """
        Get list of registered specialized agents.

        Returns:
            Dict[str, str]: Mapping of agent types to names
        """
        return {
            agent_type: agent.name
            for agent_type, agent in self.specialized_agents.items()
        }

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation history.

        Args:
            limit: Optional limit on number of messages to return

        Returns:
            List[Dict[str, str]]: Conversation history
        """
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        self.memory.clear()
        self.logger.info("Conversation history cleared")

    def get_status(self) -> Dict[str, Any]:
        """
        Get enhanced agent status with AI info.

        Returns:
            Dict[str, Any]: Extended status information
        """
        base_status = super().get_status()
        base_status.update({
            "ai_enabled": not self.demo_mode,
            "model": "claude-3-sonnet-20240229" if not self.demo_mode else None,
            "registered_agents": list(self.specialized_agents.keys()),
            "conversation_messages": len(self.conversation_history)
        })
        return base_status
