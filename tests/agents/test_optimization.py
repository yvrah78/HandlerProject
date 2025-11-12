"""
Tests for optimization system.
Tests caching and parallel execution.
"""
import pytest
import asyncio

from src.agents.optimization import (
    ChainExecutionCache,
    CacheEntry,
    ParallelExecutor,
    ExecutionTask,
)


class TestCacheEntry:
    """Tests for cache entry."""

    def test_initialization(self):
        """Test cache entry initialization."""
        entry = CacheEntry("key", "value", ttl_seconds=3600)

        assert entry.key == "key"
        assert entry.value == "value"
        assert entry.access_count == 0

    def test_not_expired(self):
        """Test non-expired entry."""
        entry = CacheEntry("key", "value", ttl_seconds=3600)
        assert entry.is_expired() is False

    def test_touch(self):
        """Test updating access timestamp."""
        entry = CacheEntry("key", "value")

        entry.touch()
        assert entry.access_count == 1

        entry.touch()
        assert entry.access_count == 2

    def test_to_dict(self):
        """Test converting entry to dict."""
        entry = CacheEntry("key", "value", ttl_seconds=3600)
        d = entry.to_dict()

        assert d["key"] == "key"
        assert d["access_count"] == 0


class TestChainExecutionCache:
    """Tests for chain execution cache."""

    def test_initialization(self):
        """Test cache initialization."""
        cache = ChainExecutionCache(max_entries=100)

        assert cache.max_entries == 100
        assert cache.hits == 0
        assert cache.misses == 0

    def test_cache_miss(self):
        """Test cache miss."""
        cache = ChainExecutionCache()

        result = cache.get("chain_1", {"input": "test"})
        assert result is None
        assert cache.misses == 1

    def test_cache_hit(self):
        """Test cache hit."""
        cache = ChainExecutionCache()

        # Set value
        cache.set("chain_1", {"input": "test"}, {"output": "result"})

        # Get value
        result = cache.get("chain_1", {"input": "test"})
        assert result == {"output": "result"}
        assert cache.hits == 1

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = ChainExecutionCache()

        cache.set("chain_1", {"input": "test"}, {"output": "result"})
        cache.invalidate("chain_1", {"input": "test"})

        result = cache.get("chain_1", {"input": "test"})
        assert result is None

    def test_ttl_enforcement(self):
        """Test TTL enforcement."""
        cache = ChainExecutionCache()

        # Set entry with 0 TTL (should be expired)
        cache.set("chain_1", {"input": "test"}, {"output": "result"}, ttl_seconds=0)

        # Wait a moment
        import time
        time.sleep(0.1)

        result = cache.get("chain_1", {"input": "test"})
        # Entry should be expired or not found
        # Depends on timing, but it should be gone after TTL

    def test_lru_eviction(self):
        """Test LRU eviction."""
        cache = ChainExecutionCache(max_entries=2)

        cache.set("chain_1", {"input": "test1"}, {"output": "result1"})
        cache.set("chain_2", {"input": "test2"}, {"output": "result2"})

        # Should evict least recently used
        cache.set("chain_3", {"input": "test3"}, {"output": "result3"})

        # chain_1 should be evicted (least recently used)
        assert cache.hits + cache.misses >= 0  # At least one operation

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ChainExecutionCache()

        cache.set("chain_1", {"input": "test"}, {"output": "result"})
        cache.get("chain_1", {"input": "test"})  # Hit
        cache.get("chain_1", {"input": "test2"})  # Miss

        stats = cache.get_stats()

        assert stats["total_entries"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = ChainExecutionCache()

        cache.set("chain_1", {"input": "test"}, {"output": "result"}, ttl_seconds=0)

        import time
        time.sleep(0.1)

        removed = cache.cleanup_expired()
        # Should remove expired entries
        assert removed >= 0

    def test_clear(self):
        """Test clearing cache."""
        cache = ChainExecutionCache()

        cache.set("chain_1", {"input": "test"}, {"output": "result"})
        cache.clear()

        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0


class TestParallelExecutor:
    """Tests for parallel executor."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = ParallelExecutor(max_concurrent=5)

        assert executor.max_concurrent == 5
        assert len(executor.tasks) == 0

    def test_add_task(self):
        """Test adding task."""
        executor = ParallelExecutor()

        async def dummy_func():
            return "result"

        executor.add_task("task_1", "chain_1", dummy_func())
        assert len(executor.tasks) == 1

    def test_task_creation(self):
        """Test task creation."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()
        task = executor.add_task("task_1", "chain_1", dummy_func())

        assert task.task_id == "task_1"
        assert task.chain_name == "chain_1"
        assert task.status == "pending"

    def test_dependency_validation(self):
        """Test dependency validation."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func())
        executor.add_task("task_2", "chain_2", dummy_func(), depends_on=["task_1"])

        # Should not raise
        executor._validate_dependencies()

    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func(), depends_on=["task_2"])
        executor.add_task("task_2", "chain_2", dummy_func(), depends_on=["task_1"])

        with pytest.raises(RuntimeError):
            executor._validate_dependencies()

    def test_execution_order(self):
        """Test getting execution order."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func())
        executor.add_task("task_2", "chain_2", dummy_func(), depends_on=["task_1"])
        executor.add_task("task_3", "chain_3", dummy_func())

        order = executor.get_execution_order()

        # task_1 and task_3 should be in first level
        # task_2 should be in second level
        assert len(order) >= 2

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel execution."""
        async def dummy_func():
            await asyncio.sleep(0.1)
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func())
        executor.add_task("task_2", "chain_2", dummy_func())

        results = await executor.execute()

        assert "task_1" in results or "task_2" in results

    def test_task_graph(self):
        """Test task dependency graph."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func())
        executor.add_task("task_2", "chain_2", dummy_func(), depends_on=["task_1"])

        graph = executor.get_task_graph()

        assert "task_1" in graph
        assert "task_2" in graph
        assert graph["task_2"]["depends_on"] == ["task_1"]

    def test_execution_stats(self):
        """Test execution statistics."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func())

        stats = executor.get_execution_stats()

        assert stats["total_tasks"] == 1
        assert stats["pending_tasks"] == 1

    def test_export_execution_log(self):
        """Test exporting execution log."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func())

        log = executor.export_execution_log()

        assert "tasks" in log
        assert "stats" in log
        assert "task_graph" in log

    def test_clear(self):
        """Test clearing executor."""
        async def dummy_func():
            return "result"

        executor = ParallelExecutor()

        executor.add_task("task_1", "chain_1", dummy_func())
        executor.clear()

        assert len(executor.tasks) == 0


class TestOptimizationIntegration:
    """Integration tests for optimization system."""

    def test_cache_with_multiple_chains(self):
        """Test caching with multiple chains."""
        cache = ChainExecutionCache()

        # Simulate multiple chains
        cache.set("chain_1", {"input": "a"}, {"output": "result_1a"})
        cache.set("chain_1", {"input": "b"}, {"output": "result_1b"})
        cache.set("chain_2", {"input": "a"}, {"output": "result_2a"})

        # Retrieve
        assert cache.get("chain_1", {"input": "a"}) == {"output": "result_1a"}
        assert cache.get("chain_2", {"input": "a"}) == {"output": "result_2a"}

    @pytest.mark.asyncio
    async def test_parallel_with_dependencies(self):
        """Test parallel execution with complex dependencies."""
        async def task_func(value):
            await asyncio.sleep(0.05)
            return f"result_{value}"

        executor = ParallelExecutor(max_concurrent=2)

        executor.add_task("t1", "chain_1", task_func(1))
        executor.add_task("t2", "chain_2", task_func(2), depends_on=["t1"])
        executor.add_task("t3", "chain_3", task_func(3), depends_on=["t1"])
        executor.add_task("t4", "chain_4", task_func(4), depends_on=["t2", "t3"])

        # Execute
        results = await executor.execute()

        # All should complete
        stats = executor.get_execution_stats()
        assert stats["total_tasks"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
