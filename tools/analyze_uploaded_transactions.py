#!/usr/bin/env python3
"""
Analyze uploaded transactions for fraud detection
This script runs ML fraud detection on all transactions for a tenant
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../services/api'))

from psycopg import connect
from ml_enhanced_model import predict_fraud
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_transactions(tenant_id: str = 'tenant_demo_123'):
    """Analyze all transactions for a tenant and create fraud alerts"""
    
    # Database connection
    conn = connect(
        host="localhost",
        port=5432,
        dbname="frauddb",
        user="postgres",
        password="password"
    )
    
    cursor = conn.cursor()
    
    try:
        # Get all transactions for tenant
        cursor.execute("""
            SELECT t.id, t.account_id, t.amount, t.merchant, t.mcc, t.channel,
                   t.city, t.country, t.txn_time, t.tenant_id
            FROM transactions t
            WHERE t.tenant_id = %s
            ORDER BY t.txn_time DESC
        """, (tenant_id,))
        
        transactions = cursor.fetchall()
        logger.info(f"Found {len(transactions)} transactions to analyze")
        
        alerts_created = 0
        
        for txn in transactions:
            txn_id, account_id, amount, merchant, mcc, channel, city, country, txn_time, tenant_id = txn
            
            # Get historical data for this account
            cursor.execute("""
                SELECT COUNT(*), AVG(amount), STDDEV(amount)
                FROM transactions
                WHERE account_id = %s AND tenant_id = %s AND id != %s
            """, (account_id, tenant_id, txn_id))
            
            hist = cursor.fetchone()
            txn_count = hist[0] if hist else 0
            avg_amount = float(hist[1]) if hist and hist[1] else 100.0
            std_amount = float(hist[2]) if hist and hist[2] else 50.0
            
            # Prepare ML model input
            ml_input = {
                'amount': float(amount),
                'transactions_last_hour': min(txn_count, 10),
                'historical_avg_amount': avg_amount,
                'historical_std_amount': std_amount,
                'minutes_since_last_transaction': 60,
                'location_changed': False,
                'merchant_risk_score': 0.1,
                'device_changed': False,
                'ip_reputation_score': 0.5
            }
            
            # Get fraud prediction
            try:
                prediction = predict_fraud(ml_input)
                risk_score = prediction.get('risk_score', 0) / 100.0  # Convert to 0-1 scale
                
                # Create alert if high risk
                if risk_score > 0.5:
                    severity = 'HIGH' if risk_score > 0.8 else 'MEDIUM'
                    reason = f"ML Fraud Score: {risk_score:.2%} - {prediction.get('explanation_text', 'High risk transaction')}"
                    
                    cursor.execute("""
                        INSERT INTO fraud_alerts (
                            tenant_id, account_id, txn_id, rule_code, severity, reason
                        ) VALUES (
                            %s, %s, %s, 'ML_FRAUD_SCORE', %s, %s
                        )
                        ON CONFLICT DO NOTHING
                    """, (tenant_id, account_id, txn_id, severity, reason))
                    
                    alerts_created += 1
                    logger.info(f"Created alert for transaction {txn_id}: {severity} risk ({risk_score:.2%})")
                    
            except Exception as e:
                logger.warning(f"Failed to analyze transaction {txn_id}: {e}")
                continue
        
        conn.commit()
        logger.info(f"✅ Analysis complete! Created {alerts_created} fraud alerts")
        
        # Show summary
        cursor.execute("""
            SELECT COUNT(*) FROM fraud_alerts
            WHERE tenant_id = %s AND handled = FALSE
        """, (tenant_id,))
        
        total_alerts = cursor.fetchone()[0]
        logger.info(f"Total open fraud alerts: {total_alerts}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    tenant_id = sys.argv[1] if len(sys.argv) > 1 else 'tenant_demo_123'
    analyze_transactions(tenant_id)

