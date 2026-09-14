from job_platform.models import Status
from job_platform.queue import JobQueue
from job_platform.repository import JobRepository

def process_job(job):
    print(f"Processing job {job.id}")

    if job.payload.get("should_fail"):
        raise RuntimeError("Job processing failed")

    print(f"Job {job.id} succeeded")


def run_job(job, repository):
    repository.update_status(job.id, Status.RUNNING)

    try:
        process_job(job)
    except Exception as exc:
        print(f"Job {job.id} failed: {exc}")
        repository.update_status(job.id, Status.FAILED)
        return

    repository.update_status(job.id, Status.SUCCEEDED)


def handle_next_job(queue, repository):
    job_id = queue.dequeue()

    print(f"Received job {job_id}")

    job = repository.get(job_id)

    if job is None:
        print(f"Job {job_id} not found")
        queue.complete(job_id)
        return

    run_job(job, repository)
    queue.complete(job_id)


def run_worker():
    queue = JobQueue()
    repository = JobRepository()

    print("Worker started.")

    while True:
        print("Waiting for jobs...")

        handle_next_job(queue, repository)


if __name__ == "__main__":
    run_worker()