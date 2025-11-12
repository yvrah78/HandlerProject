"""
Tests for debugging system.
Tests callbacks, debugger, and visualization.
"""
import pytest
import asyncio

from src.agents.debugging import (
    CallbackManager,
    LoggingCallback,
    MetricsCallback,
    DebugCallback,
    ChainDebugger,
    BreakPoint,
    ExecutionSnapshot,
    PerformanceProfiler,
)


class TestExecutionEvent:
    """Tests for execution events."""

    @pytest.mark.asyncio
    async def test_logging_callback(self):
        """Test logging callback."""
        callback = LoggingCallback()

        await callback.on_chain_start("test_chain", {"input": "test"})
        await callback.on_chain_end("test_chain", {"output": "result"}, 1.5)

        # No exceptions should occur


class TestMetricsCallback:
    """Tests for metrics callback."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        """Test metrics tracking."""
        callback = MetricsCallback()

        await callback.on_chain_start("chain_1", {"input": "test"})
        await callback.on_chain_end("chain_1", {"output": "result"}, 1.0)
        await callback.on_chain_start("chain_1", {"input": "test2"})
        await callback.on_chain_end("chain_1", {"output": "result2"}, 1.5)

        metrics = callback.get_metrics()

        assert "chain_1" in metrics
        assert metrics["chain_1"]["executions"] == 2
        assert metrics["chain_1"]["successes"] == 2

    @pytest.mark.asyncio
    async def test_error_tracking(self):
        """Test error tracking."""
        callback = MetricsCallback()

        await callback.on_chain_start("chain_1", {"input": "test"})
        await callback.on_chain_error("chain_1", Exception("Test error"), 1.0)

        metrics = callback.get_metrics()

        assert metrics["chain_1"]["executions"] == 1
        assert metrics["chain_1"]["failures"] == 1

    @pytest.mark.asyncio
    async def test_event_log(self):
        """Test event logging."""
        callback = MetricsCallback()

        await callback.on_chain_start("chain_1", {"input": "test"})
        await callback.on_step_start("step_1", {"data": "test"})

        events = callback.get_events()

        assert len(events) >= 2


class TestDebugCallback:
    """Tests for debug callback."""

    @pytest.mark.asyncio
    async def test_debug_log(self):
        """Test debug logging."""
        callback = DebugCallback()

        await callback.on_chain_start("chain_1", {"input": "test"})
        await callback.on_chain_end("chain_1", {"output": "result"}, 1.0)

        log = callback.get_log()

        assert len(log) == 2
        assert log[0]["event"] == "chain_start"
        assert log[1]["event"] == "chain_end"

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test error logging."""
        callback = DebugCallback()

        await callback.on_chain_error("chain_1", ValueError("Test error"), 1.0)

        log = callback.get_log()

        assert len(log) == 1
        assert log[0]["level"] == "ERROR"
        assert "Test error" in log[0]["error"]


class TestBreakPoint:
    """Tests for breakpoints."""

    def test_breakpoint_creation(self):
        """Test breakpoint creation."""
        bp = BreakPoint("bp_1", "chain_1")

        assert bp.breakpoint_id == "bp_1"
        assert bp.chain_name == "chain_1"
        assert bp.hit_count == 0
        assert bp.enabled is True

    def test_should_break(self):
        """Test breakpoint trigger."""
        bp = BreakPoint("bp_1", "chain_1")

        should_break = bp.should_break({"input": "test"})
        assert should_break is True

    def test_conditional_breakpoint(self):
        """Test conditional breakpoint."""
        def condition(data):
            return data.get("value") > 10

        bp = BreakPoint("bp_1", "chain_1", condition=condition)

        assert bp.should_break({"value": 15}) is True
        assert bp.should_break({"value": 5}) is False

    def test_disabled_breakpoint(self):
        """Test disabled breakpoint."""
        bp = BreakPoint("bp_1", "chain_1")
        bp.enabled = False

        should_break = bp.should_break({"input": "test"})
        assert should_break is False

    def test_hit_count(self):
        """Test breakpoint hit counting."""
        bp = BreakPoint("bp_1", "chain_1")

        bp.record_hit()
        bp.record_hit()

        assert bp.hit_count == 2


