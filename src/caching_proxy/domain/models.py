"""Domain models for caching proxy."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CachedResponse:
    """Represents a cached HTTP response."""

    status_code: int
    headers: list[tuple[str, str]]
    body: bytes
