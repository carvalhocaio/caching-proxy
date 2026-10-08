import caching_proxy


def test_version() -> None:
    assert caching_proxy.__version__ == "0.1.0"
