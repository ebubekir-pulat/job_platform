from uuid import UUID

from job_platform.database import get_session
from job_platform.db_models import Job as JobDB
from job_platform.models import Job

class JobRepository:
    def create(self, job: Job) -> Job:
        db_job = JobDB(
            id=job.id,
            type=job.type,
            payload=job.payload,
            status=job.status.value,
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
        )