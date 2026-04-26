# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=120

# install build tools + system deps for opencv, pytesseract, psycopg2
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt-get update \
  && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       tesseract-ocr \
       libgl1 \
       libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# copy and install python requirements
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
  python -m pip install --upgrade pip setuptools wheel \
  && python -m pip install --prefer-binary -r requirements.txt

# copy application code
COPY . .

# runtime folders required by FastAPI StaticFiles and local evidence fallback
RUN mkdir -p uploads/evidence

# expose port and provide default command
EXPOSE 8000

# Run DB migrations then start the server.
# DATABASE_URL must be set as an environment variable (e.g. via Render dashboard).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
