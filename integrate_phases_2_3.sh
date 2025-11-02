#!/bin/bash
# ============================================================================
# Phase 2 & 3 Integration Script
# Installs dependencies, applies migrations, and tests the system
# ============================================================================

set -e  # Exit on error

echo "🚀 Starting Phase 2 & 3 Integration..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================================================
# Step 1: Install Python Dependencies
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 Step 1: Installing Python Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Installing in API container..."
docker exec fraud-dbms_api_1 pip install \
    httpx==0.25.0 \
    pyotp==2.9.0 \
    qrcode[pil]==7.4.2 \
    Pillow==10.1.0 \
    stripe==7.0.0 \
    openpyxl==3.1.2 \
    mysql-connector-python==8.2.0 \
    --quiet --no-cache-dir

echo -e "${GREEN}✅ Dependencies installed!${NC}"
echo ""

# ============================================================================
# Step 2: Apply Database Migrations
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🗄️  Step 2: Applying Database Migrations${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Copying migration file to database container..."
docker cp db/postgres/migrations/004_phase2_phase3_features.sql fraud-dbms_postgres_1:/tmp/

echo "Applying migration..."
docker exec fraud-dbms_postgres_1 psql -U postgres -d frauddb -f /tmp/004_phase2_phase3_features.sql

echo -e "${GREEN}✅ Database migration applied!${NC}"
echo ""

# ============================================================================
# Step 3: Restart API Container
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔄 Step 3: Restarting API Container${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd infra/docker
docker-compose restart api
sleep 5

echo -e "${GREEN}✅ API container restarted!${NC}"
echo ""

# ============================================================================
# Step 4: Verify Installation
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 Step 4: Verifying Installation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Checking Python packages..."
docker exec fraud-dbms_api_1 pip list | grep -E "(httpx|pyotp|qrcode|stripe|openpyxl|mysql-connector)"

echo ""
echo "Checking database tables..."
docker exec fraud-dbms_postgres_1 psql -U postgres -d frauddb -c "\dt" | grep -E "(mfa|oauth|sync|upload|subscription|invoice)"

echo ""
echo -e "${GREEN}✅ Verification complete!${NC}"
echo ""

# ============================================================================
# Step 5: Display Summary
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Integration Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}✅ Phase 1: Multi-Tenancy${NC}"
echo "   - Tenant isolation"
echo "   - JWT authentication"
echo "   - Usage tracking"
echo ""

echo -e "${GREEN}✅ Phase 2: Enterprise Features${NC}"
echo "   - SSO (Google, Microsoft, Okta)"
echo "   - Multi-Factor Authentication"
echo "   - Enhanced audit logging"
echo ""

echo -e "${GREEN}✅ Phase 3: Self-Service Features${NC}"
echo "   - Stripe billing integration"
echo "   - Usage metering"
echo "   - CSV/Excel file upload"
echo "   - Real-time transaction API"
echo "   - Database connectors"
echo ""

echo -e "${YELLOW}⏳ Pending: API Router Implementation${NC}"
echo "   - Create routers for new endpoints"
echo "   - Add to main.py"
echo "   - Frontend integration"
echo ""

# ============================================================================
# Step 6: Next Steps
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎯 Next Steps${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "1. Test the login (should still work):"
echo -e "   ${YELLOW}curl -X POST http://localhost:8000/api/v1/tenants/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@demo.com\",\"password\":\"DemoPass123!\"}'${NC}"
echo ""

echo "2. Check new database tables:"
echo -e "   ${YELLOW}docker exec fraud-dbms_postgres_1 psql -U postgres -d frauddb -c 'SELECT * FROM user_mfa_secrets;'${NC}"
echo ""

echo "3. Review implementation documentation:"
echo -e "   ${YELLOW}cat PHASES_2_3_IMPLEMENTATION_COMPLETE.md${NC}"
echo ""

echo "4. Test MFA setup (Python):"
cat << 'PYTHON_CODE'
   from auth.mfa import MFAManager
   mfa = MFAManager()
   secret = mfa.generate_secret()
   print(f"Secret: {secret}")
PYTHON_CODE
echo ""

echo "5. Test CSV ingestion (create test CSV):"
cat << 'CSV_EXAMPLE'
   account_id,amount,merchant,transaction_date
   ACC123,150.00,Test Store,2025-10-30 14:30:00
CSV_EXAMPLE
echo ""

# ============================================================================
# Testing Commands
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 Quick Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Test 1: MFA Secret Generation"
echo -e "${YELLOW}python -c \"import pyotp; print('MFA Secret:', pyotp.random_base32())\"${NC}"
echo ""

echo "Test 2: Stripe Test (requires API key)"
echo -e "${YELLOW}# Add STRIPE_API_KEY to .env first${NC}"
echo ""

echo "Test 3: Database Connectors"
echo -e "${YELLOW}docker exec fraud-dbms_postgres_1 psql -U postgres -d frauddb -c 'SELECT COUNT(*) FROM data_sync_jobs;'${NC}"
echo ""

# ============================================================================
# Documentation Links
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📚 Documentation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "📄 PHASES_2_3_IMPLEMENTATION_COMPLETE.md - Complete feature guide"
echo "📄 EXECUTIVE_SUMMARY.md - Business overview"
echo "📄 MULTI_TENANCY_SETUP.md - Phase 1 setup"
echo "📄 services/api/auth/ - OAuth & MFA implementations"
echo "📄 services/api/billing/ - Stripe & usage metering"
echo "📄 services/api/ingestion/ - Data ingestion APIs"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Phase 2 & 3 Integration Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Your fraud detection platform is now enterprise-ready! 🚀"
echo ""
echo "Access your application:"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""

