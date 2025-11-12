"""
Callback system for monitoring chain execution.
Provides hooks for execution events and metrics collection.
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from abc import ABC, abstractmethod
from src.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionEvent:
    """Represents a chain execution event."""

    def __init__(
        self,
        event_type: str,
        chain_name: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize execution event.

        Args:
            event_type: Type of event (start, end, error, step, etc.)
            chain_name: Name of chain
            timestamp: Event timestamp
            metadata: Additional metadata
        """
        self.event_type = event_type
        self.chain_name = chain_name
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Export event to dict."""
        return {
            "event_type": self.event_type,
            "chain_name": self.chain_name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BaseCallback(ABC):
    """Base class for callbacks."""

    @abstractmethod
    async def on_chain_start(
        self,
        chain_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Called when chain execution starts."""
        pass

    @abstractmethod
    async def on_chain_end(
        self,
        chain_name: str,
        output_data: Dict[str, Any],
        execution_time_seconds: float,
    ) -> None:
        """Called when chain execution completes."""
        pass

    @abstractmethod
    async def on_chain_error(
        self,
        chain_name: str,
        error: Exception,
        execution_time_seconds: float,
    ) -> None:
        """Called when chain execution fails."""
        pass

    @abstractmethod
    async def on_step_start(
        self,
        step_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Called when a step starts."""
        pass

    @abstractmethod
    async def on_step_end(
        self,
        step_name: str,
        output_data: Dict[str, Any],
    ) -> None:
        """Called when a step completes."""
        pass


class LoggingCallback(BaseCallback):
    """Callback that logs events."""

    async def on_chain_start(
        self,
        chain_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Log chain start."""
        logger.info(f"Chain started: {chain_name}")
        logger.debug(f"Input: {input_data}")

    async def on_chain_end(
        self,
        chain_name: str,
        output_data: Dict[str, Any],
        execution_time_seconds: float,
    ) -> None:
        """Log chain completion."""
        logger.info(
            f"Chain completed: {chain_name} ({execution_time_seconds:.2f}s)"
        )
        logger.debug(f"Output: {output_data}")

    async def on_chain_error(
        self,
        chain_name: str,
        error: Exception,
        execution_time_seconds: float,
    ) -> None:
        """Log chain error."""
        logger.error(
            f"Chain failed: {chain_name} ({execution_time_seconds:.2f}s) - {str(error)}"
        )

    async def on_step_start(
        self,
        step_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Log step start."""
        logger.debug(f"Step started: {step_name}")

    async def on_step_end(
        self,
        step_name: str,
        output_data: Dict[str, Any],
    ) -> None:
        """Log step completion."""
        logger.debug(f"Step completed: {step_name}")


class MetricsCallback(BaseCallback):
    """Callback that collects execution metrics."""

    def __init__(self):
        """Initialize metrics callback."""
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.event_log: List[ExecutionEvent] = []

    async def on_chain_start(
        self,
        chain_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Record chain start."""
        if chain_name not in self.metrics:
            self.metrics[chain_name] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0,
                "avg_time": 0,
                "input_sizes": [],
                "output_sizes": [],
            }

        self.event_log.append(
            ExecutionEvent(
                "chain_start",
                chain_name,
                metadata={"input_size": len(str(input_data))},
            )
        )

    async def on_chain_end(
        self,
        chain_name: str,
        output_data: Dict[str, Any],
        execution_time_seconds: float,
    ) -> None:
        """Record chain completion."""
        metrics = self.metrics[chain_name]
        metrics["executions"] += 1
        metrics["successes"] += 1
        metrics["total_time"] += execution_time_seconds
        metrics["avg_time"] = metrics["total_time"] / metrics["executions"]
        metrics["output_sizes"].append(len(str(output_data)))

        self.event_log.append(
            ExecutionEvent(
                "chain_end",
                chain_name,
                metadata={
                    "execution_time": execution_time_seconds,
                    "output_size": len(str(output_data)),
                },
            )
        )

    async def on_chain_error(
        self,
        chain_name: str,
        error: Exception,
        execution_time_seconds: float,
    ) -> None:
        """Record chain error."""
        metrics = self.metrics[chain_name]
        metrics["executions"] += 1
        metrics["failures"] += 1

        self.event_log.append(
            ExecutionEvent(
                "chain_error",
                chain_name,
                metadata={
                    "error": str(error),
                    "execution_time": execution_time_seconds,
                },
            )
        )

    async def on_step_start(
        self,
        step_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Record step start."""
        self.event_log.append(
            ExecutionEvent(
                "step_start",
                step_name,
                metadata={"input_size": len(str(input_data))},
            )
        )

    async def on_step_end(
        self,
        step_name: str,
        output_data: Dict[str, Any],
    ) -> None:
        """Record step completion."""
        self.event_log.append(
            ExecutionEvent(
                "step_end",
                step_name,
                metadata={"output_size": len(str(output_data))},
            )
        )

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get collected metrics."""
        return self.metrics

    def get_events(self) -> List[ExecutionEvent]:
        """Get event log."""
        return self.event_log

    def clear(self) -> None:
        """Clear metrics."""
        self.metrics.clear()
        self.event_log.clear()


class DebugCallback(BaseCallback):
    """Callback for detailed debugging."""

    def __init__(self, max_log_size: int = 1000):
        """Initialize debug callback.

        Args:
            max_log_size: Maximum log entries
        """
        self.max_log_size = max_log_size
        self.debug_log: List[Dict[str, Any]] = []

    async def on_chain_start(
        self,
        chain_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Log chain start with full details."""
        self._add_log({
            "level": "DEBUG",
            "event": "chain_start",
            "chain": chain_name,
            "input": input_data,
        })

    async def on_chain_end(
        self,
        chain_name: str,
        output_data: Dict[str, Any],
        execution_time_seconds: float,
    ) -> None:
        """Log chain completion with details."""
        self._add_log({
            "level": "DEBUG",
            "event": "chain_end",
            "chain": chain_name,
            "output": output_data,
            "execution_time": execution_time_seconds,
        })

    async def on_chain_error(
        self,
        chain_name: str,
        error: Exception,
        execution_time_seconds: float,
    ) -> None:
        """Log chain error with details."""
        self._add_log({
            "level": "ERROR",
            "event": "chain_error",
            "chain": chain_name,
            "error": str(error),
            "error_type": type(error).__name__,
            "execution_time": execution_time_seconds,
        })

    async def on_step_start(
        self,
        step_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Log step start."""
        self._add_log({
            "level": "DEBUG",
            "event": "step_start",
            "step": step_name,
            "input": input_data,
        })

    async def on_step_end(
        self,
        step_name: str,
        output_data: Dict[str, Any],
    ) -> None:
        """Log step completion."""
        self._add_log({
            "level": "DEBUG",
            "event": "step_end",
            "step": step_name,
            "output": output_data,
        })

    def get_log(self) -> List[Dict[str, Any]]:
        """Get debug log."""
        return self.debug_log

    def clear(self) -> None:
        """Clear debug log."""
        self.debug_log.clear()

    def _add_log(self, entry: Dict[str, Any]) -> None:
        """Add log entry."""
        entry["timestamp"] = datetime.utcnow().isoformat()
        self.debug_log.append(entry)

        if len(self.debug_log) > self.max_log_size:
            self.debug_log = self.debug_log[-self.max_log_size:]


class CallbackManager:
    """Manager for multiple callbacks."""

    def __init__(self):
        """Initialize callback manager."""
        self.callbacks: List[BaseCallback] = []

    def add_callback(self, callback: BaseCallback) -> None:
        """Add callback."""
        self.callbacks.append(callback)
        logger.debug(f"Added callback: {type(callback).__name__}")

    def remove_callback(self, callback: BaseCallback) -> None:
        """Remove callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    async def emit_chain_start(
        self,
        chain_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Emit chain start event."""
        for callback in self.callbacks:
            await callback.on_chain_start(chain_name, input_data)

    async def emit_chain_end(
        self,
        chain_name: str,
        output_data: Dict[str, Any],
        execution_time_seconds: float,
    ) -> None:
        """Emit chain end event."""
        for callback in self.callbacks:
            await callback.on_chain_end(chain_name, output_data, execution_time_seconds)

    async def emit_chain_error(
        self,
        chain_name: str,
        error: Exception,
        execution_time_seconds: float,
    ) -> None:
        """Emit chain error event."""
        for callback in self.callbacks:
            await callback.on_chain_error(chain_name, error, execution_time_seconds)

    async def emit_step_start(
        self,
        step_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Emit step start event."""
        for callback in self.callbacks:
            await callback.on_step_start(step_name, input_data)

    async def emit_step_end(
        self,
        step_name: str,
        output_data: Dict[str, Any],
    ) -> None:
        """Emit step end event."""
        for callback in self.callbacks:
            await callback.on_step_end(step_name, output_data)

    def clear(self) -> None:
        """Clear all callbacks."""
        self.callbacks.clear()
