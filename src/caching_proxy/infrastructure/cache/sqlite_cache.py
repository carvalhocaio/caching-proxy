"""SQLite-backed cache store."""

import json
import sqlite3
from pathlib import Path

from caching_proxy.domain.models import CachedResponse

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "caching-proxy"
DEFAULT_DB_PATH = DEFAULT_CACHE_DIR / "cache.db"


class SQLiteCache:
    """Thread-safe SQLite implementation of CacheStore."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS responses (
                    key TEXT PRIMARY KEY,
                    status_code INTEGER NOT NULL,
                    headers TEXT NOT NULL,
                    body BLOB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def get(self, key: str) -> CachedResponse | None:
        """Retrieve a cached response by key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status_code, headers, body FROM responses WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            status_code, headers_json, body = row
            headers = [(str(h[0]), str(h[1])) for h in json.loads(headers_json)]
            return CachedResponse(
                status_code=int(status_code),
                headers=headers,
                body=bytes(body),
            )

    def set(self, key: str, response: CachedResponse) -> None:
        """Store or update a response in the cache."""
        headers_json = json.dumps(response.headers)
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO responses (key, status_code, headers, body, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    status_code = excluded.status_code,
                    headers = excluded.headers,
                    body = excluded.body,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, response.status_code, headers_json, response.body),
            )

    def clear(self) -> int:
        """Clear all cached responses and return count of deleted items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM responses")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM responses")
            return int(count)
