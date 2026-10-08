from caching_proxy.domain.models import CachedResponse
from caching_proxy.errors import (
    CacheError,
    CachingProxyError,
    OriginConnectionError,
    UsageError,
)


def test_cached_response_creation():
    response = CachedResponse(
        status_code=200,
        headers=[("content-type", "application/json"), ("server", "dummy")],
        body=b'{"message": "ok"}',
    )
    assert response.status_code == 200
    assert response.headers == [
        ("content-type", "application/json"),
        ("server", "dummy"),
    ]
    assert response.body == b'{"message": "ok"}'


def test_errors_hierarchy():
    assert issubclass(UsageError, CachingProxyError)
    assert issubclass(OriginConnectionError, CachingProxyError)
    assert issubclass(CacheError, CachingProxyError)

    err = OriginConnectionError("Cannot connect to origin")
    assert str(err) == "Cannot connect to origin"