class TestExecutionSnapshot:
    """Tests for execution snapshots."""

    def test_snapshot_creation(self):
        """Test snapshot creation."""
        snapshot = ExecutionSnapshot("bp_1", {"input": "test"})

        assert snapshot.breakpoint_id == "bp_1"
        assert snapshot.input_data == {"input": "test"}

    def test_add_variable(self):
        """Test adding variables to snapshot."""
        snapshot = ExecutionSnapshot("bp_1", {"input": "test"})

        snapshot.add_variable("var1", "value1")
        snapshot.add_variable("var2", 42)

        assert snapshot.local_variables["var1"] == "value1"
        assert snapshot.local_variables["var2"] == 42

    def test_snapshot_export(self):
        """Test exporting snapshot."""
        snapshot = ExecutionSnapshot("bp_1", {"input": "test"}, {"output": "result"})
        snapshot.add_variable("var1", "value1")

        exported = snapshot.to_dict()

        assert exported["breakpoint_id"] == "bp_1"
        assert exported["input_data"] == {"input": "test"}
        assert "var1" in exported["local_variables"]


class TestChainDebugger:
    """Tests for chain debugger."""

    def test_debugger_initialization(self):
        """Test debugger initialization."""
        debugger = ChainDebugger()

        assert len(debugger.breakpoints) == 0
        assert len(debugger.snapshots) == 0
        assert debugger.step_mode is False

    def test_add_breakpoint(self):
        """Test adding breakpoint."""
        debugger = ChainDebugger()

        bp = debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")

        assert bp.breakpoint_id == "bp_1"
        assert "bp_1" in debugger.breakpoints

    def test_remove_breakpoint(self):
        """Test removing breakpoint."""
        debugger = ChainDebugger()

        debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")
        removed = debugger.remove_breakpoint("bp_1")

        assert removed is True
        assert "bp_1" not in debugger.breakpoints

    def test_disable_breakpoint(self):
        """Test disabling breakpoint."""
        debugger = ChainDebugger()

        debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")
        debugger.disable_breakpoint("bp_1")

        bp = debugger.breakpoints["bp_1"]
        assert bp.enabled is False

    def test_enable_breakpoint(self):
        """Test enabling breakpoint."""
        debugger = ChainDebugger()

        debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")
        debugger.disable_breakpoint("bp_1")
        debugger.enable_breakpoint("bp_1")

        bp = debugger.breakpoints["bp_1"]
        assert bp.enabled is True

    def test_check_breakpoints(self):
        """Test checking which breakpoints trigger."""
        debugger = ChainDebugger()

        debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")

        triggered = debugger.check_breakpoints("chain_1", {"input": "test"})

        assert len(triggered) == 1
        assert triggered[0].breakpoint_id == "bp_1"

    def test_create_snapshot(self):
        """Test creating execution snapshot."""
        debugger = ChainDebugger()

        snapshot = debugger.create_snapshot("bp_1", {"input": "test"})

        assert snapshot.breakpoint_id == "bp_1"
        assert len(debugger.snapshots) == 1

    def test_step_mode(self):
        """Test step-by-step execution mode."""
        debugger = ChainDebugger()

        debugger.enable_step_mode()
        assert debugger.step_mode is True

        debugger.disable_step_mode()
        assert debugger.step_mode is False

    def test_get_breakpoints(self):
        """Test getting all breakpoints."""
        debugger = ChainDebugger()

        debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")
        debugger.add_breakpoint("chain_1", breakpoint_id="bp_2")

        bps = debugger.get_breakpoints()

        assert len(bps) == 2
        assert "bp_1" in bps

    def test_export_debug_info(self):
        """Test exporting debug information."""
        debugger = ChainDebugger()

        debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")
        debugger.create_snapshot("bp_1", {"input": "test"})

        exported = debugger.export_debug_info()

        assert "breakpoints" in exported
        assert "snapshots" in exported
        assert "execution_trace" in exported


