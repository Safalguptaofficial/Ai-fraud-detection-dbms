-- ============================================
-- Multi-Tenancy Schema for Fraud Detection System
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. TENANTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    organization_name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(64) NOT NULL UNIQUE,
    
    -- Plan & Status
    plan VARCHAR(20) NOT NULL DEFAULT 'STARTER' CHECK (plan IN ('STARTER', 'PROFESSIONAL', 'ENTERPRISE')),
    status VARCHAR(20) NOT NULL DEFAULT 'TRIAL' CHECK (status IN ('ACTIVE', 'TRIAL', 'SUSPENDED', 'CANCELLED')),
    
    -- Configuration (JSON)
    settings JSONB DEFAULT '{}',
    ml_config JSONB DEFAULT '{}',
    
    -- Limits
    max_users INTEGER NOT NULL DEFAULT 5,
    max_transactions_per_month INTEGER NOT NULL DEFAULT 50000,
    max_storage_gb INTEGER NOT NULL DEFAULT 10,
    max_api_calls_per_minute INTEGER NOT NULL DEFAULT 100,
    
    -- Billing
    stripe_customer_id VARCHAR(255),
    billing_email VARCHAR(255),
    api_key VARCHAR(255) NOT NULL UNIQUE,
    
    -- Admin contact
    admin_name VARCHAR(255),
    admin_email VARCHAR(255) NOT NULL,
    admin_phone VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trial_ends_at TIMESTAMP,
    subscription_ends_at TIMESTAMP,
    last_activity_at TIMESTAMP
);

CREATE INDEX idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX idx_tenants_api_key ON tenants(api_key);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_plan ON tenants(plan);


-- ============================================
-- 2. TENANT USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS tenant_users (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Auth
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'ANALYST' CHECK (role IN ('ADMIN', 'MANAGER', 'ANALYST', 'VIEWER')),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    
    -- Tracking
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_tenant_users_tenant_id ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_email ON tenant_users(email);
CREATE INDEX idx_tenant_users_role ON tenant_users(role);


-- ============================================
-- 3. TENANT API KEYS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS tenant_api_keys (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Key info
    key_name VARCHAR(128) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(12) NOT NULL,
    
    -- Permissions
    scopes TEXT[] NOT NULL DEFAULT ARRAY['read:transactions', 'write:transactions', 'read:alerts', 'write:alerts'],
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 100,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES tenant_users(id),
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_tenant_api_keys_tenant_id ON tenant_api_keys(tenant_id);
CREATE INDEX idx_tenant_api_keys_hash ON tenant_api_keys(key_hash);
CREATE INDEX idx_tenant_api_keys_active ON tenant_api_keys(is_active);


-- ============================================
-- 4. TENANT USAGE TABLE (Monthly tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS tenant_usage (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Counters
    transaction_count INTEGER DEFAULT 0,
    api_call_count INTEGER DEFAULT 0,
    storage_used_mb INTEGER DEFAULT 0,
    alert_count INTEGER DEFAULT 0,
    
    -- Calculated
    overage_transactions INTEGER DEFAULT 0,
    overage_charges DECIMAL(10, 2) DEFAULT 0.00,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, period_start)
);

CREATE INDEX idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
CREATE INDEX idx_tenant_usage_period ON tenant_usage(period_start, period_end);


-- ============================================
-- 5. AUDIT LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES tenant_users(id),
    
    -- Action
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    
    -- Details
    old_value JSONB,
    new_value JSONB,
    metadata JSONB DEFAULT '{}',
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    severity VARCHAR(20) DEFAULT 'INFO' CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);


-- ============================================
-- 6. ADD TENANT_ID TO EXISTING TABLES
-- ============================================

-- Add tenant_id to accounts table
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) REFERENCES tenants(tenant_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_accounts_tenant_id ON accounts(tenant_id);

-- Add tenant_id to transactions table
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) REFERENCES tenants(tenant_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_transactions_tenant_id ON transactions(tenant_id);

-- Add tenant_id to fraud_alerts table
ALTER TABLE fraud_alerts ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) REFERENCES tenants(tenant_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_tenant_id ON fraud_alerts(tenant_id);

-- Add tenant_id to system_logs table (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'system_logs') THEN
        ALTER TABLE system_logs ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64) REFERENCES tenants(tenant_id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_system_logs_tenant_id ON system_logs(tenant_id);
    END IF;
END $$;


-- ============================================
-- 7. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on tables
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_alerts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- These policies ensure users only see data from their tenant

CREATE POLICY tenant_isolation_accounts ON accounts
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::varchar);

