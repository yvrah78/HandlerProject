"""
Integration tests for multi-agent workflows.

Tests:
- Message bus communication
- Task analysis and routing
- Priority queue management
- Load balancing
- Workflow execution
- Complete booking workflow
- Complete payment workflow
- Complete communication workflow
"""
import pytest
import asyncio
from datetime import datetime
from src.core.message_bus import (
    get_message_bus,
    EventType,
    MessagePriority,
    publish_event
)
from src.agents.coordinator import CoordinatorAgent
from src.agents.communications import CommunicationsAgent
from src.agents.financial import FinancialAgent
from src.agents.operations import OperationsAgent
from src.agents.analytics import AnalyticsAgent
from src.agents.orchestration import (
    TaskAnalyzer,
    IntelligentRouter,
    RoutingStrategy,
    PriorityTaskQueue,
    LoadBalancer,
    WorkflowExecutor,
    Workflow,
    WorkflowStep,
    WorkflowContext,
    TaskType
)
from src.agents.workflows import (
    create_booking_workflow,
    create_payment_workflow,
    create_communication_workflow
)


@pytest.fixture
async def message_bus():
    """Get message bus instance."""
    bus = get_message_bus()
    await bus.start()
    yield bus
    await bus.stop()
    bus.clear_history()


@pytest.fixture
def coordinator():
    """Create coordinator agent with registered agents."""
    coord = CoordinatorAgent()

    # Register specialized agents
    coord.register_agent("communications", CommunicationsAgent())
    coord.register_agent("financial", FinancialAgent())
    coord.register_agent("operations", OperationsAgent())
    coord.register_agent("analytics", AnalyticsAgent())

    return coord


@pytest.fixture
def task_analyzer():
    """Create task analyzer."""
    return TaskAnalyzer()


@pytest.fixture
def router():
    """Create intelligent router."""
    return IntelligentRouter(strategy=RoutingStrategy.HYBRID)


@pytest.fixture
def task_queue():
    """Create priority task queue."""
    return PriorityTaskQueue()


@pytest.fixture
def load_balancer():
    """Create load balancer."""
    lb = LoadBalancer(max_tasks_per_agent=10)

    # Register some agents
    lb.register_agent("communications")
    lb.register_agent("financial")
    lb.register_agent("operations")
    lb.register_agent("analytics")

    return lb


@pytest.fixture
def workflow_executor():
    """Create workflow executor."""
    executor = WorkflowExecutor()

    # Register mock agents
    executor.register_agent("communications", CommunicationsAgent())
    executor.register_agent("financial", FinancialAgent())
    executor.register_agent("operations", OperationsAgent())

    return executor


# Message Bus Tests
class TestMessageBus:
    """Test message bus functionality."""

    @pytest.mark.asyncio
    async def test_message_publishing(self, message_bus):
        """Test message publishing."""
        received = []

        async def callback(message):
            received.append(message)

        # Subscribe
        message_bus.subscribe(
            event_type=EventType.TASK_CREATED,
            subscriber_name="test_subscriber",
            callback=callback
        )

        # Publish message
        await publish_event(
            event_type=EventType.TASK_CREATED,
            sender="test",
            data={"task_id": "123"}
        )

        # Wait for processing
        await asyncio.sleep(0.2)

        assert len(received) == 1
        assert received[0].data["task_id"] == "123"

    @pytest.mark.asyncio
    async def test_message_filtering(self, message_bus):
        """Test message filtering by recipients."""
        received = []

        async def callback(message):
            received.append(message)

        # Subscribe two subscribers
        message_bus.subscribe(
            event_type=EventType.TASK_ASSIGNED,
            subscriber_name="agent1",
            callback=callback
        )

        message_bus.subscribe(
            event_type=EventType.TASK_ASSIGNED,
            subscriber_name="agent2",
            callback=callback
        )

        # Publish message to specific recipient
        await publish_event(
            event_type=EventType.TASK_ASSIGNED,
            sender="coordinator",
            data={"task": "test"},
            recipients={"agent1"}
        )

        await asyncio.sleep(0.2)

        # Only agent1 should receive it
        assert len(received) == 1


