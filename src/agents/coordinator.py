"""
Advanced Coordinator Agent for Project Handler.

Orchestrates and delegates tasks to specialized agents with:
- Intelligent task analysis and routing
- Priority queue management
- Load balancing
- Multi-agent workflow execution
- Conflict resolution
"""
from typing import Dict, Any, List, Optional, Set
import asyncio
from src.agents.base_agent import BaseAgent
from src.core.exceptions import ValidationError, AgentError
from src.core.message_bus import (
    get_message_bus,
    EventType,
    MessagePriority,
    publish_event,
    Message
)
from src.agents.orchestration import (
    TaskAnalyzer,
    IntelligentRouter,
    RoutingStrategy,
    PriorityTaskQueue,
    Task,
    TaskStatus,
    LoadBalancer,
    WorkflowExecutor,
    Workflow,
    WorkflowStep,
    WorkflowContext
)


class CoordinatorAgent(BaseAgent):
    """
    Advanced coordinator agent with full orchestration capabilities.

    Features:
    - Intelligent task analysis and routing
    - Priority-based task queue
    - Load balancing across agents
    - Multi-agent workflow execution
    - Event-driven communication
    - Conflict resolution
    - Performance monitoring
    """

    def __init__(self):
        super().__init__(
            name="coordinator",
            description="Advanced orchestration agent with intelligent routing and load balancing"
        )

        # Specialized agents registry
        self.specialized_agents: Dict[str, BaseAgent] = {}

        # Orchestration components
        self.task_analyzer = TaskAnalyzer()
        self.router = IntelligentRouter(strategy=RoutingStrategy.HYBRID)
        self.task_queue = PriorityTaskQueue(max_history=1000)
        self.load_balancer = LoadBalancer(max_tasks_per_agent=10, load_threshold=0.8)
        self.workflow_executor = WorkflowExecutor()

        # Message bus
        self.message_bus = get_message_bus()

        # Subscribe to relevant events
        self._subscribe_to_events()

        # Processing task
        self._processing = False
        self._processor_task = None

        # Stats
        self._stats = {
            "tasks_processed": 0,
            "tasks_delegated": 0,
            "workflows_executed": 0,
            "conflicts_resolved": 0
        }

        self.logger.info("Advanced coordinator agent initialized")

    def register_agent(self, agent_type: str, agent: BaseAgent) -> None:
        """
        Register a specialized agent.

        Args:
            agent_type: Type identifier for the agent
            agent: Agent instance to register
        """
        self.specialized_agents[agent_type] = agent
        self.load_balancer.register_agent(agent_type)
        self.workflow_executor.register_agent(agent_type, agent)

        self.logger.info(f"Registered {agent_type} agent: {agent.name}")

        # Publish agent registered event
        asyncio.create_task(
            publish_event(
                event_type=EventType.AGENT_REGISTERED,
                sender=self.name,
                data={
                    "agent_type": agent_type,
                    "agent_name": agent.name
                },
                priority=MessagePriority.LOW
            )
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process coordination request with advanced routing.

        Args:
            input_data: Must contain 'type' field and relevant data

        Returns:
            Dict[str, Any]: Coordination result
        """
        task_type = input_data.get("type")
        priority = input_data.get("priority", "normal")

        self.logger.info(f"Processing request of type: {task_type}")

        # Convert priority to numeric value
        priority_map = {
            "low": 75,
            "normal": 50,
            "high": 25,
            "critical": 0,
            "urgent": 0
        }
        priority_value = priority_map.get(priority.lower() if isinstance(priority, str) else "normal", 50)

        # Analyze task
        task_analysis = self.task_analyzer.analyze(input_data)

        self.logger.debug(
            f"Task analysis: type={task_analysis.task_type.value}, "
            f"complexity={task_analysis.complexity.value}, "
            f"requires_coordination={task_analysis.requires_coordination}"
        )

        # Route task
        agent_loads = {
            name: load.load_percentage
            for name, load in self.load_balancer.get_all_loads().items()
        }

        routing_decision = self.router.route(
            task_analysis=task_analysis,
            agent_loads=agent_loads
        )

        self.logger.info(
            f"Routing decision: primary={routing_decision.primary_agent}, "
            f"strategy={routing_decision.routing_strategy.value}, "
            f"confidence={routing_decision.confidence}%"
        )

        # Add task to queue
        task_id = self.task_queue.add_task(
            task_type=task_analysis.task_type.value,
            data=input_data,
            priority=priority_value,
            max_retries=3
        )

        # Execute task
        if task_analysis.requires_coordination:
            # Multi-agent workflow required
            result = await self._execute_coordinated_task(
                task_id=task_id,
                task_analysis=task_analysis,
                input_data=input_data
            )
        else:
            # Single agent execution
            result = await self._execute_single_agent_task(
                task_id=task_id,
                agent_name=routing_decision.primary_agent,
                input_data=input_data
            )

        self._stats["tasks_processed"] += 1

        return result

    async def _execute_single_agent_task(
        self,
        task_id: str,
        agent_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task with a single agent.

        Args:
            task_id: Task ID
            agent_name: Name of agent to execute the task
            input_data: Task input data

        Returns:
            Task result
        """
        agent = self.specialized_agents.get(agent_name)

        if not agent:
            error = f"Agent '{agent_name}' not found"
            self.task_queue.fail_task(task_id, error, retry=False)
            raise AgentError(error, agent_name=self.name)

        try:
            # Start task
            self.task_queue.start_task(task_id, agent_name)
            self.load_balancer.task_started(agent_name, task_id)

            # Publish task started event
            await publish_event(
                event_type=EventType.TASK_STARTED,
                sender=self.name,
                data={
                    "task_id": task_id,
                    "agent": agent_name
                },
                priority=MessagePriority.LOW
            )

            # Execute task
            import time
            start_time = time.time()

            result = await agent.execute(input_data)

            duration = time.time() - start_time

            # Complete task
            self.task_queue.complete_task(task_id, result)
            self.load_balancer.task_completed(agent_name, task_id, duration, success=True)

            # Publish task completed event
            await publish_event(
                event_type=EventType.TASK_COMPLETED,
                sender=self.name,
                data={
                    "task_id": task_id,
                    "agent": agent_name,
                    "duration": duration
                },
                priority=MessagePriority.LOW
            )

            self._stats["tasks_delegated"] += 1

            return {
                "task_id": task_id,
                "agent": agent_name,
                "status": "completed",
                "result": result,
                "duration": duration
            }

        except Exception as e:
            # Fail task
            import time
            duration = time.time() - start_time if 'start_time' in locals() else 0

            self.task_queue.fail_task(task_id, str(e), retry=True)
            self.load_balancer.task_completed(agent_name, task_id, duration, success=False)

            # Publish task failed event
            await publish_event(
                event_type=EventType.TASK_FAILED,
                sender=self.name,
                data={
                    "task_id": task_id,
                    "agent": agent_name,
                    "error": str(e)
                },
                priority=MessagePriority.HIGH
            )

            raise AgentError(
                f"Task execution failed: {str(e)}",
                agent_name=agent_name,
                details={"task_id": task_id}
            )

    async def _execute_coordinated_task(
        self,
        task_id: str,
        task_analysis: Any,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task that requires coordination between multiple agents.

        Args:
            task_id: Task ID
            task_analysis: Task analysis result
            input_data: Task input data

        Returns:
            Task result
        """
        self.logger.info(
            f"Executing coordinated task {task_id} with agents: "
            f"{task_analysis.required_agents}"
        )

        # Create a workflow for the coordinated task
        workflow = Workflow(
            name=f"coordinated_task_{task_analysis.task_type.value}",
            description=f"Coordinated execution of {task_analysis.task_type.value}",
            steps=[
                WorkflowStep(
                    name=f"step_{agent}",
                    agent=agent,
                    action="execute",
                    params=input_data
                )
                for agent in task_analysis.required_agents
            ],
            parallel=False,  # Sequential by default
            stop_on_error=True
        )

        # Execute workflow
        try:
            result = await self.workflow_executor.execute_workflow(workflow)

            # Complete task
            self.task_queue.complete_task(task_id, result)

            self._stats["workflows_executed"] += 1

            return {
                "task_id": task_id,
                "workflow_id": workflow.id,
                "status": "completed",
                "result": result
            }

        except Exception as e:
            # Fail task
            self.task_queue.fail_task(task_id, str(e), retry=False)

            raise AgentError(
                f"Coordinated task execution failed: {str(e)}",
                agent_name=self.name,
                details={"task_id": task_id, "workflow_id": workflow.id}
            )

    async def execute_workflow(
        self,
        workflow: Workflow
    ) -> Dict[str, Any]:
        """
        Execute a predefined workflow.

        Args:
            workflow: Workflow to execute

        Returns:
            Workflow execution result
        """
        self.logger.info(f"Executing workflow: {workflow.name}")

        result = await self.workflow_executor.execute_workflow(workflow)

        self._stats["workflows_executed"] += 1

        return result

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

        if "type" not in input_data:
            raise ValidationError(
                "Missing required field: type",
                details={"received_keys": list(input_data.keys())}
            )

        return True

    def get_registered_agents(self) -> Dict[str, str]:
        """
        Get list of registered agents.

        Returns:
            Dict[str, str]: Mapping of agent types to names
        """
        return {
            agent_type: agent.name
            for agent_type, agent in self.specialized_agents.items()
        }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.

        Returns:
            System status information
        """
        return {
            "coordinator": {
                "name": self.name,
                "status": self.status,
                "stats": self._stats
            },
            "agents": {
                agent_type: agent.get_status()
                for agent_type, agent in self.specialized_agents.items()
            },
            "task_queue": self.task_queue.get_stats(),
            "load_balancer": self.load_balancer.get_system_load(),
            "router": self.router.get_routing_stats(),
            "workflows": self.workflow_executor.get_stats(),
            "message_bus": self.message_bus.get_stats()
        }

    def get_load_recommendations(self) -> List[str]:
        """
        Get load balancing recommendations.

        Returns:
            List of recommendations
        """
        return self.load_balancer.get_recommendations()

    async def resolve_conflict(
        self,
        conflict_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between agents or tasks.

        Args:
            conflict_data: Conflict information

        Returns:
            Resolution result
        """
        conflict_type = conflict_data.get("type", "unknown")

        self.logger.info(f"Resolving conflict of type: {conflict_type}")

        # Simple priority-based resolution
        if conflict_type == "resource_conflict":
            # Use priority to resolve
            tasks = conflict_data.get("tasks", [])
            if tasks:
                # Sort by priority
                sorted_tasks = sorted(
                    tasks,
                    key=lambda t: t.get("priority", 50)
                )

                resolution = {
                    "winner": sorted_tasks[0],
                    "method": "priority_based",
                    "reasoning": "Highest priority task wins resource conflict"
                }

                self._stats["conflicts_resolved"] += 1

                return resolution

        # Default: escalate to human
        return {
            "resolution": "escalate",
            "method": "human_in_the_loop",
            "reasoning": f"Conflict type '{conflict_type}' requires human decision"
        }

    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant message bus events."""

        async def on_agent_error(message: Message):
            """Handle agent error events."""
            self.logger.error(
                f"Agent error received: {message.data.get('error')}"
            )

            # Could implement auto-recovery logic here
            agent_name = message.data.get("agent_name")
            if agent_name:
                # Mark agent as unavailable temporarily
                self.load_balancer.set_agent_availability(agent_name, False)

                # Re-enable after cooldown
                await asyncio.sleep(10)
                self.load_balancer.set_agent_availability(agent_name, True)

        # Subscribe to agent errors
        self.message_bus.subscribe(
            event_type=EventType.AGENT_ERROR,
            subscriber_name=self.name,
            callback=on_agent_error
        )

        self.logger.debug("Subscribed to message bus events")

    async def start_processing(self) -> None:
        """Start background task processing."""
        if self._processing:
            self.logger.warning("Task processing already running")
            return

        self._processing = True
        self._processor_task = asyncio.create_task(self._process_task_queue())

        # Start message bus if not running
        if not self.message_bus._running:
            await self.message_bus.start()

        self.logger.info("Started background task processing")

    async def stop_processing(self) -> None:
        """Stop background task processing."""
        if not self._processing:
            return

        self._processing = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Stopped background task processing")

    async def _process_task_queue(self) -> None:
        """Background task to process queued tasks."""
        while self._processing:
            try:
                # Get next task
                task = self.task_queue.get_next_task()

                if task:
                    # Get least loaded agent for this task
                    task_data = {"type": task.task_type, **task.data}

                    # Analyze and route
                    analysis = self.task_analyzer.analyze(task_data)
                    loads = {
                        name: load.load_percentage
                        for name, load in self.load_balancer.get_all_loads().items()
                    }

                    routing = self.router.route(analysis, loads)

                    # Execute
                    await self._execute_single_agent_task(
                        task_id=task.id,
                        agent_name=routing.primary_agent,
                        input_data=task_data
                    )
                else:
                    # No tasks, sleep briefly
                    await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error processing task queue: {e}")
                await asyncio.sleep(1)
