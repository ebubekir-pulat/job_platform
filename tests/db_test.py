import psycopg

# Replace *password* with actual user password

conn = psycopg.connect("host=localhost port=5432 dbname=jobplatform_db user=job_platform_user password=example")

print("Connected to PostgreSQL!")
conn.close()