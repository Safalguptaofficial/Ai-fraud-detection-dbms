-- Oracle Triggers for Fraud Detection

CREATE OR REPLACE PACKAGE pkg_rules AS
    FUNCTION is_midnight(txn_time TIMESTAMP) RETURN BOOLEAN;
    FUNCTION is_high_amount(amount NUMBER) RETURN BOOLEAN;
    FUNCTION is_geo_jump(p_account_id NUMBER, p_lat NUMBER, p_lon NUMBER, p_txn_time TIMESTAMP) RETURN BOOLEAN;
    FUNCTION velocity_spike(p_account_id NUMBER, p_txn_time TIMESTAMP) RETURN BOOLEAN;
END pkg_rules;
/

CREATE OR REPLACE PACKAGE BODY pkg_rules AS
    
    FUNCTION is_midnight(txn_time TIMESTAMP) RETURN BOOLEAN IS
    BEGIN
        RETURN EXTRACT(HOUR FROM txn_time) BETWEEN 0 AND 5;
    END;
    
    FUNCTION is_high_amount(amount NUMBER) RETURN BOOLEAN IS
    BEGIN
        RETURN amount > 5000;
    END;
    
    FUNCTION is_geo_jump(p_account_id NUMBER, p_lat NUMBER, p_lon NUMBER, p_txn_time TIMESTAMP) RETURN BOOLEAN IS
        v_prev_lat NUMBER;
        v_prev_lon NUMBER;
        v_prev_time TIMESTAMP;
        v_distance_km NUMBER;
        v_time_diff_hours NUMBER;
        v_earth_radius_km NUMBER := 6371;
        v_dlat NUMBER;
        v_dlon NUMBER;
        v_a NUMBER;
    BEGIN
        IF p_lat IS NULL OR p_lon IS NULL THEN
            RETURN FALSE;
        END IF;
        
        -- Find the most recent transaction for this account
        SELECT lat, lon, txn_time INTO v_prev_lat, v_prev_lon, v_prev_time
        FROM transactions
        WHERE account_id = p_account_id
          AND id != (SELECT MAX(id) FROM transactions WHERE account_id = p_account_id AND txn_time < p_txn_time)
          AND lat IS NOT NULL
          AND lon IS NOT NULL
        ORDER BY txn_time DESC
        FETCH FIRST 1 ROW ONLY;
        
        IF v_prev_lat IS NULL THEN
            RETURN FALSE;
        END IF;
        
        -- Calculate time difference
        v_time_diff_hours := EXTRACT(DAY FROM (p_txn_time - v_prev_time)) * 24 + 
                             EXTRACT(HOUR FROM (p_txn_time - v_prev_time));
        
        IF v_time_diff_hours > 2 THEN
            RETURN FALSE;
        END IF;
        
        -- Haversine formula for distance
        v_dlat := RADIANS(p_lat - v_prev_lat);
        v_dlon := RADIANS(p_lon - v_prev_lon);
        
        v_a := SIN(v_dlat/2) * SIN(v_dlat/2) + 
               COS(RADIANS(v_prev_lat)) * COS(RADIANS(p_lat)) * 
               SIN(v_dlon/2) * SIN(v_dlon/2);
        
        v_distance_km := 2 * ATAN2(SQRT(v_a), SQRT(1-v_a)) * v_earth_radius_km;
        
        RETURN v_distance_km > 800;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN FALSE;
    END;
    
    FUNCTION velocity_spike(p_account_id NUMBER, p_txn_time TIMESTAMP) RETURN BOOLEAN IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM transactions
        WHERE account_id = p_account_id
          AND txn_time BETWEEN p_txn_time - INTERVAL '10' MINUTE AND p_txn_time;
        
        RETURN v_count > 5;
    END;
    
END pkg_rules;
/

CREATE OR REPLACE TRIGGER trg_txn_insert_after
AFTER INSERT ON transactions
FOR EACH ROW
DECLARE
    v_is_midnight BOOLEAN;
    v_is_high_amt BOOLEAN;
    v_is_geo_jump BOOLEAN;
    v_is_velocity BOOLEAN;
    v_severity VARCHAR2(16);
    v_reason VARCHAR2(512);
    v_rule_code VARCHAR2(32);
    PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
    -- Midnight high amount check
    v_is_midnight := pkg_rules.is_midnight(:NEW.txn_time);
    v_is_high_amt := pkg_rules.is_high_amount(:NEW.amount);
    
    IF v_is_midnight AND v_is_high_amt THEN
        v_rule_code := 'MIDNIGHT_5K';
        v_severity := 'HIGH';
        v_reason := 'High-amount transaction between 00:00–05:00';
        
        INSERT INTO fraud_alerts(id, account_id, txn_id, rule_code, severity, reason, created_at)
        VALUES (seq_alerts.NEXTVAL, :NEW.account_id, :NEW.id, v_rule_code, v_severity, v_reason, SYSTIMESTAMP);
        
        UPDATE accounts SET status='FROZEN', updated_at=SYSTIMESTAMP WHERE id=:NEW.account_id;
        :NEW.status := 'REVIEW';
    END IF;
    
    -- Geo jump check
    v_is_geo_jump := pkg_rules.is_geo_jump(:NEW.account_id, :NEW.lat, :NEW.lon, :NEW.txn_time);
    IF v_is_geo_jump AND NOT (v_is_midnight AND v_is_high_amt) THEN
        v_rule_code := 'GEO_JUMP';
        v_severity := 'MEDIUM';
        v_reason := 'Geographical jump >800km within 2 hours';
        
        INSERT INTO fraud_alerts(id, account_id, txn_id, rule_code, severity, reason, created_at)
        VALUES (seq_alerts.NEXTVAL, :NEW.account_id, :NEW.id, v_rule_code, v_severity, v_reason, SYSTIMESTAMP);
        
        :NEW.status := 'REVIEW';
    END IF;
    
    -- Velocity spike check
    v_is_velocity := pkg_rules.velocity_spike(:NEW.account_id, :NEW.txn_time);
    IF v_is_velocity AND NOT (v_is_midnight AND v_is_high_amt) AND NOT v_is_geo_jump THEN
        v_rule_code := 'VELOCITY_SPIKE';
        v_severity := 'MEDIUM';
        v_reason := 'Transaction velocity spike: >5 txns in 10 min';
        
        INSERT INTO fraud_alerts(id, account_id, txn_id, rule_code, severity, reason, created_at)
        VALUES (seq_alerts.NEXTVAL, :NEW.account_id, :NEW.id, v_rule_code, v_severity, v_reason, SYSTIMESTAMP);
        
        :NEW.status := 'REVIEW';
    END IF;
    
    COMMIT;
    
EXCEPTION WHEN OTHERS THEN
    INSERT INTO system_logs(id, level, message, created_at)
    VALUES (seq_logs.NEXTVAL, 'ERROR', 'Trigger error: ' || SQLERRM, SYSTIMESTAMP);
    COMMIT;
END;
/