class TestPerformanceProfiler:
    """Tests for performance profiler."""

    def test_profiler_initialization(self):
        """Test profiler initialization."""
        profiler = PerformanceProfiler()

        assert len(profiler.profiles) == 0

    def test_start_and_end_profile(self):
        """Test profiling execution."""
        import time

        profiler = PerformanceProfiler()

        profiler.start_profile("task_1")
        time.sleep(0.1)
        duration = profiler.end_profile("task_1")

        assert duration >= 0.05  # At least some time passed

    def test_profile_statistics(self):
        """Test profile statistics."""
        import time

        profiler = PerformanceProfiler()

        for _ in range(2):
            profiler.start_profile("task_1")
            time.sleep(0.05)
            profiler.end_profile("task_1")

        profiles = profiler.get_profiles()

        assert "task_1" in profiles
        assert profiles["task_1"]["call_count"] == 2

    def test_multiple_profiles(self):
        """Test multiple concurrent profiles."""
        import time

        profiler = PerformanceProfiler()

        profiler.start_profile("task_1")
        time.sleep(0.05)
        profiler.start_profile("task_2")
        time.sleep(0.05)
        profiler.end_profile("task_2")
        time.sleep(0.05)
        profiler.end_profile("task_1")

        profiles = profiler.get_profiles()

        assert "task_1" in profiles
        assert "task_2" in profiles


class TestCallbackManager:
    """Tests for callback manager."""

    @pytest.mark.asyncio
    async def test_add_callback(self):
        """Test adding callback."""
        manager = CallbackManager()
        callback = LoggingCallback()

        manager.add_callback(callback)

        assert len(manager.callbacks) == 1

    @pytest.mark.asyncio
    async def test_remove_callback(self):
        """Test removing callback."""
        manager = CallbackManager()
        callback = LoggingCallback()

        manager.add_callback(callback)
        manager.remove_callback(callback)

        assert len(manager.callbacks) == 0

    @pytest.mark.asyncio
    async def test_emit_events(self):
        """Test emitting events."""
        manager = CallbackManager()
        callback = MetricsCallback()

        manager.add_callback(callback)

        await manager.emit_chain_start("chain_1", {"input": "test"})
        await manager.emit_chain_end("chain_1", {"output": "result"}, 1.0)

        metrics = callback.get_metrics()
        assert "chain_1" in metrics

    @pytest.mark.asyncio
    async def test_multiple_callbacks(self):
        """Test multiple callbacks receiving events."""
        manager = CallbackManager()

        callback1 = MetricsCallback()
        callback2 = DebugCallback()

        manager.add_callback(callback1)
        manager.add_callback(callback2)

        await manager.emit_chain_start("chain_1", {"input": "test"})

        metrics = callback1.get_metrics()
        debug_log = callback2.get_log()

        assert "chain_1" in metrics
        assert len(debug_log) > 0


class TestDebuggingIntegration:
    """Integration tests for debugging system."""

    @pytest.mark.asyncio
    async def test_complete_debugging_workflow(self):
        """Test complete debugging workflow."""
        debugger = ChainDebugger()

        # Add breakpoint
        debugger.add_breakpoint("chain_1", breakpoint_id="bp_1")

        # Simulate execution
        callback_manager = debugger.get_callback_manager()

        await callback_manager.emit_chain_start("chain_1", {"input": "test"})
        await callback_manager.emit_chain_end("chain_1", {"output": "result"}, 1.0)

        # Check debugger state
        metrics = debugger.get_metrics()
        assert "chain_1" in metrics["chain_metrics"]

    @pytest.mark.asyncio
    async def test_profiling_with_callbacks(self):
        """Test profiling with callbacks."""
        profiler = PerformanceProfiler()
        metrics_callback = MetricsCallback()

        profiler.start_profile("chain_execution")
        await metrics_callback.on_chain_start("chain_1", {"input": "test"})
        import time
        time.sleep(0.05)
        await metrics_callback.on_chain_end("chain_1", {"output": "result"}, 0.05)
        duration = profiler.end_profile("chain_execution")

        assert duration > 0
        assert len(metrics_callback.get_metrics()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
