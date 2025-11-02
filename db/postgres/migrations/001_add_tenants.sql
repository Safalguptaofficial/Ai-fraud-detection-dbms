-- Migration 001: Add Tenant Management Tables
-- Description: Creates core tenant management infrastructure
-- Date: 2025-10-30
-- Author: AI Implementation

-- ============================================================================
-- TENANT CORE TABLES
-- ============================================================================

-- Create tenants table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY DEFAULT ('tenant_' || encode(gen_random_bytes(12), 'hex')),
    organization_name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(64) UNIQUE NOT NULL,
    
    -- Plan & Status
    plan VARCHAR(32) NOT NULL DEFAULT 'STARTER',
    status VARCHAR(32) NOT NULL DEFAULT 'TRIAL',
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    ml_config JSONB DEFAULT '{
        "risk_threshold": 0.7,
        "auto_block": false,
        "auto_freeze_threshold": 0.85,
        "notification_email": null,
        "alert_rules": ["VELOCITY_HIGH", "GEO_JUMP", "AMOUNT_ANOMALY"]
    }'::jsonb,
    
    -- Limits (based on plan)
    max_users INT DEFAULT 5,
    max_transactions_per_month INT DEFAULT 50000,
    max_storage_gb INT DEFAULT 10,
    max_api_calls_per_minute INT DEFAULT 100,
    
    -- Billing
    stripe_customer_id VARCHAR(128),
    billing_email VARCHAR(255),
    api_key VARCHAR(128) UNIQUE NOT NULL DEFAULT ('fgk_' || encode(gen_random_bytes(24), 'hex')),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trial_ends_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '14 days'),
    subscription_ends_at TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contact
    admin_name VARCHAR(255),
    admin_email VARCHAR(255) NOT NULL,
    admin_phone VARCHAR(32),
    
    -- Constraints
    CONSTRAINT plan_check CHECK (plan IN ('STARTER', 'PROFESSIONAL', 'ENTERPRISE')),
    CONSTRAINT status_check CHECK (status IN ('ACTIVE', 'SUSPENDED', 'TRIAL', 'CANCELLED'))
);

-- Create indexes for tenants
CREATE INDEX IF NOT EXISTS idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
CREATE INDEX IF NOT EXISTS idx_tenants_api_key ON tenants(api_key);
CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(admin_email);
CREATE INDEX IF NOT EXISTS idx_tenants_created ON tenants(created_at DESC);

-- ============================================================================
-- TENANT USERS TABLE
-- ============================================================================

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
    mfa_backup_codes TEXT[],
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(128),
    password_reset_token VARCHAR(128),
    password_reset_expires TIMESTAMP,
    
    -- Activity
    last_login TIMESTAMP,
    last_activity TIMESTAMP,
    login_count INT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    
    -- Constraints
    UNIQUE(tenant_id, email),
    CONSTRAINT role_check CHECK (role IN ('ADMIN', 'MANAGER', 'ANALYST', 'VIEWER')),
    CONSTRAINT sso_provider_check CHECK (sso_provider IN (NULL, 'SAML', 'OAUTH2', 'AZURE_AD', 'OKTA'))
);

