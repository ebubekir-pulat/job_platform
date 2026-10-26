import time
import uuid

from job_platform.job_queue import (
    JobQueue,
    LEASE_KEY,
    LEASE_OWNER_KEY,
    QUEUE_NAME,
    PROCESSING_QUEUE_NAME,
)

def test_expired_job_is_requeued():
    queue = JobQueue()
    job_id = uuid.uuid4()
    job_id_str = str(job_id)

    try:
        queue.enqueue(job_id)
        claimed_id, first_token = queue.dequeue()

        assert claimed_id == job_id

        # Simulate a worker crash by expiring its lease.
        queue.redis.zadd(
            LEASE_KEY,
            {job_id_str: time.time() - 10},
        )

        recovered = queue.recover_expired_jobs()

        assert job_id in recovered
        assert job_id not in queue.get_processing_jobs()
        
        # Reclaim the recovered job. It should have a new token.
        reclaimed_id, second_token = queue.dequeue()

        assert reclaimed_id == job_id
        assert second_token != first_token

        assert queue.complete(job_id, second_token) is True
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, job_id_str)
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, job_id_str)
        queue.redis.zrem(LEASE_KEY, job_id_str)
        queue.redis.hdel(LEASE_OWNER_KEY, job_id_str)