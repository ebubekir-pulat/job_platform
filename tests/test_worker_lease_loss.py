
from unittest.mock import patch

import pytest

from job_platform.models import Job, Status
from job_platform.repository import JobRepository
from job_platform.worker import LeaseLostError, run_job


def test_run_job_does_not_save_success_after_lease_loss():
    repository = JobRepository()
    job = Job(type="test_job", payload={"message": "hello"})
    repository.create(job)

    class FakeHeartbeat:
        def __init__(self, queue, job_id):
            self.lease_lost = __import__("threading").Event()

        def __enter__(self):
            # Simulate the lease being lost while processing.
            self.lease_lost.set()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    with patch(
        "job_platform.worker.LeaseHeartbeat",
        FakeHeartbeat,
    ):
        with pytest.raises(LeaseLostError):
            run_job(job, repository, queue=None)

    result = repository.get(job.id)
    assert result is not None
    assert result.status != Status.SUCCEEDED