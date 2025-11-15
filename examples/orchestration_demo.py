"""
Demonstration of Multi-Agent Orchestration System.

This script demonstrates:
1. Message Bus communication
2. Task analysis and intelligent routing
3. Priority queue management
4. Load balancing
5. Workflow execution
6. Complete booking workflow
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.message_bus import get_message_bus, EventType, publish_event, MessagePriority
from src.agents.coordinator import CoordinatorAgent
from src.agents.communications import CommunicationsAgent
from src.agents.financial import FinancialAgent
from src.agents.operations import OperationsAgent
from src.agents.analytics import AnalyticsAgent
from src.agents.workflows import (
    create_booking_workflow,
    create_payment_workflow,
    create_communication_workflow
)


async def demo_message_bus():
    """Demonstrate message bus functionality."""
    print("\n" + "=" * 60)
    print("DEMO 1: Message Bus Communication")
    print("=" * 60)

    bus = get_message_bus()
    await bus.start()

    # Subscribe to events
    received_messages = []

    async def on_task_created(message):
        received_messages.append(message)
        print(f"✓ Received task created event: {message.data}")

    bus.subscribe(
        event_type=EventType.TASK_CREATED,
        subscriber_name="demo_subscriber",
        callback=on_task_created
    )

    # Publish events
    print("\nPublishing events...")
    await publish_event(
        event_type=EventType.TASK_CREATED,
        sender="demo",
        data={"task_id": "task_001", "type": "send_sms"},
        priority=MessagePriority.NORMAL
    )

    await asyncio.sleep(0.5)

    print(f"\n✓ Total events received: {len(received_messages)}")
    print(f"✓ Message bus stats: {bus.get_stats()}")

    await bus.stop()


async def demo_task_analysis():
    """Demonstrate task analysis."""
    print("\n" + "=" * 60)
    print("DEMO 2: Intelligent Task Analysis")
    print("=" * 60)

    from src.agents.orchestration import TaskAnalyzer

    analyzer = TaskAnalyzer()

    # Analyze different types of tasks
    tasks = [
        {"type": "send_sms", "recipient": "1234567890"},
        {"type": "create_booking", "customer_id": "123"},
        {"type": "process_payment", "amount": 100, "priority": "critical"},
        {"type": "booking_workflow", "customer_id": "456"}
    ]

    for task_data in tasks:
        analysis = analyzer.analyze(task_data)
        print(f"\nTask: {task_data['type']}")
        print(f"  → Type: {analysis.task_type.value}")
        print(f"  → Required agents: {analysis.required_agents}")
        print(f"  → Complexity: {analysis.complexity.value}")
        print(f"  → Priority score: {analysis.priority_score}")
        print(f"  → Needs coordination: {analysis.requires_coordination}")


async def demo_routing():
    """Demonstrate intelligent routing."""
    print("\n" + "=" * 60)
    print("DEMO 3: Intelligent Routing")
    print("=" * 60)

    from src.agents.orchestration import TaskAnalyzer, IntelligentRouter, RoutingStrategy

    analyzer = TaskAnalyzer()
    router = IntelligentRouter(strategy=RoutingStrategy.HYBRID)

    # Different load scenarios
    agent_loads = {
        "communications": 0.2,
        "financial": 0.8,
        "operations": 0.5,
        "analytics": 0.1
    }

    print("\nCurrent agent loads:")
    for agent, load in agent_loads.items():
        print(f"  {agent}: {load:.1%}")

    # Route tasks
    tasks = [
        {"type": "send_email"},
        {"type": "create_invoice"},
        {"type": "assign_vehicle"}
    ]

    print("\nRouting decisions:")
    for task_data in tasks:
        analysis = analyzer.analyze(task_data)
        decision = router.route(analysis, agent_loads)

        print(f"\nTask: {task_data['type']}")
        print(f"  → Primary agent: {decision.primary_agent}")
        print(f"  → Backup agents: {decision.backup_agents}")
        print(f"  → Strategy: {decision.routing_strategy.value}")
        print(f"  → Confidence: {decision.confidence}%")
        print(f"  → Reasoning: {decision.reasoning}")


async def demo_priority_queue():
    """Demonstrate priority queue."""
    print("\n" + "=" * 60)
    print("DEMO 4: Priority Queue Management")
    print("=" * 60)

    from src.agents.orchestration import PriorityTaskQueue

    queue = PriorityTaskQueue()

    # Add tasks with different priorities
    print("\nAdding tasks with different priorities...")
    tasks = [
        ("Normal task", {"type": "send_email"}, 50),
        ("Critical task", {"type": "process_payment"}, 0),
        ("Low priority task", {"type": "generate_report"}, 75),
        ("High priority task", {"type": "send_sms"}, 20)
    ]

    for name, data, priority in tasks:
        task_id = queue.add_task(name, data, priority=priority)
        print(f"  Added: {name} (priority: {priority})")

    # Process tasks in priority order
    print("\nProcessing tasks in priority order:")
    while queue.get_queue_size() > 0:
        task = queue.get_next_task()
        if task:
            print(f"  → Processing: {task.task_type} (priority: {task.priority})")
            queue.start_task(task.id, "demo_agent")
            queue.complete_task(task.id, {"status": "success"})

    print(f"\n✓ Queue stats: {queue.get_stats()}")


async def demo_load_balancing():
    """Demonstrate load balancing."""
    print("\n" + "=" * 60)
    print("DEMO 5: Load Balancing")
    print("=" * 60)

    from src.agents.orchestration import LoadBalancer

    lb = LoadBalancer(max_tasks_per_agent=5, load_threshold=0.8)

    # Register agents
    agents = ["communications", "financial", "operations", "analytics"]
    for agent in agents:
        lb.register_agent(agent)

    print("\nSimulating task load...")

    # Simulate tasks
    for i in range(10):
        least_loaded = lb.get_least_loaded_agent()
        if least_loaded:
            lb.task_started(least_loaded, f"task_{i}")
            print(f"  Task {i} → {least_loaded}")

    # Show load distribution
    print("\nCurrent load distribution:")
    for agent_name, load in lb.get_all_loads().items():
        print(f"  {agent_name}: {load.active_tasks} tasks ({load.load_percentage:.1%})")

    # System stats
    print(f"\n✓ System load: {lb.get_system_load()}")
    print("\n✓ Recommendations:")
    for rec in lb.get_recommendations():
        print(f"  - {rec}")


async def demo_coordinator():
    """Demonstrate coordinator agent."""
    print("\n" + "=" * 60)
    print("DEMO 6: Coordinator Agent")
    print("=" * 60)

    coordinator = CoordinatorAgent()

    # Register specialized agents
    print("\nRegistering specialized agents...")
    coordinator.register_agent("communications", CommunicationsAgent())
    coordinator.register_agent("financial", FinancialAgent())
    coordinator.register_agent("operations", OperationsAgent())
    coordinator.register_agent("analytics", AnalyticsAgent())

    print(f"✓ Registered agents: {list(coordinator.get_registered_agents().keys())}")

    # Process tasks
    print("\nProcessing tasks through coordinator...")
    tasks = [
        {
            "type": "send_sms",
            "communication_type": "sms",
            "recipient": "1234567890",
            "message": "Test message"
        },
        {
            "type": "create_booking",
            "customer_id": "cust_123",
            "service_type": "local"
        }
    ]

    for task in tasks:
        result = await coordinator.process(task)
        print(f"\n✓ Task completed:")
        print(f"  Type: {task['type']}")
        print(f"  Agent: {result.get('agent')}")
        print(f"  Status: {result.get('status')}")

    # System status
    print("\n✓ System status:")
    status = coordinator.get_system_status()
    print(f"  Active tasks: {status['task_queue']['active_tasks']}")
    print(f"  Completed tasks: {status['coordinator']['stats']['tasks_processed']}")


async def demo_workflows():
    """Demonstrate workflow execution."""
    print("\n" + "=" * 60)
    print("DEMO 7: Workflow Execution")
    print("=" * 60)

    coordinator = CoordinatorAgent()

    # Register agents
    coordinator.register_agent("communications", CommunicationsAgent())
    coordinator.register_agent("financial", FinancialAgent())
    coordinator.register_agent("operations", OperationsAgent())

    # 1. Booking Workflow
    print("\n1. Creating and executing booking workflow...")
    booking_workflow = create_booking_workflow({
        "customer_id": "cust_123",
        "service_type": "airport_transfer",
        "pickup_location": "123 Main St",
        "dropoff_location": "Airport Terminal 1",
        "pickup_time": "2024-12-01T10:00:00",
        "passenger_count": 2,
        "customer_phone": "1234567890",
        "customer_email": "test@example.com"
    })

    print(f"  Workflow: {booking_workflow.name}")
    print(f"  Steps: {len(booking_workflow.steps)}")
    for i, step in enumerate(booking_workflow.steps, 1):
        print(f"    {i}. {step.name} (agent: {step.agent})")

    result = await coordinator.execute_workflow(booking_workflow)
    print(f"\n✓ Booking workflow result: {result['success']}")

    # 2. Payment Workflow
    print("\n2. Creating and executing payment workflow...")
    payment_workflow = create_payment_workflow({
        "customer_id": "cust_123",
        "service_type": "local_ride",
        "amount": 50.00,
        "customer_email": "test@example.com",
        "auto_process_payment": False
    }, skip_quote=True)

    print(f"  Workflow: {payment_workflow.name}")
    print(f"  Steps: {len(payment_workflow.steps)}")

    result = await coordinator.execute_workflow(payment_workflow)
    print(f"\n✓ Payment workflow result: {result['success']}")

    # 3. Communication Workflow
    print("\n3. Creating and executing communication workflow...")
    comm_workflow = create_communication_workflow({
        "recipient_phone": "1234567890",
        "recipient_email": "test@example.com",
        "message": "Your booking is confirmed!",
        "subject": "Booking Confirmation",
        "channels": ["sms", "email"]
    })

    print(f"  Workflow: {comm_workflow.name}")
    print(f"  Steps: {len(comm_workflow.steps)}")

    result = await coordinator.execute_workflow(comm_workflow)
    print(f"\n✓ Communication workflow result: {result['success']}")


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("MULTI-AGENT ORCHESTRATION SYSTEM DEMONSTRATION")
    print("=" * 60)

    try:
        # Run all demos
        await demo_message_bus()
        await demo_task_analysis()
        await demo_routing()
        await demo_priority_queue()
        await demo_load_balancing()
        await demo_coordinator()
        await demo_workflows()

        print("\n" + "=" * 60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("  ✓ Message Bus for inter-agent communication")
        print("  ✓ Intelligent task analysis and classification")
        print("  ✓ Smart routing with multiple strategies")
        print("  ✓ Priority-based task queue management")
        print("  ✓ Load balancing across agents")
        print("  ✓ Coordinated multi-agent execution")
        print("  ✓ Complete workflow orchestration")
        print("\nWorkflows Available:")
        print("  ✓ Booking Workflow (6 steps)")
        print("  ✓ Payment Workflow (5 steps)")
        print("  ✓ Communication Workflow (3 steps)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
