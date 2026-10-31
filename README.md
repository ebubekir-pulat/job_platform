# Job Platform

Disclaimer: THIS README WAS WRITTEN BY ChatGPT, may include inaccuracies. This is a learning project.

A distributed job processing system built with **Python, FastAPI, PostgreSQL, and Redis**.

The platform exposes an API for submitting and tracking jobs, while independent workers claim and process jobs asynchronously. It implements job retries, expiring leases, lease renewal, and fencing tokens to handle worker failures and concurrent processing safely.

## Features

- **REST API** — Submit jobs and retrieve their status using FastAPI.
- **Persistent job storage** — Store job data and execution state in PostgreSQL using SQLAlchemy.
- **Redis-backed queue** — Manage pending and processing jobs using Redis lists.
- **Atomic job claiming** — Use Redis Lua scripts to atomically move jobs into processing and register their leases.
- **Lease-based processing** — Assign each claimed job an expiring lease and unique ownership token.
- **Lease renewal** — Keep leases alive while jobs are being processed using a background heartbeat.
- **Crash recovery support** — Requeue jobs whose processing leases have expired.
- **Retries** — Retry failed jobs up to a configurable maximum number of attempts.
- **Fencing tokens** — Prevent stale workers from overwriting results from newer attempts.
- **Database migrations** — Manage schema changes with Alembic.
- **Containerized services** — Run the API, worker, PostgreSQL, and Redis using Docker Compose.

## Architecture

The platform consists of four main services:

| Component | Responsibility |
|---|---|
| API | Accepts job submissions and provides job status |
| PostgreSQL | Stores job data, status, attempts, and fencing tokens |
| Redis | Holds pending and processing queues, lease expiry times, and lease ownership |
| Worker | Claims jobs, executes them, and persists their results |

### Job lifecycle

1. A client submits a job through the API.
2. The API creates a job record in PostgreSQL and adds its ID to the Redis queue.
3. A worker atomically claims the job and moves it into the processing queue.
4. Redis registers a lease expiry time and a unique ownership token for the worker.
5. The worker increments the job's attempt count and fencing token, then processes the job.
6. A background heartbeat periodically renews the lease while processing continues.
7. The worker persists the result only if its attempt and fencing token still match the current database state.
8. The worker completes the Redis queue entry if it still owns the lease.
9. Failed jobs are requeued while retry attempts remain; otherwise, they are marked as failed.

### Reliability mechanisms

**Atomic claiming**

Redis Lua scripts ensure that claiming a job, moving it into the processing queue, and registering its lease happen as one atomic operation.

**Leases and heartbeats**

A lease gives a worker temporary ownership of a job. If a worker stops renewing its lease, the lease expires and the job becomes eligible for recovery.

**Fencing tokens**

Each new attempt increments a monotonically increasing fencing token. Database updates are conditional on the attempt count and fencing token, preventing an older worker from persisting a result after a newer attempt has started.

**Retry handling**

Failed jobs return to the pending queue until their maximum attempt count is reached. The final failure is persisted with its error message.

## Technology Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- Redis Lua scripting
- Pydantic
- Docker and Docker Compose
- uv
- pytest

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Run the platform

Clone the repository:

```bash
git clone https://github.com/ebubekir-pulat/job_platform.git
cd job_platform
```

Start the services:

```bash
docker compose up --build
```

Docker Compose starts PostgreSQL and Redis, runs database migrations, and then starts the API and worker.

The API is available at:

```text
http://localhost:8000
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

To stop the services:

```bash
docker compose down
```

To stop the services and remove the PostgreSQL data volume:

```bash
docker compose down -v
```

**Warning:** The `-v` option deletes the persisted database volume.

### Configuration

Docker Compose supports the following environment variables:

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `job_platform` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `job_platform` | PostgreSQL password |
| `POSTGRES_DB` | `job_platform` | PostgreSQL database name |

The API and worker use `REDIS_HOST` and `REDIS_PORT` to connect to Redis. Inside Docker Compose, these are configured to use the Redis service.

For local development, the application also reads `DATABASE_URL` from the environment.

## API Usage

### Submit a job

`POST /jobs`

Example request:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "type": "example_job",
    "payload": {
      "message": "Hello, world!"
    }
  }'
```

The API creates a job and returns its details, including its generated ID and initial status.

### Retrieve a job

`GET /jobs/{job_id}`

Example:

```bash
curl http://localhost:8000/jobs/<job-id>
```

The response includes the job's current status, attempt count, maximum attempts, fencing token, and most recent error if one exists.

### Job statuses

| Status | Description |
|---|---|
| `PENDING` | Waiting to be processed or retried |
| `RUNNING` | Currently being processed |
| `SUCCEEDED` | Processing completed successfully |
| `FAILED` | Processing failed and no retries remain |

## Running Tests

Install dependencies, including development dependencies:

```bash
uv sync --all-groups
```

Ensure PostgreSQL and Redis are running and that the test environment's database and Redis connection settings are configured.

Run the test suite:

```bash
uv run pytest -v
```

The tests cover job creation and retrieval, queue operations, atomic claiming, lease renewal, expired-lease recovery, retry handling, worker execution, and fencing-token protection.

## Project Structure

```text
.
├── alembic/                 # Database migrations
├── src/
│   └── job_platform/
│       ├── database.py      # Database connection and sessions
│       ├── db_models.py     # SQLAlchemy models
│       ├── job_queue.py     # Redis queue and Lua scripts
│       ├── lease_heartbeat.py # Background lease renewal
│       ├── main.py          # FastAPI application
│       ├── models.py        # Pydantic models and job statuses
│       ├── repository.py    # Database operations
│       └── worker.py        # Job processing and worker loop
├── tests/                   # Automated tests
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pyproject.toml
└── uv.lock
```

## Scope and Limitations

This project focuses on learning and demonstrating distributed job processing concepts.

- The current `process_job` function is a demonstration handler, not a general-purpose task execution framework.
- Expired-lease recovery is implemented as a queue operation, but is not yet scheduled automatically by the worker loop.
- Redis persistence and production deployment hardening are outside the current scope.
- The API does not currently include authentication or authorization.