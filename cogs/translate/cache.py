"""
Translation cache module for the Translation cog.

Provides in-memory caching with TTL (time-to-live) to reduce API calls and
improve response latency. Uses an LRU (Least Recently Used) eviction policy
to prevent unbounded memory growth in large servers.

No Discord imports allowed - this module is pure data structure logic.
"""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    A single cached translation entry.

    Attributes:
        translated_text: The translated text
        source_language: Source language code that was detected/used
        target_language: Target language code requested
        timestamp: Unix timestamp when entry was cached
        ttl: Time-to-live in seconds (0 = no expiration)
    """

    translated_text: str
    source_language: str
    target_language: str
    timestamp: float
    ttl: int

    def is_expired(self) -> bool:
        """
        Check if this cache entry has expired.

        Returns:
            True if TTL has elapsed, False otherwise.
        """
        if self.ttl <= 0:
            return False
        elapsed = time.time() - self.timestamp
        return elapsed > self.ttl


class TranslationCache:
    """
    In-memory translation cache with LRU eviction and TTL support.

    This cache stores translations to avoid redundant API calls. It uses:
    - **LRU eviction**: When max_size is reached, least-recently-used items are evicted
    - **TTL (time-to-live)**: Entries can expire after a set duration
    - **Content hashing**: Uses SHA256 of input text as cache key for efficiency

    Thread-safe for concurrent access via asyncio locks.

    Attributes:
        max_size: Maximum number of entries before LRU eviction
        default_ttl: Default TTL in seconds (0 = no expiration)
    """

    def __init__(self, max_size: int = 5000, default_ttl: int = 604800):
        """
        Initialize the translation cache.

        Args:
            max_size: Maximum number of cached translations. Defaults to 5000.
                      When exceeded, least-recently-used entries are removed.
            default_ttl: Default time-to-live in seconds for entries.
                        Defaults to 604800 (7 days). Use 0 for no expiration.
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

        # Statistics tracking
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    @staticmethod
    def _make_key(text: str, target_language: str) -> str:
        """
        Generate a cache key from text and target language.

        Uses SHA256 hashing to ensure deterministic, collision-resistant keys.
        This avoids storing large text as dictionary keys.

        Args:
            text: Original text
            target_language: Target language code

        Returns:
            Cache key in format: "{target_lang}:{sha256_hash}"

        Examples:
            >>> key = TranslationCache._make_key("Hello world", "es")
            >>> print(key)
            'es:6b6b4b6c3d4e5f6g...'
        """
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{target_language}:{text_hash}"

    async def get(self, text: str, target_language: str) -> Optional[CacheEntry]:
        """
        Retrieve a cached translation.

        Marks the entry as recently-used for LRU purposes. If entry has expired,
        removes it and returns None.

        Args:
            text: Original text that was translated
            target_language: Target language code

        Returns:
            CacheEntry if found and not expired, None otherwise.

        Examples:
            >>> cached = await cache.get("Hola", "english")
            >>> if cached:
            ...     print(cached.translated_text)
            ...     'Hello'
        """
        async with self._lock:
            key = self._make_key(text, target_language)

            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                logger.debug(f"Cache entry expired: {key}")
                del self._cache[key]
                self._misses += 1
                return None

            # Mark as recently used (move to end in OrderedDict)
            self._cache.move_to_end(key)
            self._hits += 1
            logger.debug(f"Cache hit: {key}")
            return entry

    async def set(
        self,
        text: str,
        target_language: str,
        translated_text: str,
        source_language: str = "auto",
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store a translation in the cache.

        If cache is at max capacity, evicts the least-recently-used entry.

        Args:
            text: Original text
            target_language: Target language code
            translated_text: The translated result
            source_language: Source language detected/used. Defaults to "auto".
            ttl: Time-to-live in seconds, or None to use default.

        Examples:
            >>> await cache.set("Hola", "english", "Hello", source_language="es")
        """
        async with self._lock:
            key = self._make_key(text, target_language)
            ttl_value = ttl if ttl is not None else self.default_ttl

            # Evict LRU entry if at capacity
            if len(self._cache) >= self.max_size:
                evicted_key = next(iter(self._cache))
                del self._cache[evicted_key]
                self._evictions += 1
                logger.debug(f"Cache eviction: {evicted_key}")

            entry = CacheEntry(
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                timestamp=time.time(),
                ttl=ttl_value,
            )
            self._cache[key] = entry
            logger.debug(f"Cache set: {key}")

    async def clear(self) -> None:
        """
        Clear all entries from the cache.

        Useful for cleanup on cog unload or memory pressure situations.
        """
        async with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Call periodically to free up memory.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            before = len(self._cache)
            self._cache = OrderedDict(
                (k, v) for k, v in self._cache.items() if not v.is_expired()
            )
            after = len(self._cache)
            removed = before - after
            if removed > 0:
                logger.debug(f"Cache cleanup: removed {removed} expired entries")
            return removed

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hit/miss statistics and size info.
            Example:
                {
                    'size': 234,
                    'max_size': 5000,
                    'hits': 1200,
                    'misses': 450,
                    'hit_rate': 0.73,
                    'evictions': 5
                }
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics (hits, misses, evictions)."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0
