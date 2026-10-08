"""HTTP Server implementation for caching proxy."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from caching_proxy.errors import OriginConnectionError
from caching_proxy.infrastructure.proxy.forwarder import ProxyForwarder


class ProxyRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler forwarding requests through ProxyForwarder."""

    server: Any  # has server.forwarder

    def log_message(self, *args: Any, **kwargs: Any) -> None:
        """Suppress default stderr logging; handled by session or silent."""

    def _dispatch_proxy(self, method: str) -> None:
        forwarder: ProxyForwarder = self.server.forwarder

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req_headers = dict(self.headers.items())

        try:
            response = forwarder.handle_request(
                method=method,
                path=self.path,
                headers=req_headers,
                body=body,
            )
            self.send_response(response.status_code)
            for header_name, header_value in response.headers:
                self.send_header(header_name, header_value)
            self.end_headers()
            self.wfile.write(response.body)
        except OriginConnectionError as err:
            self.send_error(502, f"Bad Gateway: {err}")

    def do_GET(self) -> None:
        self._dispatch_proxy("GET")

    def do_POST(self) -> None:
        self._dispatch_proxy("POST")

    def do_PUT(self) -> None:
        self._dispatch_proxy("PUT")

    def do_DELETE(self) -> None:
        self._dispatch_proxy("DELETE")

    def do_PATCH(self) -> None:
        self._dispatch_proxy("PATCH")

    def do_HEAD(self) -> None:
        self._dispatch_proxy("HEAD")

    def do_OPTIONS(self) -> None:
        self._dispatch_proxy("OPTIONS")


class CachingProxyServer(ThreadingHTTPServer):
    """Multi-threaded HTTP Server for caching proxy."""

    def __init__(
        self,
        server_address: tuple[str, int],
        forwarder: ProxyForwarder,
    ) -> None:
        super().__init__(server_address, ProxyRequestHandler)
        self.forwarder = forwarder
