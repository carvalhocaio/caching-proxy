"""Main entry point for caching-proxy CLI."""

import sys

from caching_proxy.infrastructure.cli.session import Session


def main() -> None:
    """CLI composition root."""
    session = Session()
    sys.exit(session.run(sys.argv[1:]))


if __name__ == "__main__":
    main()
