"""Proxy forwarder that handles origin requests and cache lookup."""

from dataclasses import dataclass

import httpx

from caching_proxy.domain.models import CachedResponse
from caching_proxy.domain.ports import CacheStore
from caching_proxy.errors import OriginConnectionError

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
}


@dataclass(frozen=True, slots=True)
class ProxyResponse:
    """Response returned by ProxyForwarder."""

    status_code: int
    headers: list[tuple[str, str]]
    body: bytes
    cache_status: str


class ProxyForwarder:
    """Forwards incoming HTTP requests to the origin server with caching."""

    def __init__(
        self,
        origin: str,
        cache: CacheStore,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.origin = origin.rstrip("/")
        self.cache = cache
        self.client = client or httpx.Client(timeout=timeout)

    def handle_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> ProxyResponse:
        """Handle request, returning cached or forwarded response."""
        key = f"{method}:{path}"
        is_cacheable = method.upper() == "GET"

        if is_cacheable:
            cached = self.cache.get(key)
            if cached is not None:
                resp_headers = [
                    (k, v)
                    for k, v in cached.headers
                    if k.lower() not in HOP_BY_HOP_HEADERS
                ]
                resp_headers.append(("X-Cache", "HIT"))
                return ProxyResponse(
                    status_code=cached.status_code,
                    headers=resp_headers,
                    body=cached.body,
                    cache_status="HIT",
                )

        target_url = f"{self.origin}{path}"
        req_headers = {
            k: v for k, v in headers.items() if k.lower() not in ("host", "connection")
        }

        try:
            origin_resp = self.client.request(
                method=method,
                url=target_url,
                headers=req_headers,
                content=body,
            )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as err:
            raise OriginConnectionError(f"Failed to connect to origin: {err}") from err

        filtered_headers = [
            (k, v)
            for k, v in origin_resp.headers.items()
            if k.lower() not in HOP_BY_HOP_HEADERS
        ]

        if is_cacheable and origin_resp.status_code < 400:
            self.cache.set(
                key,
                CachedResponse(
                    status_code=origin_resp.status_code,
                    headers=filtered_headers,
                    body=origin_resp.content,
                ),
            )

        resp_headers = list(filtered_headers)
        resp_headers.append(("X-Cache", "MISS"))

        return ProxyResponse(
            status_code=origin_resp.status_code,
            headers=resp_headers,
            body=origin_resp.content,
            cache_status="MISS",
        )
