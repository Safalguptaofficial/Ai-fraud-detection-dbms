# 🏗️ Multi-Tenancy Implementation Guide
## Step-by-Step Guide to Convert Single-Tenant to Multi-Tenant

**Priority:** 🔴 CRITICAL - Must be done first  
**Estimated Time:** 4-6 weeks  
**Difficulty:** High

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Migration](#database-migration)
3. [Backend Implementation](#backend-implementation)
4. [Tenant Middleware](#tenant-middleware)
5. [API Changes](#api-changes)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Plan](#deployment-plan)

---

## 🎯 Overview

### Current State
```
Single tenant system where all data belongs to one organization
```

### Target State
```
Multi-tenant system where:
- Each customer (tenant) has isolated data
- Tenants cannot see each other's data
- System enforces tenant isolation at database level
- Single codebase serves all tenants
```

### Implementation Strategy

We'll use **Row-Level Security (RLS)** approach:
- ✅ Cost-effective (shared infrastructure)
- ✅ Easy to maintain (single codebase)
- ✅ Database-level isolation (security)
- ✅ Can scale to 100+ tenants

---

## 🗄️ Database Migration

### Step 1: Add Tenant Management Tables

```sql
-- File: db/postgres/001_add_tenants.sql

-- Create tenants table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    organization_name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(64) UNIQUE NOT NULL,
    
    -- Plan & Status
    plan VARCHAR(32) NOT NULL DEFAULT 'STARTER',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    ml_config JSONB DEFAULT '{
        "risk_threshold": 0.7,
        "auto_block": false,
        "notification_email": null
    }',
    
    -- Limits (based on plan)
    max_users INT DEFAULT 5,
    max_transactions_per_month INT DEFAULT 50000,
    max_storage_gb INT DEFAULT 10,
    
    -- Billing
    stripe_customer_id VARCHAR(128),
    billing_email VARCHAR(255),
    api_key VARCHAR(128) UNIQUE NOT NULL DEFAULT md5(random()::text),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trial_ends_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '14 days'),
    
    -- Contact
    admin_name VARCHAR(255),
    admin_email VARCHAR(255) NOT NULL UNIQUE,
    admin_phone VARCHAR(32),
    
    CONSTRAINT plan_check CHECK (plan IN ('STARTER', 'PROFESSIONAL', 'ENTERPRISE')),
    CONSTRAINT status_check CHECK (status IN ('ACTIVE', 'SUSPENDED', 'TRIAL', 'CANCELLED'))
);

-- Create indexes
CREATE INDEX idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_api_key ON tenants(api_key);

-- Tenant users table (replaces hardcoded DEMO_USERS)
CREATE TABLE IF NOT EXISTS tenant_users (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Authentication
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'ANALYST',
    
    -- SSO (for future)
    sso_provider VARCHAR(32),
    sso_id VARCHAR(255),
    
    -- MFA (for future)
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(128),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, email),
    CONSTRAINT role_check CHECK (role IN ('ADMIN', 'MANAGER', 'ANALYST', 'VIEWER'))
);

-- Indexes
CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_email ON tenant_users(email);
CREATE INDEX idx_tenant_users_active ON tenant_users(tenant_id, is_active);

-- API Keys table
CREATE TABLE IF NOT EXISTS tenant_api_keys (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    key_name VARCHAR(128) NOT NULL,
    key_hash VARCHAR(128) NOT NULL UNIQUE,
    key_prefix VARCHAR(16) NOT NULL,
    
    -- Permissions
    scopes TEXT[] DEFAULT ARRAY['read:transactions', 'write:transactions', 'read:alerts'],
    
    -- Rate limiting
    rate_limit_per_minute INT DEFAULT 100,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES tenant_users(id)
);

CREATE INDEX idx_api_keys_tenant ON tenant_api_keys(tenant_id);
CREATE INDEX idx_api_keys_hash ON tenant_api_keys(key_hash);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id INT REFERENCES tenant_users(id),
    
    -- Action
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(128),
    
    -- Request details
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(128),
    
    -- Changes
    old_value JSONB,
    new_value JSONB,
    
    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(16) DEFAULT 'INFO'
);

CREATE INDEX idx_audit_tenant_time ON audit_logs(tenant_id, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_logs(tenant_id, resource_type, resource_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tenants_updated_at 
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_users_updated_at 
    BEFORE UPDATE ON tenant_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Step 2: Add tenant_id to Existing Tables

```sql
-- File: db/postgres/002_add_tenant_id_to_tables.sql

-- Add tenant_id to accounts
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64);

-- Add tenant_id to transactions
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64);

-- Add tenant_id to fraud_alerts
ALTER TABLE fraud_alerts ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64);

-- Add tenant_id to system_logs (optional)
ALTER TABLE system_logs ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64);

