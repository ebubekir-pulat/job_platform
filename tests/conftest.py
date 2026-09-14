import pytest
import redis

from job_platform.queue import QUEUE_NAME, PROCESSING_QUEUE_NAME

@pytest.fixture(autouse=True)
def clear_redis_queues():
    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    redis_client.delete(
        QUEUE_NAME,
        PROCESSING_QUEUE_NAME,
    )