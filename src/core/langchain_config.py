"""
LangChain configuration and setup for Project Handler.

This module provides the base configuration for integrating LangChain
with the multi-agent system, including:
- LLM configurations (Claude, GPT, etc.)
- Memory management
- Callback handlers
- Tool registries
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from enum import Enum

from langchain.llms.base import BaseLLM
from langchain.chat_models import ChatAnthropic
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult

from src.core.logging import get_logger
from src.core.config import get_settings


logger = get_logger(__name__)
settings = get_settings()


class LLMProvider(str, Enum):
    """Available LLM providers."""
    CLAUDE = "claude"
    GPT4 = "gpt4"
    GPT35 = "gpt35"


class AgentCallbackHandler(BaseCallbackHandler):
    """
    Custom callback handler for tracking agent LLM interactions.

    Logs all LLM calls, tool usage, and agent decisions for debugging
    and analytics purposes.
    """

    def __init__(self, agent_name: str):
        """
        Initialize callback handler.

        Args:
            agent_name: Name of the agent using this handler
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"langchain.{agent_name}")
        self.call_count = 0
        self.total_tokens = 0
        self.start_time = None

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts running."""
        self.start_time = datetime.utcnow()
        self.call_count += 1
        self.logger.debug(
            f"LLM call #{self.call_count} started for {self.agent_name}",
            extra={"prompts": prompts[:100]}  # Log first 100 chars
        )

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends running."""
        duration = (datetime.utcnow() - self.start_time).total_seconds()

        # Track token usage if available
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            tokens = token_usage.get('total_tokens', 0)
            self.total_tokens += tokens

            self.logger.info(
                f"LLM call completed in {duration:.2f}s",
                extra={
                    "agent": self.agent_name,
                    "tokens": tokens,
                    "total_tokens": self.total_tokens,
                    "call_count": self.call_count
                }
            )

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        self.logger.error(
            f"LLM error in {self.agent_name}: {str(error)}",
            exc_info=True
        )

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when tool starts running."""
        tool_name = serialized.get("name", "unknown")
        self.logger.debug(
            f"Tool '{tool_name}' started",
            extra={"agent": self.agent_name, "input": input_str[:100]}
        )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool ends running."""
        self.logger.debug(
            f"Tool completed",
            extra={"agent": self.agent_name, "output": output[:100]}
        )

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when tool errors."""
        self.logger.error(
            f"Tool error in {self.agent_name}: {str(error)}",
            exc_info=True
        )

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when agent takes an action."""
        self.logger.info(
            f"Agent action: {action.tool}",
            extra={
                "agent": self.agent_name,
                "tool": action.tool,
                "input": str(action.tool_input)[:100]
            }
        )

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when agent finishes."""
        self.logger.info(
            f"Agent finished",
            extra={
                "agent": self.agent_name,
                "output": str(finish.return_values)[:100]
            }
        )


class LangChainConfig:
    """
    Configuration manager for LangChain integration.

    Provides methods to create and configure LLMs, memory, and
    other LangChain components for use with agents.
    """

    def __init__(self):
        """Initialize LangChain configuration."""
        self.logger = get_logger(__name__)
        self._llm_cache: Dict[str, BaseLLM] = {}

    def get_llm(
        self,
        provider: LLMProvider = LLMProvider.CLAUDE,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> BaseLLM:
        """
        Get or create an LLM instance.

        Args:
            provider: LLM provider to use
            model: Specific model name (optional, uses defaults)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Returns:
            BaseLLM: Configured LLM instance

        Raises:
            ValueError: If provider is not supported or API key is missing
        """
        cache_key = f"{provider}_{model}_{temperature}_{max_tokens}"

        # Return cached LLM if available
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]

        # Create new LLM based on provider
        if provider == LLMProvider.CLAUDE:
            llm = self._create_claude_llm(model, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # Cache and return
        self._llm_cache[cache_key] = llm
        self.logger.info(f"Created {provider} LLM with model {model or 'default'}")
        return llm

    def _create_claude_llm(
        self,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> ChatAnthropic:
        """
        Create Claude LLM instance.

        Args:
            model: Model name (e.g., 'claude-3-opus-20240229')
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional arguments

        Returns:
            ChatAnthropic: Configured Claude LLM

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Please set it to use Claude."
            )

        # Default to Claude 3 Sonnet if no model specified
        model_name = model or "claude-3-sonnet-20240229"

        return ChatAnthropic(
            model=model_name,
            anthropic_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def get_memory(
        self,
        memory_type: str = "buffer",
        max_token_limit: int = 2000,
        **kwargs
    ) -> ConversationBufferMemory:
        """
        Get conversation memory for an agent.

        Args:
            memory_type: Type of memory ("buffer" or "summary")
            max_token_limit: Maximum tokens to keep in memory
            **kwargs: Additional memory-specific arguments

        Returns:
            ConversationBufferMemory: Configured memory instance
        """
        if memory_type == "buffer":
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                **kwargs
            )
        elif memory_type == "summary":
            llm = self.get_llm()
            return ConversationSummaryMemory(
                llm=llm,
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=max_token_limit,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

    def get_callback_handler(self, agent_name: str) -> AgentCallbackHandler:
        """
        Get callback handler for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentCallbackHandler: Callback handler instance
        """
        return AgentCallbackHandler(agent_name)

    def clear_cache(self):
        """Clear the LLM cache."""
        self._llm_cache.clear()
        self.logger.info("LLM cache cleared")


# Global configuration instance
_langchain_config: Optional[LangChainConfig] = None


def get_langchain_config() -> LangChainConfig:
    """
    Get global LangChain configuration instance.

    Returns:
        LangChainConfig: Global configuration instance
    """
    global _langchain_config
    if _langchain_config is None:
        _langchain_config = LangChainConfig()
    return _langchain_config


def reset_langchain_config():
    """Reset global LangChain configuration (useful for testing)."""
    global _langchain_config
    _langchain_config = None