-- Create a default tenant for existing data
INSERT INTO tenants (
    tenant_id, 
    organization_name, 
    subdomain, 
    admin_name, 
    admin_email,
    plan
) VALUES (
    'default-tenant-001',
    'Demo Organization',
    'demo',
    'Demo Admin',
    'admin@demo.com',
    'ENTERPRISE'
) ON CONFLICT DO NOTHING;

-- Migrate existing data to default tenant
UPDATE accounts SET tenant_id = 'default-tenant-001' WHERE tenant_id IS NULL;
UPDATE transactions SET tenant_id = 'default-tenant-001' WHERE tenant_id IS NULL;
UPDATE fraud_alerts SET tenant_id = 'default-tenant-001' WHERE tenant_id IS NULL;
UPDATE system_logs SET tenant_id = 'default-tenant-001' WHERE tenant_id IS NULL;

-- Make tenant_id NOT NULL after data migration
ALTER TABLE accounts ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE transactions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE fraud_alerts ALTER COLUMN tenant_id SET NOT NULL;

-- Add foreign key constraints
ALTER TABLE accounts 
    ADD CONSTRAINT fk_accounts_tenant 
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE;

ALTER TABLE transactions 
    ADD CONSTRAINT fk_transactions_tenant 
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE;

ALTER TABLE fraud_alerts 
    ADD CONSTRAINT fk_alerts_tenant 
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE;

-- Create composite indexes for better performance
CREATE INDEX idx_accounts_tenant_id ON accounts(tenant_id, id);
CREATE INDEX idx_transactions_tenant_time ON transactions(tenant_id, txn_time DESC);
CREATE INDEX idx_alerts_tenant_handled ON fraud_alerts(tenant_id, handled);
```

### Step 3: Enable Row-Level Security

```sql
-- File: db/postgres/003_enable_row_level_security.sql

-- Enable RLS on all tenant tables
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation_policy ON accounts
    USING (tenant_id = current_setting('app.current_tenant', true)::text);

CREATE POLICY tenant_isolation_policy ON transactions
    USING (tenant_id = current_setting('app.current_tenant', true)::text);

CREATE POLICY tenant_isolation_policy ON fraud_alerts
    USING (tenant_id = current_setting('app.current_tenant', true)::text);

CREATE POLICY tenant_isolation_policy ON system_logs
    USING (tenant_id = current_setting('app.current_tenant', true)::text);

-- Create function to set current tenant
CREATE OR REPLACE FUNCTION set_current_tenant(p_tenant_id text)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', p_tenant_id, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION set_current_tenant(text) TO PUBLIC;
```

---

## 🐍 Backend Implementation

### Step 1: Tenant Model

```python
# services/api/models/tenant.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class TenantPlan(str, Enum):
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"

class TenantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"

class Tenant(BaseModel):
    tenant_id: str
    organization_name: str
    subdomain: str
    plan: TenantPlan
    status: TenantStatus
    
    settings: Dict = {}
    ml_config: Dict = {}
    
    max_users: int = 5
    max_transactions_per_month: int = 50000
    max_storage_gb: int = 10
    
    api_key: str
    admin_name: Optional[str]
    admin_email: EmailStr
    admin_phone: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    trial_ends_at: Optional[datetime]

