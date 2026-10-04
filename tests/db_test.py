import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    f"host=localhost port=5432 dbname=jobplatform_db user=job_platform_user password={os.environ["DATABASE_PASS"]}"
)

print("Connected to PostgreSQL!")
conn.close()