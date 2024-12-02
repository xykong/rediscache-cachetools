import base64
import json
from typing import Any, MutableMapping

import redis


class RedisCache(MutableMapping):
    """A cache class that uses Redis as the backend storage with key prefixing and unique key generation.

    :param host: Redis server host.
    :param port: Redis server port.
    :param db: Redis database number.
    :param ttl: Default time-to-live for cache entries in seconds.
    :param prefix: Optional prefix to add to all keys.
    """

    def __init__(self, host='localhost', port=6379, db=0, ttl=None, prefix=""):
        self._redis = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self._ttl = ttl
        self.prefix = prefix if prefix.endswith(":") else prefix + ":"

    @staticmethod
    def _serialize(value: Any) -> str:
        """Serialize a value to a JSON string."""
        if isinstance(value, bytes):
            # Encode bytes to a base64 string
            value = base64.b64encode(value).decode('utf-8')
            return json.dumps({"__type__": "bytes", "data": value})
        return json.dumps(value)

    @staticmethod
    def _deserialize(value: str) -> Any:
        """Deserialize a JSON string to a Python object."""
        obj = json.loads(value)
        if isinstance(obj, dict) and obj.get("__type__") == "bytes":
            # Decode base64 string back to bytes
            return base64.b64decode(obj["data"])
        return obj

    def make_key(self, func, *args, **kwargs) -> str:
        """Generate a unique key with prefix and function path."""

        return f"{self.prefix}{func.__module__}.{func.__qualname__}:{args}:{kwargs}"

    @staticmethod
    def _make_key(key):
        """Generate a unique key with prefix."""
        if isinstance(key, (str, bytes)):
            return key
        return json.dumps(key, sort_keys=True)

    def __getitem__(self, key: Any) -> Any:
        """Retrieve a value from the cache."""
        value = self._redis.get(self._make_key(key))
        if value is None:
            raise KeyError(key)
        # noinspection PyTypeChecker
        return self._deserialize(value)

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a value in the cache with an optional TTL."""
        if self._ttl is None:
            self._redis.set(self._make_key(key), self._serialize(value))
        else:
            self._redis.setex(self._make_key(key), self._ttl, self._serialize(value))

    def __delitem__(self, key: Any) -> None:
        """Delete a value from the cache."""
        if not self._redis.delete(self._make_key(key)):
            raise KeyError(self._make_key(key))

    def __len__(self) -> int:
        """Return an approximate count of items in the cache."""
        return self._redis.dbsize()

    def __iter__(self):
        """Iterate over cache keys."""
        for key in self._redis.scan_iter():
            yield key

    def clear(self) -> None:
        """Clear all items in the cache."""
        # self._redis.flushdb()
        for key in self._redis.scan_iter():
            self._redis.delete(key)

    def stats(self) -> dict[str, Any]:
        """Return statistics about the Redis cache."""
        info = self._redis.info()
        return {
            'keys': self._redis.dbsize(),
            'hits': info['keyspace_hits'],
            'misses': info['keyspace_misses'],
        }

    def hits(self) -> float:
        """Calculate the cache hit ratio."""
        stats = self.stats()
        total = stats['hits'] + stats['misses']
        return float(stats['hits']) / total if total > 0 else 0.0

    def reset(self) -> None:
        """Reset the cache statistics."""
        self.clear()
