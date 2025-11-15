"""
LangChain Agent Demonstration Script.

This script demonstrates the LangChain-enabled agents with various
real-world scenarios. Can run with or without actual Claude API.

Usage:
    # With mocked LLM (no API key needed)
    python examples/langchain_demo.py --mock

    # With real Claude API (requires ANTHROPIC_API_KEY)
    python examples/langchain_demo.py
"""
import asyncio
import sys
from pathlib import Path
import argparse
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def demo_communications_agent(use_mock=False):
    """Demonstrate communications agent capabilities."""
    print("\n" + "=" * 60)
    print("DEMO 1: Communications Agent")
    print("=" * 60)

    if use_mock:
        print("[RUNNING IN MOCK MODE - No API calls]\n")
        # Mock the LangChain config
        with patch('src.agents.langchain_agent.get_langchain_config') as mock_config:
            mock_lc = MagicMock()
            mock_lc.get_llm.return_value = Mock()
            mock_lc.get_memory.return_value = Mock(buffer="")
            mock_callback = Mock()
            mock_callback.call_count = 0
            mock_callback.total_tokens = 0
            mock_lc.get_callback_handler.return_value = mock_callback
            mock_config.return_value = mock_lc

            from src.agents import LangChainCommunicationsAgent

            agent = LangChainCommunicationsAgent()

            # Mock the executor
            agent.agent_executor.invoke = Mock(return_value={
                "output": "I've sent an SMS to +1234567890 confirming the booking for tomorrow at 10am. Message ID: SM123abc",
                "intermediate_steps": []
            })

            task = "Send an SMS to customer at +1234567890 confirming their booking for tomorrow at 10am"
            print(f"Task: {task}\n")

            result = await agent.process({"task": task})

            print(f"✓ Status: {result['status']}")
            print(f"✓ Output: {result['output']}")
    else:
        from src.agents import LangChainCommunicationsAgent

        agent = LangChainCommunicationsAgent()

        task = "Send an SMS to customer at +1234567890 confirming their booking for tomorrow at 10am"
        print(f"Task: {task}\n")

        result = await agent.process({"task": task})

        print(f"✓ Status: {result['status']}")
        print(f"✓ Output: {result['output']}")
        print(f"✓ Tools used: {len(result.get('tool_usage', []))}")


async def demo_financial_agent(use_mock=False):
    """Demonstrate financial agent capabilities."""
    print("\n" + "=" * 60)
    print("DEMO 2: Financial Agent")
    print("=" * 60)

    if use_mock:
        print("[RUNNING IN MOCK MODE - No API calls]\n")
        with patch('src.agents.langchain_agent.get_langchain_config') as mock_config:
            mock_lc = MagicMock()
            mock_lc.get_llm.return_value = Mock()
            mock_lc.get_memory.return_value = Mock(buffer="")
            mock_callback = Mock()
            mock_callback.call_count = 0
            mock_callback.total_tokens = 0
            mock_lc.get_callback_handler.return_value = mock_callback
            mock_config.return_value = mock_lc

            from src.agents import LangChainFinancialAgent

            agent = LangChainFinancialAgent()

            agent.agent_executor.invoke = Mock(return_value={
                "output": "I've created a quote of $75.00 for the airport transfer service. Quote ID: quote_abc123. The quote is valid for 7 days.",
                "intermediate_steps": []
            })

            task = "Create a quote for airport transfer from downtown to JFK for 2 passengers"
            print(f"Task: {task}\n")

            result = await agent.process({"task": task})

            print(f"✓ Status: {result['status']}")
            print(f"✓ Output: {result['output']}")
    else:
        from src.agents import LangChainFinancialAgent

        agent = LangChainFinancialAgent()

        task = "Create a quote for airport transfer from downtown to JFK for 2 passengers"
        print(f"Task: {task}\n")

        result = await agent.process({"task": task})

        print(f"✓ Status: {result['status']}")
        print(f"✓ Output: {result['output']}")


async def demo_operations_agent(use_mock=False):
    """Demonstrate operations agent capabilities."""
    print("\n" + "=" * 60)
    print("DEMO 3: Operations Agent")
    print("=" * 60)

    if use_mock:
        print("[RUNNING IN MOCK MODE - No API calls]\n")
        with patch('src.agents.langchain_agent.get_langchain_config') as mock_config:
            mock_lc = MagicMock()
            mock_lc.get_llm.return_value = Mock()
            mock_lc.get_memory.return_value = Mock(buffer="")
            mock_callback = Mock()
            mock_callback.call_count = 0
            mock_callback.total_tokens = 0
            mock_lc.get_callback_handler.return_value = mock_callback
            mock_config.return_value = mock_lc

            from src.agents import LangChainOperationsAgent

            agent = LangChainOperationsAgent()

            agent.agent_executor.invoke = Mock(return_value={
                "output": "I've assigned a SUV (capacity: 7) to the booking and matched driver John Smith (license: DL-001). Estimated travel time: 25 minutes.",
                "intermediate_steps": []
            })

            task = "Assign vehicle and driver for booking with 5 passengers going to the airport"
            print(f"Task: {task}\n")

            result = await agent.process({"task": task})

            print(f"✓ Status: {result['status']}")
            print(f"✓ Output: {result['output']}")
    else:
        from src.agents import LangChainOperationsAgent

        agent = LangChainOperationsAgent()

        task = "Assign vehicle and driver for booking with 5 passengers going to the airport"
        print(f"Task: {task}\n")

        result = await agent.process({"task": task})

        print(f"✓ Status: {result['status']}")
        print(f"✓ Output: {result['output']}")


