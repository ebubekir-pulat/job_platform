from fastapi.testclient import TestClient
import uuid
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