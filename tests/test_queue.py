import uuid

from job_platform.queue import JobQueue

def test_enqueue_and_dequeue():
    queue = JobQueue()

    job_id = uuid.uuid4()

    queue.enqueue(job_id)

    result = queue.dequeue()

    assert result == job_id