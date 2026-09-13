#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load env vars
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
else
    echo "Error: .env file not found. Copy .env.example to .env and fill in your credentials."
    exit 1
fi

DB_USER="${DATABASE_USER:?DATABASE_USER not set in .env}"
DB_PASS="${DATABASE_PASSWORD:?DATABASE_PASSWORD not set in .env}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:?DATABASE_NAME not set in .env}"

export PGPASSWORD="$DB_PASS"

echo "==> Dropping existing database '$DB_NAME' (if exists)..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres -c \
    "DROP DATABASE IF EXISTS $DB_NAME"

echo "==> Creating database '$DB_NAME'..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres -c \
    "CREATE DATABASE $DB_NAME"

echo "==> Applying schema..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$SCRIPT_DIR/schema.sql"

echo "==> Seeding data..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$SCRIPT_DIR/seed.sql"

echo "==> Done! Database '$DB_NAME' is ready."
