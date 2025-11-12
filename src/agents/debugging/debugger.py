"""
Chain debugger for troubleshooting and execution analysis.
Provides tools for step-by-step debugging and execution introspection.
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from src.agents.debugging.callbacks import (
    MetricsCallback,
    DebugCallback,
    CallbackManager,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


class BreakPoint:
    """Represents a breakpoint in chain execution."""

    def __init__(
        self,
        breakpoint_id: str,
        chain_name: str,
        step_index: Optional[int] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        """Initialize breakpoint.

        Args:
            breakpoint_id: Unique breakpoint ID
            chain_name: Chain name
            step_index: Optional step index
            condition: Optional condition function
        """
        self.breakpoint_id = breakpoint_id
        self.chain_name = chain_name
        self.step_index = step_index
        self.condition = condition
        self.hit_count = 0
        self.enabled = True

    def should_break(self, data: Dict[str, Any]) -> bool:
        """Check if breakpoint should trigger."""
        if not self.enabled:
            return False

        if self.condition:
            return self.condition(data)

        return True

    def record_hit(self) -> None:
        """Record breakpoint hit."""
        self.hit_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Export breakpoint info."""
        return {
            "breakpoint_id": self.breakpoint_id,
            "chain_name": self.chain_name,
            "step_index": self.step_index,
            "hit_count": self.hit_count,
            "enabled": self.enabled,
        }


class ExecutionSnapshot:
    """Snapshot of execution state at a breakpoint."""

    def __init__(
        self,
        breakpoint_id: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
    ):
        """Initialize snapshot.

        Args:
            breakpoint_id: Breakpoint ID that triggered snapshot
            input_data: Input data at breakpoint
            output_data: Optional output data
        """
        self.breakpoint_id = breakpoint_id
        self.timestamp = datetime.utcnow()
        self.input_data = input_data
        self.output_data = output_data
        self.local_variables: Dict[str, Any] = {}

    def add_variable(self, name: str, value: Any) -> None:
        """Add local variable to snapshot."""
        self.local_variables[name] = value

    def to_dict(self) -> Dict[str, Any]:
        """Export snapshot."""
        return {
            "breakpoint_id": self.breakpoint_id,
            "timestamp": self.timestamp.isoformat(),
            "input_data": self.input_data,
            "output_data": self.output_data,
            "local_variables": self.local_variables,
        }


