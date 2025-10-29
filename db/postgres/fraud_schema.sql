-- PostgreSQL Comprehensive Schema for Fraud Detection
-- Includes both OLTP (transactional) and OLAP (analytical) tables

-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Drop existing objects
DROP TABLE IF EXISTS fraud_alerts CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS system_logs CASCADE;
DROP SEQUENCE IF EXISTS seq_accounts CASCADE;
DROP SEQUENCE IF EXISTS seq_txns CASCADE;
DROP SEQUENCE IF EXISTS seq_alerts CASCADE;
DROP SEQUENCE IF EXISTS seq_logs CASCADE;

-- Create sequences
CREATE SEQUENCE seq_accounts START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_txns START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_alerts START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_logs START WITH 1 INCREMENT BY 1;

-- OLTP Tables (for real-time fraud detection)

-- Accounts table
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_accounts'),
    customer_id VARCHAR(64) NOT NULL,
    status VARCHAR(16) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'FROZEN', 'CLOSED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_txns'),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    merchant VARCHAR(128),
    mcc VARCHAR(4), -- Merchant Category Code
    channel VARCHAR(16) CHECK (channel IN ('ATM', 'POS', 'ONLINE', 'MOBILE', 'PHONE')),
    city VARCHAR(64),
    country VARCHAR(2),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    txn_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fraud alerts table
CREATE TABLE fraud_alerts (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_alerts'),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    txn_id INTEGER REFERENCES transactions(id),
    rule_code VARCHAR(32) NOT NULL,
    severity VARCHAR(8) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    handled BOOLEAN DEFAULT FALSE,
    handled_at TIMESTAMP,
    handled_by VARCHAR(64)
);

-- System logs table
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_logs'),
    level VARCHAR(8) CHECK (level IN ('DEBUG', 'INFO', 'WARN', 'ERROR')),
    message TEXT NOT NULL,
    module VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_txn_time ON transactions(txn_time);
CREATE INDEX idx_transactions_amount ON transactions(amount);
CREATE INDEX idx_transactions_location ON transactions(latitude, longitude);
CREATE INDEX idx_fraud_alerts_account_id ON fraud_alerts(account_id);
CREATE INDEX idx_fraud_alerts_handled ON fraud_alerts(handled);
CREATE INDEX idx_fraud_alerts_created_at ON fraud_alerts(created_at);

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO accounts (customer_id, status) VALUES
('CUST001', 'ACTIVE'),
('CUST002', 'FROZEN'),
('CUST003', 'ACTIVE'),
('CUST004', 'ACTIVE'),
('CUST005', 'CLOSED');

INSERT INTO transactions (account_id, amount, currency, merchant, mcc, channel, city, country, latitude, longitude) VALUES
(1, 150.00, 'USD', 'STARBUCKS', '5814', 'POS', 'New York', 'US', 40.7128, -74.0060),
(2, 2500.00, 'USD', 'ATM-CORP', '6011', 'ATM', 'Los Angeles', 'US', 34.0522, -118.2437),
(3, 75.50, 'USD', 'AMAZON', '5942', 'ONLINE', 'Chicago', 'US', 41.8781, -87.6298),
(1, 5000.00, 'USD', 'WIRE-TRANSFER', '6010', 'ONLINE', 'Miami', 'US', 25.7617, -80.1918),
(4, 1200.00, 'USD', 'GAS-STATION', '5541', 'POS', 'Seattle', 'US', 47.6062, -122.3321);

INSERT INTO fraud_alerts (account_id, txn_id, rule_code, severity, reason) VALUES
(2, 2, 'VELOCITY_HIGH', 'HIGH', 'Transaction velocity exceeds threshold'),
(1, 4, 'GEO_JUMP', 'MEDIUM', 'Geographic location jump detected'),
(3, 3, 'AMOUNT_ANOMALY', 'HIGH', 'Transaction amount significantly higher than usual'),
(4, 5, 'TIME_ANOMALY', 'LOW', 'Transaction outside normal hours');

-- Create materialized views for analytics (OLAP)
CREATE MATERIALIZED VIEW mv_account_stats AS
SELECT 
    a.id as account_id,
    a.customer_id,
    a.status,
    COUNT(t.id) as total_transactions,
    SUM(t.amount) as total_amount,
    AVG(t.amount) as avg_amount,
    MAX(t.amount) as max_amount,
    MIN(t.txn_time) as first_transaction,
    MAX(t.txn_time) as last_transaction
FROM accounts a
LEFT JOIN transactions t ON a.id = t.account_id
GROUP BY a.id, a.customer_id, a.status;

CREATE MATERIALIZED VIEW mv_fraud_alerts_summary AS
SELECT 
    DATE(created_at) as alert_date,
    severity,
    COUNT(*) as alert_count,
    COUNT(CASE WHEN handled = FALSE THEN 1 END) as open_alerts
FROM fraud_alerts
GROUP BY DATE(created_at), severity
ORDER BY alert_date DESC;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW mv_account_stats;
REFRESH MATERIALIZED VIEW mv_fraud_alerts_summary;

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_fraud_analytics()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_account_stats;
    REFRESH MATERIALIZED VIEW mv_fraud_alerts_summary;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;
