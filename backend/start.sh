#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
  echo "DATABASE_URL detected (Neon/managed Postgres). Skipping local pg_isready check."
else
  DB_HOST="${DB_HOST:-db}"
  DB_PORT="${DB_PORT:-5432}"
  echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
  until pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; do
    sleep 1
  done
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
