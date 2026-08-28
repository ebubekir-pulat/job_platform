import uuid
import pytest
from pydantic import ValidationError

from app.models import Job, Status

def test_valid_job_can_be_constructed():
    job = Job(
        id="123e4567-e89b-12d3-a456-426614174000",
        type="sleep",
        payload={"seconds": 10},
        status=Status.PENDING,
    )

    assert isinstance(job.id, uuid.UUID)
    assert job.type == "sleep"
    assert job.payload == {"seconds": 10}
    assert job.status == Status.PENDING

def test_invalid_status_is_rejected():
    with pytest.raises(ValidationError):
        Job(
            id="123e4567-e89b-12d3-a456-426614174000",
            type="model_training_job",
            payload={"epochs": 10},
            status=502,
        )