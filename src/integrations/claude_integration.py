"""
Claude AI integration for Project Handler.
Handles all Claude API interactions including streaming, cost tracking, and rate limiting.
"""
import os
import json
import time
import asyncio
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime, timedelta
from collections import deque
from anthropic import Anthropic, AsyncAnthropic
from src.core.logging import get_logger
from src.core.exceptions import AgentError


logger = get_logger("integration.claude")


class TokenCounter:
    """Count tokens and estimate costs."""

    # Approximate token counts per 1K tokens (prices from Anthropic)
    PRICING = {
        "claude-3-opus-20250219": {
            "input": 0.015,  # $15 per 1M input tokens
            "output": 0.075,  # $75 per 1M output tokens
        },
        "claude-3-5-sonnet-20241022": {
            "input": 0.003,  # $3 per 1M input tokens
            "output": 0.015,  # $15 per 1M output tokens
        },
        "claude-3-haiku-20250307": {
            "input": 0.00008,  # $0.08 per 1M input tokens
            "output": 0.0004,  # $0.4 per 1M output tokens
        },
    }

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.requests_count = 0

    def update(self, input_tokens: int, output_tokens: int) -> None:
        """Update token counts."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.requests_count += 1

    def estimate_cost(self, model: str) -> float:
        """Estimate cost in USD."""
        pricing = self.PRICING.get(model, self.PRICING["claude-3-5-sonnet-20241022"])
        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def get_stats(self) -> Dict[str, Any]:
        """Get token statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "requests": self.requests_count,
            "avg_tokens_per_request": (
                (self.total_input_tokens + self.total_output_tokens) / self.requests_count
                if self.requests_count > 0
                else 0
            ),
        }


class RateLimiter:
    """Rate limiter with sliding window."""

    def __init__(self, max_requests: int = 50, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times: deque = deque()

    async def acquire(self) -> None:
        """Acquire permission to make a request, blocking if necessary."""
        now = time.time()

        # Remove old requests outside the window
        while self.request_times and self.request_times[0] < now - self.window_seconds:
            self.request_times.popleft()

        # If we've hit the limit, wait
        if len(self.request_times) >= self.max_requests:
            wait_time = self.request_times[0] + self.window_seconds - now
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            # Recursively try again
            await self.acquire()
        else:
            self.request_times.append(time.time())

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "current_requests_in_window": len(self.request_times),
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
        }


class ClaudeAPIClient:
    """Synchronous Claude API client wrapper."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1,
    ):
        """Initialize Claude client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.client = Anthropic(api_key=api_key)
        self.token_counter = TokenCounter()
        self.rate_limiter = RateLimiter()

        logger.info(f"Claude client initialized with model: {model}")

    def send_message(
        self,
        system: str,
        user_message: str,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send message to Claude."""
        messages = messages or []
        messages.append({"role": "user", "content": user_message})

        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system,
                    messages=messages,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    **kwargs,
                )

                # Update token counter
                self.token_counter.update(
                    response.usage.input_tokens, response.usage.output_tokens
                )

                response_text = response.content[0].text

                return {
                    "success": True,
                    "content": response_text,
                    "model": self.model,
                    "tokens": {
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens,
                    },
                    "stop_reason": response.stop_reason,
                }

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e),
                        "model": self.model,
                    }

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "token_counter": self.token_counter.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
            "estimated_cost_usd": self.token_counter.estimate_cost(self.model),
        }


class AsyncClaudeAPIClient:
    """Asynchronous Claude API client wrapper."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1,
    ):
        """Initialize async Claude client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.client = AsyncAnthropic(api_key=api_key)
        self.token_counter = TokenCounter()
        self.rate_limiter = RateLimiter()

        logger.info(f"Async Claude client initialized with model: {model}")

    async def send_message(
        self,
        system: str,
        user_message: str,
        messages: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        **kwargs,
    ):
        """Send message to Claude asynchronously."""
        messages = messages or []
        messages.append({"role": "user", "content": user_message})

        await self.rate_limiter.acquire()

        for attempt in range(self.max_retries):
            try:
                if stream:
                    return await self._stream_message(system, messages, **kwargs)
                else:
                    return await self._regular_message(system, messages, **kwargs)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e),
                        "model": self.model,
                    }

    async def _regular_message(
        self, system: str, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """Send regular (non-streaming) message."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
            temperature=self.temperature,
            timeout=self.timeout,
            **kwargs,
        )

        self.token_counter.update(response.usage.input_tokens, response.usage.output_tokens)

        return {
            "success": True,
            "content": response.content[0].text,
            "model": self.model,
            "tokens": {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
        }

    async def _stream_message(
        self, system: str, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncIterator[str]:
        """Stream message from Claude."""
        async with await self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
            temperature=self.temperature,
            timeout=self.timeout,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "token_counter": self.token_counter.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
            "estimated_cost_usd": self.token_counter.estimate_cost(self.model),
        }


class ClaudeResponseParser:
    """Parse and validate Claude responses."""

    @staticmethod
    def parse_json(response: str) -> Dict[str, Any]:
        """Parse JSON from Claude response."""
        try:
            # Try to extract JSON if it's wrapped in markdown
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse JSON from response: {str(e)}")
            return {"raw_response": response}

    @staticmethod
    def parse_structured(response: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response according to schema."""
        try:
            data = ClaudeResponseParser.parse_json(response)
            # Validate against schema
            validated = {}
            for key, field_type in schema.items():
                if key in data:
                    validated[key] = data[key]
            return validated
        except Exception as e:
            logger.error(f"Failed to parse structured response: {str(e)}")
            return {"error": str(e), "raw_response": response}

    @staticmethod
    def extract_text_blocks(response: str) -> List[str]:
        """Extract text blocks from markdown response."""
        blocks = []
        in_code = False
        current_block = []

        for line in response.split("\n"):
            if line.startswith("```"):
                in_code = not in_code
                if not in_code and current_block:
                    blocks.append("\n".join(current_block))
                    current_block = []
            elif not in_code:
                current_block.append(line)

        if current_block:
            blocks.append("\n".join(current_block))

        return [block.strip() for block in blocks if block.strip()]


# Global client instance
_claude_client: Optional[AsyncClaudeAPIClient] = None


def get_claude_client() -> AsyncClaudeAPIClient:
    """Get global Claude client instance."""
    global _claude_client
    if _claude_client is None:
        _claude_client = AsyncClaudeAPIClient()
    return _claude_client
