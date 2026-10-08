import pytest

from caching_proxy.errors import UsageError
from caching_proxy.infrastructure.cli.parser import CLIArgs, parse_args


def test_parse_args_server_mode():
    args = parse_args(["--port", "3000", "--origin", "http://dummyjson.com"])
    assert args == CLIArgs(
        clear_cache=False,
        port=3000,
        origin="http://dummyjson.com",
    )


def test_parse_args_clear_cache_mode():
    args = parse_args(["--clear-cache"])
    assert args == CLIArgs(
        clear_cache=True,
        port=None,
        origin=None,
    )


def test_parse_args_missing_all():
    with pytest.raises(UsageError, match="Either --clear-cache or both --port"):
        parse_args([])


def test_parse_args_missing_origin():
    with pytest.raises(UsageError, match="--origin is required"):
        parse_args(["--port", "3000"])


def test_parse_args_missing_port():
    with pytest.raises(UsageError, match="--port is required"):
        parse_args(["--origin", "http://dummyjson.com"])


def test_parse_args_invalid_port():
    with pytest.raises(UsageError, match="Port must be between 1 and 65535"):
        parse_args(["--port", "0", "--origin", "http://dummyjson.com"])

    with pytest.raises(UsageError, match="Port must be between 1 and 65535"):
        parse_args(["--port", "70000", "--origin", "http://dummyjson.com"])


def test_parse_args_invalid_origin_url():
    with pytest.raises(
        UsageError, match="--origin must start with http:// or https://"
    ):
        parse_args(["--port", "3000", "--origin", "dummyjson.com"])
