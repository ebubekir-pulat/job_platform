from job_platform.models import Status
from job_platform.queue import JobQueue
from job_platform.repository import JobRepository

def process_job(job):
    print(f"Processing job {job.id}")

    if job.payload.get("should_fail"):
        raise RuntimeError("Job processing failed")

    print(f"Job {job.id} succeeded")


def run_job(job, repository):
    job = repository.start_attempt(job.id)

    try:
        process_job(job)
    except Exception as exc:
        job.last_error = str(exc)

        if job.attempts < job.max_attempts:
            job.status = Status.PENDING
        else:
            job.status = Status.FAILED

        repository.update_job(job)
        return job

    job.status = Status.SUCCEEDED
    job.last_error = None

    repository.update_job(job)
    return job


def handle_next_job(queue, repository):
    job_id = queue.dequeue()
    print(f"Received job {job_id}")

    job = repository.get(job_id)

    if job is None:
        print(f"Job {job_id} not found")
        queue.complete(job_id)
        return

    result = run_job(job, repository)
    queue.complete(job_id)

    if result.status == Status.PENDING:
        queue.enqueue(job_id)


def run_worker():
    queue = JobQueue()
    repository = JobRepository()

    print("Worker started.")

    while True:
        print("Waiting for jobs...")

        handle_next_job(queue, repository)


if __name__ == "__main__":
    run_worker()