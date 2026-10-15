import uuid
import time

from job_platform.job_queue import (
    JobQueue,
    LEASE_KEY,
    QUEUE_NAME,
    PROCESSING_QUEUE_NAME,
)


def test_lease_can_be_renewed():
    queue = JobQueue()
    job_id = uuid.uuid4()

    try:
        queue.enqueue(job_id)
        assert queue.dequeue() == job_id

        # Make the lease nearly expired
        queue.redis.zadd(
            LEASE_KEY,
            {str(job_id): time.time() + 2},
        )

        assert queue.renew_lease(job_id) is True

        expiry = queue.redis.zscore(LEASE_KEY, str(job_id))
        assert expiry is not None
        assert expiry > time.time() + 290
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, str(job_id))
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, str(job_id))
        queue.redis.zrem(LEASE_KEY, str(job_id))


def test_missing_lease_cannot_be_renewed():
    queue = JobQueue()
    job_id = uuid.uuid4()

    assert queue.renew_lease(job_id) is False