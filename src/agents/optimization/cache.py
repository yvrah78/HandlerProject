"""
Caching system for chain execution results.
Provides in-memory and persistent caching for chain outputs.
"""
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import hashlib
import json
from src.core.logging import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """Single cache entry with metadata."""

    def __init__(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize cache entry.

        Args:
            key: Cache key
            value: Cached value
            ttl_seconds: Time to live in seconds
            metadata: Additional metadata
        """
        self.key = key
        self.value = value
        self.created_at = datetime.utcnow()
        self.accessed_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.metadata = metadata or {}

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds is None:
            return False

        age = datetime.utcnow() - self.created_at
        return age > timedelta(seconds=self.ttl_seconds)

    def touch(self) -> None:
        """Update access timestamp."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Export entry to dict."""
        return {
            "key": self.key,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata,
        }


class ChainExecutionCache:
    """
    Cache system for chain execution results.

    Features:
    - Key-value caching with TTL
    - LRU eviction
    - Cache statistics
    - Selective cache bypass
    """

    def __init__(
        self,
        max_entries: int = 10000,
        default_ttl_seconds: Optional[int] = 3600,
    ):
        """Initialize cache.

        Args:
            max_entries: Maximum cache entries
            default_ttl_seconds: Default TTL for entries
        """
        self.max_entries = max_entries
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def _make_key(self, chain_name: str, input_data: Dict[str, Any]) -> str:
        """Generate cache key from chain name and input.

        Args:
            chain_name: Chain name
            input_data: Input dictionary

        Returns:
            str: Cache key
        """
        # Create hashable representation of input
        try:
            input_str = json.dumps(input_data, sort_keys=True, default=str)
        except (TypeError, ValueError):
            input_str = str(input_data)

        combined = f"{chain_name}:{input_str}"
        key_hash = hashlib.sha256(combined.encode()).hexdigest()
        return f"cache_{key_hash}"

    def get(
        self,
        chain_name: str,
        input_data: Dict[str, Any],
    ) -> Optional[Any]:
        """Get value from cache.

        Args:
            chain_name: Chain name
            input_data: Input data

        Returns:
            Cached value or None
        """
        key = self._make_key(chain_name, input_data)
        entry = self.cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            logger.debug(f"Cache entry expired: {key}")
            return None

        entry.touch()
        self.hits += 1
        logger.debug(f"Cache hit: {key}")
        return entry.value

    def set(
        self,
        chain_name: str,
        input_data: Dict[str, Any],
        output_data: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set value in cache.

        Args:
            chain_name: Chain name
            input_data: Input data
            output_data: Output data to cache
            ttl_seconds: Override default TTL
            metadata: Cache metadata
        """
        key = self._make_key(chain_name, input_data)

        if len(self.cache) >= self.max_entries:
            self._evict_lru()

        ttl = ttl_seconds or self.default_ttl_seconds
        entry = CacheEntry(key, output_data, ttl, metadata)
        self.cache[key] = entry

        logger.debug(f"Cached result for: {chain_name}")

    def invalidate(
        self,
        chain_name: str,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Invalidate cache entries.

        Args:
            chain_name: Chain name to invalidate
            input_data: Optional specific input to invalidate

        Returns:
            int: Number of entries removed
        """
        removed = 0

        if input_data is not None:
            key = self._make_key(chain_name, input_data)
            if key in self.cache:
                del self.cache[key]
                removed = 1
        else:
            # Remove all entries for chain
            keys_to_remove = [
                k for k in self.cache.keys() if k.startswith(f"cache_{chain_name}")
            ]
            for key in keys_to_remove:
                del self.cache[key]
            removed = len(keys_to_remove)

        logger.debug(f"Invalidated {removed} cache entries for {chain_name}")
        return removed

    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            int: Number of entries removed
        """
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]

        for key in expired_keys:
            del self.cache[key]

        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache stats
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "total_entries": len(self.cache),
            "max_entries": self.max_entries,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate,
            "size_estimate_kb": self._estimate_size_kb(),
        }

    def export_stats(self) -> Dict[str, Any]:
        """Export detailed cache statistics.

        Returns:
            Dict with detailed stats
        """
        entries_info = []
        for key, entry in self.cache.items():
            if not entry.is_expired():
                entries_info.append(entry.to_dict())

        return {
            "summary": self.get_stats(),
            "entries": entries_info,
        }

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].accessed_at,
        )

        del self.cache[lru_key]
        logger.debug(f"Evicted LRU cache entry: {lru_key}")

    def _estimate_size_kb(self) -> float:
        """Estimate cache size in KB."""
        try:
            total_size = 0
            for entry in self.cache.values():
                # Rough estimate
                total_size += len(str(entry.value))
            return total_size / 1024
        except Exception:
            return 0.0


class CacheDecorator:
    """Decorator for caching chain execution results."""

    def __init__(self, cache: ChainExecutionCache):
        """Initialize decorator.

        Args:
            cache: Cache instance to use
        """
        self.cache = cache

    def cached_execution(
        self,
        ttl_seconds: Optional[int] = None,
        key_prefix: Optional[str] = None,
    ) -> Callable:
        """Decorator for cached chain execution.

        Args:
            ttl_seconds: TTL for cache entry
            key_prefix: Optional key prefix

        Returns:
            Callable: Decorated function
        """

        def decorator(func: Callable) -> Callable:
            async def wrapper(chain_name: str, input_data: Dict[str, Any], *args, **kwargs) -> Any:
                # Check cache
                cached = self.cache.get(chain_name, input_data)
                if cached is not None:
                    return cached

                # Execute function
                result = await func(chain_name, input_data, *args, **kwargs)

                # Cache result
                self.cache.set(
                    chain_name,
                    input_data,
                    result,
                    ttl_seconds=ttl_seconds,
                )

                return result

            return wrapper

        return decorator
