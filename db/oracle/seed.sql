-- Seed data for Oracle OLTP

-- Insert accounts
INSERT INTO accounts(id, customer_id, status) VALUES (seq_accounts.NEXTVAL, 'C001', 'ACTIVE');
INSERT INTO accounts(id, customer_id, status) VALUES (seq_accounts.NEXTVAL, 'C002', 'ACTIVE');
INSERT INTO accounts(id, customer_id, status) VALUES (seq_accounts.NEXTVAL, 'C003', 'ACTIVE');
INSERT INTO accounts(id, customer_id, status) VALUES (seq_accounts.NEXTVAL, 'C004', 'ACTIVE');
INSERT INTO accounts(id, customer_id, status) VALUES (seq_accounts.NEXTVAL, 'C005', 'ACTIVE');

-- Normal transactions for account 1
INSERT INTO transactions(id, account_id, amount, currency, merchant, mcc, channel, city, country, txn_time, status)
VALUES (seq_txns.NEXTVAL, 1, 25.50, 'USD', 'COFFEE SHOP', '5812', 'POS', 'NYC', 'US', SYSTIMESTAMP - 2, 'APPROVED');

INSERT INTO transactions(id, account_id, amount, currency, merchant, mcc, channel, city, country, txn_time, status)
VALUES (seq_txns.NEXTVAL, 1, 45.00, 'USD', 'GROCERY STORE', '5411', 'POS', 'NYC', 'US', SYSTIMESTAMP - 1, 'APPROVED');

-- Suspicious transaction: midnight high amount
INSERT INTO transactions(id, account_id, amount, currency, merchant, mcc, channel, city, country, txn_time, status)
VALUES (seq_txns.NEXTVAL, 1, 7500.00, 'USD', 'ATM-CORP', '6011', 'ATM', 'NYC', 'US', 
        TO_TIMESTAMP(TO_CHAR(SYSDATE, 'YYYY-MM-DD') || ' 00:30:00', 'YYYY-MM-DD HH24:MI:SS'), 'APPROVED');

-- Geo jump for account 2
INSERT INTO transactions(id, account_id, amount, currency, merchant, mcc, channel, lat, lon, city, country, txn_time, status)
VALUES (seq_txns.NEXTVAL, 2, 120.00, 'USD', 'RESTAURANT', '5812', 'POS', 40.7128, -74.0060, 'NYC', 'US', 
        SYSTIMESTAMP - 3, 'APPROVED');

INSERT INTO transactions(id, account_id, amount, currency, merchant, mcc, channel, lat, lon, city, country, txn_time, status)
VALUES (seq_txns.NEXTVAL, 2, 350.00, 'USD', 'HOTEL', '7011', 'POS', 34.0522, -118.2437, 'LA', 'US', 
        SYSTIMESTAMP - 2, 'APPROVED');

COMMIT;

