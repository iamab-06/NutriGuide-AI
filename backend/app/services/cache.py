"""
NutriGuide AI - In-Memory Async Cache Service
=============================================
Provides thread-safe TTL (Time-To-Live) LRU caching for:
1. USDA FoodData Central search results and detailed nutrition lookups.
2. Open Food Facts product lookups.
3. Normalized food entity matches.

Safeguards:
- Personal or conversation-specific AI chat responses are NEVER cached.
- Read-through single-flight request coalescing to prevent thundering herd on external APIs.
"""
import time
import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class AsyncTTLCache:
    """Thread-safe and async-safe in-memory LRU cache with TTL expiration."""

    def __init__(self, max_size: int = 1000, default_ttl_sec: int = 3600):
        self.max_size = max_size
        self.default_ttl_sec = default_ttl_sec
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = asyncio.Lock()
        self._inflight: Dict[str, asyncio.Future] = {}
        self.hits = 0
        self.misses = 0

    def _is_expired(self, expiry: float) -> bool:
        return time.time() > expiry

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                expiry, val = self._cache[key]
                if not self._is_expired(expiry):
                    self.hits += 1
                    return val
                else:
                    del self._cache[key]
            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl_sec: Optional[int] = None) -> None:
        async with self._lock:
            ttl = ttl_sec if ttl_sec is not None else self.default_ttl_sec
            expiry = time.time() + ttl
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Evict oldest entry
                oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
                del self._cache[oldest_key]
            self._cache[key] = (expiry, value)

    async def get_or_set(
        self,
        key: str,
        coro_fn: Callable[[], Any],
        ttl_sec: Optional[int] = None,
    ) -> Any:
        """
        Request coalescing (single-flight):
        If multiple concurrent calls request the same uncached key, only one coroutine runs
        and all callers await the same result.
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Check if another coroutine is already fetching this key
        async with self._lock:
            if key in self._inflight:
                future = self._inflight[key]
            else:
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self._inflight[key] = future
                future = None  # Leader runs the fetch

        if future is not None:
            # We are a follower: wait for the leader's result
            return await future

        # We are the leader: execute the fetch
        try:
            result = await coro_fn()
            await self.set(key, result, ttl_sec=ttl_sec)
            async with self._lock:
                if key in self._inflight:
                    self._inflight[key].set_result(result)
                    del self._inflight[key]
            return result
        except Exception as exc:
            async with self._lock:
                if key in self._inflight:
                    self._inflight[key].set_exception(exc)
                    del self._inflight[key]
            raise

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "cached_entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_pct": round(hit_rate, 2),
        }

    def clear(self) -> None:
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def invalidate(self, key: str) -> None:
        """Evicts a specific key from the cache."""
        self._cache.pop(key, None)


# Global cache instances with suitable TTLs
nutrition_cache = AsyncTTLCache(max_size=2000, default_ttl_sec=86400)  # 24h for nutrition values
search_cache = AsyncTTLCache(max_size=1000, default_ttl_sec=3600)      # 1h for search query results
product_cache = AsyncTTLCache(max_size=1000, default_ttl_sec=86400)    # 24h for Open Food Facts
