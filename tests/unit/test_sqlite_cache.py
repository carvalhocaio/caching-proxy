from caching_proxy.domain.models import CachedResponse
from caching_proxy.infrastructure.cache.sqlite_cache import SQLiteCache


def test_sqlite_cache_get_non_existent(tmp_path):
    db_file = tmp_path / "test_cache.db"
    cache = SQLiteCache(db_path=db_file)

    assert cache.get("GET:/products") is None


def test_sqlite_cache_set_and_get(tmp_path):
    db_file = tmp_path / "test_cache.db"
    cache = SQLiteCache(db_path=db_file)

    response = CachedResponse(
        status_code=200,
        headers=[("content-type", "application/json"), ("x-custom", "value")],
        body=b'{"id": 1, "name": "Phone"}',
    )
    cache.set("GET:/products/1", response)

    retrieved = cache.get("GET:/products/1")
    assert retrieved is not None
    assert retrieved.status_code == 200
    assert retrieved.headers == [
        ("content-type", "application/json"),
        ("x-custom", "value"),
    ]
    assert retrieved.body == b'{"id": 1, "name": "Phone"}'


def test_sqlite_cache_overwrite(tmp_path):
    db_file = tmp_path / "test_cache.db"
    cache = SQLiteCache(db_path=db_file)

    res1 = CachedResponse(status_code=200, headers=[], body=b"first")
    res2 = CachedResponse(status_code=200, headers=[], body=b"second")

    cache.set("GET:/test", res1)
    cache.set("GET:/test", res2)

    retrieved = cache.get("GET:/test")
    assert retrieved is not None
    assert retrieved.body == b"second"


def test_sqlite_cache_clear(tmp_path):
    db_file = tmp_path / "test_cache.db"
    cache = SQLiteCache(db_path=db_file)

    cache.set("GET:/a", CachedResponse(status_code=200, headers=[], body=b"a"))
    cache.set("GET:/b", CachedResponse(status_code=200, headers=[], body=b"b"))

    cleared = cache.clear()
    assert cleared == 2
    assert cache.get("GET:/a") is None
    assert cache.get("GET:/b") is None
