import json
from unittest.mock import patch

import pytest

from rediscache_cachetools.redis_cache import RedisCache


@patch('redis.StrictRedis')
def test_redis_cache_init(mock_redis):
    cache = RedisCache()

    assert cache._redis is not None

    mock_redis.assert_called_once()


@patch('redis.StrictRedis')
def test_redis_cache_set_get(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.get.return_value = json.dumps({'value': 42})

    cache = RedisCache(prefix="test:")
    cache['test_key'] = {'value': 42}
    full_key = f"test:{cache._function_path}:test_key"
    redis_mock.setex.assert_called_once_with(full_key, 600, json.dumps({'value': 42}))

    result = cache['test_key']
    assert result == {'value': 42}


@patch('redis.StrictRedis')
def test_redis_cache_get_keyerror(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.get.return_value = None

    cache = RedisCache()
    with pytest.raises(KeyError):
        _ = cache['missing']


@patch('redis.StrictRedis')
def test_redis_cache_delete(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.delete.return_value = 1

    cache = RedisCache(prefix="test:")
    cache['test_key'] = {'value': 42}
    del cache['test_key']
    full_key = f"test:{cache._function_path}:test_key"
    redis_mock.delete.assert_called_with(full_key)


@patch('redis.StrictRedis')
def test_redis_cache_delete_keyerror(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.delete.return_value = 0

    cache = RedisCache()
    with pytest.raises(KeyError):
        del cache['missing']


@patch('redis.StrictRedis')
def test_redis_cache_len(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.dbsize.return_value = 42

    cache = RedisCache()
    assert len(cache) == 42


@patch('redis.StrictRedis')
def test_redis_cache_iter(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.scan_iter.return_value = iter(['key1', 'key2'])

    cache = RedisCache()
    keys = list(iter(cache))
    assert keys == ['key1', 'key2']


@patch('redis.StrictRedis')
def test_redis_cache_clear(mock_redis):
    redis_mock = mock_redis.return_value

    cache = RedisCache()
    cache.clear()
    redis_mock.flushdb.assert_called_once()


@patch('redis.StrictRedis')
def test_redis_cache_stats(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.info.return_value = {'keyspace_hits': 10, 'keyspace_misses': 5}
    redis_mock.dbsize.return_value = 42

    cache = RedisCache()
    stats = cache.stats()
    assert stats['keys'] == 42
    assert stats['hits'] == 10
    assert stats['misses'] == 5


@patch('redis.StrictRedis')
def test_redis_cache_hits(mock_redis):
    redis_mock = mock_redis.return_value
    redis_mock.info.return_value = {'keyspace_hits': 10, 'keyspace_misses': 5}

    cache = RedisCache()
    assert cache.hits() == 10 / 15