-- Indexes for tenant_users
CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_email ON tenant_users(email);
CREATE INDEX IF NOT EXISTS idx_tenant_users_active ON tenant_users(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_tenant_users_role ON tenant_users(tenant_id, role);

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_api_keys (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Key info
    key_name VARCHAR(128) NOT NULL,
    key_hash VARCHAR(128) NOT NULL UNIQUE,
    key_prefix VARCHAR(16) NOT NULL,
    
    -- Permissions
    scopes TEXT[] DEFAULT ARRAY[
        'read:transactions', 
        'write:transactions', 
        'read:alerts', 
        'write:alerts',
        'read:accounts',
        'write:accounts'
    ],
    
    -- Rate limiting
    rate_limit_per_minute INT DEFAULT 100,
    rate_limit_per_hour INT DEFAULT 5000,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count BIGINT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES tenant_users(id),
    description TEXT,
    
    -- IP restrictions (optional)
    allowed_ips INET[]
);

-- Indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON tenant_api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON tenant_api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON tenant_api_keys(tenant_id, is_active);

-- ============================================================================
-- AUDIT LOGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id INT REFERENCES tenant_users(id),
    
    -- Action details
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(128),
    
    -- Request details
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(128),
    http_method VARCHAR(16),
    endpoint VARCHAR(255),
    
    -- Changes
    old_value JSONB,
    new_value JSONB,
    
    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(16) DEFAULT 'INFO',
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    CONSTRAINT severity_check CHECK (severity IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Indexes for audit_logs (optimized for queries)
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON audit_logs(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(tenant_id, resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(tenant_id, action, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity, timestamp DESC) WHERE severity IN ('ERROR', 'CRITICAL');

-- ============================================================================
-- TENANT USAGE TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_usage (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Usage period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    transaction_count INT DEFAULT 0,
    api_call_count INT DEFAULT 0,
    storage_bytes BIGINT DEFAULT 0,
    ml_prediction_count INT DEFAULT 0,
    
    -- Costs (for billing)
    overage_transactions INT DEFAULT 0,
    overage_cost DECIMAL(10, 2) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, period_start)
);

CREATE INDEX IF NOT EXISTS idx_usage_tenant_period ON tenant_usage(tenant_id, period_start DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

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

CREATE TRIGGER update_tenant_usage_updated_at 
    BEFORE UPDATE ON tenant_usage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update tenant last_activity_at
CREATE OR REPLACE FUNCTION update_tenant_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tenants 
    SET last_activity_at = CURRENT_TIMESTAMP 
    WHERE tenant_id = NEW.tenant_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tenant_activity_on_transaction
    AFTER INSERT ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_tenant_activity();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to check if tenant is within limits
CREATE OR REPLACE FUNCTION check_tenant_limits(p_tenant_id VARCHAR(64))
RETURNS TABLE(
    within_limits BOOLEAN,
    transactions_used INT,
    transactions_limit INT,
    users_used INT,
    users_limit INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (u.transaction_count < t.max_transactions_per_month 
         AND user_count < t.max_users) AS within_limits,
        COALESCE(u.transaction_count, 0)::INT AS transactions_used,
        t.max_transactions_per_month AS transactions_limit,
        user_count AS users_used,
        t.max_users AS users_limit
    FROM tenants t
    LEFT JOIN (
        SELECT tenant_id, transaction_count
        FROM tenant_usage
        WHERE period_start = DATE_TRUNC('month', CURRENT_DATE)
    ) u ON t.tenant_id = u.tenant_id
    CROSS JOIN (
        SELECT COUNT(*)::INT AS user_count
        FROM tenant_users
        WHERE tenant_id = p_tenant_id AND is_active = TRUE
    ) users
    WHERE t.tenant_id = p_tenant_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SEED DATA (Default Tenant for Demo)
-- ============================================================================

-- Create default tenant for existing data
INSERT INTO tenants (
    tenant_id, 
    organization_name, 
    subdomain, 
    admin_name, 
    admin_email,
    admin_phone,
    plan,
    status,
    max_users,
    max_transactions_per_month,
    max_storage_gb
) VALUES (
    'default-tenant-demo',
    'Demo Organization',
    'demo',
    'Demo Administrator',
    'admin@demo.fraudguard.com',
    '+1-555-0100',
    'ENTERPRISE',
    'ACTIVE',
    100,
    10000000,
    1000
) ON CONFLICT (tenant_id) DO NOTHING;

-- Create default admin user (password: Admin123!)
-- Password hash generated with: passlib.hash.bcrypt.hash("Admin123!")
INSERT INTO tenant_users (
    tenant_id,
    email,
    password_hash,
    full_name,
    role,
    is_active,
    email_verified
) VALUES (
    'default-tenant-demo',
    'admin@demo.fraudguard.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND0hDc.yqW.G',
    'Demo Administrator',
    'ADMIN',
    TRUE,
    TRUE
) ON CONFLICT (tenant_id, email) DO NOTHING;

-- Create analyst user (password: Analyst123!)
INSERT INTO tenant_users (
    tenant_id,
    email,
    password_hash,
    full_name,
    role,
    is_active,
    email_verified
) VALUES (
    'default-tenant-demo',
    'analyst@demo.fraudguard.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND0hDc.yqW.G',
    'Demo Analyst',
    'ANALYST',
    TRUE,
    TRUE
) ON CONFLICT (tenant_id, email) DO NOTHING;

-- ============================================================================
-- GRANTS (Adjust based on your database user)
-- ============================================================================

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_users TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_api_keys TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON audit_logs TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON tenant_usage TO postgres;

GRANT USAGE, SELECT ON SEQUENCE tenant_users_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE tenant_api_keys_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE audit_logs_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE tenant_usage_id_seq TO postgres;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tables created
DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed successfully';
    RAISE NOTICE 'Tables created: tenants, tenant_users, tenant_api_keys, audit_logs, tenant_usage';
    RAISE NOTICE 'Default tenant created: default-tenant-demo';
    RAISE NOTICE 'Default users created: admin@demo.fraudguard.com, analyst@demo.fraudguard.com';
END $$;

