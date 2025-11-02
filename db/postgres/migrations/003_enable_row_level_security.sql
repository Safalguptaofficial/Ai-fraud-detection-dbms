-- Migration 003: Enable Row-Level Security
-- Description: Implements PostgreSQL Row-Level Security for tenant isolation
-- Date: 2025-10-30
-- Author: AI Implementation

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tenant tables
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES
-- ============================================================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS tenant_isolation_policy ON accounts;
DROP POLICY IF EXISTS tenant_isolation_policy ON transactions;
DROP POLICY IF EXISTS tenant_isolation_policy ON fraud_alerts;
DROP POLICY IF EXISTS tenant_isolation_policy ON system_logs;

-- Create tenant isolation policy for accounts
CREATE POLICY tenant_isolation_policy ON accounts
    USING (tenant_id = current_setting('app.current_tenant', true)::text);

-- Create tenant isolation policy for transactions
CREATE POLICY tenant_isolation_policy ON transactions
    USING (tenant_id = current_setting('app.current_tenant', true)::text);

-- Create tenant isolation policy for fraud_alerts
CREATE POLICY tenant_isolation_policy ON fraud_alerts
    USING (tenant_id = current_setting('app.current_tenant', true)::text);

-- Create tenant isolation policy for system_logs (only if tenant_id is set)
CREATE POLICY tenant_isolation_policy ON system_logs
    USING (
        tenant_id IS NULL 
        OR tenant_id = current_setting('app.current_tenant', true)::text
    );

-- ============================================================================
-- TENANT CONTEXT FUNCTIONS
-- ============================================================================

-- Function to set current tenant (used by application middleware)
CREATE OR REPLACE FUNCTION set_current_tenant(p_tenant_id text)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', p_tenant_id, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current tenant
CREATE OR REPLACE FUNCTION get_current_tenant()
RETURNS text AS $$
BEGIN
    RETURN current_setting('app.current_tenant', true)::text;
END;
$$ LANGUAGE plpgsql;

-- Function to clear current tenant
CREATE OR REPLACE FUNCTION clear_current_tenant()
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', '', false);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ADMIN BYPASS (for superuser operations)
-- ============================================================================

-- Allow superuser/admin to bypass RLS for maintenance
ALTER TABLE accounts FORCE ROW LEVEL SECURITY;
ALTER TABLE transactions FORCE ROW LEVEL SECURITY;
ALTER TABLE fraud_alerts FORCE ROW LEVEL SECURITY;
-- Don't force RLS on system_logs to allow system-wide logging

-- Create bypass policy for superuser (optional)
-- Uncomment if you need admin user to see all tenants
/*
CREATE POLICY admin_bypass_policy ON accounts
    TO admin_role
    USING (true);

CREATE POLICY admin_bypass_policy ON transactions
    TO admin_role
    USING (true);

CREATE POLICY admin_bypass_policy ON fraud_alerts
    TO admin_role
    USING (true);
*/

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant execute permission on tenant functions
GRANT EXECUTE ON FUNCTION set_current_tenant(text) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_current_tenant() TO PUBLIC;
GRANT EXECUTE ON FUNCTION clear_current_tenant() TO PUBLIC;

-- ============================================================================
-- TESTING & VERIFICATION
-- ============================================================================

-- Test RLS functionality
DO $$
DECLARE
    tenant1_id VARCHAR(64) := 'default-tenant-demo';
    tenant2_id VARCHAR(64) := 'test-tenant-isolation';
    count1 INT;
    count2 INT;
BEGIN
    -- Create test tenant
    INSERT INTO tenants (tenant_id, organization_name, subdomain, admin_email, plan, status)
    VALUES (tenant2_id, 'Test Tenant', 'test-isolation', 'test@example.com', 'STARTER', 'TRIAL')
    ON CONFLICT DO NOTHING;
    
    -- Set tenant context to tenant1
    PERFORM set_current_tenant(tenant1_id);
    
    -- Count records for tenant1
    SELECT COUNT(*) INTO count1 FROM accounts;
    
    -- Set tenant context to tenant2
    PERFORM set_current_tenant(tenant2_id);
    
    -- Count records for tenant2 (should be 0)
    SELECT COUNT(*) INTO count2 FROM accounts;
    
    -- Clear context
    PERFORM clear_current_tenant();
    
    -- Report results
    IF count2 = 0 THEN
        RAISE NOTICE 'RLS Test PASSED: Tenant isolation working correctly';
        RAISE NOTICE 'Tenant 1 sees % accounts', count1;
        RAISE NOTICE 'Tenant 2 sees % accounts (expected 0)', count2;
    ELSE
        RAISE WARNING 'RLS Test FAILED: Tenant 2 should see 0 accounts but sees %', count2;
    END IF;
    
    -- Cleanup test tenant
    DELETE FROM tenants WHERE tenant_id = tenant2_id;
END $$;

-- ============================================================================
-- AUDIT LOG FOR RLS
-- ============================================================================

-- Log RLS policy changes
INSERT INTO audit_logs (
    tenant_id,
    action,
    resource_type,
    severity,
    new_value
) VALUES (
    'default-tenant-demo',
    'ENABLE_RLS',
    'DATABASE',
    'INFO',
    '{"tables": ["accounts", "transactions", "fraud_alerts", "system_logs"], "policies": ["tenant_isolation_policy"]}'::jsonb
);

-- ============================================================================
-- VERIFICATION OUTPUT
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '================================================================';
    RAISE NOTICE 'Migration 003: Row-Level Security COMPLETED';
    RAISE NOTICE '================================================================';
    RAISE NOTICE 'RLS enabled on tables:';
    RAISE NOTICE '  - accounts';
    RAISE NOTICE '  - transactions';
    RAISE NOTICE '  - fraud_alerts';
    RAISE NOTICE '  - system_logs';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions created:';
    RAISE NOTICE '  - set_current_tenant(text)';
    RAISE NOTICE '  - get_current_tenant()';
    RAISE NOTICE '  - clear_current_tenant()';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANT: Application must call set_current_tenant() before queries!';
    RAISE NOTICE 'Example: SELECT set_current_tenant(''tenant_id'');';
    RAISE NOTICE '================================================================';
END $$;

-- Show RLS status
SELECT 
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE tablename IN ('accounts', 'transactions', 'fraud_alerts', 'system_logs')
ORDER BY tablename;

-- Show RLS policies
SELECT 
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename IN ('accounts', 'transactions', 'fraud_alerts', 'system_logs')
ORDER BY tablename, policyname;

