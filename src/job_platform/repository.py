from uuid import UUID
from job_platform.models import Job

class JobRepository:
    def __init__(self):
        self.jobs: dict[UUID, Job] = {}

    def create(self, job: Job) -> Job:
        self.jobs[job.id] = job
        return job

    def get(self, job_id: UUID) -> Job | None:
        return self.jobs.get(job_id)