async def demo_analytics_agent(use_mock=False):
    """Demonstrate analytics agent capabilities."""
    print("\n" + "=" * 60)
    print("DEMO 4: Analytics Agent")
    print("=" * 60)

    if use_mock:
        print("[RUNNING IN MOCK MODE - No API calls]\n")
        with patch('src.agents.langchain_agent.get_langchain_config') as mock_config:
            mock_lc = MagicMock()
            mock_lc.get_llm.return_value = Mock()
            mock_lc.get_memory.return_value = Mock(buffer="")
            mock_callback = Mock()
            mock_callback.call_count = 0
            mock_callback.total_tokens = 0
            mock_lc.get_callback_handler.return_value = mock_callback
            mock_config.return_value = mock_lc

            from src.agents import LangChainAnalyticsAgent

            agent = LangChainAnalyticsAgent()

            agent.agent_executor.invoke = Mock(return_value={
                "output": "Based on last month's data: Total revenue: $12,450, Average booking value: $65, Conversion rate: 78%. Predicted demand for next week: 45 bookings.",
                "intermediate_steps": []
            })

            task = "Generate revenue report for last month and predict demand for next week"
            print(f"Task: {task}\n")

            result = await agent.process({"task": task})

            print(f"✓ Status: {result['status']}")
            print(f"✓ Output: {result['output']}")
    else:
        from src.agents import LangChainAnalyticsAgent

        agent = LangChainAnalyticsAgent()

        task = "Generate revenue report for last month and predict demand for next week"
        print(f"Task: {task}\n")

        result = await agent.process({"task": task})

        print(f"✓ Status: {result['status']}")
        print(f"✓ Output: {result['output']}")


async def demo_agent_stats(use_mock=False):
    """Demonstrate agent statistics and monitoring."""
    print("\n" + "=" * 60)
    print("DEMO 5: Agent Statistics")
    print("=" * 60)

    if use_mock:
        print("[RUNNING IN MOCK MODE]\n")
        with patch('src.agents.langchain_agent.get_langchain_config') as mock_config:
            mock_lc = MagicMock()
            mock_lc.get_llm.return_value = Mock()
            mock_lc.get_memory.return_value = Mock(buffer="")
            mock_callback = Mock()
            mock_callback.call_count = 3
            mock_callback.total_tokens = 1500
            mock_lc.get_callback_handler.return_value = mock_callback
            mock_config.return_value = mock_lc

            from src.agents import LangChainCommunicationsAgent

            agent = LangChainCommunicationsAgent()

            stats = agent.get_stats()

            print("Agent Statistics:")
            print(f"  Name: {stats['agent']}")
            print(f"  LangChain Enabled: {stats['langchain_enabled']}")
            print(f"  LLM Provider: {stats['llm_provider']}")
            print(f"  Tools Available: {stats['tool_count']}")
            print(f"  Tool Names: {', '.join(stats['tools'][:3])}...")
            print(f"  Has Memory: {stats['has_memory']}")
            print(f"  LLM Calls: {stats['llm_calls']}")
            print(f"  Total Tokens: {stats['total_tokens']}")
    else:
        from src.agents import LangChainCommunicationsAgent

        agent = LangChainCommunicationsAgent()

        stats = agent.get_stats()

        print("Agent Statistics:")
        print(f"  Name: {stats['agent']}")
        print(f"  LangChain Enabled: {stats['langchain_enabled']}")
        print(f"  LLM Provider: {stats['llm_provider']}")
        print(f"  Tools Available: {stats['tool_count']}")
        print(f"  Tool Names: {', '.join(stats['tools'])}")
        print(f"  Has Memory: {stats['has_memory']}")


async def main():
    """Run all demonstrations."""
    parser = argparse.ArgumentParser(description="LangChain Agent Demonstration")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode (no API calls required)"
    )
    args = parser.parse_args()

    use_mock = args.mock

    if not use_mock:
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("\n⚠️  WARNING: ANTHROPIC_API_KEY not found!")
            print("Running in mock mode automatically.\n")
            use_mock = True

    print("\n" + "=" * 60)
    print("LANGCHAIN AGENT DEMONSTRATION")
    if use_mock:
        print("Mode: MOCK (No API calls)")
    else:
        print("Mode: LIVE (Using Claude API)")
    print("=" * 60)

    try:
        # Run all demos
        await demo_communications_agent(use_mock)
        await demo_financial_agent(use_mock)
        await demo_operations_agent(use_mock)
        await demo_analytics_agent(use_mock)
        await demo_agent_stats(use_mock)

        print("\n" + "=" * 60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("  ✓ Communications Agent (SMS, Email, Calls)")
        print("  ✓ Financial Agent (Quotes, Invoices, Payments)")
        print("  ✓ Operations Agent (Routes, Vehicles, Drivers)")
        print("  ✓ Analytics Agent (Reports, Metrics, Predictions)")
        print("  ✓ Agent Statistics and Monitoring")
        print("\nTools Used:")
        print("  ✓ 20+ LangChain tools")
        print("  ✓ Claude LLM for reasoning")
        print("  ✓ ReAct pattern (Reasoning + Acting)")
        print("  ✓ Memory for context")

        if use_mock:
            print("\n💡 To run with real Claude API:")
            print("   1. Set ANTHROPIC_API_KEY environment variable")
            print("   2. Run: python examples/langchain_demo.py")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
