-- Migration: Portal & Account Management Tables
-- Adds tables for tenant_settings, team_invitations, and tenant_onboarding

-- ============================================================================
-- Tenant Settings Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_settings (
    tenant_id VARCHAR(255) PRIMARY KEY REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_settings_tenant ON tenant_settings(tenant_id);

COMMENT ON TABLE tenant_settings IS 'Account settings and preferences for tenants';

-- ============================================================================
-- Team Invitations Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS team_invitations (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'ANALYST',
    invited_by INTEGER REFERENCES tenant_users(id) ON DELETE SET NULL,
    invite_token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, ACCEPTED, EXPIRED
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_team_invitations_tenant ON team_invitations(tenant_id);
CREATE INDEX idx_team_invitations_email ON team_invitations(email);
CREATE INDEX idx_team_invitations_token ON team_invitations(invite_token);
CREATE INDEX idx_team_invitations_status ON team_invitations(status);

COMMENT ON TABLE team_invitations IS 'Pending team member invitations';

-- ============================================================================
-- Tenant Onboarding Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_onboarding (
    tenant_id VARCHAR(255) PRIMARY KEY REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    current_step VARCHAR(100),
    steps_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_onboarding_current_step ON tenant_onboarding(current_step);
CREATE INDEX idx_tenant_onboarding_completed ON tenant_onboarding(completed_at);

COMMENT ON TABLE tenant_onboarding IS 'Tracks customer onboarding progress';

-- ============================================================================
-- Triggers for updated_at
-- ============================================================================

CREATE TRIGGER update_tenant_settings_updated_at
    BEFORE UPDATE ON tenant_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_onboarding_updated_at
    BEFORE UPDATE ON tenant_onboarding
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Data (for demo tenant)
-- ============================================================================

-- Default settings for demo tenant
INSERT INTO tenant_settings (tenant_id, settings)
SELECT 'tenant_demo_123', '{
    "notifications_enabled": true,
    "email_alerts": true,
    "sms_alerts": false,
    "alert_threshold": 0.8,
    "daily_summary": true,
    "timezone": "UTC",
    "language": "en"
}'::jsonb
ON CONFLICT (tenant_id) DO NOTHING;

-- Initialize onboarding for demo tenant
INSERT INTO tenant_onboarding (tenant_id, current_step, steps_data)
SELECT 'tenant_demo_123', 'create_account', '{
    "steps": [
        {"step_id": "create_account", "step_name": "Create Account", "completed": true, "completed_at": "2025-10-30T00:00:00Z"},
        {"step_id": "verify_email", "step_name": "Verify Email", "completed": true, "completed_at": "2025-10-30T00:00:00Z"},
        {"step_id": "choose_plan", "step_name": "Choose Subscription Plan", "completed": false},
        {"step_id": "setup_payment", "step_name": "Setup Payment Method", "completed": false},
        {"step_id": "configure_basics", "step_name": "Basic Configuration", "completed": false},
        {"step_id": "upload_data", "step_name": "Upload Initial Data", "completed": false},
        {"step_id": "invite_team", "step_name": "Invite Team Members", "completed": false},
        {"step_id": "complete", "step_name": "Complete Onboarding", "completed": false}
    ]
}'::jsonb
ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================================================
-- Views
-- ============================================================================

-- View: Team Invitations Summary
CREATE OR REPLACE VIEW team_invitations_summary AS
SELECT 
    ti.id,
    ti.tenant_id,
    ti.email,
    ti.role,
    ti.status,
    ti.created_at,
    ti.expires_at,
    tu.full_name as invited_by_name,
    tu.email as invited_by_email,
    CASE 
        WHEN ti.status = 'ACCEPTED' THEN 'Accepted'
        WHEN ti.expires_at < CURRENT_TIMESTAMP THEN 'Expired'
        ELSE 'Pending'
    END as current_status
FROM team_invitations ti
LEFT JOIN tenant_users tu ON ti.invited_by = tu.id;

-- View: Onboarding Progress
CREATE OR REPLACE VIEW onboarding_progress AS
SELECT 
    t.tenant_id,
    t.organization_name,
    o.current_step,
    o.started_at,
    o.completed_at,
    CASE 
        WHEN o.completed_at IS NOT NULL THEN 100
        ELSE (
            SELECT COUNT(*)::float / 8 * 100
            FROM jsonb_array_elements(o.steps_data->'steps') step
            WHERE (step->>'completed')::boolean = true
        )
    END as progress_percentage,
    (
        SELECT COUNT(*)
        FROM jsonb_array_elements(o.steps_data->'steps') step
        WHERE (step->>'completed')::boolean = true
    ) as completed_steps
FROM tenants t
LEFT JOIN tenant_onboarding o ON t.tenant_id = o.tenant_id;

-- ============================================================================
-- Migration Complete
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Portal tables migration completed successfully!';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - tenant_settings';
    RAISE NOTICE '  - team_invitations';
    RAISE NOTICE '  - tenant_onboarding';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  - team_invitations_summary';
    RAISE NOTICE '  - onboarding_progress';
END $$;