class TenantCreate(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=255)
    subdomain: str = Field(..., min_length=3, max_length=64, regex=r'^[a-z0-9-]+$')
    admin_name: str
    admin_email: EmailStr
    admin_phone: Optional[str]
    plan: TenantPlan = TenantPlan.STARTER
    
    @validator('subdomain')
    def subdomain_must_be_lowercase(cls, v):
        return v.lower()

class TenantUpdate(BaseModel):
    organization_name: Optional[str]
    admin_name: Optional[str]
    admin_email: Optional[EmailStr]
    admin_phone: Optional[str]
    settings: Optional[Dict]
    ml_config: Optional[Dict]

class TenantUser(BaseModel):
    id: int
    tenant_id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime

class TenantUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: str = "ANALYST"
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

### Step 2: Tenant Manager

```python
# services/api/tenants/manager.py
import secrets
import hashlib
from passlib.context import CryptContext
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TenantManager:
    """Manages tenant operations"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def create_tenant(self, tenant_create: TenantCreate, 
                           admin_password: str) -> Tenant:
        """
        Create new tenant with admin user
        
        Steps:
        1. Create tenant record
        2. Generate API key
        3. Create admin user
        4. Setup default settings
        5. Send welcome email
        """
        
        # Generate tenant ID
        tenant_id = f"tenant_{secrets.token_urlsafe(16)}"
        
        # Generate API key
        api_key = self._generate_api_key()
        
        # Hash admin password
        password_hash = pwd_context.hash(admin_password)
        
        cursor = self.db.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Start transaction
            cursor.execute("BEGIN")
            
            # Insert tenant
            cursor.execute("""
                INSERT INTO tenants (
                    tenant_id, organization_name, subdomain,
                    admin_name, admin_email, admin_phone,
                    plan, api_key
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                tenant_id,
                tenant_create.organization_name,
                tenant_create.subdomain,
                tenant_create.admin_name,
                tenant_create.admin_email,
                tenant_create.admin_phone,
                tenant_create.plan.value,
                api_key
            ))
            
            tenant_record = cursor.fetchone()
            
            # Create admin user
            cursor.execute("""
                INSERT INTO tenant_users (
                    tenant_id, email, password_hash,
                    full_name, role, is_active, email_verified
                ) VALUES (%s, %s, %s, %s, 'ADMIN', true, false)
                RETURNING id
            """, (
                tenant_id,
                tenant_create.admin_email,
                password_hash,
                tenant_create.admin_name
            ))
            
            admin_user_id = cursor.fetchone()['id']
            
            # Commit transaction
            cursor.execute("COMMIT")
            
            # Send welcome email (async task)
            await self._send_welcome_email(
                tenant_create.admin_email,
                tenant_create.organization_name,
                api_key
            )
            
            return Tenant(**tenant_record)
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise Exception(f"Failed to create tenant: {str(e)}")
        finally:
            cursor.close()
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        cursor = self.db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM tenants WHERE tenant_id = %s",
            (tenant_id,)
        )
        
        record = cursor.fetchone()
        cursor.close()
        
        return Tenant(**record) if record else None
    
    async def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """Get tenant by subdomain"""
        cursor = self.db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM tenants WHERE subdomain = %s",
            (subdomain,)
        )
        
        record = cursor.fetchone()
        cursor.close()
        
        return Tenant(**record) if record else None
    
    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key"""
        cursor = self.db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT * FROM tenants WHERE api_key = %s AND status = 'ACTIVE'",
            (api_key,)
        )
        
        record = cursor.fetchone()
        cursor.close()
        
        return Tenant(**record) if record else None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate tenant user"""
        cursor = self.db.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT u.*, t.tenant_id, t.organization_name, t.plan
            FROM tenant_users u
            JOIN tenants t ON u.tenant_id = t.tenant_id
            WHERE u.email = %s AND u.is_active = true
        """, (email,))
        
        user = cursor.fetchone()
        
        if not user:
            return None
        
        # Verify password
        if not pwd_context.verify(password, user['password_hash']):
            return None
        
        # Update last login
        cursor.execute(
            "UPDATE tenant_users SET last_login = NOW() WHERE id = %s",
            (user['id'],)
        )
        self.db.commit()
        
        cursor.close()
        
        return {
            "user_id": user['id'],
            "tenant_id": user['tenant_id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role'],
            "organization_name": user['organization_name'],
            "plan": user['plan']
        }
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"fgk_live_{secrets.token_urlsafe(32)}"
    
    async def _send_welcome_email(self, email: str, org_name: str, api_key: str):
        """Send welcome email to new tenant (implement with email service)"""
        # TODO: Implement with SendGrid/SES
        pass
```

