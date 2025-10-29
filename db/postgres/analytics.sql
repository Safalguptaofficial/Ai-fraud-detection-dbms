-- PostgreSQL Analytics Queries for Fraud Detection

-- Function to find midnight high-amount transactions
CREATE OR REPLACE FUNCTION get_midnight_high_amount_txns(days_back INTEGER DEFAULT 7)
RETURNS TABLE (
    txn_id INTEGER,
    account_id INTEGER,
    amount NUMERIC,
    txn_time TIMESTAMPTZ,
    hour INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ft.txn_id,
        ft.account_id,
        ft.amount,
        ft.txn_time,
        ft.hour
    FROM fact_transactions ft
    WHERE ft.hour BETWEEN 0 AND 5
      AND ft.amount > 5000
      AND ft.day >= CURRENT_DATE - INTERVAL '1 day' * days_back
    ORDER BY ft.txn_time DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to find velocity anomalies
CREATE OR REPLACE FUNCTION get_velocity_anomalies(
    hours_back INTEGER DEFAULT 24,
    threshold_percentile NUMERIC DEFAULT 0.95
)
RETURNS TABLE (
    account_id INTEGER,
    hour_window TIMESTAMPTZ,
    txn_count BIGINT,
    p95_peer NUMERIC,
    is_anomaly BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH account_stats AS (
        SELECT 
            a.account_id,
            DATE_TRUNC('hour', a.txn_time) AS hour_window,
            COUNT(*) AS txn_count
        FROM fact_transactions a
        WHERE a.txn_time >= NOW() - INTERVAL '1 hour' * hours_back
        GROUP BY a.account_id, hour_window
    ),
    peer_stats AS (
        SELECT 
            hour_window,
            PERCENTILE_CONT(threshold_percentile) WITHIN GROUP (ORDER BY txn_count) AS p95_count
        FROM account_stats
        GROUP BY hour_window
    )
    SELECT 
        ast.account_id,
        ast.hour_window,
        ast.txn_count,
        ps.p95_count,
        (ast.txn_count > COALESCE(ps.p95_count * 1.5, 0)) AS is_anomaly
    FROM account_stats ast
    JOIN peer_stats ps ON ast.hour_window = ps.hour_window
    WHERE ast.txn_count > COALESCE(ps.p95_count * 1.5, 0)
    ORDER BY ast.hour_window DESC, ast.txn_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to find geo-jump anomalies (PostGIS)
CREATE OR REPLACE FUNCTION get_geo_jump_anomalies(
    min_distance_km NUMERIC DEFAULT 800,
    max_time_hours NUMERIC DEFAULT 2
)
RETURNS TABLE (
    account_id INTEGER,
    txn_id INTEGER,
    distance_meters NUMERIC,
    time_diff_hours NUMERIC,
    from_city VARCHAR,
    to_city VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH txn_sequence AS (
        SELECT 
            account_id,
            txn_id,
            txn_time,
            city,
            geom,
            LAG(geom) OVER (PARTITION BY account_id ORDER BY txn_time) AS prev_geom,
            LAG(city) OVER (PARTITION BY account_id ORDER BY txn_time) AS prev_city,
            EXTRACT(EPOCH FROM (txn_time - LAG(txn_time) OVER (PARTITION BY account_id ORDER BY txn_time))) / 3600 AS time_diff_hours
        FROM fact_transactions
        WHERE geom IS NOT NULL
    )
    SELECT 
        account_id,
        txn_id,
        ST_Distance(geom, prev_geom) AS distance_meters,
        time_diff_hours,
        prev_city,
        city
    FROM txn_sequence
    WHERE prev_geom IS NOT NULL
      AND ST_Distance(geom, prev_geom) > min_distance_km * 1000
      AND time_diff_hours <= max_time_hours
    ORDER BY txn_time DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to find time-of-day z-score outliers
CREATE OR REPLACE FUNCTION get_time_of_day_zscore_outliers(
    z_threshold NUMERIC DEFAULT 2.5
)
RETURNS TABLE (
    txn_id INTEGER,
    account_id INTEGER,
    amount NUMERIC,
    hour INTEGER,
    z_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH hour_stats AS (
        SELECT 
            hour,
            AVG(amount) AS mean_amount,
            STDDEV(amount) AS std_amount
        FROM fact_transactions
        WHERE day >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY hour
    )
    SELECT 
        ft.txn_id,
        ft.account_id,
        ft.amount,
        ft.hour,
        ABS((ft.amount - hs.mean_amount) / NULLIF(hs.std_amount, 0)) AS z_score
    FROM fact_transactions ft
    JOIN hour_stats hs ON ft.hour = hs.hour
    WHERE ft.day >= CURRENT_DATE - INTERVAL '7 days'
      AND hs.std_amount > 0
      AND ABS((ft.amount - hs.mean_amount) / hs.std_amount) > z_threshold
    ORDER BY z_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_amount_buckets_hourly;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_velocity_by_account;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_time_of_day_stats;
    
    INSERT INTO system_logs(level, message, created_at)
    VALUES ('INFO', 'Refreshed all materialized views', NOW());
END;
$$ LANGUAGE plpgsql;

-- Helper table for system logs
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(16),
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

