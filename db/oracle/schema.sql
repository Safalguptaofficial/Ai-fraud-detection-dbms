-- Oracle OLTP Schema for Fraud Detection

-- Drop existing objects
DROP SEQUENCE seq_logs;
DROP SEQUENCE seq_alerts;
DROP SEQUENCE seq_txns;
DROP SEQUENCE seq_accounts;

DROP TABLE system_logs;
DROP TABLE fraud_alerts;
DROP TABLE transactions;
DROP TABLE accounts;

-- Ініціалізую структури для створення сутностей
CREATE SEQUENCE seq_accounts START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_txns START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_alerts START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_logs START WITH 1 INCREMENT BY 1;

-- Таблиця account
CREATE TABLE accounts (
    id NUMBER PRIMARY KEY,
    customer_id VARCHAR2(64) NOT NULL,
    status VARCHAR2(16) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'FROZEN', 'CLOSED')),
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- Таблиця transactions
CREATE TABLE transactions (
    id NUMBER PRIMARY KEY,
    account_id NUMBER REFERENCES accounts(id),
    amount NUMBER(12,2) NOT NULL,
    currency VARCHAR2(8) DEFAULT 'USD',
    merchant VARCHAR2(128),
    mcc VARCHAR2(8),
    channel VARCHAR2(32),
    device_id VARCHAR2(64),
    lat NUMBER(9,6),
    lon NUMBER(9,6),
    city VARCHAR2(64),
    country VARCHAR2(64),
    txn_time TIMESTAMP NOT NULL,
    auth_code VARCHAR2(32),
    status VARCHAR2(16) DEFAULT 'APPROVED' CHECK (status IN ('APPROVED', 'DECLINED', 'REVIEW')),
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

-- Індекси
CREATE INDEX idx_txns_account_id ON transactions(account_id);
CREATE INDEX idx_txns_time ON transactions(txn_time);
CREATE INDEX idx_txns_amount ON transactions(amount);
CREATE INDEX idx_txns_location ON transactions(city, country);
CREATE INDEX idx_txns_status ON transactions(status);

-- Таблиця fraud_alerts
CREATE TABLE fraud_alerts (
    id NUMBER PRIMARY KEY,
    account_id NUMBER REFERENCES accounts(id),
    txn_id NUMBER REFERENCES transactions(id),
    rule_code VARCHAR2(32) NOT NULL,
    severity VARCHAR2(16) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),
    reason CLOB,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    handled NUMBER(1) DEFAULT 0,
    handled_at TIMESTAMP,
    handled_by VARCHAR2(128)
);

CREATE INDEX idx_alerts_account ON fraud_alerts(account_id);
CREATE INDEX idx_alerts_unhandled ON fraud_alerts(handled, created_at);

-- Таблиця system_logs
CREATE TABLE system_logs (
    id NUMBER PRIMARY KEY,
    level VARCHAR2(16),
    message CLOB,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_logs_created ON system_logs(created_at);

