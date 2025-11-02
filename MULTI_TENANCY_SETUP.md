# 🏢 Multi-Tenancy Setup Guide

## Overview

This guide walks you through setting up and using the multi-tenancy system for converting your fraud detection demo into a production SaaS platform.

## ✅ What's Implemented

### 1. **Tenant Management**
- ✅ Tenant signup with organization details
- ✅ Subdomain-based tenant identification
- ✅ API key authentication
- ✅ JWT token authentication
- ✅ Automatic tenant context extraction

### 2. **Data Isolation**
- ✅ Row-Level Security (RLS) at database level
- ✅ Automatic tenant_id filtering
- ✅ Each tenant sees only their own data
- ✅ Database-level isolation policies

### 3. **User Management**
- ✅ Multi-user per tenant
- ✅ Role-based access control (ADMIN, MANAGER, ANALYST, VIEWER)
- ✅ Secure password hashing (bcrypt)
- ✅ User authentication and sessions

### 4. **Usage Tracking**
- ✅ Transaction limits per plan
- ✅ User limits
- ✅ API rate limiting
- ✅ Storage tracking
- ✅ Monthly usage reports

### 5. **Security**
- ✅ Password strength validation
- ✅ API key management
- ✅ JWT tokens with expiration
- ✅ Audit logging
- ✅ Database-level data isolation

---

## 🚀 Quick Start

### Step 1: Initialize Database

```bash
cd /Users/safalgupta/Desktop/AI_FRAUD_DETECTION

# Apply multi-tenancy schema
docker exec -i fraud-dbms_postgres_1 psql -U postgres -d fraud_detection < db/postgres/tenants_schema.sql

# Or use the initialization script
docker exec -i fraud-dbms_postgres_1 bash < db/postgres/init_tenants.sh
```

### Step 2: Restart API Server

```bash
# Restart the API to load new code
docker-compose -f infra/docker/docker-compose.yml restart api

# Check logs
docker logs fraud-dbms_api_1 -f
```

### Step 3: Test the System

The system is now ready! You can:

**Option A: Use Demo Tenant**
```bash
# Login with pre-created demo tenant
curl -X POST http://localhost:8000/api/v1/tenants/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.com",
    "password": "DemoPass123!"
  }'
```

**Option B: Sign Up New Tenant**
```bash
# Create your own tenant
curl -X POST http://localhost:8000/api/v1/tenants/signup \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Acme Corp",
    "subdomain": "acme",
    "admin_name": "John Doe",
    "admin_email": "john@acme.com",
    "admin_password": "SecurePass123!",
    "admin_phone": "+1234567890",
    "plan": "STARTER"
  }'
```

---

## 📖 API Endpoints

### **Tenant Management**

#### 1. Sign Up New Tenant
```bash
POST /api/v1/tenants/signup
```

**Request:**
```json
{
  "organization_name": "Your Company Name",
  "subdomain": "yourcompany",
  "admin_name": "Admin Name",
  "admin_email": "admin@yourcompany.com",
  "admin_password": "SecurePass123!",
  "admin_phone": "+1234567890",
  "plan": "STARTER"
}
```

**Response:**
```json
{
  "message": "Organization created successfully!",
  "tenant_id": "tenant_abc123",
  "organization_name": "Your Company Name",
  "subdomain": "yourcompany",
  "api_key": "fgk_live_...",
  "plan": "STARTER",
  "status": "TRIAL"
}
```

⚠️ **Save the API key! It's shown only once.**

---

#### 2. Login
```bash
POST /api/v1/tenants/login
```

**Request:**
```json
{
  "email": "admin@yourcompany.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "admin@yourcompany.com",
    "full_name": "Admin Name",
    "role": "ADMIN",
    "tenant_id": "tenant_abc123"
  },
  "tenant": {
    "tenant_id": "tenant_abc123",
    "organization_name": "Your Company Name",
    "plan": "STARTER"
  }
}
```

---

#### 3. Get Current Tenant Info
```bash
GET /api/v1/tenants/me
Authorization: Bearer <your_jwt_token>
```

---

#### 4. Get Usage Statistics
```bash
GET /api/v1/tenants/usage
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "tenant_id": "tenant_abc123",
  "transactions_this_month": 1250,
  "transactions_limit": 50000,
  "transactions_percentage": 2.5,
  "active_users": 3,
  "users_limit": 5,
  "storage_used_gb": 0.5,
  "storage_limit_gb": 10
}
```

---

#### 5. Create API Key
```bash
POST /api/v1/tenants/api-keys
Authorization: Bearer <your_jwt_token>
```

**Request:**
```json
{
  "key_name": "Production API Key",
  "scopes": ["read:transactions", "write:transactions", "read:alerts"],
  "rate_limit_per_minute": 100,
  "expires_days": 365
}
```

---

#### 6. Create User
```bash
POST /api/v1/tenants/users
Authorization: Bearer <your_jwt_token>
```

**Request:**
```json
{
  "email": "analyst@yourcompany.com",
  "password": "SecurePass123!",
  "full_name": "Jane Analyst",
  "role": "ANALYST"
}
```

---

## 🔐 Authentication Methods

The system supports 3 authentication methods:

### 1. **JWT Token (for web UI)**
```bash
# Login to get token
curl -X POST http://localhost:8000/api/v1/tenants/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass"}'

# Use token in requests
curl http://localhost:8000/api/v1/tenants/me \
  -H "Authorization: Bearer eyJhbGc..."
```

