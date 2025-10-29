import os
import time
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
import oracledb
import psycopg
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

ORACLE_URI = os.getenv("ORACLE_URI")
POSTGRES_URI = os.getenv("POSTGRES_URI")
ETL_INTERVAL = int(os.getenv("ETL_INTERVAL", "60"))


def etl_oracle_to_postgres():
    logger.info("Starting ETL: Oracle -> Postgres")
    try:
        # Connect to Oracle
        oracle_conn = oracledb.connect(ORACLE_URI)
        oracle_cursor = oracle_conn.cursor()
        
        # Connect to Postgres
        postgres_conn = psycopg.connect(POSTGRES_URI)
        postgres_cursor = postgres_conn.cursor()
        
        # Get checkpoint
        postgres_cursor.execute("SELECT last_id, last_timestamp FROM etl_checkpoints WHERE source_table = 'transactions'")
        checkpoint = postgres_cursor.fetchone()
        last_id = checkpoint[0] if checkpoint else 0
        
        # Fetch new transactions
        oracle_cursor.execute("""
            SELECT id, account_id, amount, currency, merchant, mcc, channel,
                   lat, lon, city, country, txn_time, status, created_at
            FROM transactions
            WHERE id > :last_id
            ORDER BY id
        """, [last_id])
        
        rows = oracle_cursor.fetchall()
        logger.info(f"Fetched {len(rows)} new transactions")
        
        for row in rows:
            txn_id, account_id, amount, currency, merchant, mcc, channel, lat, lon, city, country, txn_time, status, created_at = row
            
            # Create geometry if lat/lon exist
            geom = None
            if lat and lon:
                geom = f"POINT({lon} {lat})"
            
            postgres_cursor.execute("""
                INSERT INTO fact_transactions (
                    account_id, txn_id, amount, currency, mcc, channel,
                    geom, city, country, txn_time, status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::geography, %s, %s, %s, %s, %s)
                ON CONFLICT (txn_id, day) DO NOTHING
            """, [
                account_id, txn_id, amount, currency, mcc, channel,
                geom, city, country, txn_time, status, created_at
            ])
            
            # Update checkpoint
            postgres_cursor.execute("""
                UPDATE etl_checkpoints
                SET last_id = %s, last_timestamp = %s, updated_at = NOW()
                WHERE source_table = 'transactions'
            """, [txn_id, txn_time])
        
        postgres_conn.commit()
        logger.info(f"ETL complete. Processed {len(rows)} rows.")
        
        oracle_cursor.close()
        oracle_conn.close()
        postgres_cursor.close()
        postgres_conn.close()
        
    except Exception as e:
        logger.error(f"ETL error: {str(e)}", exc_info=True)


def refresh_analytics():
    logger.info("Refreshing analytics")
    try:
        postgres_conn = psycopg.connect(POSTGRES_URI)
        postgres_cursor = postgres_conn.cursor()
        
        # Refresh materialized views
        postgres_cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_amount_buckets_hourly")
        postgres_cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_velocity_by_account")
        postgres_cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_time_of_day_stats")
        
        # Run anomaly detection
        postgres_cursor.execute("SELECT * FROM get_geo_jump_anomalies()")
        geo_jumps = postgres_cursor.fetchall()
        
        for row in geo_jumps:
            account_id, txn_id, distance, time_diff, from_city, to_city = row
            postgres_cursor.execute("""
                INSERT INTO anomaly_events (account_id, txn_id, rule, severity, extra)
                VALUES (%s, %s, 'GEO_JUMP', 'MEDIUM', %s::jsonb)
                ON CONFLICT DO NOTHING
            """, [account_id, txn_id, {
                'distance_km': float(distance) / 1000,
                'time_hours': time_diff,
                'from_city': from_city,
                'to_city': to_city
            }])
        
        postgres_conn.commit()
        logger.info(f"Analytics refreshed. Found {len(geo_jumps)} geo-jumps")
        
        postgres_cursor.close()
        postgres_conn.close()
        
    except Exception as e:
        logger.error(f"Analytics refresh error: {str(e)}", exc_info=True)


def health_check():
    logger.info("Worker healthy")


if __name__ == "__main__":
    logger.info("Starting Fraud Detection Worker")
    
    # Run initial ETL
    etl_oracle_to_postgres()
    
    # Schedule jobs
    scheduler = BlockingScheduler()
    scheduler.add_job(etl_oracle_to_postgres, 'interval', minutes=ETL_INTERVAL)
    scheduler.add_job(refresh_analytics, 'interval', minutes=5)
    scheduler.add_job(health_check, 'interval', minutes=1)
    
    scheduler.start()

