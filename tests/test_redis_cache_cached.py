from rediscache_cachetools.cached import Cached
from rediscache_cachetools.redis_cache import RedisCache

redis = RedisCache()

cached = Cached(cache=redis)


@cached
def get_value_0(a=0, b=0) -> str:
    return f"Value for 0 -> {a} {b}"


@cached
def get_value_1(a=0, b=0) -> str:
    return f"Value for 1 -> {a} {b}"


def test_cache():
    a, b = 1, 2

    # Get the value for 0
    value_0 = get_value_0(a)
    assert value_0 == "Value for 0 -> 1 0"

    # Get the value for 0
    value_0 = get_value_0(a)
    assert value_0 == "Value for 0 -> 1 0"

    # Get the value for 0
    value_0 = get_value_0(b)
    assert value_0 == "Value for 0 -> 2 0"

    # Get the value for 0
    value_0 = get_value_0(b)
    assert value_0 == "Value for 0 -> 2 0"

    # Get the value for 0
    value_0 = get_value_0(a, b)
    assert value_0 == "Value for 0 -> 1 2"

    # Get the value for 0 again
    value_0 = get_value_0(a, b)
    assert value_0 == "Value for 0 -> 1 2"

    # Get the value for 1
    value_1 = get_value_1(a, b)
    assert value_1 == "Value for 1 -> 1 2"

    # Get the value for 1
    value_1 = get_value_1(a, b)
    assert value_1 == "Value for 1 -> 1 2"
