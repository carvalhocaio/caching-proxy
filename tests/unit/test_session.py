import io
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from caching_proxy.domain.models import CachedResponse
from caching_proxy.infrastructure.cli.session import Session


class FakeCacheStore:
    def __init__(self, count: int = 5) -> None:
        self.count = count
        self._store: dict[str, CachedResponse] = {}

    def get(self, key: str) -> CachedResponse | None:
        return self._store.get(key)

    def set(self, key: str, response: CachedResponse) -> None:
        self._store[key] = response

    def clear(self) -> int:
        cleared = self.count + len(self._store)
        self.count = 0
        self._store.clear()
        return cleared


def test_session_clear_cache_success():
    stdout_io = io.StringIO()
    stderr_io = io.StringIO()
    stdout_console = Console(file=stdout_io, color_system=None, width=120)
    stderr_console = Console(file=stderr_io, color_system=None, width=120)

    cache = FakeCacheStore()
    session = Session(
        cache=cache,
        stdout_console=stdout_console,
        stderr_console=stderr_console,
    )

    code = session.run(["--clear-cache"])
    assert code == 0
    assert "Cache cleared successfully" in stdout_io.getvalue()
    assert stderr_io.getvalue() == ""
    assert cache.count == 0


def test_session_usage_error():
    stderr_io = io.StringIO()
    stderr_console = Console(file=stderr_io, color_system=None, width=120)

    session = Session(stderr_console=stderr_console)
    code = session.run([])

    assert code == 1
    assert "Error:" in stderr_io.getvalue()


def test_session_server_start_and_keyboard_interrupt():
    stdout_io = io.StringIO()
    stdout_console = Console(file=stdout_io, color_system=None, width=120)

    mock_server = MagicMock()
    mock_server.serve_forever.side_effect = KeyboardInterrupt

    def server_factory(port, forwarder):
        return mock_server

    session = Session(
        cache=FakeCacheStore(),
        stdout_console=stdout_console,
        server_factory=server_factory,
    )

    code = session.run(["--port", "3000", "--origin", "http://dummyjson.com"])
    assert code == 0
    assert "Starting caching proxy on port 3000" in stdout_io.getvalue()
    assert "forwarding to http://dummyjson.com" in stdout_io.getvalue()
    assert "Proxy server stopped" in stdout_io.getvalue()
    mock_server.server_close.assert_called_once()


def test_session_unexpected_error():
    stderr_io = io.StringIO()
    stderr_console = Console(file=stderr_io, color_system=None, width=120)

    mock_server = MagicMock()
    mock_server.serve_forever.side_effect = RuntimeError("Fatal crash")

    def server_factory(port, forwarder):
        return mock_server

    session = Session(
        cache=FakeCacheStore(),
        stderr_console=stderr_console,
        server_factory=server_factory,
    )

    code = session.run(["--port", "3000", "--origin", "http://dummyjson.com"])
    assert code == 4
    assert "Unexpected error" in stderr_io.getvalue()


def test_main_entrypoint(monkeypatch):
    import caching_proxy.__main__ as main_mod

    monkeypatch.setattr("sys.argv", ["caching-proxy", "--clear-cache"])
    monkeypatch.setattr(
        "caching_proxy.infrastructure.cli.session.Session.run",
        lambda self, args: 0,
    )
    with pytest.raises(SystemExit) as exc:
        main_mod.main()
    assert exc.value.code == 0
