from job_platform.models import Job
from job_platform.worker import process_job

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