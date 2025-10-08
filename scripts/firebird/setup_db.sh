#!/bin/bash
# Setup Firebird database and schema using docker exec

set -e

echo "Creating database and schema in Firebird container..."

# Execute SQL commands via docker exec
docker compose exec -T firebird bash -c "cat <<'EOF' | /opt/firebird/bin/isql -user SYSDBA -password masterkey
CREATE DATABASE 'localhost:/firebird/data/production.fdb';
QUIT;
EOF"

echo "Database created, now creating schema..."

# Create the schema
docker compose exec -T firebird bash -c "/opt/firebird/bin/isql -user SYSDBA -password masterkey localhost:/firebird/data/production.fdb" < scripts/firebird/01_create_schema.sql

echo "Schema created successfully!"
