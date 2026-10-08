# caching-proxy (Caching Server CLI)

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![uv](https://img.shields.io/badge/package%20manager-uv-blueviolet)
![pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC)
![Ruff](https://img.shields.io/badge/lint%2Fformat-ruff-red)
![Pyright](https://img.shields.io/badge/type%20checker-pyright-267BBA)

A command-line interface (CLI) tool that starts a caching proxy server. It forwards incoming HTTP requests to an origin server, caches the responses, and serves subsequent identical requests directly from the local cache.

Implementation of the [roadmap.sh - Caching Server](https://roadmap.sh/projects/caching-server) challenge.

---

## Features

- **Transparent Proxying:** Forwards incoming HTTP requests to any target `--origin` URL.
- **Response Caching:** Automatically caches successful `GET` responses in a persistent, concurrent SQLite database.
- **Cache Status Headers:** Injects diagnostic headers into all responses:
  - `X-Cache: HIT` when served from the local cache.
  - `X-Cache: MISS` when fetched from the origin server.
- **Cache Invalidation:** Clear cached responses anytime with `caching-proxy --clear-cache` (even from a separate terminal session).
- **Hop-by-Hop Header Stripping:** Safely filters connection and transport-specific headers (`Connection`, `Keep-Alive`, `Transfer-Encoding`, etc.) ensuring standard-compliant proxy forwarding.
- **Robust Concurrency:** Built on Python's native `ThreadingHTTPServer` with SQLite WAL mode.

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

---

## Installation & Setup

```bash
git clone https://github.com/carvalhocaio/caching-proxy.git
cd caching-proxy
make sync
```

---

## Usage

### 1. Start the Caching Proxy Server

Run via `uv run` or `make run`:

```bash
# Start proxy on port 3000 forwarding to dummyjson.com
uv run caching-proxy --port 3000 --origin http://dummyjson.com

# Using make run
make run ARGS="--port 3000 --origin http://dummyjson.com"
```

### 2. Make Requests

In another terminal, send requests to the proxy:

```bash
# First request: forwarded to origin server (Cache MISS)
curl -i http://localhost:3000/products

# Header in response:
# X-Cache: MISS

# Second request: served from cache (Cache HIT)
curl -i http://localhost:3000/products

# Header in response:
# X-Cache: HIT
```

### 3. Clear the Cache

Clear all cached responses:

```bash
uv run caching-proxy --clear-cache
```

---

## Options

| Flag | Argument | Description |
|---|---|---|
| `--port` | `<number>` | Port on which the caching proxy server will listen (1-65535). |
| `--origin` | `<url>` | URL of the origin server to forward requests to (must start with `http://` or `https://`). |
| `--clear-cache` | | Clear all cached responses and exit immediately. |
| `--help` | | Show help message and exit. |

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success (server shutdown cleanly or cache cleared) |
| `1` | Invalid usage or missing arguments |
| `2` | Cache storage error |
| `3` | Origin connection failure |
| `4` | Unexpected error |

---

## Development

```bash
make sync          # Install runtime and dev dependencies
make test          # Run tests with pytest
make lint          # Check code with ruff
make lint-fix      # Automatically fix linting issues
make format        # Format code with ruff
make format-check  # Verify code formatting
make typecheck     # Run static type checking with pyright
make audit         # Audit dependencies for security vulnerabilities
make check         # Run full check (lint, format-check, typecheck, audit, test)
```

---

## Project Structure

```text
src/caching_proxy/
├── __init__.py
├── __main__.py               # Composition root
├── errors.py                 # Custom exception hierarchy
├── domain/
│   ├── __init__.py
│   ├── models.py             # CachedResponse model
│   └── ports.py              # CacheStore protocol
└── infrastructure/
    ├── __init__.py
    ├── cache/
    │   ├── __init__.py
    │   └── sqlite_cache.py   # SQLite-backed CacheStore with WAL mode
    ├── proxy/
    │   ├── __init__.py
    │   ├── forwarder.py      # Request forwarding and cache coordination
    │   └── server.py         # ThreadingHTTPServer and ProxyRequestHandler
    └── cli/
        ├── __init__.py
        ├── parser.py         # Argument parsing and validation
        └── session.py        # CLI orchestration and lifecycle management
tests/
├── test_smoke.py
└── unit/
    ├── test_models.py
    ├── test_parser.py
    ├── test_proxy.py
    ├── test_server.py
    ├── test_session.py
    └── test_sqlite_cache.py
```

---

## Design notes

- **Thread-safe persistent cache:** Uses SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) stored under `~/.cache/caching-proxy/cache.db`. This allows the separate `caching-proxy --clear-cache` process to atomically clear the cache without locking out active reader threads.
- **Pure domain separation:** `CacheStore` is defined as a `Protocol`, isolating domain and forwarding components from the underlying SQLite storage implementation.
- **Lightweight multi-threading:** Powered by Python's standard `http.server.ThreadingHTTPServer` and `httpx`, eliminating heavyweight web framework dependencies while providing concurrency.
