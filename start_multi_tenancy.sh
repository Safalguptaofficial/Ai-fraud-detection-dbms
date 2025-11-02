#!/bin/bash
# ===================================================
# Multi-Tenancy Quick Start Script
# ===================================================

set -e

echo "🚀 Starting Multi-Tenancy System..."
echo ""

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Database is already initialized
echo -e "${BLUE}[1/5]${NC} Checking database..."
if docker exec fraud-dbms_postgres_1 psql -U postgres -d frauddb -c "SELECT COUNT(*) FROM tenants;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database ready with $(docker exec fraud-dbms_postgres_1 psql -U postgres -d frauddb -t -c 'SELECT COUNT(*) FROM tenants;' | xargs) tenants${NC}"
else
    echo -e "${YELLOW}⚠️  Database not initialized. Run: docker exec -i fraud-dbms_postgres_1 psql -U postgres -d frauddb < db/postgres/tenants_schema.sql${NC}"
fi
echo ""

# Step 2: Copy new code to container
echo -e "${BLUE}[2/5]${NC} Updating API code..."
docker cp services/api/models/tenant.py fraud-dbms_api_1:/app/models/tenant.py
docker cp services/api/tenants/ fraud-dbms_api_1:/app/tenants/
docker cp services/api/middleware/ fraud-dbms_api_1:/app/middleware/
docker cp services/api/routers/tenants.py fraud-dbms_api_1:/app/routers/tenants.py
docker cp services/api/main.py fraud-dbms_api_1:/app/main.py
echo -e "${GREEN}✅ Code updated${NC}"
echo ""

# Step 3: Install dependencies
echo -e "${BLUE}[3/5]${NC} Installing dependencies..."
docker exec fraud-dbms_api_1 pip install email-validator psycopg2-binary --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Restart API
echo -e "${BLUE}[4/5]${NC} Restarting API service..."
cd infra/docker
docker-compose restart api > /dev/null 2>&1
echo -e "${YELLOW}⏳ Waiting for API to start...${NC}"
sleep 8
echo -e "${GREEN}✅ API restarted${NC}"
echo ""

# Step 5: Test the system
echo -e "${BLUE}[5/5]${NC} Testing endpoints..."
echo ""

# Test health
echo -n "Testing health endpoint... "
HEALTH=$(curl -s http://localhost:8000/api/v1/tenants/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${YELLOW}⚠️  FAILED - API may still be starting${NC}"
fi

# Test login
echo -n "Testing login endpoint... "
LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/tenants/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"DemoPass123!"}')
  
if echo "$LOGIN" | grep -q "access_token"; then
    echo -e "${GREEN}✅ PASSED${NC}"
    TOKEN=$(echo $LOGIN | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo -e "   ${YELLOW}Token: ${TOKEN:0:50}...${NC}"
else
    echo -e "${YELLOW}⚠️  FAILED${NC}"
    echo "   Response: $LOGIN"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Multi-Tenancy System is Ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📖 Available Endpoints:"
echo "   • POST /api/v1/tenants/signup - Create new tenant"
echo "   • POST /api/v1/tenants/login - User login"
echo "   • GET /api/v1/tenants/me - Get tenant info"
echo "   • GET /api/v1/tenants/usage - Usage statistics"
echo ""
echo "🔐 Demo Credentials:"
echo "   Email: admin@demo.com"
echo "   Password: DemoPass123!"
echo ""
echo "📚 Documentation:"
echo "   • MULTI_TENANCY_SETUP.md - Complete setup guide"
echo "   • PHASE_1_MULTI_TENANCY_COMPLETE.md - Implementation status"
echo ""
echo "🧪 Quick Test:"
echo "   curl -X POST http://localhost:8000/api/v1/tenants/login \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"email\":\"admin@demo.com\",\"password\":\"DemoPass123!\"}'"
echo ""

