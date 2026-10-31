import uuid

from job_platform.models import Job, Status
from job_platform.repository import JobRepository

def test_get_existing_job():
    repository = JobRepository()
    
    job = Job(
        type="model_training",
        payload={"epochs": 10},
    )

    repository.create(job)

    result = repository.get(job.id)

    assert result == job

def test_get_nonexistent_job_returns_none():
    repository = JobRepository()

    job_id = uuid.uuid4()

    result = repository.get(job_id)

    assert result is None

def test_update_status():
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    repository.create(job)

    repository.update_status(job.id, Status.RUNNING)

    result = repository.get(job.id)

    assert result is not None
    assert result.status == Status.RUNNING


def test_update_job_rejects_non_running_job():
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    stale_job = repository.create(job)
    stale_job = repository.get(stale_job.id)

    assert stale_job is not None

    repository.update_status(stale_job.id, Status.FAILED)
    stale_job.status = Status.SUCCEEDED

    updated = repository.update_job(stale_job)

    assert updated is False

    current_job = repository.get(stale_job.id)
    assert current_job is not None
    assert current_job.status == Status.FAILED


def test_update_job_rejects_stale_attempts_no_status_diff():
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    stale_job = repository.create(job)
    stale_job = repository.get(stale_job.id)

    assert stale_job is not None

    repository.start_attempt(stale_job.id)
    stale_job.status = Status.RUNNING

    updated = repository.update_job(stale_job)

    assert updated is False

    current_job = repository.get(stale_job.id)
    assert current_job is not None
    assert current_job.status == Status.RUNNING
    assert current_job.attempts == stale_job.attempts + 1


def test_update_job_rejects_stale_attempts_status_diff():
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    stale_job = repository.create(job)
    stale_job = repository.get(stale_job.id)

    assert stale_job is not None

    repository.start_attempt(stale_job.id)
    stale_job.status = Status.SUCCEEDED

    updated = repository.update_job(stale_job)

    assert updated is False

    current_job = repository.get(stale_job.id)
    assert current_job is not None
    assert current_job.status == Status.RUNNING
    assert current_job.attempts == stale_job.attempts + 1


def test_update_job_rejects_stale_fencing_token_with_diff_status():
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    repository.create(job)

    stale_job = repository.start_attempt(job.id)

    # Simulate a newer claim.
    current_job = repository.start_attempt(job.id)

    assert current_job.fencing_token == stale_job.fencing_token + 1

    stale_job.status = Status.SUCCEEDED

    updated = repository.update_job(stale_job)

    assert updated is False

    result = repository.get(job.id)

    assert result is not None
    assert result.status == Status.RUNNING
    assert result.fencing_token == current_job.fencing_token


def test_update_job_rejects_stale_fencing_token_with_same_status():
    repository = JobRepository()

    job = Job(
        type="test_job",
        payload={"message": "hello"},
    )

    repository.create(job)

    stale_job = repository.start_attempt(job.id)

    # Simulate a newer claim.
    current_job = repository.start_attempt(job.id)

    assert current_job.fencing_token == stale_job.fencing_token + 1

    updated = repository.update_job(stale_job)

    assert updated is False

    result = repository.get(job.id)

    assert result is not None
    assert result.status == Status.RUNNING
    assert result.fencing_token == current_job.fencing_token