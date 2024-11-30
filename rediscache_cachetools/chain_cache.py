import logging
from typing import Any, MutableMapping

log = logging.getLogger(__name__)


class ChainCache(MutableMapping):
    """A multi-level cache chain that tries multiple caches in order.

    :param caches: A list of caches ordered by priority.
    :param resilient: If True, will ignore exceptions from lower-level caches.
    """

    def __init__(self, *caches: MutableMapping, resilient: bool = False):
        if len(caches) < 2:
            raise ValueError("CacheChain requires at least two cache levels.")
        self._caches = caches
        self._resilient = resilient

    def __getitem__(self, key: Any) -> Any:
        last_exception = None

        for i, cache in enumerate(self._caches):
            try:
                value = cache[key]
                # Promote item to higher-level caches if found in a lower-level cache
                for j in range(i):
                    self._caches[j][key] = value
                return value
            except KeyError:
                continue
            except Exception as e:
                if self._resilient:
                    log.debug(e, exc_info=True)
                    last_exception = e
                else:
                    raise

        if last_exception:
            raise last_exception
        raise KeyError(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        last_exception = None

        for cache in self._caches:
            try:
                cache[key] = value
            except Exception as e:
                if self._resilient:
                    log.debug(e, exc_info=True)
                    last_exception = e
                else:
                    raise

        if last_exception:
            raise last_exception

    def __delitem__(self, key: Any) -> None:
        last_exception = None

        for cache in self._caches:
            try:
                del cache[key]
            except KeyError:
                continue
            except Exception as e:
                if self._resilient:
                    log.debug(e, exc_info=True)
                    last_exception = e
                else:
                    raise

        if last_exception:
            raise last_exception

    def __len__(self) -> int:
        return len(self._caches[0])

    def __iter__(self):
        return iter(self._caches[0])

    def clear(self) -> None:
        for cache in self._caches:
            cache.clear()

    def stats(self) -> dict[str, Any]:
        """Return statistics for each cache level."""
        data = {"type": "multi"}
        for i, cache in enumerate(self._caches):
            try:
                data[f"cache{i + 1}"] = cache.stats()  # type: ignore
            except Exception as e:
                log.debug(e, exc_info=True)
                data[f"cache{i + 1}"] = {}  # type: ignore
        return data

    def hits(self) -> float | None:
        """Calculate the hit ratio across all caches."""
        data = self.stats()
        total_reads = total_hits = 0
        for cache_stats in data.values():
            if cache_stats and "type" in cache_stats and cache_stats["type"] == 1:
                total_reads += cache_stats["reads"]
                total_hits += cache_stats["hits"]
        return float(total_hits) / max(total_reads, 1) if total_reads > 0 else None

    def reset(self) -> None:
        """Reset all cache statistics."""
        for cache in self._caches:
            try:
                cache.reset()  # type: ignore
            except Exception as e:
                log.debug(e, exc_info=True)
                continue
