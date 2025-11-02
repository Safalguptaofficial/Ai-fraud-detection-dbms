-- Migration: Phase 2 & 3 Features
-- Adds tables for MFA, OAuth, File Uploads, and Data Sync Jobs

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PHASE 2: Enterprise Features
-- ============================================================================

-- Table for MFA Secrets
CREATE TABLE IF NOT EXISTS user_mfa_secrets (
    user_id INTEGER PRIMARY KEY REFERENCES tenant_users(id) ON DELETE CASCADE,
    secret VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    backup_codes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_mfa_secrets_enabled ON user_mfa_secrets(enabled);

COMMENT ON TABLE user_mfa_secrets IS 'Stores MFA (TOTP) secrets for two-factor authentication';

-- Table for OAuth Connections
CREATE TABLE IF NOT EXISTS user_oauth_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES tenant_users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'google', 'microsoft', 'okta'
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_user_oauth_user_id ON user_oauth_connections(user_id);
CREATE INDEX idx_user_oauth_provider ON user_oauth_connections(provider);
CREATE INDEX idx_user_oauth_provider_user_id ON user_oauth_connections(provider, provider_user_id);

COMMENT ON TABLE user_oauth_connections IS 'Stores OAuth/SSO connections for users';

-- ============================================================================
-- PHASE 3: Self-Service Features
-- ============================================================================

-- Table for File Uploads (CSV/Excel ingestion tracking)
CREATE TABLE IF NOT EXISTS file_uploads (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    uploaded_by INTEGER REFERENCES tenant_users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- 'csv', 'xlsx', 'xls'
    file_size BIGINT NOT NULL,  -- in bytes
    file_hash VARCHAR(64),  -- SHA256 hash for deduplication
    
    -- Processing status
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    rows_total INTEGER,
    rows_inserted INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    
    -- Error tracking
    error_summary TEXT,
    error_details JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_file_uploads_tenant ON file_uploads(tenant_id);
CREATE INDEX idx_file_uploads_status ON file_uploads(status);
CREATE INDEX idx_file_uploads_created ON file_uploads(created_at DESC);
CREATE INDEX idx_file_uploads_hash ON file_uploads(file_hash);

COMMENT ON TABLE file_uploads IS 'Tracks CSV/Excel file uploads for bulk data ingestion';

-- Table for Data Sync Jobs (Database connector configurations)
CREATE TABLE IF NOT EXISTS data_sync_jobs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Connection configuration
    name VARCHAR(255) NOT NULL,
    connector_type VARCHAR(50) NOT NULL,  -- 'postgresql', 'mysql', 'oracle', 'mssql'
    connection_params JSONB NOT NULL,  -- Encrypted connection details
    
    -- Source table mapping
    source_table VARCHAR(255) NOT NULL,
    column_mapping JSONB NOT NULL,  -- Maps source columns to our schema
    
    -- Sync configuration
    schedule VARCHAR(100) NOT NULL,  -- Cron expression: '0 * * * *'
    sync_mode VARCHAR(20) DEFAULT 'INCREMENTAL',  -- 'INCREMENTAL' or 'FULL'
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- 'ACTIVE', 'PAUSED', 'FAILED', 'DISABLED'
    
    -- Sync statistics
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(20),  -- 'SUCCESS', 'FAILED'
    last_sync_count INTEGER DEFAULT 0,
    last_sync_error TEXT,
    total_synced INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES tenant_users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_sync_jobs_tenant ON data_sync_jobs(tenant_id);
CREATE INDEX idx_data_sync_jobs_status ON data_sync_jobs(status);
CREATE INDEX idx_data_sync_jobs_schedule ON data_sync_jobs(schedule);
CREATE INDEX idx_data_sync_jobs_last_sync ON data_sync_jobs(last_sync_at);

COMMENT ON TABLE data_sync_jobs IS 'Configuration for automated database connector sync jobs';

-- Table for Sync Job History (detailed log of each sync execution)
CREATE TABLE IF NOT EXISTS data_sync_history (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES data_sync_jobs(id) ON DELETE CASCADE,
    
    -- Execution details
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,  -- Duration in milliseconds
    
    -- Results
    status VARCHAR(20) NOT NULL,  -- 'SUCCESS', 'FAILED', 'PARTIAL'
    rows_fetched INTEGER DEFAULT 0,
    rows_inserted INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    
    -- Performance metrics
    throughput_rps DECIMAL(10, 2)  -- Rows per second
);

CREATE INDEX idx_data_sync_history_job ON data_sync_history(job_id);
CREATE INDEX idx_data_sync_history_started ON data_sync_history(started_at DESC);
CREATE INDEX idx_data_sync_history_status ON data_sync_history(status);

COMMENT ON TABLE data_sync_history IS 'Historical log of data sync job executions';

-- Table for Billing/Subscription Information (Stripe integration)
CREATE TABLE IF NOT EXISTS tenant_subscriptions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Stripe details
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_payment_method_id VARCHAR(255),
    
    -- Subscription details
    plan VARCHAR(50) NOT NULL,  -- 'STARTER', 'PROFESSIONAL', 'ENTERPRISE'
    status VARCHAR(20) NOT NULL,  -- 'ACTIVE', 'TRIALING', 'PAST_DUE', 'CANCELED', 'UNPAID'
    
    -- Billing period
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    cancel_at TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_subscriptions_tenant ON tenant_subscriptions(tenant_id);
CREATE INDEX idx_tenant_subscriptions_stripe_customer ON tenant_subscriptions(stripe_customer_id);
CREATE INDEX idx_tenant_subscriptions_status ON tenant_subscriptions(status);

COMMENT ON TABLE tenant_subscriptions IS 'Stripe subscription information for tenant billing';

-- Table for Invoice History
CREATE TABLE IF NOT EXISTS tenant_invoices (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    
    -- Stripe details
    stripe_invoice_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_invoice_pdf VARCHAR(512),
    
    -- Invoice details
    amount_due BIGINT NOT NULL,  -- Amount in cents
    amount_paid BIGINT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) NOT NULL,  -- 'DRAFT', 'OPEN', 'PAID', 'VOID', 'UNCOLLECTIBLE'
    
    -- Billing period
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    invoice_date TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_invoices_tenant ON tenant_invoices(tenant_id);
CREATE INDEX idx_tenant_invoices_status ON tenant_invoices(status);
CREATE INDEX idx_tenant_invoices_date ON tenant_invoices(invoice_date DESC);

COMMENT ON TABLE tenant_invoices IS 'Historical record of tenant invoices';

-- ============================================================================
-- Triggers for updated_at columns
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to new tables
CREATE TRIGGER update_user_mfa_secrets_updated_at
    BEFORE UPDATE ON user_mfa_secrets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_oauth_connections_updated_at
    BEFORE UPDATE ON user_oauth_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sync_jobs_updated_at
    BEFORE UPDATE ON data_sync_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_subscriptions_updated_at
    BEFORE UPDATE ON tenant_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Add missing columns to tenant_usage table (if needed)
-- ============================================================================

-- Check if columns exist, add if they don't
DO $$ 
BEGIN
    -- Add overage_charges column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tenant_usage' AND column_name = 'overage_charges'
    ) THEN
        ALTER TABLE tenant_usage ADD COLUMN overage_charges DECIMAL(10, 2) DEFAULT 0;
    END IF;
    
    -- Add storage_used_mb column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tenant_usage' AND column_name = 'storage_used_mb'
    ) THEN
        ALTER TABLE tenant_usage ADD COLUMN storage_used_mb BIGINT DEFAULT 0;
    END IF;
    
    -- Add updated_at column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tenant_usage' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE tenant_usage ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- ============================================================================
