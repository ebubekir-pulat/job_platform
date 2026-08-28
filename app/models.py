from pydantic import BaseModel, ConfigDict
import uuid
from enum import IntEnum

# Define Status Enum
class Status(IntEnum):
    PENDING = 0
    RUNNING = 1
    SUCCEEDED = 2
    FAILED = 3

class Job(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict
    status: Status