-- Seed data for PostgreSQL OLAP

-- Insert dim_account data
INSERT INTO dim_account(account_id, customer_id, status, first_txn_date)
VALUES 
    (1, 'C001', 'FROZEN', CURRENT_DATE),
    (2, 'C002', 'ACTIVE', CURRENT_DATE),
    (3, 'C003', 'ACTIVE', CURRENT_DATE);

-- Insert time dimension
INSERT INTO dim_time(date_key, year, month, day, day_of_week, is_weekend)
SELECT 
    date_val,
    EXTRACT(YEAR FROM date_val),
    EXTRACT(MONTH FROM date_val),
    EXTRACT(DAY FROM date_val),
    EXTRACT(DOW FROM date_val),
    EXTRACT(DOW FROM date_val) IN (0, 6)
FROM generate_series(CURRENT_DATE - 30, CURRENT_DATE, INTERVAL '1 day') AS date_val
ON CONFLICT (date_key) DO NOTHING;

-- Sample fact data (ETL will populate this from Oracle)
-- Just inserting a few reference rows for now
INSERT INTO fact_transactions (account_id, txn_id, amount, currency, city, country, txn_time, status)
VALUES 
    (1, 1001, 25.50, 'USD', 'NYC', 'US', NOW() - INTERVAL '2 hours', 'APPROVED'),
    (2, 1002, 120.00, 'USD', 'NYC', 'US', NOW() - INTERVAL '3 hours', 'APPROVED'),
    (2, 1003, 350.00, 'USD', 'LA', 'US', NOW() - INTERVAL '2 hours', 'REVIEW');