-- Views for easier access
-- ============================================================================

-- View: Tenant Subscription Summary
CREATE OR REPLACE VIEW tenant_subscription_summary AS
SELECT 
    t.tenant_id,
    t.organization_name,
    t.plan as tenant_plan,
    t.status as tenant_status,
    ts.status as subscription_status,
    ts.stripe_customer_id,
    ts.current_period_end,
    ts.cancel_at,
    tu.transaction_count as transactions_this_month,
    t.max_transactions_per_month as transaction_limit
FROM tenants t
LEFT JOIN tenant_subscriptions ts ON t.tenant_id = ts.tenant_id
LEFT JOIN tenant_usage tu ON t.tenant_id = tu.tenant_id 
    AND tu.period_start = DATE_TRUNC('month', CURRENT_DATE);

-- View: Data Sync Job Status
CREATE OR REPLACE VIEW data_sync_job_status AS
SELECT 
    j.id as job_id,
    j.tenant_id,
    j.name,
    j.connector_type,
    j.status,
    j.last_sync_at,
    j.last_sync_status,
    j.last_sync_count,
    j.total_synced,
    COUNT(h.id) as total_runs,
    COUNT(CASE WHEN h.status = 'SUCCESS' THEN 1 END) as successful_runs,
    COUNT(CASE WHEN h.status = 'FAILED' THEN 1 END) as failed_runs
FROM data_sync_jobs j
LEFT JOIN data_sync_history h ON j.id = h.job_id
GROUP BY j.id, j.tenant_id, j.name, j.connector_type, j.status, 
         j.last_sync_at, j.last_sync_status, j.last_sync_count, j.total_synced;

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Add MFA for demo admin user
INSERT INTO user_mfa_secrets (user_id, secret, enabled, backup_codes)
SELECT 
    id,
    'DEMO_SECRET_FOR_TESTING',
    FALSE,
    ARRAY['BACKUP01', 'BACKUP02', 'BACKUP03']
FROM tenant_users
WHERE email = 'admin@demo.com'
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- Grants (if using specific database roles)
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO fraud_api_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fraud_api_user;

-- ============================================================================
-- Migration Complete
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Phase 2 & 3 migration completed successfully!';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - user_mfa_secrets';
    RAISE NOTICE '  - user_oauth_connections';
    RAISE NOTICE '  - file_uploads';
    RAISE NOTICE '  - data_sync_jobs';
    RAISE NOTICE '  - data_sync_history';
    RAISE NOTICE '  - tenant_subscriptions';
    RAISE NOTICE '  - tenant_invoices';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  - tenant_subscription_summary';
    RAISE NOTICE '  - data_sync_job_status';
END $$;

