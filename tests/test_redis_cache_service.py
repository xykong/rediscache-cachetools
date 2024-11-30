import socket

import pytest

from redis_cachetools.redis_cache import RedisCache

KEY, VAL = "hello-world!", "Hello World…"


def has_service(host="localhost", port=6379):
    """Check whether a network TCP/IP service is available."""
    tcp_ip = None
    try:
        tcp_ip = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_ip.settimeout(1)
        res = tcp_ip.connect_ex((host, port))
        return res == 0
    except Exception as e:
        print(f"Error checking for service: {e}")
        return False
    finally:
        if tcp_ip:
            tcp_ip.close()


@pytest.fixture(scope="module")
def redis_cache():
    """Fixture to provide a RedisCache instance connected to a local Redis server."""
    if not has_service(port=6379):
        pytest.skip("No local Redis service available for testing")
    cache = RedisCache(host='localhost', port=6379, db=0, ttl=600, prefix="test:")
    cache.clear()  # Ensure the cache is clear before each test
    return cache


def test_redis_cache_set_get(redis_cache):
    redis_cache[KEY] = VAL
    assert redis_cache[KEY] == VAL


def test_redis_cache_get_keyerror(redis_cache):
    with pytest.raises(KeyError):
        _ = redis_cache["missing_key"]


def test_redis_cache_delete(redis_cache):
    redis_cache[KEY] = VAL
    del redis_cache[KEY]
    with pytest.raises(KeyError):
        _ = redis_cache[KEY]


def test_redis_cache_len(redis_cache):
    redis_cache[KEY] = VAL
    assert len(redis_cache) > 0


def test_redis_cache_iter(redis_cache):
    redis_cache[KEY] = VAL
    keys = list(iter(redis_cache))
    assert len(keys) > 0


def test_redis_cache_clear(redis_cache):
    redis_cache[KEY] = VAL
    redis_cache.clear()
    with pytest.raises(KeyError):
        _ = redis_cache[KEY]


def test_redis_cache_stats(redis_cache):
    redis_cache[KEY] = VAL
    stats = redis_cache.stats()
    assert "keys" in stats
    assert "hits" in stats
    assert "misses" in stats


def test_redis_cache_hits(redis_cache):
    redis_cache[KEY] = VAL
    val = redis_cache[KEY]  # Access to simulate a hit
    assert val == VAL

    hits_ratio = redis_cache.hits()
    assert hits_ratio > 0


def test_redis_cache_setgetdel_bytes(redis_cache):
    key, val, cst = KEY.encode("UTF8"), VAL.encode("UTF8"), b"FOO"
    redis_cache[key] = val
    assert redis_cache[key] == val
    del redis_cache[key]
    with pytest.raises(KeyError):
        _ = redis_cache[key]
