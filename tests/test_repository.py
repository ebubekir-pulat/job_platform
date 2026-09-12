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