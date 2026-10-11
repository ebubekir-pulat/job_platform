import uuid
import redis

import time

LEASE_KEY = "jobs:processing_leases"
LEASE_SECONDS = 300
POLL_INTERVAL_SECONDS = 0.25

CLAIM_SCRIPT = """
local job_id = redis.call(
    'LMOVE',
    KEYS[1],
    KEYS[2],
    'RIGHT',
    'LEFT'
)

if job_id then
    local now = redis.call('TIME')
    local timestamp = tonumber(now[1])
        + tonumber(now[2]) / 1000000

    redis.call(
        'ZADD',
        KEYS[3],
        timestamp + tonumber(ARGV[1]),
        job_id
    )
end

return job_id
"""

COMPLETE_SCRIPT = """
redis.call('LREM', KEYS[1], 1, ARGV[1])
redis.call('ZREM', KEYS[2], ARGV[1])
return 1
"""

RECOVER_SCRIPT = """
local now = redis.call('TIME')
local timestamp = tonumber(now[1])
    + tonumber(now[2]) / 1000000

local expired_jobs = redis.call(
    'ZRANGE',
    KEYS[3],
    '-inf',
    timestamp,
    'BYSCORE',
    'LIMIT',
    0,
    tonumber(ARGV[1])
)

local recovered = {}

for _, job_id in ipairs(expired_jobs) do
    local removed = redis.call(
        'LREM',
        KEYS[2],
        1,
        job_id
    )

    redis.call('ZREM', KEYS[3], job_id)

    if removed == 1 then
        redis.call('LPUSH', KEYS[1], job_id)
        table.insert(recovered, job_id)
    end
end

return recovered
"""

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
        while True:
            job_id = self.redis.eval(
                CLAIM_SCRIPT,
                3,
                QUEUE_NAME,
                PROCESSING_QUEUE_NAME,
                LEASE_KEY,
                LEASE_SECONDS,
            )

            if job_id is not None:
                return uuid.UUID(job_id)

            time.sleep(POLL_INTERVAL_SECONDS)

    def complete(self, job_id: uuid.UUID) -> None:
        self.redis.eval(
            COMPLETE_SCRIPT,
            2,
            PROCESSING_QUEUE_NAME,
            LEASE_KEY,
            str(job_id),
        )

    def get_processing_jobs(self) -> list[uuid.UUID]:
        job_ids = self.redis.lrange(
            PROCESSING_QUEUE_NAME,
            0,
            -1,
        )

        return [uuid.UUID(job_id) for job_id in job_ids]

    def recover_expired_jobs(self, limit: int = 100) -> list[uuid.UUID]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        recovered = self.redis.eval(
            RECOVER_SCRIPT,
            3,
            QUEUE_NAME,
            PROCESSING_QUEUE_NAME,
            LEASE_KEY,
            limit,
        )

        return [uuid.UUID(job_id) for job_id in recovered]