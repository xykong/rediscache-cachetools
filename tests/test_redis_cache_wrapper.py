import cachetools

from rediscache_cachetools.redis_cache import RedisCache

redis = RedisCache()


@cachetools.cached(cache=redis, key=lambda: "value_0")
def get_value_0() -> str:
    return f"Value for 0"


@cachetools.cached(cache=redis, key=lambda: "value_1")
def get_value_1() -> str:
    return f"Value for 1"


def test_cache():
    # Get the value for 0
    value_0 = get_value_0()
    assert value_0 == "Value for 0"

    # Get the value for 1
    value_1 = get_value_1()
    assert value_1 == "Value for 1"

    # Get the value for 0 again
    value_0 = get_value_0()
    assert value_0 == "Value for 0"

    # Get the value for 1
    value_1 = get_value_1()
    assert value_1 == "Value for 1"
