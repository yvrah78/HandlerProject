"""
Optimization modules for Project Handler agents.
Provides caching, parallel execution, and performance optimization.
"""
from src.agents.optimization.cache import (
    ChainExecutionCache,
    CacheEntry,
    CacheDecorator,
)
from src.agents.optimization.parallel_executor import ParallelExecutor, ExecutionTask

__all__ = [
    "ChainExecutionCache",
    "CacheEntry",
    "CacheDecorator",
    "ParallelExecutor",
    "ExecutionTask",
]