### 2. **API Key (for programmatic access)**
```bash
curl http://localhost:8000/api/v1/transactions \
  -H "X-API-Key: fgk_live_your_api_key_here"
```

### 3. **Subdomain (for multi-tenant SaaS)**
```bash
# Tenant identified by subdomain
curl http://acme.fraudguard.com/api/v1/transactions
```

---

## 📊 Subscription Plans

| Plan | Price | Transactions/Month | Users | Storage | API Calls/Min |
|------|-------|-------------------|-------|---------|---------------|
| **STARTER** | $99/mo | 50,000 | 5 | 10 GB | 100 |
| **PROFESSIONAL** | $299/mo | 250,000 | 20 | 50 GB | 500 |
| **ENTERPRISE** | Custom | Unlimited | Unlimited | Unlimited | Unlimited |

---

## 🔒 Row-Level Security

Data isolation is enforced at the PostgreSQL level using Row-Level Security (RLS):

```sql
-- Every query is automatically filtered by tenant_id
SELECT * FROM transactions;
-- Becomes: SELECT * FROM transactions WHERE tenant_id = 'current_tenant'
```

This means:
- ✅ **Impossible to access other tenant's data** (even with SQL injection)
- ✅ **No application-level filtering needed**
- ✅ **Database enforces isolation**

---

## 👥 User Roles

| Role | Permissions |
|------|-------------|
| **ADMIN** | Full access, manage users, billing, settings |
| **MANAGER** | View all data, manage cases, configure rules |
| **ANALYST** | View data, investigate alerts, update cases |
| **VIEWER** | Read-only access to dashboards and reports |

---

## 📈 Usage Monitoring

Track tenant usage in real-time:

```sql
-- View tenant usage
SELECT * FROM v_tenant_summary;

-- View tenant health
SELECT * FROM v_tenant_health 
WHERE health_status != 'HEALTHY';
```

---

## 🔄 Data Migration

To migrate existing data to a tenant:

```sql
-- Option 1: Assign all existing data to demo tenant
UPDATE accounts SET tenant_id = 'tenant_demo_123' WHERE tenant_id IS NULL;
UPDATE transactions SET tenant_id = 'tenant_demo_123' WHERE tenant_id IS NULL;
UPDATE fraud_alerts SET tenant_id = 'tenant_demo_123' WHERE tenant_id IS NULL;

-- Option 2: Create separate tenant for each account
-- (more complex, requires custom migration script)
```

---

## 🧪 Testing

### Test Signup Flow
```bash
# 1. Sign up
curl -X POST http://localhost:8000/api/v1/tenants/signup \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Test Corp",
    "subdomain": "test",
    "admin_name": "Test Admin",
    "admin_email": "test@test.com",
    "admin_password": "TestPass123!",
    "plan": "STARTER"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/tenants/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "TestPass123!"
  }'

# 3. Get tenant info (use token from step 2)
curl http://localhost:8000/api/v1/tenants/me \
  -H "Authorization: Bearer <token>"
```

---

## 🐛 Troubleshooting

### Issue: "No tenant identified"
**Solution:** Provide authentication via:
- JWT token: `Authorization: Bearer <token>`
- API key: `X-API-Key: <key>`

### Issue: "Tenant not found"
**Solution:** Ensure tenant is created and status is ACTIVE or TRIAL

### Issue: "Permission denied for table"
**Solution:** Row-Level Security is working! Ensure `tenant_id` is set correctly

---

## 🚀 Next Steps

Now that multi-tenancy is working, implement:

1. **Billing Integration** (Stripe)
2. **Email Notifications** (SendGrid)
3. **Customer Onboarding Flow** (guided setup)
4. **Admin Dashboard** (manage all tenants)
5. **Usage-based Billing** (metered pricing)
6. **Data Import API** (CSV/JSON upload)
7. **Webhooks** (alert notifications)
8. **SSO Integration** (SAML, OAuth)

---

## 📝 Demo Credentials

**Demo Tenant:**
- Organization: Demo Corporation
- Subdomain: `demo`
- Email: `admin@demo.com`
- Password: `DemoPass123!`
- API Key: `fgk_live_demo_api_key_12345`

---

## 💡 Production Checklist

Before going to production:

- [ ] Change JWT_SECRET in environment variables
- [ ] Set up proper SSL/TLS certificates
- [ ] Configure production database with backups
- [ ] Set up monitoring and alerting
- [ ] Implement rate limiting with Redis
- [ ] Add email verification flow
- [ ] Set up Stripe for billing
- [ ] Create terms of service and privacy policy
- [ ] Implement data retention policies
- [ ] Set up log aggregation (ELK/Datadog)
- [ ] Load testing and performance optimization
- [ ] Security audit and penetration testing

---

## 🎉 You're Done!

Your fraud detection system now supports multiple customers with full data isolation, user management, and usage tracking!

Test it out by signing up a tenant and exploring the API endpoints.

**Questions?** Check the implementation files:
- `services/api/models/tenant.py` - Data models
- `services/api/tenants/manager.py` - Business logic
- `services/api/middleware/tenant.py` - Request handling
- `services/api/routers/tenants.py` - API endpoints
- `db/postgres/tenants_schema.sql` - Database schema

