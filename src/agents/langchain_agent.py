"""
LangChain-powered Agent for Project Handler.
Extends BaseAgent with LangChain and Claude integration.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnablePassthrough

from src.agents.base_agent import BaseAgent
from src.agents.llm_config import get_llm_config
from src.core.exceptions import ValidationError, AgentError
from src.core.logging import get_logger

logger = get_logger(__name__)


class LangChainAgent(BaseAgent):
    """
    LangChain-powered agent that uses Claude for intelligent processing.

    Extends BaseAgent with LangChain integration for advanced NLP capabilities.
    Supports message history, system prompts, and tool calling.
    """

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_iterations: int = 3,
        memory_enabled: bool = True,
    ):
        """
        Initialize LangChain agent.

        Args:
            name: Unique agent name
            description: Agent description
            system_prompt: System prompt for the agent
            model: Claude model to use
            temperature: Temperature for generation
            max_iterations: Max iterations for agent loop
            memory_enabled: Enable message history memory
        """
        super().__init__(name, description)

        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.memory_enabled = memory_enabled

        # Initialize LLM client
        self.llm_config = get_llm_config(model=model, temperature=temperature)
        self.llm = self.llm_config.get_client()

        # Message history for conversation memory
        self.message_history: List[BaseMessage] = []

        # Tools available to the agent (populated by subclasses)
        self.tools: Dict[str, Any] = {}

        self.logger.info(
            f"LangChain agent '{self.name}' initialized with model {self.model}"
        )

    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt for the agent.

        Returns:
            str: Default system prompt
        """
        return f"""You are {self.name}, a specialized AI agent in Project Handler.
Description: {self.description}

Your responsibilities:
- Process requests efficiently and accurately
- Provide clear, structured responses
- Handle errors gracefully
- Always consider the full context of the conversation

Current capabilities:
- Process complex business logic
- Integrate with external services
- Maintain conversation context
- Make decisions based on available information

Always format your responses clearly and be concise."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input using LangChain and Claude.

        Args:
            input_data: Input dictionary containing:
                - 'message': User message or request
                - 'context': Optional context dict
                - 'tools': Optional list of tools to use

        Returns:
            Dict[str, Any]: Processing result with response and metadata

        Raises:
            AgentError: If processing fails
        """
        try:
            message = input_data.get("message", "")
            context = input_data.get("context", {})

            # Validate message
            if not message:
                raise ValidationError("Message is required", details={"input": input_data})

            self.logger.info(f"Agent {self.name} processing: {message[:100]}...")

            # Build message chain
            messages = self._build_message_chain(message, context)

            # Call Claude API
            response = await self._call_claude(messages)

            # Update message history
            if self.memory_enabled:
                self.message_history.append(HumanMessage(content=message))
                self.message_history.append(AIMessage(content=response))

            # Parse and return result
            return {
                "response": response,
                "message_count": len(self.message_history),
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_estimated": self.llm_config.estimate_tokens(response),
            }

        except Exception as e:
            self.logger.error(f"Agent {self.name} processing error: {str(e)}")
            raise AgentError(
                f"Agent {self.name} processing failed: {str(e)}",
                agent_name=self.name,
                details={"error": str(e), "input": input_data},
            )

    def _build_message_chain(
        self, message: str, context: Dict[str, Any]
    ) -> List[BaseMessage]:
        """
        Build message chain including history and context.

        Args:
            message: Current message
            context: Additional context

        Returns:
            List[BaseMessage]: Complete message chain
        """
        messages: List[BaseMessage] = []

        # System message
        system_msg = self.system_prompt
        if context:
            context_str = "\n".join(
                f"- {k}: {v}" for k, v in context.items() if k != "message"
            )
            system_msg += f"\n\nContext:\n{context_str}"

        messages.append(SystemMessage(content=system_msg))

        # Add message history if enabled
        if self.memory_enabled and self.message_history:
            messages.extend(self.message_history[-10:])  # Keep last 10 messages

        # Add current message
        messages.append(HumanMessage(content=message))

        return messages

    async def _call_claude(self, messages: List[BaseMessage]) -> str:
        """
        Call Claude API with message chain.

        Args:
            messages: List of messages

        Returns:
            str: Claude's response

        Raises:
            AgentError: If API call fails
        """
        try:
            # Create runnable chain
            chain = RunnablePassthrough() | self.llm

            # Call API
            response = chain.invoke({"messages": messages})

            # Extract text from response
            if hasattr(response, "content"):
                return response.content
            else:
                return str(response)

        except Exception as e:
            self.logger.error(f"Claude API call failed: {str(e)}")
            raise AgentError(
                f"Failed to call Claude API: {str(e)}",
                agent_name=self.name,
                details={"error": str(e)},
            )

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.

        Args:
            input_data: Input to validate

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If invalid
        """
        if not isinstance(input_data, dict):
            raise ValidationError(
                "Input must be a dictionary",
                details={"type": type(input_data).__name__},
            )

        if "message" not in input_data or not input_data["message"]:
            raise ValidationError(
                "Missing required field: 'message'",
                details={"keys": list(input_data.keys())},
            )

        return True

    def register_tool(self, tool_name: str, tool_func: Any) -> None:
        """
        Register a tool for the agent.

        Args:
            tool_name: Name of the tool
            tool_func: Callable tool function
        """
        self.tools[tool_name] = tool_func
        self.logger.info(f"Tool '{tool_name}' registered for agent {self.name}")

    def get_tools(self) -> Dict[str, Any]:
        """
        Get available tools.

        Returns:
            Dict[str, Any]: Mapping of tool names to functions
        """
        return self.tools.copy()

    def clear_history(self) -> None:
        """Clear message history."""
        self.message_history = []
        self.logger.info(f"Message history cleared for agent {self.name}")

    def get_memory_status(self) -> Dict[str, Any]:
        """
        Get memory/conversation status.

        Returns:
            Dict[str, Any]: Memory information
        """
        return {
            "memory_enabled": self.memory_enabled,
            "message_count": len(self.message_history),
            "tools_available": len(self.tools),
            "model": self.model,
            "system_prompt_length": len(self.system_prompt),
        }
