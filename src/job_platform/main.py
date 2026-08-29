from fastapi import FastAPI, HTTPException
from uuid import UUID

from job_platform.models import Job, JobCreate
from job_platform.repository import JobRepository

app = FastAPI()

repository = JobRepository()

@app.get("/")
async def root():
    return {"message": "Job Platform API"}

@app.post("/jobs", response_model=Job)
async def create_job(job_data: JobCreate):
    job = Job(
        type=job_data.type,
        payload=job_data.payload,
    )

    return repository.create(job)

@app.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: UUID):
    job = repository.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job