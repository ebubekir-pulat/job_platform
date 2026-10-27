from unittest.mock import patch

from job_platform.models import Job, Status
from job_platform.repository import JobRepository
from job_platform.worker import process_job, run_job, handle_next_job
from job_platform.job_queue import JobQueue, QUEUE_NAME, PROCESSING_QUEUE_NAME, LEASE_KEY, LEASE_OWNER_KEY


def test_process_job_succeeds():
    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    process_job(job)


def test_process_job_fails():
    job = Job(
        type="test_job",
        payload={"should_fail": True},
    )

    try:
        process_job(job)
    except RuntimeError as exc:
        assert str(exc) == "Job processing failed"
    else:
        raise AssertionError("Expected process_job to fail")


def test_run_job_succeeds():
    try:
        repository = JobRepository()
        queue = JobQueue()

        job = Job(
            type="test_job",
            payload={"message": "hello"},
        )

        repository.create(job)

        queue.enqueue(job.id)
        claimed_id, lease_token = queue.dequeue()

        assert claimed_id == job.id

        result = run_job(job, repository, queue, lease_token)
        queue.complete(job.id, lease_token)

        assert result is not None
        assert result.status == Status.SUCCEEDED
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, str(job.id))
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, str(job.id))
        queue.redis.zrem(LEASE_KEY, str(job.id))
        queue.redis.hdel(LEASE_OWNER_KEY, str(job.id))


def test_run_job_fails_with_retry():
    try:
        repository = JobRepository()
        queue = JobQueue()

        job = Job(
            type="test_job",
            payload={"should_fail": True},
        )

        repository.create(job)

        queue.enqueue(job.id)
        claimed_id, lease_token = queue.dequeue()

        assert claimed_id == job.id

        result = run_job(job, repository, queue, lease_token)
        queue.complete(job.id, lease_token)

        assert result is not None
        assert result.attempts == 1
        assert result.status == Status.PENDING
        assert result.last_error == "Job processing failed"
    finally:
        queue.redis.lrem(QUEUE_NAME, 0, str(job.id))
        queue.redis.lrem(PROCESSING_QUEUE_NAME, 0, str(job.id))
        queue.redis.zrem(LEASE_KEY, str(job.id))
        queue.redis.hdel(LEASE_OWNER_KEY, str(job.id))


def test_handle_next_job_processes_queued_job():
    queue = JobQueue()
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    repository.create(job)
    queue.enqueue(job.id)

    handle_next_job(queue, repository)

    result = repository.get(job.id)

    assert result is not None
    assert result.status == Status.SUCCEEDED
    assert queue.redis.llen(PROCESSING_QUEUE_NAME) == 0

def test_failed_job_is_reenqueued():
    queue = JobQueue()
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"should_fail": True},
    )

    repository.create(job)
    queue.enqueue(job.id)

    handle_next_job(queue, repository)

    result = repository.get(job.id)

    assert result is not None
    assert result.attempts == 1
    assert result.status == Status.PENDING
    assert result.last_error == "Job processing failed"

    assert queue.redis.llen(PROCESSING_QUEUE_NAME) == 0
    assert queue.redis.llen("jobs:queue") == 1


def test_job_fails_after_three_attempts():
    queue = JobQueue()
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"should_fail": True},
        max_attempts=3,
    )

    repository.create(job)
    queue.enqueue(job.id)

    # Attempt 1
    handle_next_job(queue, repository)

    result = repository.get(job.id)
    assert result is not None
    assert result.attempts == 1
    assert result.status == Status.PENDING
    assert queue.redis.llen("jobs:queue") == 1

    # Attempt 2
    handle_next_job(queue, repository)

    result = repository.get(job.id)
    assert result is not None
    assert result.attempts == 2
    assert result.status == Status.PENDING
    assert queue.redis.llen("jobs:queue") == 1

    # Attempt 3 — final failure
    handle_next_job(queue, repository)

    result = repository.get(job.id)
    assert result is not None
    assert result.attempts == 3
    assert result.status == Status.FAILED
    assert result.last_error == "Job processing failed"

    # No queued or processing job remains
    assert queue.redis.llen("jobs:queue") == 0
    assert queue.redis.llen(PROCESSING_QUEUE_NAME) == 0


def test_rejected_job_update_does_not_complete_queue():
    queue = JobQueue()
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    repository.create(job)
    queue.enqueue(job.id)

    # Simulate another worker winning the database update race.
    with patch.object(repository, "update_job", return_value=False):
        handle_next_job(queue, repository)

    assert job.id in queue.get_processing_jobs()
    assert queue.redis.zscore(LEASE_KEY, str(job.id)) is not None