from pydantic import BaseModel, Field
import uuid
from enum import IntEnum

# Define Status Enum
class Status(IntEnum):
    PENDING = 0
    RUNNING = 1
    SUCCEEDED = 2
    FAILED = 3

class JobCreate(BaseModel):
    type: str
    payload: dict

class Job(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: str
    payload: dict
    status: Status = Status.PENDING