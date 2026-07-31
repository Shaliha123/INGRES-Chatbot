import abc
import time
from typing import Any, Optional
from cachetools import TTLCache

class CacheManager(abc.ABC):
    """Abstract Base Class for caching conversation data and retrieval results."""

    @abc.abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abc.abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        pass


class InMemoryCacheManager(CacheManager):
    """LRU In-Memory Cache implementation using cachetools."""

    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        # Default 1-hour TTL
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        # Note: TTLCache has a fixed global TTL per instance. For dynamic TTL, 
        # a more advanced cache or wrapper is needed. For now, we use the global TTL.
        self.cache[key] = value

    def delete(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]


# Instantiate the default cache provider
conversation_cache = InMemoryCacheManager()
