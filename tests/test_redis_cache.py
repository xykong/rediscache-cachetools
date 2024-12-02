import json
import unittest
from unittest.mock import patch

from rediscache_cachetools.redis_cache import RedisCache


# Assuming the RedisCache class is defined in redis_cache.py


class TestRedisCache(unittest.TestCase):

    @patch('redis.StrictRedis')
    def setUp(self, mock_redis):
        self.mock_redis = mock_redis.return_value
        self.cache = RedisCache(host='localhost', port=6379, db=0, ttl=10, prefix="test")

    def test_set_and_get_item(self):
        key = 'test_key'
        prefixed_key = f'test:{key}'
        value = {'foo': 'bar'}
        self.cache[prefixed_key] = value
        self.mock_redis.setex.assert_called_once_with(prefixed_key, 10, json.dumps(value))

        self.mock_redis.get.return_value = json.dumps(value)
        result = self.cache[prefixed_key]
        self.mock_redis.get.assert_called_once_with(prefixed_key)
        self.assertEqual(result, value)

    def test_get_nonexistent_item_raises_keyerror(self):
        key = 'nonexistent_key'
        prefixed_key = f'test:{key}'
        self.mock_redis.get.return_value = None
        with self.assertRaises(KeyError):
            _ = self.cache[prefixed_key]

    def test_delete_item(self):
        key = 'test_key'
        prefixed_key = f'test:{key}'
        self.mock_redis.delete.return_value = 1
        del self.cache[prefixed_key]
        self.mock_redis.delete.assert_called_once_with(prefixed_key)

        self.mock_redis.delete.return_value = 0
        with self.assertRaises(KeyError):
            del self.cache[key]

    def test_len(self):
        self.mock_redis.dbsize.return_value = 5
        self.assertEqual(len(self.cache), 5)

    def test_iter(self):
        keys = ['test:test_key1', 'test:test_key2']
        self.mock_redis.scan_iter.return_value = iter(keys)
        self.assertEqual(list(self.cache), keys)

    def test_clear(self):
        keys = ['test:test_key1', 'test:test_key2']
        self.mock_redis.scan_iter.return_value = iter(keys)
        self.cache.clear()
        self.mock_redis.delete.assert_any_call('test:test_key1')
        self.mock_redis.delete.assert_any_call('test:test_key2')

    def test_stats(self):
        info = {
            'keyspace_hits': 5,
            'keyspace_misses': 3
        }
        self.mock_redis.info.return_value = info
        self.mock_redis.dbsize.return_value = 8
        expected_stats = {
            'keys': 8,
            'hits': 5,
            'misses': 3
        }
        self.assertEqual(self.cache.stats(), expected_stats)

    def test_hits(self):
        info = {
            'keyspace_hits': 5,
            'keyspace_misses': 5
        }
        self.mock_redis.info.return_value = info
        self.assertEqual(self.cache.hits(), 0.5)

        info['keyspace_hits'] = 0
        info['keyspace_misses'] = 0
        self.assertEqual(self.cache.hits(), 0.0)

    def test_reset(self):
        keys = ['test:test_key1', 'test:test_key2']
        self.mock_redis.scan_iter.return_value = iter(keys)
        self.cache.reset()
        self.mock_redis.delete.assert_any_call('test:test_key1')
        self.mock_redis.delete.assert_any_call('test:test_key2')

    def test_serialize(self):
        value = {'foo': 'bar'}
        self.assertEqual(self.cache._serialize(value), json.dumps(value))

    def test_deserialize(self):
        value = {'foo': 'bar'}
        self.assertEqual(self.cache._deserialize(json.dumps(value)), value)

    def test_seri_deseri(self):
        value = {'foo': 'bar'}
        self.assertEqual(self.cache._deserialize(self.cache._serialize(value)), value)

        value = b'foo'
        self.assertEqual(self.cache._deserialize(self.cache._serialize(value)), value)
