from redis import StrictRedis
from redis_cache import RedisCache

client = StrictRedis(host="localhost", decode_responses=True)
cache = RedisCache(redis_client=client)


@cache.cache()
def get_value_0() -> str:
    return f"Value for 0"


@cache.cache()
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

    # Invalidate the value for 0
    get_value_0.invalidate()

    # Get the value for 0 again
    value_0 = get_value_0()
    assert value_0 == "Value for 0"

    # Get the value for 1 again
    value_1 = get_value_1()
    assert value_1 == "Value for 1"

    # Invalidate all values
    get_value_0.invalidate_all()
    get_value_1.invalidate_all()

    # Get the value for 0 again
    value_0 = get_value_0()
    assert value_0 == "Value for 0"

    # Get the value for 1 again
    value_1 = get_value_1()
    assert value_1 == "Value for 1"
