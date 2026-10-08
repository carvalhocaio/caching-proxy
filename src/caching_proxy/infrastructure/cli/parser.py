"""CLI argument parsing and validation for caching-proxy."""

import argparse
from dataclasses import dataclass
from typing import NoReturn

from caching_proxy.errors import UsageError


@dataclass(frozen=True, slots=True)
class CLIArgs:
    """Validated CLI arguments."""

    clear_cache: bool = False
    port: int | None = None
    origin: str | None = None


class _CLIArgumentParser(argparse.ArgumentParser):
    """Custom parser raising UsageError instead of exiting."""

    def error(self, message: str) -> NoReturn:
        raise UsageError(message)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for caching-proxy."""
    parser = _CLIArgumentParser(
        prog="caching-proxy",
        description=(
            "A caching proxy server that forwards requests and caches responses."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port number on which the caching proxy server will listen.",
    )
    parser.add_argument(
        "--origin",
        type=str,
        default=None,
        help="Base URL of the origin server to forward requests to.",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        default=False,
        help="Clear all cached responses and exit.",
    )
    return parser


def parse_args(args: list[str] | None = None) -> CLIArgs:
    """Parse and validate command line arguments."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.clear_cache:
        return CLIArgs(clear_cache=True)

    if parsed.port is None and parsed.origin is None:
        raise UsageError(
            "Either --clear-cache or both --port and --origin must be provided."
        )

    if parsed.port is None:
        raise UsageError("--port is required when running the proxy server.")

    if parsed.origin is None:
        raise UsageError("--origin is required when running the proxy server.")

    if not (1 <= parsed.port <= 65535):
        raise UsageError(f"Port must be between 1 and 65535, got {parsed.port}.")

    origin = parsed.origin.strip().rstrip("/")
    if not (origin.startswith("http://") or origin.startswith("https://")):
        raise UsageError("--origin must start with http:// or https://")

    return CLIArgs(
        clear_cache=False,
        port=parsed.port,
        origin=origin,
    )
