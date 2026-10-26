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