FROM python:3.11-slim

WORKDIR /app

# Install build tools & PostgreSQL client (for pg_isready)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure the data directory exists (holds incident_types.json)
RUN mkdir -p /app/data

# Ensure uploads directory exists (for static file serving)
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["sh", "-c", "\
  if [ -n \"${DB_HOST}\" ]; then \
    echo '>>> Waiting for PostgreSQL...' && \
    until pg_isready -h \"${DB_HOST}\" -p \"${DB_PORT:-5432}\" -U \"${DB_USER:-postgres}\" 2>/dev/null; do \
      echo 'Postgres not ready, retrying in 2s...'; \
      sleep 2; \
    done; \
  else \
    echo '>>> Using DATABASE_URL (external DB), skipping pg_isready...'; \
    sleep 3; \
  fi && \
  echo '>>> Running Alembic migrations...' && \
  alembic upgrade head && \
  echo '>>> Starting uvicorn...' && \
  uvicorn app.main:app --host 0.0.0.0 --port 8000"]