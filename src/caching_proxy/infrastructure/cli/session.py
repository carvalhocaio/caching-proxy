"""CLI session orchestration and exit code mapping for caching-proxy."""

from collections.abc import Callable
from typing import Any

from rich.console import Console

from caching_proxy.domain.ports import CacheStore
from caching_proxy.errors import CacheError, OriginConnectionError, UsageError
from caching_proxy.infrastructure.cache.sqlite_cache import SQLiteCache
from caching_proxy.infrastructure.cli.parser import parse_args
from caching_proxy.infrastructure.proxy.forwarder import ProxyForwarder
from caching_proxy.infrastructure.proxy.server import CachingProxyServer


def default_server_factory(port: int, forwarder: ProxyForwarder) -> CachingProxyServer:
    """Create the default ThreadingHTTPServer instance."""
    return CachingProxyServer(("0.0.0.0", port), forwarder=forwarder)


class Session:
    """Coordinates CLI execution lifecycle and handles errors."""

    def __init__(
        self,
        cache: CacheStore | None = None,
        stdout_console: Console | None = None,
        stderr_console: Console | None = None,
        server_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._cache = cache or SQLiteCache()
        self._stdout = stdout_console or Console()
        self._stderr = stderr_console or Console(stderr=True)
        self._server_factory = server_factory or default_server_factory

    def run(self, args: list[str] | None = None) -> int:
        """Run the CLI session and return an integer exit code."""
        try:
            parsed = parse_args(args)
            if parsed.clear_cache:
                cleared_count = self._cache.clear()
                self._stdout.print(
                    f"[bold green]Cache cleared successfully[/bold green] "
                    f"({cleared_count} items removed)."
                )
                return 0

            # Server mode
            assert parsed.port is not None
            assert parsed.origin is not None

            forwarder = ProxyForwarder(origin=parsed.origin, cache=self._cache)
            server = self._server_factory(parsed.port, forwarder)

            self._stdout.print(
                f"[bold cyan]Starting caching proxy on port {parsed.port} "
                f"forwarding to {parsed.origin}...[/bold cyan]"
            )
            self._stdout.print("[dim]Press Ctrl+C to stop the server.[/dim]")

            try:
                server.serve_forever()
            except KeyboardInterrupt:
                self._stdout.print("\n[yellow]Proxy server stopped.[/yellow]")
            finally:
                server.server_close()

            return 0

        except UsageError as err:
            self._stderr.print(f"[bold red]Error:[/bold red] {err}")
            return 1
        except CacheError as err:
            self._stderr.print(f"[bold red]Cache Error:[/bold red] {err}")
            return 2
        except OriginConnectionError as err:
            self._stderr.print(f"[bold red]Origin Error:[/bold red] {err}")
            return 3
        except Exception as err:
            self._stderr.print(f"[bold red]Unexpected error:[/bold red] {err}")
            return 4
