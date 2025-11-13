"""
Tests for AI3: Claude Integration
Tests Claude API client, rate limiting, cost tracking, and response parsing.
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from src.integrations.claude_integration import (
    TokenCounter,
    RateLimiter,
    ClaudeResponseParser,
)
from src.agents.claude_executor import (
    ClaudeExecutor,
    CommunicationsClaudeExecutor,
    FinancialClaudeExecutor,
)


class TestTokenCounter:
    """Test token counting and cost estimation."""

    def test_update_tokens(self):
        """Test updating token counts."""
        counter = TokenCounter()
        counter.update(100, 50)

        assert counter.total_input_tokens == 100
        assert counter.total_output_tokens == 50
        assert counter.requests_count == 1

    def test_multiple_updates(self):
        """Test multiple token updates."""
        counter = TokenCounter()
        counter.update(100, 50)
        counter.update(200, 100)

        assert counter.total_input_tokens == 300
        assert counter.total_output_tokens == 150
        assert counter.requests_count == 2

    def test_estimate_cost(self):
        """Test cost estimation."""
        counter = TokenCounter()
        counter.update(1_000_000, 1_000_000)

        cost = counter.estimate_cost("claude-3-5-sonnet-20241022")
        # 1M input tokens at $3 per 1M = $3
        # 1M output tokens at $15 per 1M = $15
        # Total = $18
        assert cost == pytest.approx(18.0, rel=0.1)

    def test_get_stats(self):
        """Test getting stats."""
        counter = TokenCounter()
        counter.update(100, 50)

        stats = counter.get_stats()
        assert stats["total_input_tokens"] == 100
        assert stats["total_output_tokens"] == 50
        assert stats["total_tokens"] == 150
        assert stats["requests"] == 1


class TestRateLimiter:
    """Test rate limiting."""

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring under rate limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # Should not block
        for _ in range(5):
            await limiter.acquire()

        assert len(limiter.request_times) == 5

    @pytest.mark.asyncio
    async def test_rate_limiter_stats(self):
        """Test rate limiter stats."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)

        for _ in range(5):
            await limiter.acquire()

        stats = limiter.get_stats()
        assert stats["current_requests_in_window"] == 5
        assert stats["max_requests"] == 10


class TestClaudeResponseParser:
    """Test response parsing."""

    def test_parse_plain_json(self):
        """Test parsing plain JSON response."""
        response = '{"status": "success", "result": "test"}'
        parsed = ClaudeResponseParser.parse_json(response)

        assert parsed["status"] == "success"
        assert parsed["result"] == "test"

    def test_parse_markdown_json(self):
        """Test parsing JSON in markdown code blocks."""
        response = """Here's the result:
```json
{"status": "success", "result": "test"}
```
"""
        parsed = ClaudeResponseParser.parse_json(response)
        assert parsed["status"] == "success"

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns raw response."""
        response = "This is not JSON"
        parsed = ClaudeResponseParser.parse_json(response)

        assert "raw_response" in parsed

    def test_parse_structured(self):
        """Test parsing structured response with schema."""
        response = '{"status": "success", "amount": 100, "currency": "USD"}'
        schema = {"status": str, "amount": int, "currency": str}

        parsed = ClaudeResponseParser.parse_structured(response, schema)
        assert parsed["status"] == "success"
        assert parsed["amount"] == 100

    def test_extract_text_blocks(self):
        """Test extracting text blocks from markdown."""
        response = """First paragraph.

```python
code block
```

Second paragraph."""

        blocks = ClaudeResponseParser.extract_text_blocks(response)
        assert len(blocks) == 2
        assert "First paragraph" in blocks[0]
        assert "Second paragraph" in blocks[1]


class TestClaudeExecutor:
    """Test Claude executor."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = ClaudeExecutor("test_agent")
        assert executor.agent_name == "test_agent"
        assert executor.client is not None

    def test_format_input_data(self):
        """Test formatting input data."""
        data = {"customer": "John", "amount": 100, "items": ["a", "b"]}
        formatted = ClaudeExecutor._format_input_data(data)

        assert "customer: John" in formatted
        assert "amount: 100" in formatted
        assert "items:" in formatted

    def test_build_prompt(self):
        """Test building complete prompt."""
        executor = ClaudeExecutor("test_agent")
        prompt = executor._build_prompt(
            task="Process payment",
            context="Customer context",
            input_data={"amount": 100},
            tools_info="Available tools",
            memory_context="Previous conversation",
        )

        assert "TASK: Process payment" in prompt
        assert "CONTEXT FROM MEMORY" in prompt
        assert "AVAILABLE TOOLS" in prompt
        assert "INPUT DATA" in prompt
        assert "JSON format" in prompt

    def test_default_system_prompt(self):
        """Test default system prompt."""
        executor = ClaudeExecutor("test_agent")
        prompt = executor._get_default_system_prompt()

        assert "test_agent" in prompt
        assert "Process incoming requests" in prompt


class TestSpecializedExecutors:
    """Test specialized Claude executors."""

    def test_communications_executor_prompt(self):
        """Test communications executor system prompt."""
        executor = CommunicationsClaudeExecutor()
        prompt = executor._get_default_system_prompt()

        assert "Communications Agent" in prompt
        assert "SMS" in prompt or "email" in prompt

    def test_financial_executor_prompt(self):
        """Test financial executor system prompt."""
        executor = FinancialClaudeExecutor()
        prompt = executor._get_default_system_prompt()

        assert "Financial Agent" in prompt
        assert "pricing" in prompt or "quote" in prompt

    def test_operations_executor_prompt(self):
        """Test operations executor system prompt."""
        executor = OperationsClaudeExecutor()
        prompt = executor._get_default_system_prompt()

        assert "Operations Agent" in prompt
        assert "route" in prompt.lower()


@pytest.mark.asyncio
async def test_executor_execute_success():
    """Test successful executor execution."""
    from src.agents.claude_executor import ClaudeExecutor

    executor = ClaudeExecutor("test_agent")

    # Mock the client
    mock_response = {
        "success": True,
        "content": '{"status": "success", "result": "test"}',
        "tokens": {"input": 100, "output": 50},
        "model": "test-model",
    }

    with patch.object(executor.client, "send_message", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response

        result = await executor.execute(
            task="test",
            context="context",
            input_data={"test": "data"},
        )

        assert result["success"] is True
        assert "result" in result
        assert result["agent"] == "test_agent"


@pytest.mark.asyncio
async def test_executor_execute_failure():
    """Test failed executor execution."""
    from src.agents.claude_executor import ClaudeExecutor

    executor = ClaudeExecutor("test_agent")

    # Mock failure response
    mock_response = {
        "success": False,
        "error": "API error",
    }

    with patch.object(executor.client, "send_message", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response

        result = await executor.execute(
            task="test",
            context="context",
            input_data={"test": "data"},
        )

        assert result["success"] is False
        assert "error" in result
