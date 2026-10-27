from job_platform.models import Status
from job_platform.job_queue import JobQueue
from job_platform.repository import JobRepository
from job_platform.lease_heartbeat import LeaseHeartbeat

class LeaseLostError(Exception):
    """Raised when a worker no longer has a valid job lease."""


def process_job(job):
    print(f"Processing job {job.id}")

    if job.payload.get("should_fail"):
        raise RuntimeError("Job processing failed")

    print(f"Job {job.id} succeeded")


def run_job(job, repository, queue, lease_token):
    job = repository.start_attempt(job.id)
    
    with LeaseHeartbeat(queue, job.id, lease_token) as heartbeat:
        try:
            process_job(job)
        except Exception as exc:
            # Never persist a result if the heartbeat detected lease loss.
            if heartbeat.lease_lost.is_set():
                raise LeaseLostError(
                    f"Lost lease for job {job.id}"
                ) from exc
            
            
            job.last_error = str(exc)

            if job.attempts < job.max_attempts:
                job.status = Status.PENDING
            else:
                job.status = Status.FAILED

            if not repository.update_job(job):
                raise LeaseLostError(
                    f"Job {job.id} was updated by another worker"
                )

            return job

        # Check lease status before persisting success.
        if heartbeat.lease_lost.is_set():
            raise LeaseLostError(f"Lost lease for job {job.id}")

        job.status = Status.SUCCEEDED
        job.last_error = None

        if not repository.update_job(job):
            raise LeaseLostError(
                f"Job {job.id} was updated by another worker"
            )

        return job


def handle_next_job(queue, repository):
    job_id, lease_token = queue.dequeue()
    print(f"Received job {job_id}")

    job = repository.get(job_id)

    if job is None:
        print(f"Job {job_id} not found")
        queue.complete(job_id, lease_token)
        return

    try:
        result = run_job(job, repository, queue, lease_token)
    except LeaseLostError:
        print(f"Lease lost for job {job_id}; skipping completion")
        return

    completed = queue.complete(job_id, lease_token)

    if not completed:
        print(f"Could not complete job {job_id}: lease ownership lost")
        return

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