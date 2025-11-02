-- Migration 002: Add tenant_id to Existing Tables
-- Description: Adds tenant_id column to all data tables for multi-tenancy support
-- Date: 2025-10-30
-- Author: AI Implementation

-- ============================================================================
-- BACKUP REMINDER
-- ============================================================================

-- ⚠️ IMPORTANT: Backup your database before running this migration!
-- pg_dump -U postgres -d frauddb > backup_before_tenancy.sql

-- ============================================================================
-- ADD TENANT_ID COLUMNS
-- ============================================================================

-- Add tenant_id to accounts (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'accounts' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE accounts ADD COLUMN tenant_id VARCHAR(64);
        RAISE NOTICE 'Added tenant_id to accounts table';
    END IF;
END $$;

-- Add tenant_id to transactions (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'transactions' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE transactions ADD COLUMN tenant_id VARCHAR(64);
        RAISE NOTICE 'Added tenant_id to transactions table';
    END IF;
END $$;

-- Add tenant_id to fraud_alerts (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'fraud_alerts' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE fraud_alerts ADD COLUMN tenant_id VARCHAR(64);
        RAISE NOTICE 'Added tenant_id to fraud_alerts table';
    END IF;
END $$;

-- Add tenant_id to system_logs (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'system_logs' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE system_logs ADD COLUMN tenant_id VARCHAR(64);
        RAISE NOTICE 'Added tenant_id to system_logs table';
    END IF;
END $$;

-- ============================================================================
-- MIGRATE EXISTING DATA
-- ============================================================================

-- Update existing records to use default tenant
UPDATE accounts 
SET tenant_id = 'default-tenant-demo' 
WHERE tenant_id IS NULL;

UPDATE transactions 
SET tenant_id = 'default-tenant-demo' 
WHERE tenant_id IS NULL;

UPDATE fraud_alerts 
SET tenant_id = 'default-tenant-demo' 
WHERE tenant_id IS NULL;

UPDATE system_logs 
SET tenant_id = 'default-tenant-demo' 
WHERE tenant_id IS NULL;

-- ============================================================================
-- MAKE TENANT_ID NOT NULL
-- ============================================================================

-- Make tenant_id NOT NULL after data migration
ALTER TABLE accounts ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE transactions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE fraud_alerts ALTER COLUMN tenant_id SET NOT NULL;
-- system_logs can remain nullable (for system-wide logs)

-- ============================================================================
-- ADD FOREIGN KEY CONSTRAINTS
-- ============================================================================

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

-- ============================================================================
-- CREATE COMPOSITE INDEXES
-- ============================================================================

-- Drop old indexes if they exist (to rebuild with tenant_id)
DROP INDEX IF EXISTS idx_accounts_customer_id;
DROP INDEX IF EXISTS idx_accounts_status;
DROP INDEX IF EXISTS idx_transactions_account_id;
DROP INDEX IF EXISTS idx_transactions_txn_time;
DROP INDEX IF EXISTS idx_transactions_amount;
DROP INDEX IF EXISTS idx_fraud_alerts_account_id;
DROP INDEX IF EXISTS idx_fraud_alerts_handled;
DROP INDEX IF EXISTS idx_fraud_alerts_created_at;

-- Create new composite indexes with tenant_id first (for better performance)
CREATE INDEX idx_accounts_tenant_id ON accounts(tenant_id, id);
CREATE INDEX idx_accounts_tenant_customer ON accounts(tenant_id, customer_id);
CREATE INDEX idx_accounts_tenant_status ON accounts(tenant_id, status);

CREATE INDEX idx_transactions_tenant_id ON transactions(tenant_id, id);
CREATE INDEX idx_transactions_tenant_time ON transactions(tenant_id, txn_time DESC);
CREATE INDEX idx_transactions_tenant_account ON transactions(tenant_id, account_id);
CREATE INDEX idx_transactions_tenant_amount ON transactions(tenant_id, amount DESC);
CREATE INDEX idx_transactions_tenant_status ON transactions(tenant_id, status);

CREATE INDEX idx_alerts_tenant_id ON fraud_alerts(tenant_id, id);
CREATE INDEX idx_alerts_tenant_handled ON fraud_alerts(tenant_id, handled);
CREATE INDEX idx_alerts_tenant_time ON fraud_alerts(tenant_id, created_at DESC);
CREATE INDEX idx_alerts_tenant_severity ON fraud_alerts(tenant_id, severity);
CREATE INDEX idx_alerts_tenant_account ON fraud_alerts(tenant_id, account_id);

CREATE INDEX idx_logs_tenant_time ON system_logs(tenant_id, created_at DESC) WHERE tenant_id IS NOT NULL;

-- ============================================================================
-- UPDATE TABLE CONSTRAINTS
-- ============================================================================

-- Ensure account references are tenant-aware (optional, for strict isolation)
-- This ensures accounts and transactions belong to same tenant
-- Commented out by default - enable if you want strict referential integrity

-- ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_account_id_fkey;
-- ALTER TABLE transactions ADD CONSTRAINT transactions_account_tenant_fkey
--     FOREIGN KEY (tenant_id, account_id) 
--     REFERENCES accounts(tenant_id, id);

-- ============================================================================
-- ANALYTICS TABLES (IF THEY EXIST)
-- ============================================================================

-- Add tenant_id to analytics tables if they exist
DO $$ 
BEGIN
    -- dim_account
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dim_account') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'dim_account' AND column_name = 'tenant_id'
        ) THEN
            ALTER TABLE dim_account ADD COLUMN tenant_id VARCHAR(64);
            UPDATE dim_account SET tenant_id = 'default-tenant-demo' WHERE tenant_id IS NULL;
            CREATE INDEX idx_dim_account_tenant ON dim_account(tenant_id);
        END IF;
    END IF;

    -- fact_transactions
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'fact_transactions') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'fact_transactions' AND column_name = 'tenant_id'
        ) THEN
            ALTER TABLE fact_transactions ADD COLUMN tenant_id VARCHAR(64);
            UPDATE fact_transactions SET tenant_id = 'default-tenant-demo' WHERE tenant_id IS NULL;
            CREATE INDEX idx_fact_transactions_tenant ON fact_transactions(tenant_id);
        END IF;
    END IF;

    -- anomaly_events
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'anomaly_events') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'anomaly_events' AND column_name = 'tenant_id'
        ) THEN
            ALTER TABLE anomaly_events ADD COLUMN tenant_id VARCHAR(64);
            UPDATE anomaly_events SET tenant_id = 'default-tenant-demo' WHERE tenant_id IS NULL;
            CREATE INDEX idx_anomaly_events_tenant ON anomaly_events(tenant_id);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tenant_id was added to all tables
DO $$
DECLARE
    accounts_count INT;
    transactions_count INT;
    alerts_count INT;
BEGIN
    SELECT COUNT(*) INTO accounts_count FROM accounts WHERE tenant_id = 'default-tenant-demo';
    SELECT COUNT(*) INTO transactions_count FROM transactions WHERE tenant_id = 'default-tenant-demo';
    SELECT COUNT(*) INTO alerts_count FROM fraud_alerts WHERE tenant_id = 'default-tenant-demo';
    
    RAISE NOTICE 'Migration 002 completed successfully';
    RAISE NOTICE 'Accounts migrated: %', accounts_count;
    RAISE NOTICE 'Transactions migrated: %', transactions_count;
    RAISE NOTICE 'Alerts migrated: %', alerts_count;
    RAISE NOTICE 'All existing data assigned to: default-tenant-demo';
END $$;

-- Show table structures
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name IN ('accounts', 'transactions', 'fraud_alerts')
    AND column_name = 'tenant_id'
ORDER BY table_name;

