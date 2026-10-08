"""Domain ports and interfaces for cache storage."""

from typing import Protocol

from caching_proxy.domain.models import CachedResponse


class CacheStore(Protocol):
    """Protocol for cache storage backends."""

    def get(self, key: str) -> CachedResponse | None: ...

    def set(self, key: str, response: CachedResponse) -> None: ...

    def clear(self) -> int: ...
