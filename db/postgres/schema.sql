-- PostgreSQL OLAP Schema for Fraud Detection Analytics

-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Drop existing objects
DROP TABLE IF EXISTS anomaly_events CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_time_of_day_stats;
DROP MATERIALIZED VIEW IF EXISTS mv_velocity_by_account;
DROP MATERIALIZED VIEW IF EXISTS mv_amount_buckets_hourly;
DROP TABLE IF EXISTS fact_transactions CASCADE;
DROP TABLE IF EXISTS dim_geo CASCADE;
DROP TABLE IF EXISTS dim_time CASCADE;
DROP TABLE IF EXISTS dim_account CASCADE;
DROP TABLE IF EXISTS etl_checkpoints CASCADE;

-- Dimension tables
CREATE TABLE dim_account (
    account_id INTEGER PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    status VARCHAR(16),
    first_txn_date DATE
);

CREATE TABLE dim_time (
    date_key DATE PRIMARY KEY,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    is_weekend BOOLEAN
);

CREATE TABLE dim_geo (
    geo_key SERIAL PRIMARY KEY,
    city VARCHAR(64),
    country VARCHAR(64),
    lat NUMERIC(9,6),
    lon NUMERIC(9,6),
    UNIQUE(city, country)
);

-- Fact table (partitioned by day)
CREATE TABLE fact_transactions (
    account_id INTEGER,
    txn_id INTEGER,
    amount NUMERIC(12,2),
    currency VARCHAR(8),
    mcc VARCHAR(8),
    channel VARCHAR(32),
    geom GEOGRAPHY(Point, 4326),
    city VARCHAR(64),
    country VARCHAR(64),
    txn_time TIMESTAMPTZ NOT NULL,
    day DATE GENERATED ALWAYS AS (DATE(txn_time)) STORED,
    hour SMALLINT GENERATED ALWAYS AS (EXTRACT(HOUR FROM txn_time)) STORED,
    status VARCHAR(16),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (txn_id, day)
) PARTITION BY RANGE (day);

-- Create partitions for last 30 days
DO $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..60 LOOP
        partition_date := CURRENT_DATE + i;
        partition_name := 'fact_transactions_' || TO_CHAR(partition_date, 'YYYY_MM_DD');
        
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF fact_transactions
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, partition_date, partition_date + INTERVAL '1 day');
    END LOOP;
END $$;

CREATE INDEX idx_fact_account_date ON fact_transactions(account_id, txn_time DESC);
CREATE INDEX idx_fact_amount ON fact_transactions(amount);
CREATE INDEX idx_fact_geo ON fact_transactions USING GIST(geom);
CREATE INDEX idx_fact_city ON fact_transactions(city, country);

-- Materialized views
CREATE MATERIALIZED VIEW mv_amount_buckets_hourly AS
SELECT 
    DATE_TRUNC('hour', txn_time) AS hour,
    CASE 
        WHEN amount < 10 THEN '0-10'
        WHEN amount < 50 THEN '10-50'
        WHEN amount < 100 THEN '50-100'
        WHEN amount < 500 THEN '100-500'
        WHEN amount < 5000 THEN '500-5K'
        ELSE '5K+'
    END AS bucket,
    COUNT(*) AS txn_count,
    SUM(amount) AS total_amount
FROM fact_transactions
GROUP BY hour, bucket
ORDER BY hour DESC, bucket;

CREATE INDEX idx_mv_amount_hour ON mv_amount_buckets_hourly(hour);

CREATE MATERIALIZED VIEW mv_velocity_by_account AS
SELECT 
    account_id,
    DATE_TRUNC('hour', txn_time) AS hour_window,
    COUNT(*) AS txn_count,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY amount) AS p95_amount
FROM fact_transactions
GROUP BY account_id, hour_window;

CREATE INDEX idx_mv_velocity_account ON mv_velocity_by_account(account_id, hour_window);

CREATE MATERIALIZED VIEW mv_time_of_day_stats AS
SELECT 
    hour,
    COUNT(*) AS total_txns,
    AVG(amount) AS avg_amount,
    STDDEV(amount) AS std_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median_amount
FROM fact_transactions
GROUP BY hour
ORDER BY hour;

-- Anomaly events table
CREATE TABLE anomaly_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id INTEGER,
    txn_id INTEGER,
    rule VARCHAR(64) NOT NULL,
    score NUMERIC(10,4),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    severity VARCHAR(16),
    extra JSONB
);

CREATE INDEX idx_anomalies_account ON anomaly_events(account_id, detected_at DESC);
CREATE INDEX idx_anomalies_rule ON anomaly_events(rule, detected_at DESC);

-- ETL checkpoint table
CREATE TABLE etl_checkpoints (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(128) NOT NULL,
    last_id INTEGER,
    last_timestamp TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_table)
);

INSERT INTO etl_checkpoints(source_table, last_id, last_timestamp) 
VALUES ('transactions', 0, NOW());

