import threading

import httpx

from caching_proxy.domain.models import CachedResponse
from caching_proxy.infrastructure.proxy.forwarder import ProxyForwarder
from caching_proxy.infrastructure.proxy.server import CachingProxyServer


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


def test_caching_proxy_server_live_request():
    cache = FakeCacheStore()

    def origin_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            content=b'{"items": [1, 2, 3]}',
        )

    mock_client = httpx.Client(transport=httpx.MockTransport(origin_handler))
    forwarder = ProxyForwarder(
        origin="http://mock-origin.com",
        cache=cache,
        client=mock_client,
    )

    server = CachingProxyServer(("127.0.0.1", 0), forwarder=forwarder)
    port = server.server_address[1]

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}") as test_client:
            # 1. First request -> MISS
            resp1 = test_client.get("/items")
            assert resp1.status_code == 200
            assert resp1.headers["X-Cache"] == "MISS"
            assert resp1.json() == {"items": [1, 2, 3]}

            # 2. Second request -> HIT
            resp2 = test_client.get("/items")
            assert resp2.status_code == 200
            assert resp2.headers["X-Cache"] == "HIT"
            assert resp2.json() == {"items": [1, 2, 3]}
    finally:
        server.shutdown()
        server.server_close()


def test_caching_proxy_server_bad_gateway():
    cache = FakeCacheStore()

    def origin_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    mock_client = httpx.Client(transport=httpx.MockTransport(origin_handler))
    forwarder = ProxyForwarder(
        origin="http://mock-origin.com",
        cache=cache,
        client=mock_client,
    )

    server = CachingProxyServer(("127.0.0.1", 0), forwarder=forwarder)
    port = server.server_address[1]

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}") as test_client:
            resp = test_client.get("/error")
            assert resp.status_code == 502
    finally:
        server.shutdown()
        server.server_close()