---

## 🔧 Tenant Middleware

```python
# services/api/middleware/tenant.py
from fastapi import Request, HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """
    Middleware to extract and set current tenant
    
    Tenant can be identified by:
    1. Subdomain (tenant.fraudguard.com)
    2. API key header (X-API-Key)
    3. JWT token (for logged-in users)
    """
    
    async def __call__(self, request: Request, call_next):
        tenant_id = await self.extract_tenant_id(request)
        
        if not tenant_id and not self.is_public_route(request.url.path):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No tenant identified"
            )
        
        # Store tenant_id in request state
        request.state.tenant_id = tenant_id
        
        # Set PostgreSQL session variable for RLS
        if tenant_id:
            await self.set_database_tenant(request, tenant_id)
        
        response = await call_next(request)
        return response
    
    async def extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        
        # 1. Try API Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            tenant = await get_tenant_by_api_key(api_key)
            if tenant:
                logger.info(f"Tenant identified by API key: {tenant.tenant_id}")
                return tenant.tenant_id
        
        # 2. Try JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_jwt(token)
            if payload and "tenant_id" in payload:
                logger.info(f"Tenant identified by JWT: {payload['tenant_id']}")
                return payload["tenant_id"]
        
        # 3. Try subdomain
        host = request.headers.get("Host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "admin"]:
                tenant = await get_tenant_by_subdomain(subdomain)
                if tenant:
                    logger.info(f"Tenant identified by subdomain: {tenant.tenant_id}")
                    return tenant.tenant_id
        
        return None
    
    async def set_database_tenant(self, request: Request, tenant_id: str):
        """Set PostgreSQL session variable for Row-Level Security"""
        db = request.app.state.db
        cursor = db.cursor()
        
        try:
            cursor.execute("SELECT set_current_tenant(%s)", (tenant_id,))
            db.commit()
        except Exception as e:
            logger.error(f"Failed to set database tenant: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to set tenant context"
            )
        finally:
            cursor.close()
    
    def is_public_route(self, path: str) -> bool:
        """Check if route is public (no tenant required)"""
        public_routes = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/signup",
            "/auth/forgot-password"
        ]
        return path in public_routes
```

### Using Middleware in FastAPI

```python
# services/api/main.py (updated)
from fastapi import FastAPI, Request
from middleware.tenant import TenantMiddleware

app = FastAPI(title="FraudGuard API")

# Add tenant middleware
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    middleware = TenantMiddleware()
    return await middleware(request, call_next)

# Dependency to get current tenant
def get_current_tenant(request: Request) -> str:
    """Get current tenant ID from request"""
    if not hasattr(request.state, 'tenant_id'):
        raise HTTPException(
            status_code=401,
            detail="No tenant identified"
        )
    return request.state.tenant_id
```

---

## 📡 API Changes

### Updated Endpoints

