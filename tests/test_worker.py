from job_platform.models import Job, Status
from job_platform.repository import JobRepository
from job_platform.worker import process_job, run_job, handle_next_job
from job_platform.queue import JobQueue, PROCESSING_QUEUE_NAME


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
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    repository.create(job)

    run_job(job, repository)

    result = repository.get(job.id)

    assert result is not None
    assert result.status == Status.SUCCEEDED


def test_run_job_fails_with_retry():
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"should_fail": True},
    )

    repository.create(job)

    result = run_job(job, repository)

    assert result is not None
    assert result.attempts == 1
    assert result.status == Status.PENDING
    assert result.last_error == "Job processing failed"


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