# Task Analysis Tests
class TestTaskAnalyzer:
    """Test task analyzer."""

    def test_task_type_identification(self, task_analyzer):
        """Test identifying task types."""
        # SMS task
        result = task_analyzer.analyze({"type": "send_sms", "recipient": "123"})
        assert result.task_type == TaskType.SEND_SMS
        assert "communications" in result.required_agents

        # Booking task
        result = task_analyzer.analyze({"type": "create_booking", "customer_id": "1"})
        assert result.task_type == TaskType.CREATE_BOOKING
        assert "operations" in result.required_agents

        # Payment task
        result = task_analyzer.analyze({"type": "process_payment", "amount": 100})
        assert result.task_type == TaskType.PROCESS_PAYMENT
        assert "financial" in result.required_agents

    def test_priority_calculation(self, task_analyzer):
        """Test priority score calculation."""
        # High priority task
        result = task_analyzer.analyze({
            "type": "process_payment",
            "priority": "critical",
            "deadline": "2024-12-31"
        })
        assert result.priority_score > 70

        # Low priority task
        result = task_analyzer.analyze({
            "type": "generate_report",
            "priority": "low"
        })
        assert result.priority_score < 50


# Routing Tests
class TestIntelligentRouter:
    """Test intelligent router."""

    def test_capability_based_routing(self, router, task_analyzer):
        """Test routing based on capabilities."""
        analysis = task_analyzer.analyze({"type": "send_email"})

        decision = router.route(
            task_analysis=analysis,
            strategy=RoutingStrategy.CAPABILITY_BASED
        )

        assert decision.primary_agent == "communications"
        assert decision.confidence > 0

    def test_load_balanced_routing(self, router, task_analyzer):
        """Test load-balanced routing."""
        analysis = task_analyzer.analyze({"type": "create_invoice"})

        agent_loads = {
            "financial": 0.8,  # Highly loaded
            "operations": 0.2
        }

        decision = router.route(
            task_analysis=analysis,
            agent_loads=agent_loads,
            strategy=RoutingStrategy.LOAD_BALANCED
        )

        assert decision.primary_agent == "financial"  # Still routes to capable agent


# Priority Queue Tests
class TestPriorityTaskQueue:
    """Test priority task queue."""

    def test_task_queuing(self, task_queue):
        """Test adding tasks to queue."""
        # Add tasks with different priorities
        id1 = task_queue.add_task("task1", {"data": 1}, priority=50)
        id2 = task_queue.add_task("task2", {"data": 2}, priority=10)  # Higher priority
        id3 = task_queue.add_task("task3", {"data": 3}, priority=90)  # Lower priority

        # Higher priority task should be first
        task = task_queue.get_next_task()
        assert task.task_type == "task2"

        task = task_queue.get_next_task()
        assert task.task_type == "task1"

        task = task_queue.get_next_task()
        assert task.task_type == "task3"

    def test_task_retry(self, task_queue):
        """Test task retry mechanism."""
        task_id = task_queue.add_task("retry_test", {"data": 1}, max_retries=3)

        # Get and fail task
        task = task_queue.get_next_task()
        task_queue.start_task(task_id, "test_agent")
        task_queue.fail_task(task_id, "Test error", retry=True)

        # Task should be back in queue
        stats = task_queue.get_stats()
        assert stats["total_retries"] == 1


# Load Balancer Tests
class TestLoadBalancer:
    """Test load balancer."""

    def test_agent_registration(self, load_balancer):
        """Test agent registration."""
        load_balancer.register_agent("test_agent")

        loads = load_balancer.get_all_loads()
        assert "test_agent" in loads
        assert loads["test_agent"].active_tasks == 0

    def test_load_tracking(self, load_balancer):
        """Test load tracking."""
        agent_name = "communications"

        # Start task
        load_balancer.task_started(agent_name, "task1")
        load = load_balancer.get_agent_load(agent_name)
        assert load.active_tasks == 1

        # Complete task
        load_balancer.task_completed(agent_name, "task1", duration=1.0, success=True)
        load = load_balancer.get_agent_load(agent_name)
        assert load.active_tasks == 0
        assert load.completed_tasks == 1

    def test_least_loaded_agent(self, load_balancer):
        """Test finding least loaded agent."""
        # Start tasks on different agents
        load_balancer.task_started("communications", "task1")
        load_balancer.task_started("communications", "task2")
        load_balancer.task_started("financial", "task3")

        # Financial should be less loaded
        least_loaded = load_balancer.get_least_loaded_agent(
            ["communications", "financial"]
        )
        assert least_loaded == "financial"


# Workflow Executor Tests
class TestWorkflowExecutor:
    """Test workflow executor."""

    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, workflow_executor):
        """Test executing a simple workflow."""
        workflow = Workflow(
            name="test_workflow",
            steps=[
                WorkflowStep(
                    name="step1",
                    agent="communications",
                    action="execute",
                    params={"type": "send_sms", "communication_type": "sms", "recipient": "123"}
                )
            ],
            parallel=False
        )

        result = await workflow_executor.execute_workflow(workflow)

        assert result["success"] is True
        assert workflow.status.value == "completed"

    @pytest.mark.asyncio
    async def test_workflow_context_sharing(self, workflow_executor):
        """Test context sharing between workflow steps."""
        context = WorkflowContext()
        context.set("shared_value", "test")

        def check_context(ctx, result):
            assert ctx.get("shared_value") == "test"
            ctx.set("step1_executed", True)

        workflow = Workflow(
            name="context_test",
            steps=[
                WorkflowStep(
                    name="step1",
                    agent="communications",
                    action="execute",
                    params={"type": "send_sms", "communication_type": "sms", "recipient": "123"},
                    on_success=check_context
                )
            ],
            context=context
        )

        await workflow_executor.execute_workflow(workflow)

        assert workflow.context.get("step1_executed") is True


