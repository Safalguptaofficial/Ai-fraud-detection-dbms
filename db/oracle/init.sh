#!/bin/bash
set -e

echo "Running Oracle migrations..."

sqlplus -s admin/password@XE <<-EOF
    @/docker-entrypoint-initdb.d/schema.sql
    @/docker-entrypoint-initdb.d/triggers.sql
    @/docker-entrypoint-initdb.d/seed.sql
    COMMIT;
    EXIT;
EOF

echo "Oracle migrations complete."

