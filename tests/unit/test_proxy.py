import httpx
import pytest

from caching_proxy.domain.models import CachedResponse
from caching_proxy.errors import OriginConnectionError
from caching_proxy.infrastructure.proxy.forwarder import ProxyForwarder


class FakeCacheStore:
    def __init__(self):
        self.store = {}

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, response: CachedResponse):
        self.store[key] = response

    def clear(self):
        count = len(self.store)
        self.store.clear()
        return count


def test_proxy_forwarder_cache_miss():
    cache = FakeCacheStore()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://dummyjson.com/products"
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"products": []}',
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    forwarder = ProxyForwarder(
        origin="http://dummyjson.com",
        cache=cache,
        client=client,
    )

    response = forwarder.handle_request(
        method="GET",
        path="/products",
        headers={"accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.body == b'{"products": []}'
    assert response.cache_status == "MISS"
    assert ("X-Cache", "MISS") in response.headers

    # Verify response was cached
    cached = cache.get("GET:/products")
    assert cached is not None
    assert cached.status_code == 200
    assert cached.body == b'{"products": []}'


def test_proxy_forwarder_cache_hit():
    cache = FakeCacheStore()
    cache.set(
        "GET:/products",
        CachedResponse(
            status_code=200,
            headers=[("content-type", "application/json")],
            body=b'{"products": ["cached"]}',
        ),
    )

    forwarder = ProxyForwarder(
        origin="http://dummyjson.com",
        cache=cache,
        client=httpx.Client(),  # No requests should be made
    )

    response = forwarder.handle_request(
        method="GET",
        path="/products",
        headers={},
    )

    assert response.status_code == 200
    assert response.body == b'{"products": ["cached"]}'
    assert response.cache_status == "HIT"
    assert ("X-Cache", "HIT") in response.headers


def test_proxy_forwarder_post_not_cached():
    cache = FakeCacheStore()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(201, content=b'{"created": true}')

    client = httpx.Client(transport=httpx.MockTransport(handler))
    forwarder = ProxyForwarder(
        origin="http://dummyjson.com",
        cache=cache,
        client=client,
    )

    response = forwarder.handle_request(
        method="POST",
        path="/products/add",
        headers={},
        body=b'{"title": "test"}',
    )

    assert response.status_code == 201
    assert response.cache_status == "MISS"
    assert ("X-Cache", "MISS") in response.headers
    assert cache.get("POST:/products/add") is None


def test_proxy_forwarder_connection_error():
    cache = FakeCacheStore()

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Failed to connect to origin")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    forwarder = ProxyForwarder(
        origin="http://dummyjson.com",
        cache=cache,
        client=client,
    )

    with pytest.raises(OriginConnectionError, match="Failed to connect to origin"):
        forwarder.handle_request(method="GET", path="/error", headers={})
