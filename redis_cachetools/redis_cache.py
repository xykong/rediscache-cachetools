import base64
import json
from inspect import stack, getmodule
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

    def __init__(self, host='localhost', port=6379, db=0, ttl=600, prefix=""):
        self._redis = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self._ttl = ttl
        self._prefix = prefix
        self._function_path = self._get_calling_function_path()  # Initialize once

    @staticmethod
    def _serialize(value: Any) -> str:
        """Serialize a value to a JSON string."""
        if isinstance(value, bytes):
            value = base64.b64encode(value).decode('utf-8')
        return json.dumps(value)

    @staticmethod
    def _deserialize(value: str) -> Any:
        """Deserialize a JSON string to a Python object."""
        value = json.loads(value)
        if isinstance(value, str):
            try:
                # Try to decode the base64 string back to bytes
                value = base64.b64decode(value)
            except Exception as e:
                print(f"Error decoding base64: {e}")
                pass
        return value

    @staticmethod
    def _get_calling_function_path() -> str:
        """Get the calling function's module and name."""
        stack_frame = stack()[2]
        module = getmodule(stack_frame[0])
        function_name = stack_frame.function
        return f"{module.__name__}.{function_name}" if module else function_name

    def _make_key(self, key: Any) -> str:
        """Generate a unique key with prefix and function path."""
        full_key = f"{self._prefix}{self._function_path}:{key}"
        return full_key

    def __getitem__(self, key: Any) -> Any:
        """Retrieve a value from the cache."""
        full_key = self._make_key(key)
        value = self._redis.get(full_key)
        if value is None:
            raise KeyError(key)
        # noinspection PyTypeChecker
        return self._deserialize(value)

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a value in the cache with an optional TTL."""
        full_key = self._make_key(key)
        self._redis.setex(full_key, self._ttl, self._serialize(value))

    def __delitem__(self, key: Any) -> None:
        """Delete a value from the cache."""
        full_key = self._make_key(key)
        if not self._redis.delete(full_key):
            raise KeyError(key)

    def __len__(self) -> int:
        """Return an approximate count of items in the cache."""
        return self._redis.dbsize()

    def __iter__(self):
        """Iterate over cache keys."""
        for key in self._redis.scan_iter():
            yield key

    def clear(self) -> None:
        """Clear all items in the cache."""
        self._redis.flushdb()

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
