import uuid
import redis

QUEUE_NAME = "jobs:queue"

class JobQueue:
    def __init__(self):
        self.redis = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True,
        )

    def enqueue(self, job_id: uuid.UUID) -> None:
        self.redis.rpush(QUEUE_NAME, str(job_id))

    def dequeue(self) -> uuid.UUID:
        job_id = self.redis.lpop(QUEUE_NAME)

        if job_id is None:
            raise RuntimeError("Queue is empty")

        return uuid.UUID(job_id)
