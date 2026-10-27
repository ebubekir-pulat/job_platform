import time
import uuid

from job_platform.job_queue import (
    JobQueue,
    LEASE_KEY,
    LEASE_OWNER_KEY,
    QUEUE_NAME,
    PROCESSING_QUEUE_NAME,
)

def test_enqueue_and_dequeue():
    queue = JobQueue()
    job_id = uuid.uuid4()
    job_id_str = str(job_id)

    try:
        queue.enqueue(job_id)

        result_id, lease_token = queue.dequeue()

        assert result_id == job_id
        assert isinstance(lease_token, str)
        assert lease_token
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, job_id_str)
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, job_id_str)
        queue.redis.zrem(LEASE_KEY, job_id_str)
        queue.redis.hdel(LEASE_OWNER_KEY, job_id_str)


def test_get_processing_jobs():
    queue = JobQueue()
    job_id = uuid.uuid4()
    job_id_str = str(job_id)

    try:
        queue.enqueue(job_id)
        claimed_id, _ = queue.dequeue()

        assert claimed_id == job_id
        assert queue.get_processing_jobs() == [job_id]
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, job_id_str)
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, job_id_str)
        queue.redis.zrem(LEASE_KEY, job_id_str)
        queue.redis.hdel(LEASE_OWNER_KEY, job_id_str)


def test_complete_removes_job_from_processing():
    queue = JobQueue()
    job_id = uuid.uuid4()
    job_id_str = str(job_id)

    try:
        queue.enqueue(job_id)
        claimed_id, lease_token = queue.dequeue()

        assert claimed_id == job_id
        assert queue.complete(job_id, lease_token) is True

        assert queue.get_processing_jobs() == []
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, job_id_str)
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, job_id_str)
        queue.redis.zrem(LEASE_KEY, job_id_str)
        queue.redis.hdel(LEASE_OWNER_KEY, job_id_str)


def test_stale_owner_cannot_renew_or_complete_reclaimed_job():
    queue = JobQueue()
    job_id = uuid.uuid4()
    job_id_str = str(job_id)

    try:
        # Worker A claims the job.
        queue.enqueue(job_id)
        first_id, first_token = queue.dequeue()
        assert first_id == job_id

        # Expire A's lease and recover the job.
        queue.redis.zadd(
            LEASE_KEY,
            {job_id_str: time.time() - 10},
        )
        recovered = queue.recover_expired_jobs()
        assert job_id in recovered

        # Worker B claims the same job with a new token.
        second_id, second_token = queue.dequeue()
        assert second_id == job_id
        assert second_token != first_token

        # A must not renew or complete B's lease.
        assert queue.renew_lease(job_id, first_token) is False
        assert queue.complete(job_id, first_token) is False

        # B still owns the lease and can complete the job.
        assert (
            queue.redis.hget(LEASE_OWNER_KEY, job_id_str)
            == second_token
        )
        assert queue.complete(job_id, second_token) is True

    finally:
        queue.redis.lrem(QUEUE_NAME, 0, job_id_str)
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, job_id_str)
        queue.redis.zrem(LEASE_KEY, job_id_str)
        queue.redis.hdel(LEASE_OWNER_KEY, job_id_str)