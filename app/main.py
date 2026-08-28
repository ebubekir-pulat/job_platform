from fastapi import FastAPI
from app.models import Job, JobCreate

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Job Platform API"}

@app.post("/jobs", response_model=Job)
async def create_job(job_data: JobCreate):
    job = Job(
        type=job_data.type,
        payload=job_data.payload,
    )

    return job