from fastapi.testclient import TestClient
import uuid
import redis

from job_platform.main import app
from job_platform.models import Status

client = TestClient(app)

def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Job Platform API"}


def test_create_job_with_valid_data():
    response = client.post(
        "/jobs",
        json={
            "type": "model_training_job",
            "payload": {"epochs": 10},
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify returned id is a valid UUID
    assert "id" in data
    job_id = uuid.UUID(data["id"])
    assert isinstance(job_id, uuid.UUID)

    #Verify the job starts as PENDING
    assert data["status"] == Status.PENDING

    assert data["type"] == "model_training_job"
    assert data["payload"] == {"epochs": 10}


def test_create_job_missing_type():
    response = client.post(
        "/jobs",
        json={
            "payload": {"epochs": 10},
        },
    )

    assert response.status_code == 422


def test_create_job_missing_payload():
    response = client.post(
        "/jobs",
        json={
            "type": "model_training_job",
        },
    )

    assert response.status_code == 422


def test_create_job_then_get_job():
    # Create a job
    create_response = client.post(
        "/jobs",
        json={
            "type": "model_training",
            "payload": {"epochs": 10},
        },
    )

    assert create_response.status_code == 200

    created_job = create_response.json()

    # Get created job
    job_id = created_job["id"]

    get_response = client.get(f"/jobs/{job_id}")

    assert get_response.status_code == 200
    assert get_response.json() == created_job


def test_get_nonexistent_job_returns_404():
    job_id = uuid.uuid4()

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_two_created_jobs_have_different_ids():
    response_1 = client.post(
        "/jobs",
        json={
            "type": "model_training",
            "payload": {"epochs": 10},
        },
    )

    response_2 = client.post(
        "/jobs",
        json={
            "type": "model_training",
            "payload": {"epochs": 5},
        },
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    job_1 = response_1.json()
    job_2 = response_2.json()

    assert job_1["id"] != job_2["id"]


def test_create_job_enqueues_job():
    response = client.post(
        "/jobs",
        json={
            "type": "model_training",
            "payload": {"epochs": 10},
        },
    )

    assert response.status_code == 200

    job = response.json()

    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    queued_job_id = redis_client.lpop("jobs:queue")

    assert queued_job_id == job["id"]