```python
# services/api/routers/tenants.py
from fastapi import APIRouter, Depends, HTTPException
from models.tenant import Tenant, TenantCreate, TenantUpdate
from tenants.manager import TenantManager
from dependencies import get_db, get_current_tenant

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])

@router.post("/signup", response_model=Tenant, status_code=201)
async def signup_tenant(
    tenant_data: TenantCreate,
    admin_password: str,
    db = Depends(get_db)
):
    """
    Public endpoint to create new tenant (self-service signup)
    
    Returns tenant info and API key (show API key ONCE!)
    """
    manager = TenantManager(db)
    
    # Check if subdomain already exists
    existing = await manager.get_tenant_by_subdomain(tenant_data.subdomain)
    if existing:
        raise HTTPException(400, "Subdomain already taken")
    
    # Check if email already exists
    # ... validation ...
    
    tenant = await manager.create_tenant(tenant_data, admin_password)
    
    return tenant

@router.get("/me", response_model=Tenant)
async def get_current_tenant_info(
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_db)
):
    """Get current tenant information"""
    manager = TenantManager(db)
    tenant = await manager.get_tenant_by_id(tenant_id)
    
    if not tenant:
        raise HTTPException(404, "Tenant not found")
    
    return tenant

@router.put("/me", response_model=Tenant)
async def update_tenant(
    updates: TenantUpdate,
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_db)
):
    """Update current tenant"""
    manager = TenantManager(db)
    tenant = await manager.update_tenant(tenant_id, updates)
    return tenant

@router.get("/usage")
async def get_usage_stats(
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_db)
):
    """
    Get current usage statistics
    
    Returns:
    - Transactions this month
    - Active users
    - Storage used
    - API calls
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    # Transactions this month
    cursor.execute("""
        SELECT COUNT(*) as transaction_count
        FROM transactions
        WHERE tenant_id = %s
        AND txn_time >= date_trunc('month', CURRENT_DATE)
    """, (tenant_id,))
    
    txn_count = cursor.fetchone()['transaction_count']
    
    # Active users
    cursor.execute("""
        SELECT COUNT(*) as user_count
        FROM tenant_users
        WHERE tenant_id = %s AND is_active = true
    """, (tenant_id,))
    
    user_count = cursor.fetchone()['user_count']
    
    # Get tenant limits
    cursor.execute("""
        SELECT max_transactions_per_month, max_users, max_storage_gb
        FROM tenants
        WHERE tenant_id = %s
    """, (tenant_id,))
    
    limits = cursor.fetchone()
    
    cursor.close()
    
    return {
        "transactions_this_month": txn_count,
        "transactions_limit": limits['max_transactions_per_month'],
        "transactions_percentage": (txn_count / limits['max_transactions_per_month']) * 100,
        
        "active_users": user_count,
        "users_limit": limits['max_users'],
        
        "storage_used_gb": 0,  # TODO: Calculate actual storage
        "storage_limit_gb": limits['max_storage_gb']
    }
```

### Updated Transaction Endpoint

