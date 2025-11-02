#!/bin/bash
# ============================================
# Initialize Multi-Tenancy Database Schema
# ============================================

set -e

echo "🚀 Initializing Multi-Tenancy Schema..."

# Database connection parameters
export PGHOST="${POSTGRES_HOST:-localhost}"
export PGPORT="${POSTGRES_PORT:-5432}"
export PGUSER="${POSTGRES_USER:-postgres}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
export PGDATABASE="${POSTGRES_DB:-fraud_detection}"

echo "📊 Connecting to PostgreSQL at $PGHOST:$PGPORT/$PGDATABASE..."

# Apply multi-tenancy schema
echo "📝 Creating tenant tables..."
psql -v ON_ERROR_STOP=1 <<-EOSQL
    \i /docker-entrypoint-initdb.d/tenants_schema.sql
EOSQL

echo "✅ Multi-tenancy schema initialized successfully!"

# Show tenant summary
echo ""
echo "📋 Tenant Summary:"
psql -c "SELECT tenant_id, organization_name, subdomain, plan, status FROM tenants;"

echo ""
echo "👤 Tenant Users:"
psql -c "SELECT t.organization_name, u.email, u.full_name, u.role FROM tenant_users u JOIN tenants t ON u.tenant_id = t.tenant_id;"

echo ""
echo "✨ Done! You can now:"
echo "   1. Sign up new tenants via API: POST /api/v1/tenants/signup"
echo "   2. Login: POST /api/v1/tenants/login"
echo "   3. Use demo credentials:"
echo "      Email: admin@demo.com"
echo "      Password: DemoPass123!"
echo ""

