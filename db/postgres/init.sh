#!/bin/bash
set -e

echo "Running PostgreSQL migrations..."

psql -v ON_ERROR_STOP=1 --username postgres --dbname frauddb <<-EOSQL
    \i /docker-entrypoint-initdb.d/schema.sql
    \i /docker-entrypoint-initdb.d/analytics.sql
    \i /docker-entrypoint-initdb.d/seed.sql
EOSQL

echo "PostgreSQL migrations complete."

