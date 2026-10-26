import uuid
import time

from job_platform.job_queue import (
    JobQueue,
    LEASE_KEY,
    LEASE_OWNER_KEY,
    QUEUE_NAME,
    PROCESSING_QUEUE_NAME,
)


def test_lease_can_be_renewed():
    queue = JobQueue()
    job_id = uuid.uuid4()
    job_id_str = str(job_id)
    lease_token = None

    try:
        queue.enqueue(job_id)
        claimed_job_id, lease_token = queue.dequeue()
        assert claimed_job_id == job_id

        # Make the lease nearly expired and register its owner.
        queue.redis.zadd(
            LEASE_KEY,
            {job_id_str: time.time() + 2},
        )
        queue.redis.hset(
            LEASE_OWNER_KEY,
            job_id_str,
            lease_token,
        )

        assert queue.renew_lease(job_id, lease_token) is True

        expiry = queue.redis.zscore(LEASE_KEY, job_id_str)
        assert expiry is not None
        assert expiry > time.time() + 290
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, str(job_id))
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, str(job_id))
        queue.redis.zrem(LEASE_KEY, str(job_id))
        queue.redis.hdel(LEASE_OWNER_KEY, str(job_id))


def test_missing_lease_cannot_be_renewed():
    queue = JobQueue()
    job_id = uuid.uuid4()
    lease_token = str(uuid.uuid4())

    try:
        assert queue.renew_lease(job_id, lease_token) is False
    finally:
        queue.redis.zrem(LEASE_KEY, str(job_id))
        queue.redis.hdel(LEASE_OWNER_KEY, str(job_id))