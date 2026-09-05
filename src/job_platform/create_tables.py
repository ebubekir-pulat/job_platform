from job_platform.database import engine
from job_platform.db_models import Base

Base.metadata.create_all(engine)