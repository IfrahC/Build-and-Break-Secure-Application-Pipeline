#!/bin/sh
# Keep this file checked out with LF line endings for Linux containers.
# Initialise the SQLite database from init.sql if the DB file does not exist,
# then start the Flask application.

set -e

DB_PATH="/app/database/app.db"
SQL_PATH="/app/database/init.sql"

mkdir -p "$(dirname "$DB_PATH")"
mkdir -p /app/uploads

if [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] Initialising database from $SQL_PATH"
  sqlite3 "$DB_PATH" < "$SQL_PATH"
  echo "[entrypoint] Database initialised."
else
  echo "[entrypoint] Database already exists, skipping init."
fi

CERT_PATH="/app/database/cert.pem"
KEY_PATH="/app/database/key.pem"

if [ ! -f "$CERT_PATH" ]; then
  echo "[entrypoint] Generating self-signed certificate for nexus.local..."
  openssl req -x509 -newkey rsa:4096 -nodes -out "$CERT_PATH" -keyout "$KEY_PATH" -days 365 -subj "/CN=nexus.local"
  echo "[entrypoint] Certificate generated."
fi

echo "[entrypoint] Starting Flask application..."
exec python app.py