# Coordinator Tests
class TestCoordinator:
    """Test coordinator agent."""

    @pytest.mark.asyncio
    async def test_agent_registration(self, coordinator):
        """Test agent registration."""
        agents = coordinator.get_registered_agents()

        assert "communications" in agents
        assert "financial" in agents
        assert "operations" in agents
        assert "analytics" in agents

    @pytest.mark.asyncio
    async def test_task_delegation(self, coordinator):
        """Test task delegation to specialized agents."""
        result = await coordinator.process({
            "type": "send_sms",
            "communication_type": "sms",
            "recipient": "1234567890",
            "message": "Test message"
        })

        assert result["status"] == "completed"
        assert result["agent"] == "communications"

    @pytest.mark.asyncio
    async def test_system_status(self, coordinator):
        """Test getting system status."""
        status = coordinator.get_system_status()

        assert "coordinator" in status
        assert "agents" in status
        assert "task_queue" in status
        assert "load_balancer" in status

    @pytest.mark.asyncio
    async def test_conflict_resolution(self, coordinator):
        """Test conflict resolution."""
        conflict_data = {
            "type": "resource_conflict",
            "tasks": [
                {"id": "task1", "priority": 50},
                {"id": "task2", "priority": 10},  # Higher priority (lower number)
            ]
        }

        resolution = await coordinator.resolve_conflict(conflict_data)

        assert resolution["winner"]["id"] == "task2"
        assert resolution["method"] == "priority_based"


# Workflow Integration Tests
class TestWorkflowIntegration:
    """Test complete workflow execution."""

    @pytest.mark.asyncio
    async def test_booking_workflow(self, coordinator):
        """Test complete booking workflow."""
        booking_data = {
            "customer_id": "cust_123",
            "service_type": "airport_transfer",
            "pickup_location": "123 Main St",
            "dropoff_location": "Airport Terminal 1",
            "pickup_time": "2024-12-01T10:00:00",
            "passenger_count": 2,
            "customer_phone": "1234567890",
            "customer_email": "test@example.com",
            "payment_method": "card"
        }

        workflow = create_booking_workflow(booking_data)

        result = await coordinator.execute_workflow(workflow)

        assert result["success"] is True
        assert "workflow_id" in result

    @pytest.mark.asyncio
    async def test_payment_workflow(self, coordinator):
        """Test complete payment workflow."""
        payment_data = {
            "customer_id": "cust_123",
            "service_type": "local_ride",
            "amount": 50.00,
            "payment_method": "card",
            "customer_email": "test@example.com",
            "auto_process_payment": False  # Don't auto-process in test
        }

        workflow = create_payment_workflow(payment_data, skip_quote=True)

        result = await coordinator.execute_workflow(workflow)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_communication_workflow(self, coordinator):
        """Test complete communication workflow."""
        communication_data = {
            "recipient_phone": "1234567890",
            "recipient_email": "test@example.com",
            "message": "Test notification",
            "subject": "Test Subject",
            "priority": "normal",
            "channels": ["sms", "email"]
        }

        workflow = create_communication_workflow(communication_data)

        result = await coordinator.execute_workflow(workflow)

        assert result["success"] is True


# Performance Tests
class TestPerformance:
    """Test system performance and load handling."""

    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, coordinator):
        """Test processing multiple tasks concurrently."""
        tasks = [
            coordinator.process({
                "type": "send_sms",
                "communication_type": "sms",
                "recipient": f"123456789{i}",
                "message": f"Message {i}"
            })
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All tasks should complete
        assert len(results) == 5
        # Check that at least some completed successfully
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "completed")
        assert successful > 0

    def test_load_balancing_under_load(self, load_balancer):
        """Test load balancer under heavy load."""
        # Simulate many tasks
        for i in range(50):
            agent = load_balancer.get_least_loaded_agent()
            if agent:
                load_balancer.task_started(agent, f"task_{i}")

        # Check system load
        system_load = load_balancer.get_system_load()

        assert system_load["total_active_tasks"] > 0
        assert system_load["average_load"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
