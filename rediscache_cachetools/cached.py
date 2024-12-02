import collections
import contextlib
import functools

_CacheInfo = collections.namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])


class Cached:
    def __init__(self, cache, key=None, lock=None, info=False, prefix=""):
        self.cache = cache
        self.key_function = key
        self.lock = lock
        self.info = info

        self.namespace = None
        self.prefix = prefix if prefix.endswith(":") else prefix + ":"
        self.keys_key = None
        self.original_func = None

        if self.info:
            self.hits = 0
            self.misses = 0

        self.key_cache = {}

    def make_key(self, func, *args, **kwargs):
        """Generate a cache key using the cache's make_key method if available."""

        if hasattr(func, 'cached_key'):
            return func.cached_key

        if hasattr(self.cache, 'make_key'):
            return self.prefix + self.cache.make_key(func, *args, **kwargs)
        elif self.key_function:
            return self.prefix + self.key_function(func, *args, **kwargs)
        else:
            return f"{self.prefix}{args}:{kwargs}"

    def wrapper(self, func, *args, **kwargs):
        cached_key = self.make_key(func, *args, **kwargs)

        try:
            with self.lock if self.lock else contextlib.nullcontext():
                result = self.cache[cached_key]
                if self.info:
                    self.hits += 1
                return result
        except KeyError:
            if self.info:
                self.misses += 1
            result = func(*args, **kwargs)
            try:
                with self.lock if self.lock else contextlib.nullcontext():
                    self.cache[cached_key] = result
            except ValueError:
                pass  # value too large
            return result

    def __call__(self, func):

        def wrapped_func(*args, **kwargs):
            return self.wrapper(func, *args, **kwargs)

        if self.info:
            wrapped_func.cache_info = self.get_cache_info
            wrapped_func.cache_clear = self.cache_clear
        else:
            wrapped_func.cache_info = None
            wrapped_func.cache_clear = lambda: None

        wrapped_func.cache = self.cache
        wrapped_func.cache_key = self.key_function
        wrapped_func.cache_lock = self.lock

        return functools.update_wrapper(wrapped_func, func)

    def get_cache_info(self):
        if isinstance(self.cache, collections.abc.Mapping):
            return _CacheInfo(self.hits, self.misses, None, len(self.cache))
        else:
            return _CacheInfo(self.hits, self.misses, 0, 0)

    def cache_clear(self):
        self.cache.clear()
        self.key_cache.clear()
        if self.info:
            self.hits = self.misses = 0
