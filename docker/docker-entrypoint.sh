#!/bin/sh
# Keep this file checked out with LF line endings for Linux containers.
# Validate Supabase/Postgres configuration, then start the Flask application.

set -e

if [ -z "$DATABASE_URL" ]; then
  echo "[entrypoint] DATABASE_URL is required. Set it to your Supabase Postgres connection string for normal runtime."
  exit 1
fi

if [ -z "$FLASK_SECRET_KEY" ]; then
  echo "[entrypoint] FLASK_SECRET_KEY is required in production."
  exit 1
fi

mkdir -p /app/database
mkdir -p /app/uploads

CERT_PATH="/app/database/cert.pem"
KEY_PATH="/app/database/key.pem"

if [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
  echo "[entrypoint] Generating self-signed certificate for local HTTPS..."
  openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$CERT_PATH" \
    -keyout "$KEY_PATH" \
    -days 365 \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:nexus.local,IP:127.0.0.1"
  echo "[entrypoint] Certificate generated."
fi

echo "[entrypoint] Starting Flask application..."
python -c "from app import init_db; init_db()"
exec gunicorn \
  --bind "${FLASK_RUN_HOST:-0.0.0.0}:5000" \
  --certfile "$CERT_PATH" \
  --keyfile "$KEY_PATH" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads "${WEB_THREADS:-4}" \
  --timeout "${WEB_TIMEOUT:-60}" \
  "app:app"
