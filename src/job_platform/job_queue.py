import uuid
import redis
import time

LEASE_KEY = "jobs:processing_leases"
LEASE_OWNER_KEY = "jobs:processing:owners"
LEASE_SECONDS = 300
POLL_INTERVAL_SECONDS = 0.25

QUEUE_NAME = "jobs:queue"
PROCESSING_QUEUE_NAME = "jobs:processing"

CLAIM_SCRIPT = """
local job_id = redis.call(
    'LMOVE',
    KEYS[1],
    KEYS[2],
    'RIGHT',
    'LEFT'
)

if not job_id then
    return nil
end

local token = ARGV[2]

local now = redis.call('TIME')
local timestamp = tonumber(now[1])
    + tonumber(now[2]) / 1000000

redis.call(
    'ZADD',
    KEYS[3],
    timestamp + tonumber(ARGV[1]),
    job_id
)

redis.call('HSET', KEYS[4], job_id, token)

return {job_id, token}
"""

COMPLETE_SCRIPT = """
local current_token = redis.call(
    'HGET',
    KEYS[3],
    ARGV[2]
)

if not current_token or current_token ~= ARGV[1] then
    return 0
end

redis.call('LREM', KEYS[1], 1, ARGV[2])
redis.call('ZREM', KEYS[2], ARGV[2])
redis.call('HDEL', KEYS[3], ARGV[2])

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
    redis.call('HDEL', KEYS[4], job_id)

    if removed == 1 then
        redis.call('LPUSH', KEYS[1], job_id)
        table.insert(recovered, job_id)
    end
end

return recovered
"""

RENEW_LEASE_SCRIPT = """
local current_token = redis.call(
    'HGET',
    KEYS[2],
    ARGV[1]
)

if not current_token or current_token ~= ARGV[2] then
    return 0
end

local score = redis.call('ZSCORE', KEYS[1], ARGV[1])

if not score then
    return 0
end

local now = redis.call('TIME')
local timestamp = tonumber(now[1])
    + tonumber(now[2]) / 1000000

redis.call(
    'ZADD',
    KEYS[1],
    timestamp + tonumber(ARGV[3]),
    ARGV[1]
)

return 1
"""


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


    def dequeue(self) -> tuple[uuid.UUID, str]:
        while True:
            token = str(uuid.uuid4())

            result = self.redis.eval(
                CLAIM_SCRIPT,
                4,
                QUEUE_NAME,
                PROCESSING_QUEUE_NAME,
                LEASE_KEY,
                LEASE_OWNER_KEY,
                LEASE_SECONDS,
                token,
            )

            if result is not None:
                job_id, lease_token = result
                return uuid.UUID(job_id), lease_token

            time.sleep(POLL_INTERVAL_SECONDS)


    def complete(self, job_id: uuid.UUID, lease_token: str) -> bool:
        completed = self.redis.eval(
            COMPLETE_SCRIPT,
            3,
            PROCESSING_QUEUE_NAME,
            LEASE_KEY,
            LEASE_OWNER_KEY,
            lease_token,
            str(job_id),
        )

        return completed == 1


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
            4,
            QUEUE_NAME,
            PROCESSING_QUEUE_NAME,
            LEASE_KEY,
            LEASE_OWNER_KEY,
            limit,
        )

        return [uuid.UUID(job_id) for job_id in recovered]


    def renew_lease(self, job_id: uuid.UUID, lease_token: str) -> bool:
        renewed = self.redis.eval(
            RENEW_LEASE_SCRIPT,
            2,
            LEASE_KEY,
            LEASE_OWNER_KEY,
            str(job_id),
            lease_token,
            LEASE_SECONDS,
        )

        return renewed == 1