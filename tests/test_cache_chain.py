from unittest.mock import MagicMock

import pytest
from cachetools import LRUCache, LFUCache

from redis_cachetools.chain_cache import ChainCache


def test_cache_chain_init():
    with pytest.raises(ValueError, match="CacheChain requires at least two cache levels."):
        ChainCache(LRUCache(maxsize=10))


def test_cache_chain_getitem():
    cache1 = LRUCache(maxsize=2)
    cache2 = LFUCache(maxsize=5)
    chain = ChainCache(cache1, cache2)

    cache2['a'] = 1
    assert chain['a'] == 1
    assert 'a' in cache1  # Ensure promotion


def test_cache_chain_getitem_keyerror():
    cache1 = LRUCache(maxsize=2)
    cache2 = LFUCache(maxsize=5)
    chain = ChainCache(cache1, cache2)

    with pytest.raises(KeyError):
        _ = chain['missing']


def test_cache_chain_getitem_resilient():
    cache1 = LRUCache(maxsize=2)
    cache2 = MagicMock()
    cache2.__getitem__.side_effect = Exception("Cache failure")
    chain = ChainCache(cache1, cache2, resilient=True)

    with pytest.raises(Exception):
        _ = chain['missing']


def test_cache_chain_setitem():
    cache1 = LRUCache(maxsize=2)
    cache2 = LFUCache(maxsize=5)
    chain = ChainCache(cache1, cache2)

    chain['a'] = 1
    assert cache1['a'] == 1
    assert cache2['a'] == 1


def test_cache_chain_delitem():
    cache1 = LRUCache(maxsize=2)
    cache2 = LFUCache(maxsize=5)
    chain = ChainCache(cache1, cache2)

    chain['a'] = 1
    del chain['a']
    assert 'a' not in cache1
    assert 'a' not in cache2


def test_cache_chain_len():
    cache1 = LRUCache(maxsize=2)
    cache2 = LFUCache(maxsize=5)
    chain = ChainCache(cache1, cache2)

    chain['a'] = 1
    assert len(chain) == 1


def test_cache_chain_iter():
    cache1 = LRUCache(maxsize=2)
    cache2 = LFUCache(maxsize=5)
    cache1['a'] = 1
    chain = ChainCache(cache1, cache2)

    assert list(iter(chain)) == ['a']


def test_cache_chain_clear():
    cache1 = LRUCache(maxsize=2)
    cache2 = LFUCache(maxsize=5)
    chain = ChainCache(cache1, cache2)

    chain['a'] = 1
    chain.clear()
    assert len(cache1) == 0
    assert len(cache2) == 0


def test_cache_chain_stats():
    cache1 = MagicMock()
    cache1.stats.return_value = {'type': 1, 'reads': 10, 'hits': 5}
    cache2 = MagicMock()
    cache2.stats.return_value = {}
    chain = ChainCache(cache1, cache2)

    stats = chain.stats()
    assert stats['cache1']['reads'] == 10
    assert stats['cache1']['hits'] == 5


def test_cache_chain_hits():
    cache1 = MagicMock()
    cache1.stats.return_value = {'type': 1, 'reads': 10, 'hits': 5}
    cache2 = MagicMock()
    cache2.stats.return_value = {'type': 1, 'reads': 5, 'hits': 3}
    chain = ChainCache(cache1, cache2)

    assert chain.hits() == 8 / 15


def test_cache_chain_reset():
    cache1 = MagicMock()
    cache2 = MagicMock()
    chain = ChainCache(cache1, cache2)

    chain.reset()
    cache1.reset.assert_called_once()
    cache2.reset.assert_called_once()
