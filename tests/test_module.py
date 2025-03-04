from unittest.mock import Mock

import pytest
import redis

from rediscache_cachetools.redis_cache import RedisCache


# Fixture for creating the RedisCache instance
@pytest.fixture
def cache():
    return RedisCache(host='localhost', port=6379, db=1, ttl=10, prefix="test:")


# Fixture to ensure Redis is available and flush the db before each test
@pytest.fixture(autouse=True)
def setup_and_teardown_redis():
    client = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)
    client.flushdb()
    yield
    client.flushdb()


def test_set_and_get_item(cache):
    cache["key1"] = "value1"
    assert cache["key1"] == "value1"


def test_get_missing_key(cache):
    with pytest.raises(KeyError):
        _ = cache["missing_key"]


def test_delete_item(cache):
    cache["key2"] = "value2"
    del cache["key2"]
    with pytest.raises(KeyError):
        _ = cache["key2"]


def test_len(cache):
    cache["key1"] = "value1"
    cache["key2"] = "value2"
    assert len(cache) == 2


def test_iteration(cache):
    cache["key1"] = "value1"
    cache["key2"] = "value2"
    keys = list(iter(cache))
    # assert set(keys) == {"test:__main__.test_iteration:('key1',):{}", "test:__main__.test_iteration:('key2',):{}"}
    assert set(keys) == {'key1', 'key2'}


def test_clear(cache):
    cache["key1"] = "value1"
    cache.clear()
    assert len(cache) == 0


def test_key_generation_with_make_key():
    cache = RedisCache()
    func = Mock(__module__='module', __qualname__='function')
    key = cache.make_key(func, 1, 2, a=3)
    assert key == "module.function:(1, 2):{'a': 3}"


def test_serialize_deserialize():
    data = {"key": "value"}
    serialized = RedisCache._serialize(data)
    assert serialized.startswith("json:")
    deserialized = RedisCache._deserialize(serialized)
    assert deserialized == data


def test_serialize_deserialize_raw():
    data = "simple string"
    serialized = RedisCache._serialize(data)
    assert serialized == data  # No prefix for raw strings
    deserialized = RedisCache._deserialize(serialized)
    assert deserialized == data


def test_serialize_deserialize_bytes():
    data = b"bytes data"
    serialized = RedisCache._serialize(data)
    assert serialized.startswith("b64:")
    deserialized = RedisCache._deserialize(serialized)
    assert deserialized == data


def test_cache_stats(cache):
    cache["key1"] = "value1"
    stats = cache.stats()
    assert "keys" in stats
    assert "hits" in stats
    assert "misses" in stats


def test_cache_hits(cache):
    cache["key1"] = "value1"
    _ = cache["key1"]  # This should count as a hit
    assert cache.hits() < 1.0  # 100% hit rate
