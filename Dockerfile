
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for better build caching
COPY pyproject.toml uv.lock ./

# Install project dependencies without installing the project itself
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source and migrations
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY README.md ./

# Install the project
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

CMD ["uvicorn", "job_platform.main:app", "--host", "0.0.0.0", "--port", "8000"]
