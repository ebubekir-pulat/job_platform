import uuid
import redis

QUEUE_NAME = "jobs:queue"

class JobQueue:
    def __init__(self):
        self.redis = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True,
            socket_timeout=None,
        )

    def enqueue(self, job_id: uuid.UUID) -> None:
        self.redis.rpush(QUEUE_NAME, str(job_id))

    def dequeue(self) -> uuid.UUID:
        _, job_id = self.redis.blpop(QUEUE_NAME, timeout=0)
        return uuid.UUID(job_id)
