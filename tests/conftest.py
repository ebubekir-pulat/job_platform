import pytest
import redis

@pytest.fixture(autouse=True)
def clear_redis_queue():
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    redis_client.delete("jobs:queue")