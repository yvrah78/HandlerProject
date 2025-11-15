"""
Priority Queue for task management.

Manages tasks with priorities and ensures high-priority tasks
are processed first while maintaining fairness.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import heapq
import uuid
from enum import Enum
from src.core.logging import get_logger


class TaskStatus(Enum):
    """Task status values."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(order=True)
class Task:
    """
    Task representation for priority queue.

    Uses priority and timestamp for ordering.
    Lower priority values are processed first.
    """

    # Fields used for ordering (come first)
    priority: int = field(compare=True)
    created_at_ts: float = field(compare=True)

    # Other fields (not used for ordering)
    id: str = field(default_factory=lambda: str(uuid.uuid4()), compare=False)
    task_type: str = field(default="", compare=False)
    data: Dict[str, Any] = field(default_factory=dict, compare=False)
    assigned_agent: Optional[str] = field(default=None, compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    created_at: datetime = field(default_factory=datetime.utcnow, compare=False)
    started_at: Optional[datetime] = field(default=None, compare=False)
    completed_at: Optional[datetime] = field(default=None, compare=False)
    result: Optional[Dict[str, Any]] = field(default=None, compare=False)
    error: Optional[str] = field(default=None, compare=False)
    retry_count: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)
    correlation_id: Optional[str] = field(default=None, compare=False)

    def __post_init__(self):
        """Set timestamp for ordering."""
        if not hasattr(self, 'created_at_ts') or self.created_at_ts is None:
            self.created_at_ts = self.created_at.timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "data": self.data,
            "priority": self.priority,
            "assigned_agent": self.assigned_agent,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "correlation_id": self.correlation_id
        }


class PriorityTaskQueue:
    """
    Priority queue for task management.

    Features:
    - Priority-based ordering
    - FIFO for tasks with same priority
    - Task status tracking
    - Retry mechanism
    - Task history
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize priority task queue.

        Args:
            max_history: Maximum number of completed tasks to keep in history
        """
        self.logger = get_logger("priority_queue")

        # Priority queue (heap)
        self._queue: List[Task] = []

        # Active tasks (by ID)
        self._active_tasks: Dict[str, Task] = {}

        # Completed tasks history
        self._history: List[Task] = []
        self._max_history = max_history

        # Stats
        self._stats = {
            "tasks_queued": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "total_retries": 0
        }

        self.logger.info("Priority task queue initialized")

    def add_task(
        self,
        task_type: str,
        data: Dict[str, Any],
        priority: int = 50,
        correlation_id: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Add a task to the queue.

        Args:
            task_type: Type of task
            data: Task data
            priority: Priority (0 = highest, 100 = lowest)
            correlation_id: Optional correlation ID for tracking
            max_retries: Maximum number of retries

        Returns:
            Task ID
        """
        # Create task
        task = Task(
            task_type=task_type,
            data=data,
            priority=priority,
            correlation_id=correlation_id,
            max_retries=max_retries
        )

        # Add to queue
        heapq.heappush(self._queue, task)
        self._active_tasks[task.id] = task

        self._stats["tasks_queued"] += 1

        self.logger.info(
            f"Task {task.id} added to queue "
            f"(type: {task_type}, priority: {priority})"
        )

        return task.id

    def get_next_task(self) -> Optional[Task]:
        """
        Get the next highest-priority task.

        Returns:
            Next task or None if queue is empty
        """
        while self._queue:
            task = heapq.heappop(self._queue)

            # Skip if already processed or cancelled
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                continue

            # Mark as assigned
            task.status = TaskStatus.ASSIGNED

            self.logger.debug(f"Retrieved task {task.id} from queue")

            return task

        return None

    def start_task(self, task_id: str, agent_name: str) -> bool:
        """
        Mark a task as started.

        Args:
            task_id: Task ID
            agent_name: Name of agent handling the task

        Returns:
            True if successful, False if task not found
        """
        task = self._active_tasks.get(task_id)

        if not task:
            self.logger.warning(f"Task {task_id} not found")
            return False

        task.status = TaskStatus.IN_PROGRESS
        task.assigned_agent = agent_name
        task.started_at = datetime.utcnow()

        self.logger.info(f"Task {task_id} started by agent {agent_name}")

        return True

    def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID
            result: Task result

        Returns:
            True if successful, False if task not found
        """
        task = self._active_tasks.get(task_id)

        if not task:
            self.logger.warning(f"Task {task_id} not found")
            return False

        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.utcnow()

        # Move to history
        self._move_to_history(task)

        self._stats["tasks_completed"] += 1

        self.logger.info(f"Task {task_id} completed successfully")

        return True

    def fail_task(
        self,
        task_id: str,
        error: str,
        retry: bool = True
    ) -> bool:
        """
        Mark a task as failed.

        Args:
            task_id: Task ID
            error: Error message
            retry: Whether to retry the task

        Returns:
            True if successful, False if task not found
        """
        task = self._active_tasks.get(task_id)

        if not task:
            self.logger.warning(f"Task {task_id} not found")
            return False

        task.error = error
        task.retry_count += 1
        self._stats["total_retries"] += 1

        # Check if we should retry
        if retry and task.retry_count <= task.max_retries:
            # Reset status and re-queue
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.assigned_agent = None

            # Increase priority slightly for retries
            task.priority = max(0, task.priority - 5)

            heapq.heappush(self._queue, task)

            self.logger.warning(
                f"Task {task_id} failed, retrying "
                f"(attempt {task.retry_count}/{task.max_retries})"
            )
        else:
            # Max retries reached, mark as failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()

            # Move to history
            self._move_to_history(task)

            self._stats["tasks_failed"] += 1

            self.logger.error(
                f"Task {task_id} failed permanently after "
                f"{task.retry_count} retries: {error}"
            )

        return True

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            True if successful, False if task not found
        """
        task = self._active_tasks.get(task_id)

        if not task:
            self.logger.warning(f"Task {task_id} not found")
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()

        # Move to history
        self._move_to_history(task)

        self._stats["tasks_cancelled"] += 1

        self.logger.info(f"Task {task_id} cancelled")

        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None if not found
        """
        # Check active tasks
        task = self._active_tasks.get(task_id)

        if task:
            return task

        # Check history
        for hist_task in self._history:
            if hist_task.id == task_id:
                return hist_task

        return None

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return len(self._queue)

    def get_active_tasks(self) -> List[Task]:
        """Get all active tasks."""
        return list(self._active_tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        Get tasks by status.

        Args:
            status: Task status

        Returns:
            List of tasks with the given status
        """
        return [
            task for task in self._active_tasks.values()
            if task.status == status
        ]

    def get_tasks_by_correlation_id(self, correlation_id: str) -> List[Task]:
        """
        Get tasks by correlation ID.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of tasks with the given correlation ID
        """
        tasks = [
            task for task in self._active_tasks.values()
            if task.correlation_id == correlation_id
        ]

        # Also check history
        tasks.extend([
            task for task in self._history
            if task.correlation_id == correlation_id
        ])

        return tasks

    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self._stats,
            "queue_size": len(self._queue),
            "active_tasks": len(self._active_tasks),
            "history_size": len(self._history)
        }

    def _move_to_history(self, task: Task) -> None:
        """
        Move a task to history.

        Args:
            task: Task to move
        """
        # Remove from active tasks
        if task.id in self._active_tasks:
            del self._active_tasks[task.id]

        # Add to history
        self._history.append(task)

        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def clear_history(self) -> None:
        """Clear task history."""
        self._history.clear()
        self.logger.info("Task history cleared")
