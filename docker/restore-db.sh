#!/bin/sh
set -eu

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-trustbond}"
DB_USER="${POSTGRES_USER:-postgres}"
DUMP_FILE="${DB_DUMP_FILE:-/backup/trustbond.sql}"

export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo "[restore] Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}"; do
  sleep 1
done

echo "[restore] Connected to Postgres."

TABLE_COUNT="$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")"
if [ "${TABLE_COUNT:-0}" -gt 0 ]; then
  echo "[restore] Database already has ${TABLE_COUNT} public tables. Skipping restore."
  exit 0
fi

if [ ! -f "${DUMP_FILE}" ]; then
  echo "[restore] Dump file not found: ${DUMP_FILE}"
  exit 1
fi

MAGIC="$(head -c 5 "${DUMP_FILE}" || true)"
if [ "${MAGIC}" = "PGDMP" ]; then
  echo "[restore] Detected custom-format PostgreSQL dump. Restoring with pg_restore..."
  pg_restore \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    "${DUMP_FILE}"
else
  echo "[restore] Detected plain SQL dump. Restoring with psql..."
  psql \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -f "${DUMP_FILE}"
fi

echo "[restore] Restore completed successfully."
