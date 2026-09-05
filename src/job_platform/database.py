from sqlalchemy import create_engine
from sqlalchemy.orm import Session 

# Replace *password* with actual user password

DATABASE_URL = (
    "postgresql+psycopg://"
    "job_platform_user:*password*"
    "@localhost:5432/jobplatform_db"
)

engine = create_engine(DATABASE_URL)

def get_session() -> Session:
    return Session(engine)