from uuid import UUID

from job_platform.database import get_session
from job_platform.db_models import Job as JobDB
from job_platform.models import Job, Status

class JobRepository:
    def create(self, job: Job) -> Job:
        db_job = JobDB(
            id=job.id,
            type=job.type,
            payload=job.payload,
            status=job.status.value,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            last_error=job.last_error,
        )

        with get_session() as session:
            session.add(db_job)
            session.commit()

        return job

    def get(self, job_id: UUID) -> Job | None:
        with get_session() as session:
            db_job = session.get(JobDB, job_id)

            if db_job is None:
                return None
        
            return Job(
                id=db_job.id,
                type=db_job.type,
                payload=db_job.payload,
                status=db_job.status,
                attempts=db_job.attempts,
                max_attempts=db_job.max_attempts,
                last_error=db_job.last_error,
            )

    def update_status(self, job_id: UUID, status: Status) -> None:
        with get_session() as session:
            db_job = session.get(JobDB, job_id)

            if db_job is None:
                raise ValueError(f"Job {job_id} not found")

            db_job.status = status.value
            session.commit()

    def start_attempt(self, job_id: UUID) -> Job:
        with get_session() as session:
            db_job = session.get(JobDB, job_id)

            if db_job is None:
                raise ValueError(f"Job {job_id} not found")

            db_job.attempts += 1
            db_job.status = Status.RUNNING.value

            session.commit()
            session.refresh(db_job)

            return Job(
                id=db_job.id,
                type=db_job.type,
                payload=db_job.payload,
                status=db_job.status,
                attempts=db_job.attempts,
                max_attempts=db_job.max_attempts,
                last_error=db_job.last_error,
            )

    def update_job(self, job: Job) -> None:
        with get_session() as session:
            db_job = session.get(JobDB, job.id)

            if db_job is None:
                raise ValueError(f"Job {job.id} not found")

            db_job.status = job.status.value
            db_job.attempts = job.attempts
            db_job.last_error = job.last_error

            session.commit()