import time
import uuid

from job_platform.job_queue import (
    JobQueue,
    LEASE_KEY,
    QUEUE_NAME,
    PROCESSING_QUEUE_NAME,
)

def test_expired_job_is_requeued():
    queue = JobQueue()
    job_id = uuid.uuid4()

    try:
        queue.enqueue(job_id)
        claimed_id = queue.dequeue()

        assert claimed_id == job_id

        # Simulate a worker crash by expiring its lease.
        queue.redis.zadd(
            LEASE_KEY,
            {str(job_id): time.time() - 10},
        )

        recovered = queue.recover_expired_jobs()

        assert job_id in recovered
        assert job_id not in queue.get_processing_jobs()
        assert queue.dequeue() == job_id

        queue.complete(job_id)
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, str(job_id))
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, str(job_id))
        queue.redis.zrem(LEASE_KEY, str(job_id))