import uuid

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    type: Mapped[str] = mapped_column(String)

    payload: Mapped[dict] = mapped_column(JSON)

    status: Mapped[int] = mapped_column(Integer)

    attempts: Mapped[int] = mapped_column(Integer, default=0)

    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    last_error: Mapped[str | None] = mapped_column(String, nullable=True)