CREATE POLICY tenant_isolation_transactions ON transactions
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::varchar);

CREATE POLICY tenant_isolation_fraud_alerts ON fraud_alerts
    USING (tenant_id = current_setting('app.current_tenant', TRUE)::varchar);


-- ============================================
-- 8. HELPER FUNCTIONS
-- ============================================

-- Function to set current tenant for session
CREATE OR REPLACE FUNCTION set_current_tenant(tenant_id_param VARCHAR)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_id_param, FALSE);
END;
$$ LANGUAGE plpgsql;


-- Function to get current tenant
CREATE OR REPLACE FUNCTION get_current_tenant()
RETURNS VARCHAR AS $$
BEGIN
    RETURN current_setting('app.current_tenant', TRUE)::varchar;
END;
$$ LANGUAGE plpgsql;


-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Add update triggers
CREATE TRIGGER update_tenants_updated_at 
    BEFORE UPDATE ON tenants 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_users_updated_at 
    BEFORE UPDATE ON tenant_users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_usage_updated_at 
    BEFORE UPDATE ON tenant_usage 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- 9. SAMPLE DATA (for testing)
-- ============================================

-- Insert demo tenant
INSERT INTO tenants (
    tenant_id, organization_name, subdomain,
    admin_name, admin_email, plan, status,
    api_key, trial_ends_at
) VALUES (
    'tenant_demo_123',
    'Demo Corporation',
    'demo',
    'Demo Admin',
    'admin@demo.com',
    'PROFESSIONAL',
    'ACTIVE',
    'fgk_live_demo_api_key_12345',
    CURRENT_TIMESTAMP + INTERVAL '30 days'
) ON CONFLICT (tenant_id) DO NOTHING;

-- Insert demo admin user (password: DemoPass123!)
INSERT INTO tenant_users (
    tenant_id, email, password_hash, full_name, role, email_verified
) VALUES (
    'tenant_demo_123',
    'admin@demo.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdkLX.8WkVLM9WJ8G', -- DemoPass123!
    'Demo Admin',
    'ADMIN',
    true
) ON CONFLICT (tenant_id, email) DO NOTHING;

-- Initialize usage for current month
INSERT INTO tenant_usage (
    tenant_id, period_start, period_end
) VALUES (
    'tenant_demo_123',
    DATE_TRUNC('month', CURRENT_DATE),
    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day'
) ON CONFLICT (tenant_id, period_start) DO NOTHING;


-- ============================================
-- 10. VIEWS FOR ANALYTICS
-- ============================================

-- View: Active tenants with usage
CREATE OR REPLACE VIEW v_tenant_summary AS
SELECT 
    t.tenant_id,
    t.organization_name,
    t.subdomain,
    t.plan,
    t.status,
    t.created_at,
    COUNT(DISTINCT tu.id) as user_count,
    u.transaction_count as transactions_this_month,
    t.max_transactions_per_month,
    ROUND((u.transaction_count::numeric / t.max_transactions_per_month * 100), 2) as usage_percentage
FROM tenants t
LEFT JOIN tenant_users tu ON t.tenant_id = tu.tenant_id AND tu.is_active = true
LEFT JOIN tenant_usage u ON t.tenant_id = u.tenant_id 
    AND u.period_start = DATE_TRUNC('month', CURRENT_DATE)
WHERE t.status IN ('ACTIVE', 'TRIAL')
GROUP BY t.tenant_id, t.organization_name, t.subdomain, t.plan, t.status, 
         t.created_at, u.transaction_count, t.max_transactions_per_month;


-- View: Tenant health metrics
CREATE OR REPLACE VIEW v_tenant_health AS
SELECT 
    t.tenant_id,
    t.organization_name,
    t.status,
    t.plan,
    CASE 
        WHEN t.status = 'TRIAL' AND t.trial_ends_at < CURRENT_TIMESTAMP THEN 'TRIAL_EXPIRED'
        WHEN u.transaction_count > t.max_transactions_per_month THEN 'OVER_LIMIT'
        WHEN u.transaction_count > (t.max_transactions_per_month * 0.9) THEN 'NEAR_LIMIT'
        ELSE 'HEALTHY'
    END as health_status,
    u.transaction_count,
    t.max_transactions_per_month,
    t.trial_ends_at,
    t.last_activity_at
FROM tenants t
LEFT JOIN tenant_usage u ON t.tenant_id = u.tenant_id 
    AND u.period_start = DATE_TRUNC('month', CURRENT_DATE);

-- ============================================
-- DONE!
-- ============================================