```python
# services/api/routers/transactions.py (updated)
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/transactions")

@router.post("/", status_code=201)
async def create_transaction(
    transaction: TransactionCreate,
    tenant_id: str = Depends(get_current_tenant),  # ← Automatic tenant injection
    db = Depends(get_db)
):
    """
    Create new transaction
    
    tenant_id is automatically added from context
    """
    cursor = db.cursor()
    
    # Insert with tenant_id
    cursor.execute("""
        INSERT INTO transactions (
            tenant_id, account_id, amount, currency, merchant, ...
        ) VALUES (%s, %s, %s, %s, %s, ...)
        RETURNING id
    """, (
        tenant_id,  # ← Tenant ID from auth context
        transaction.account_id,
        transaction.amount,
        transaction.currency,
        transaction.merchant,
        ...
    ))
    
    txn_id = cursor.fetchone()[0]
    db.commit()
    cursor.close()
    
    return {"transaction_id": txn_id, "status": "created"}

@router.get("/")
async def list_transactions(
    tenant_id: str = Depends(get_current_tenant),
    limit: int = 100,
    db = Depends(get_db)
):
    """
    List transactions for current tenant
    
    Row-Level Security automatically filters by tenant_id
    """
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    # Query WITHOUT tenant_id filter - RLS handles it!
    cursor.execute("""
        SELECT *
        FROM transactions
        ORDER BY txn_time DESC
        LIMIT %s
    """, (limit,))
    
    transactions = cursor.fetchall()
    cursor.close()
    
    return transactions
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_multi_tenancy.py
import pytest
from tenants.manager import TenantManager
from models.tenant import TenantCreate

@pytest.mark.asyncio
async def test_create_tenant():
    """Test tenant creation"""
    manager = TenantManager(test_db)
    
    tenant_data = TenantCreate(
        organization_name="Test Corp",
        subdomain="testcorp",
        admin_name="John Doe",
        admin_email="john@testcorp.com"
    )
    
    tenant = await manager.create_tenant(tenant_data, "SecurePass123!")
    
    assert tenant.tenant_id is not None
    assert tenant.subdomain == "testcorp"
    assert tenant.status == "TRIAL"

@pytest.mark.asyncio
async def test_tenant_isolation():
    """Test that tenants cannot see each other's data"""
    
    # Create two tenants
    tenant1 = await create_test_tenant("tenant1")
    tenant2 = await create_test_tenant("tenant2")
    
    # Create transaction for tenant1
    await create_transaction(tenant1.tenant_id, amount=1000)
    
    # Query as tenant2 - should return empty
    transactions = await get_transactions(tenant2.tenant_id)
    
    assert len(transactions) == 0

@pytest.mark.asyncio
async def test_row_level_security():
    """Test PostgreSQL Row-Level Security enforcement"""
    
    tenant1_id = "tenant_abc123"
    tenant2_id = "tenant_xyz789"
    
    # Set tenant1 context
    await set_database_tenant(tenant1_id)
    
    # Create transaction
    txn_id = await create_transaction(tenant1_id, amount=500)
    
    # Switch to tenant2 context
    await set_database_tenant(tenant2_id)
    
    # Try to query tenant1's transaction - should return None
    txn = await get_transaction(txn_id)
    
    assert txn is None
```

### Integration Tests

```python
# tests/integration/test_tenant_api.py
import pytest
from fastapi.testclient import TestClient

def test_signup_flow():
    """Test complete tenant signup flow"""
    client = TestClient(app)
    
    # Signup
    response = client.post("/api/v1/tenants/signup", json={
        "organization_name": "Test Corp",
        "subdomain": "testcorp",
        "admin_name": "John Doe",
        "admin_email": "john@testcorp.com",
        "admin_password": "SecurePass123!"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    api_key = data['api_key']
    
    # Use API key to create transaction
    response = client.post(
        "/api/v1/transactions",
        headers={"X-API-Key": api_key},
        json={
            "account_id": 1,
            "amount": 1000,
            "currency": "USD",
            ...
        }
    )
    
    assert response.status_code == 201
```

---

## 🚀 Deployment Plan

### Phase 1: Development Environment (Week 1)
```bash
# Run migrations
cd db/postgres
psql -U postgres -d frauddb < 001_add_tenants.sql
psql -U postgres -d frauddb < 002_add_tenant_id_to_tables.sql
psql -U postgres -d frauddb < 003_enable_row_level_security.sql

# Test locally
python -m pytest tests/test_multi_tenancy.py -v
```

### Phase 2: Staging Deployment (Week 2-3)
```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run smoke tests
pytest tests/integration/ -v

# Create test tenants
curl -X POST https://staging-api.fraudguard.com/api/v1/tenants/signup \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Phase 3: Production Rollout (Week 4)
```
1. Backup database
2. Run migrations during maintenance window
3. Deploy new code
4. Migrate existing demo data to first tenant
5. Monitor for issues
6. Enable signup for new tenants
```

---

## 📚 Next Steps

After multi-tenancy is implemented:

1. ✅ **Week 5-6:** Data ingestion pipeline
2. ✅ **Week 7-8:** Enterprise authentication (SSO, MFA)
3. ✅ **Week 9-10:** Customer portal & billing
4. ✅ **Week 11-12:** Security audit & compliance

---

**Document Version:** 1.0  
**Last Updated:** October 30, 2025  
**Next Review:** Weekly during implementation