class ChainDebugger:
    """
    Debugger for chain execution.

    Features:
    - Breakpoints with conditions
    - Execution snapshots
    - Step-by-step execution
    - Variable inspection
    - Performance profiling
    """

    def __init__(self):
        """Initialize debugger."""
        self.breakpoints: Dict[str, BreakPoint] = {}
        self.snapshots: List[ExecutionSnapshot] = []
        self.metrics_callback = MetricsCallback()
        self.debug_callback = DebugCallback()
        self.callback_manager = CallbackManager()

        # Add callbacks
        self.callback_manager.add_callback(self.metrics_callback)
        self.callback_manager.add_callback(self.debug_callback)

        self.step_mode = False
        self.stopped = False

    def add_breakpoint(
        self,
        chain_name: str,
        breakpoint_id: Optional[str] = None,
        step_index: Optional[int] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> BreakPoint:
        """Add breakpoint.

        Args:
            chain_name: Chain name
            breakpoint_id: Optional breakpoint ID
            step_index: Optional step index
            condition: Optional condition function

        Returns:
            BreakPoint: Created breakpoint
        """
        bp_id = breakpoint_id or f"bp_{len(self.breakpoints)}"
        breakpoint = BreakPoint(bp_id, chain_name, step_index, condition)
        self.breakpoints[bp_id] = breakpoint

        logger.debug(f"Added breakpoint: {bp_id} on {chain_name}")
        return breakpoint

    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """Remove breakpoint.

        Args:
            breakpoint_id: Breakpoint ID

        Returns:
            bool: Success
        """
        if breakpoint_id in self.breakpoints:
            del self.breakpoints[breakpoint_id]
            logger.debug(f"Removed breakpoint: {breakpoint_id}")
            return True
        return False

    def disable_breakpoint(self, breakpoint_id: str) -> bool:
        """Disable breakpoint without removing it.

        Args:
            breakpoint_id: Breakpoint ID

        Returns:
            bool: Success
        """
        if breakpoint_id in self.breakpoints:
            self.breakpoints[breakpoint_id].enabled = False
            return True
        return False

    def enable_breakpoint(self, breakpoint_id: str) -> bool:
        """Enable breakpoint.

        Args:
            breakpoint_id: Breakpoint ID

        Returns:
            bool: Success
        """
        if breakpoint_id in self.breakpoints:
            self.breakpoints[breakpoint_id].enabled = True
            return True
        return False

    def check_breakpoints(
        self,
        chain_name: str,
        data: Dict[str, Any],
    ) -> List[BreakPoint]:
        """Check which breakpoints should trigger.

        Args:
            chain_name: Chain name
            data: Execution data

        Returns:
            List of triggered breakpoints
        """
        triggered = []

        for bp in self.breakpoints.values():
            if bp.chain_name == chain_name and bp.should_break(data):
                bp.record_hit()
                triggered.append(bp)

        return triggered

    def create_snapshot(
        self,
        breakpoint_id: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
    ) -> ExecutionSnapshot:
        """Create execution snapshot.

        Args:
            breakpoint_id: Breakpoint ID
            input_data: Input data
            output_data: Optional output data

        Returns:
            ExecutionSnapshot: Created snapshot
        """
        snapshot = ExecutionSnapshot(breakpoint_id, input_data, output_data)
        self.snapshots.append(snapshot)

        logger.debug(f"Created snapshot for breakpoint: {breakpoint_id}")
        return snapshot

    def enable_step_mode(self) -> None:
        """Enable step-by-step execution mode."""
        self.step_mode = True
        logger.info("Step mode enabled")

    def disable_step_mode(self) -> None:
        """Disable step mode."""
        self.step_mode = False
        self.stopped = False
        logger.info("Step mode disabled")

    def step_continue(self) -> None:
        """Continue to next breakpoint."""
        self.stopped = False

    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics.

        Returns:
            Dict with metrics
        """
        return {
            "chain_metrics": self.metrics_callback.get_metrics(),
            "breakpoint_count": len(self.breakpoints),
            "snapshot_count": len(self.snapshots),
        }

    def get_breakpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get all breakpoints.

        Returns:
            Dict of breakpoint info
        """
        return {bp_id: bp.to_dict() for bp_id, bp in self.breakpoints.items()}

    def get_snapshots(self) -> List[Dict[str, Any]]:
        """Get all snapshots.

        Returns:
            List of snapshot info
        """
        return [snapshot.to_dict() for snapshot in self.snapshots]

    def get_execution_trace(self) -> List[Dict[str, Any]]:
        """Get execution trace from debug callback.

        Returns:
            List of trace entries
        """
        trace = []
        for entry in self.debug_callback.get_log():
            trace.append(entry)
        return trace

    def export_debug_info(self) -> Dict[str, Any]:
        """Export complete debug information.

        Returns:
            Dict with all debug data
        """
        return {
            "breakpoints": self.get_breakpoints(),
            "snapshots": self.get_snapshots(),
            "execution_trace": self.get_execution_trace(),
            "metrics": self.get_metrics(),
        }

    def clear(self) -> None:
        """Clear debugger state."""
        self.breakpoints.clear()
        self.snapshots.clear()
        self.metrics_callback.clear()
        self.debug_callback.clear()
        self.step_mode = False
        self.stopped = False
        logger.info("Cleared debugger")

    def get_callback_manager(self) -> CallbackManager:
        """Get callback manager for integration with chains.

        Returns:
            CallbackManager: Manager instance
        """
        return self.callback_manager


class PerformanceProfiler:
    """Profiles chain execution performance."""

    def __init__(self):
        """Initialize profiler."""
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.call_stack: List[tuple] = []

    def start_profile(self, name: str) -> None:
        """Start profiling a function/chain.

        Args:
            name: Profile name
        """
        self.call_stack.append((name, datetime.utcnow()))

    def end_profile(self, name: str) -> float:
        """End profiling and return duration.

        Args:
            name: Profile name

        Returns:
            float: Execution time in seconds
        """
        if not self.call_stack or self.call_stack[-1][0] != name:
            logger.warning(f"End profile called without matching start: {name}")
            return 0.0

        start_name, start_time = self.call_stack.pop()
        duration = (datetime.utcnow() - start_time).total_seconds()

        if name not in self.profiles:
            self.profiles[name] = {
                "call_count": 0,
                "total_time": 0,
                "min_time": float("inf"),
                "max_time": 0,
                "calls": [],
            }

        profile = self.profiles[name]
        profile["call_count"] += 1
        profile["total_time"] += duration
        profile["min_time"] = min(profile["min_time"], duration)
        profile["max_time"] = max(profile["max_time"], duration)
        profile["calls"].append({
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return duration

    def get_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get profile statistics.

        Returns:
            Dict with profile stats
        """
        result = {}
        for name, profile in self.profiles.items():
            result[name] = {
                "call_count": profile["call_count"],
                "total_time": profile["total_time"],
                "avg_time": profile["total_time"] / profile["call_count"]
                if profile["call_count"] > 0
                else 0,
                "min_time": profile["min_time"],
                "max_time": profile["max_time"],
            }
        return result

    def clear(self) -> None:
        """Clear profiles."""
        self.profiles.clear()
        self.call_stack.clear()
