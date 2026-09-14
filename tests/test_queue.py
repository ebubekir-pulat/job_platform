import uuid

from job_platform.queue import JobQueue

def test_enqueue_and_dequeue():
    queue = JobQueue()

    job_id = uuid.uuid4()

    queue.enqueue(job_id)

    result = queue.dequeue()

    assert result == job_id

def test_get_processing_jobs():
    queue = JobQueue()

    job_id = uuid.uuid4()

    queue.enqueue(job_id)
    queue.dequeue()

    result = queue.get_processing_jobs()

    assert result == [job_id]

def test_complete_removes_job_from_processing():
    queue = JobQueue()

    job_id = uuid.uuid4()

    queue.enqueue(job_id)
    queue.dequeue()

    queue.complete(job_id)

    result = queue.get_processing_jobs()

    assert result == []