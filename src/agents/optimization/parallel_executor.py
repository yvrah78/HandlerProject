"""
Parallel execution system for chains.
Enables concurrent chain execution with dependency management.
"""
from typing import Dict, Any, List, Optional, Set, Callable, Coroutine
import asyncio
from datetime import datetime
from src.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionTask:
    """Represents a task in the execution graph."""

    def __init__(
        self,
        task_id: str,
        chain_name: str,
        execute_func: Coroutine,
        depends_on: Optional[List[str]] = None,
    ):
        """Initialize execution task.

        Args:
            task_id: Unique task ID
            chain_name: Name of chain to execute
            execute_func: Async execution function
            depends_on: List of task IDs this depends on
        """
        self.task_id = task_id
        self.chain_name = chain_name
        self.execute_func = execute_func
        self.depends_on = depends_on or []
        self.status = "pending"  # pending, running, completed, failed
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None

    def get_execution_time(self) -> Optional[float]:
        """Get execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Export task to dict."""
        return {
            "task_id": self.task_id,
            "chain_name": self.chain_name,
            "status": self.status,
            "depends_on": self.depends_on,
            "execution_time_seconds": self.get_execution_time(),
            "error": str(self.error) if self.error else None,
        }


class ParallelExecutor:
    """
    Executor for parallel chain execution.

    Features:
    - Task dependency management
    - Concurrent execution
    - Error handling and recovery
    - Execution monitoring
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout_seconds: Optional[int] = None,
    ):
        """Initialize parallel executor.

        Args:
            max_concurrent: Maximum concurrent tasks
            timeout_seconds: Timeout for entire execution
        """
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.tasks: Dict[str, ExecutionTask] = {}
        self.execution_results: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def add_task(
        self,
        task_id: str,
        chain_name: str,
        execute_func: Coroutine,
        depends_on: Optional[List[str]] = None,
    ) -> ExecutionTask:
        """Add task to execution plan.

        Args:
            task_id: Unique task ID
            chain_name: Chain name
            execute_func: Async function to execute
            depends_on: List of task IDs to wait for

        Returns:
            ExecutionTask: The created task
        """
        task = ExecutionTask(task_id, chain_name, execute_func, depends_on)
        self.tasks[task_id] = task
        logger.debug(f"Added task: {task_id} ({chain_name})")
        return task

    async def execute(self) -> Dict[str, Any]:
        """Execute all tasks respecting dependencies.

        Returns:
            Dict mapping task_id to results

        Raises:
            RuntimeError: If circular dependency detected
            asyncio.TimeoutError: If execution exceeds timeout
        """
        # Validate task graph
        self._validate_dependencies()

        # Execute with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_task(task_id: str) -> None:
            task = self.tasks[task_id]

            # Wait for dependencies
            await self._wait_for_dependencies(task_id)

            # Run task with semaphore
            async with semaphore:
                await self._execute_task(task)

        # Create tasks
        execution_tasks = [
            run_task(task_id)
            for task_id in self.tasks.keys()
        ]

        # Execute with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*execution_tasks, return_exceptions=True),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.error("Parallel execution timed out")
            raise

        # Collect results
        self.execution_results = {
            task_id: task.result
            for task_id, task in self.tasks.items()
            if task.status == "completed"
        }

        return self.execution_results

    async def _execute_task(self, task: ExecutionTask) -> None:
        """Execute a single task.

        Args:
            task: Task to execute
        """
        try:
            task.status = "running"
            task.started_at = datetime.utcnow()

            logger.debug(f"Executing task: {task.task_id}")

            # Execute the coroutine
            result = await task.execute_func

            task.result = result
            task.status = "completed"
            task.completed_at = datetime.utcnow()

            logger.debug(f"Task completed: {task.task_id}")

        except Exception as e:
            task.error = e
            task.status = "failed"
            task.completed_at = datetime.utcnow()

            logger.error(f"Task failed: {task.task_id} - {str(e)}")

    async def _wait_for_dependencies(self, task_id: str) -> None:
        """Wait for task dependencies to complete.

        Args:
            task_id: Task ID to wait for
        """
        task = self.tasks[task_id]

        for dep_id in task.depends_on:
            dep_task = self.tasks.get(dep_id)
            if not dep_task:
                raise RuntimeError(f"Dependency not found: {dep_id}")

            # Wait for dependency completion
            max_wait = 3600  # 1 hour max
            elapsed = 0
            while dep_task.status != "completed" and elapsed < max_wait:
                if dep_task.status == "failed":
                    raise RuntimeError(
                        f"Dependency failed: {dep_id} - {str(dep_task.error)}"
                    )
                await asyncio.sleep(0.1)
                elapsed += 0.1

    def _validate_dependencies(self) -> None:
        """Validate task dependency graph.

        Raises:
            RuntimeError: If circular dependency detected
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            task = self.tasks.get(task_id)
            if not task:
                return False

            for dep_id in task.depends_on:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    raise RuntimeError("Circular dependency detected in task graph")

    def get_execution_order(self) -> List[List[str]]:
        """Get execution order (levels of concurrency).

        Returns:
            List of task ID lists, each list is a concurrency level
        """
        levels: List[Set[str]] = []
        completed: Set[str] = set()

        while len(completed) < len(self.tasks):
            current_level = set()

            for task_id, task in self.tasks.items():
                if task_id not in completed:
                    # Can execute if all dependencies completed
                    if all(dep_id in completed for dep_id in task.depends_on):
                        current_level.add(task_id)

            if not current_level:
                break

            levels.append(current_level)
            completed.update(current_level)

        return [list(level) for level in levels]

    def get_task_graph(self) -> Dict[str, Dict[str, Any]]:
        """Get task dependency graph.

        Returns:
            Dict with task information and dependencies
        """
        return {
            task_id: {
                "chain_name": task.chain_name,
                "depends_on": task.depends_on,
                "status": task.status,
            }
            for task_id, task in self.tasks.items()
        }

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics.

        Returns:
            Dict with execution stats
        """
        completed_tasks = [
            t for t in self.tasks.values() if t.status == "completed"
        ]
        failed_tasks = [t for t in self.tasks.values() if t.status == "failed"]

        execution_times = [
            t.get_execution_time()
            for t in completed_tasks
            if t.get_execution_time()
        ]

        return {
            "total_tasks": len(self.tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "pending_tasks": len(
                [t for t in self.tasks.values() if t.status == "pending"]
            ),
            "total_execution_time_seconds": sum(execution_times or [0]),
            "avg_task_time_seconds": (
                sum(execution_times) / len(execution_times)
                if execution_times
                else 0
            ),
            "concurrency_levels": len(self.get_execution_order()),
        }

    def export_execution_log(self) -> Dict[str, Any]:
        """Export execution log.

        Returns:
            Dict with complete execution information
        """
        return {
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "stats": self.get_execution_stats(),
            "task_graph": self.get_task_graph(),
            "execution_order": self.get_execution_order(),
        }

    def clear(self) -> None:
        """Clear execution state."""
        self.tasks.clear()
        self.execution_results.clear()
        logger.info("Cleared parallel executor")
