"""
LLM Configuration for Project Handler.
Sets up Claude API and LangChain integration.
"""
from typing import Optional, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.language_model import LanguageModel
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LLMConfig:
    """
    Centralized LLM configuration for Project Handler.
    Manages Claude API setup and token optimization.
    """

    # Default Claude model (latest available)
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    # Token limits for different models
    MODEL_LIMITS = {
        "claude-3-5-sonnet-20241022": {
            "max_tokens": 200000,
            "rpm_limit": 40,  # Requests per minute
            "tpm_limit": 40000,  # Tokens per minute
        },
        "claude-3-opus-20250219": {
            "max_tokens": 200000,
            "rpm_limit": 40,
            "tpm_limit": 40000,
        },
        "claude-3-sonnet-20240229": {
            "max_tokens": 200000,
            "rpm_limit": 40,
            "tpm_limit": 40000,
        },
    }

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize LLM configuration.

        Args:
            model: Claude model to use
            temperature: Temperature for response generation (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

        # Get model limits
        if model in self.MODEL_LIMITS:
            model_config = self.MODEL_LIMITS[model]
            self.max_tokens = max_tokens or model_config["max_tokens"]
            self.rpm_limit = model_config["rpm_limit"]
            self.tpm_limit = model_config["tpm_limit"]
        else:
            self.max_tokens = max_tokens or 4096
            self.rpm_limit = 40
            self.tpm_limit = 40000

        # Initialize the Claude client
        self.client = self._initialize_client()
        logger.info(f"LLM configured with model: {self.model}")

    def _initialize_client(self) -> ChatAnthropic:
        """
        Initialize Claude API client.

        Returns:
            ChatAnthropic: Configured Claude client
        """
        return ChatAnthropic(
            model_name=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            max_retries=self.max_retries,
            api_key=settings.anthropic_api_key,
        )

    def get_client(self) -> ChatAnthropic:
        """
        Get the LLM client.

        Returns:
            ChatAnthropic: Configured Claude client
        """
        return self.client

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the configured model.

        Returns:
            Dict[str, Any]: Model configuration and limits
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "rpm_limit": self.rpm_limit,
            "tpm_limit": self.tpm_limit,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            int: Approximate token count (rough estimate)
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    def check_token_budget(self, text: str, margin: float = 0.1) -> bool:
        """
        Check if text fits within token budget.

        Args:
            text: Text to check
            margin: Safety margin (0.1 = 10%)

        Returns:
            bool: True if text fits within budget
        """
        estimated_tokens = self.estimate_tokens(text)
        budget = int(self.max_tokens * (1 - margin))
        return estimated_tokens <= budget


# Global LLM config instance
_llm_config: Optional[LLMConfig] = None


def get_llm_config(
    model: str = LLMConfig.DEFAULT_MODEL,
    temperature: float = 0.7,
) -> LLMConfig:
    """
    Get or create global LLM configuration.

    Args:
        model: Claude model to use
        temperature: Temperature for response generation

    Returns:
        LLMConfig: Global LLM configuration instance
    """
    global _llm_config

    if _llm_config is None:
        _llm_config = LLMConfig(model=model, temperature=temperature)

    return _llm_config


def reset_llm_config() -> None:
    """Reset global LLM configuration (for testing)."""
    global _llm_config
    _llm_config = None
