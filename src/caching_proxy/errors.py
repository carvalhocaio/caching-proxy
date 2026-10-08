"""Custom exception hierarchy for caching-proxy."""


class CachingProxyError(Exception):
    """Base exception for all caching-proxy errors."""


class UsageError(CachingProxyError):
    """Raised when command-line arguments are invalid."""


class OriginConnectionError(CachingProxyError):
    """Raised when proxy fails to connect to the origin server."""


class CacheError(CachingProxyError):
    """Raised when an error occurs reading or writing the cache."""
