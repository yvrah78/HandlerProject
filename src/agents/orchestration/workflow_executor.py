"""
Workflow Executor for multi-step agent workflows.

Executes complex workflows that involve multiple agents and steps:
- Sequential execution
- Parallel execution
- Conditional branching
- Error handling and retries
- Context sharing between steps
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from src.core.logging import get_logger
from src.core.message_bus import (
    get_message_bus,
    EventType,
    MessagePriority,
    publish_event
)


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Workflow step status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.

    Attributes:
        name: Step name
        agent: Agent to execute the step
        action: Action/method to execute
        params: Parameters for the action
        retry_count: Number of retries on failure
        timeout: Timeout in seconds
        on_success: Callback on success
        on_failure: Callback on failure
        condition: Optional condition function (returns bool)
    """

    name: str
    agent: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 3
    timeout: float = 30.0
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None
    condition: Optional[Callable] = None
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class WorkflowContext:
    """
    Shared context for workflow execution.

    Allows steps to share data and state.
    """

    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context."""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """Check if a key exists in the context."""
        return key in self.data

    def update(self, data: Dict[str, Any]) -> None:
        """Update context with multiple values."""
        self.data.update(data)


@dataclass
class Workflow:
    """
    Workflow definition.

    Attributes:
        id: Unique workflow ID
        name: Workflow name
        description: Workflow description
        steps: List of workflow steps
        context: Shared workflow context
        status: Current workflow status
        parallel: Whether to execute steps in parallel
        stop_on_error: Whether to stop workflow on step failure
        created_at: Creation timestamp
        started_at: Start timestamp
        completed_at: Completion timestamp
    """

    name: str
    steps: List[WorkflowStep]
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: WorkflowContext = field(default_factory=WorkflowContext)
    status: WorkflowStatus = WorkflowStatus.PENDING
    parallel: bool = False
    stop_on_error: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "parallel": self.parallel,
            "stop_on_error": self.stop_on_error,
            "steps": [
                {
                    "name": step.name,
                    "agent": step.agent,
                    "action": step.action,
                    "status": step.status.value,
                    "result": step.result,
                    "error": step.error
                }
                for step in self.steps
            ],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "context": self.context.data
        }


class WorkflowExecutor:
    """
    Executes multi-step workflows with agent coordination.

    Features:
    - Sequential and parallel execution
    - Error handling and retries
    - Context sharing between steps
    - Conditional execution
    - Event publishing for monitoring
    """

    def __init__(self):
        """Initialize workflow executor."""
        self.logger = get_logger("workflow_executor")

        # Active workflows
        self._active_workflows: Dict[str, Workflow] = {}

        # Workflow history
        self._workflow_history: List[Workflow] = []
        self._max_history = 100

        # Registered agents
        self._agents: Dict[str, Any] = {}

        # Message bus
        self._message_bus = get_message_bus()

        # Stats
        self._stats = {
            "workflows_executed": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "total_steps_executed": 0
        }

        self.logger.info("Workflow executor initialized")

    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Register an agent for workflow execution.

        Args:
            agent_name: Name of the agent
            agent_instance: Agent instance
        """
        self._agents[agent_name] = agent_instance
        self.logger.info(f"Agent '{agent_name}' registered with workflow executor")

    async def execute_workflow(
        self,
        workflow: Workflow
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow: Workflow to execute

        Returns:
            Workflow execution result
        """
        self.logger.info(f"Starting workflow '{workflow.name}' (ID: {workflow.id})")

        # Update status
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()

        # Add to active workflows
        self._active_workflows[workflow.id] = workflow

        # Publish workflow started event
        await publish_event(
            event_type=EventType.WORKFLOW_STARTED,
            sender="workflow_executor",
            data={
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "step_count": len(workflow.steps)
            },
            priority=MessagePriority.NORMAL,
            correlation_id=workflow.id
        )

        self._stats["workflows_executed"] += 1

        try:
            # Execute workflow
            if workflow.parallel:
                await self._execute_parallel(workflow)
            else:
                await self._execute_sequential(workflow)

            # Mark as completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()

            self._stats["workflows_completed"] += 1

            # Publish completion event
            await publish_event(
                event_type=EventType.WORKFLOW_COMPLETED,
                sender="workflow_executor",
                data={
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "duration": (workflow.completed_at - workflow.started_at).total_seconds()
                },
                priority=MessagePriority.NORMAL,
                correlation_id=workflow.id
            )

            self.logger.info(
                f"Workflow '{workflow.name}' completed successfully "
                f"in {(workflow.completed_at - workflow.started_at).total_seconds():.2f}s"
            )

            return {
                "success": True,
                "workflow_id": workflow.id,
                "status": workflow.status.value,
                "context": workflow.context.data
            }

        except Exception as e:
            # Mark as failed
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()

            self._stats["workflows_failed"] += 1

            # Publish failure event
            await publish_event(
                event_type=EventType.WORKFLOW_FAILED,
                sender="workflow_executor",
                data={
                    "workflow_id": workflow.id,
                    "workflow_name": workflow.name,
                    "error": str(e)
                },
                priority=MessagePriority.HIGH,
                correlation_id=workflow.id
            )

            self.logger.error(f"Workflow '{workflow.name}' failed: {e}")

            return {
                "success": False,
                "workflow_id": workflow.id,
                "status": workflow.status.value,
                "error": str(e)
            }

        finally:
            # Move to history
            self._move_to_history(workflow)

    async def _execute_sequential(self, workflow: Workflow) -> None:
        """
        Execute workflow steps sequentially.

        Args:
            workflow: Workflow to execute
        """
        for step in workflow.steps:
            # Check if workflow was cancelled
            if workflow.status == WorkflowStatus.CANCELLED:
                break

            # Execute step
            success = await self._execute_step(workflow, step)

            # Handle failure
            if not success and workflow.stop_on_error:
                raise Exception(f"Step '{step.name}' failed: {step.error}")

    async def _execute_parallel(self, workflow: Workflow) -> None:
        """
        Execute workflow steps in parallel.

        Args:
            workflow: Workflow to execute
        """
        tasks = [
            self._execute_step(workflow, step)
            for step in workflow.steps
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for failures
        if workflow.stop_on_error:
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    step = workflow.steps[i]
                    raise Exception(f"Step '{step.name}' failed: {result}")

    async def _execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep
    ) -> bool:
        """
        Execute a single workflow step.

        Args:
            workflow: Parent workflow
            step: Step to execute

        Returns:
            True if successful, False otherwise
        """
        self.logger.debug(f"Executing step '{step.name}' in workflow '{workflow.name}'")

        # Check condition if present
        if step.condition and not step.condition(workflow.context):
            step.status = StepStatus.SKIPPED
            self.logger.debug(f"Step '{step.name}' skipped (condition not met)")
            return True

        # Update step status
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()

        # Get agent
        agent = self._agents.get(step.agent)
        if not agent:
            step.status = StepStatus.FAILED
            step.error = f"Agent '{step.agent}' not found"
            self.logger.error(step.error)
            return False

        # Execute with retries
        for attempt in range(step.retry_count):
            try:
                # Execute action
                result = await self._execute_action(agent, step, workflow.context)

                # Mark as completed
                step.status = StepStatus.COMPLETED
                step.result = result
                step.completed_at = datetime.utcnow()

                self._stats["total_steps_executed"] += 1

                # Publish step completed event
                await publish_event(
                    event_type=EventType.WORKFLOW_STEP_COMPLETED,
                    sender="workflow_executor",
                    data={
                        "workflow_id": workflow.id,
                        "step_name": step.name,
                        "agent": step.agent
                    },
                    priority=MessagePriority.LOW,
                    correlation_id=workflow.id
                )

                # Call success callback if present
                if step.on_success:
                    step.on_success(workflow.context, result)

                self.logger.debug(f"Step '{step.name}' completed successfully")

                return True

            except Exception as e:
                step.error = str(e)

                if attempt < step.retry_count - 1:
                    self.logger.warning(
                        f"Step '{step.name}' failed (attempt {attempt + 1}/{step.retry_count}): {e}"
                    )
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    # Final failure
                    step.status = StepStatus.FAILED
                    step.completed_at = datetime.utcnow()

                    # Call failure callback if present
                    if step.on_failure:
                        step.on_failure(workflow.context, e)

                    self.logger.error(
                        f"Step '{step.name}' failed after {step.retry_count} attempts: {e}"
                    )

                    return False

        return False

    async def _execute_action(
        self,
        agent: Any,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> Any:
        """
        Execute an agent action.

        Args:
            agent: Agent instance
            step: Step to execute
            context: Workflow context

        Returns:
            Action result
        """
        # Merge step params with context data
        params = {**context.data, **step.params}

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                agent.execute(params),
                timeout=step.timeout
            )

            # Update context with result if it's a dict
            if isinstance(result, dict) and "result" in result:
                context.update(result["result"])

            return result

        except asyncio.TimeoutError:
            raise Exception(f"Step timed out after {step.timeout}s")

    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if successful, False if not found
        """
        workflow = self._active_workflows.get(workflow_id)

        if not workflow:
            self.logger.warning(f"Workflow {workflow_id} not found")
            return False

        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.utcnow()

        self.logger.info(f"Workflow {workflow_id} cancelled")

        return True

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow or None if not found
        """
        # Check active workflows
        workflow = self._active_workflows.get(workflow_id)

        if workflow:
            return workflow

        # Check history
        for hist_workflow in self._workflow_history:
            if hist_workflow.id == workflow_id:
                return hist_workflow

        return None

    def get_active_workflows(self) -> List[Workflow]:
        """Get all active workflows."""
        return list(self._active_workflows.values())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get workflow executor statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self._stats,
            "active_workflows": len(self._active_workflows),
            "registered_agents": len(self._agents)
        }

    def _move_to_history(self, workflow: Workflow) -> None:
        """
        Move a workflow to history.

        Args:
            workflow: Workflow to move
        """
        # Remove from active workflows
        if workflow.id in self._active_workflows:
            del self._active_workflows[workflow.id]

        # Add to history
        self._workflow_history.append(workflow)

        # Trim history if needed
        if len(self._workflow_history) > self._max_history:
            self._workflow_history.pop(0)
