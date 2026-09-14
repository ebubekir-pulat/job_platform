import uuid
import redis

QUEUE_NAME = "jobs:queue"
PROCESSING_QUEUE_NAME = "jobs:processing"

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
        job_id = self.redis.blmove(
            first_list=QUEUE_NAME, 
            second_list=PROCESSING_QUEUE_NAME, 
            timeout=0,
            src="RIGHT",
            dest="LEFT",
        )
        return uuid.UUID(job_id)

    def complete(self, job_id: uuid.UUID) -> None:
        self.redis.lrem(
            PROCESSING_QUEUE_NAME,
            1,
            str(job_id),
        )