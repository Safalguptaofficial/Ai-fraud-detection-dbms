from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection
from deps import get_postgres
from models.alert import FraudAlert, AlertUpdate
from middleware.tenant import get_current_tenant
from pydantic import BaseModel
from utils.audit_logger import log_audit_sync

router = APIRouter()


@router.get("/alerts", response_model=List[FraudAlert])
async def list_alerts(
    status: Optional[str] = Query(None, pattern="^(open|all)$"),
    limit: int = Query(100, ge=1, le=1000),
    postgres: Connection = Depends(get_postgres),
    tenant_id: str = Depends(get_current_tenant)
):
    cursor = None
    try:
        cursor = postgres.cursor()
        
        # Check if tenant_id column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fraud_alerts' AND column_name = 'tenant_id'
        """)
        has_tenant_id = cursor.fetchone() is not None
        
        # Build query with tenant_id filter if column exists, otherwise query all
        if has_tenant_id:
            if status == "open":
                cursor.execute("""
                    SELECT id, account_id, txn_id, rule_code, severity, reason,
                           created_at, handled, handled_at, handled_by
                    FROM fraud_alerts
                    WHERE tenant_id = %s AND handled = FALSE
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (tenant_id, limit))
            else:
                cursor.execute("""
                    SELECT id, account_id, txn_id, rule_code, severity, reason,
                           created_at, handled, handled_at, handled_by
                    FROM fraud_alerts
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (tenant_id, limit))
        else:
            # Fallback if tenant_id column doesn't exist yet
            if status == "open":
                cursor.execute("""
                    SELECT id, account_id, txn_id, rule_code, severity, reason,
                           created_at, handled, handled_at, handled_by
                    FROM fraud_alerts
                    WHERE handled = FALSE
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT id, account_id, txn_id, rule_code, severity, reason,
                           created_at, handled, handled_at, handled_by
                    FROM fraud_alerts
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
        
        rows = cursor.fetchall()
        return [
            FraudAlert(
                id=row[0],
                account_id=row[1],
                txn_id=row[2],
                rule_code=row[3],
                severity=row[4],
                reason=row[5],
                created_at=row[6],
                handled=bool(row[7]),
                handled_at=row[8],
                handled_by=row[9]
            )
            for row in rows
        ]
    except Exception as e:
        # Log error and return empty list instead of mock data
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching alerts: {e}")
        return []
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass


@router.get("/alerts/{alert_id}", response_model=FraudAlert)
async def get_alert(alert_id: int, postgres: Connection = Depends(get_postgres)):
    cursor = postgres.cursor()
    try:
        cursor.execute("""
            SELECT id, account_id, txn_id, rule_code, severity, reason,
                   created_at, handled, handled_at, handled_by
            FROM fraud_alerts
            WHERE id = %s
        """, [alert_id])
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return FraudAlert(
            id=row[0],
            account_id=row[1],
            txn_id=row[2],
            rule_code=row[3],
            severity=row[4],
            reason=row[5],
            created_at=row[6],
            handled=bool(row[7]),
            handled_at=row[8],
            handled_by=row[9]
        )
    finally:
        cursor.close()


@router.patch("/alerts/{alert_id}", response_model=FraudAlert)
async def update_alert(
    alert_id: int,
    data: AlertUpdate,
    postgres: Connection = Depends(get_postgres)
):
    cursor = postgres.cursor()
    try:
        cursor.execute("""
            UPDATE fraud_alerts
            SET handled = %s, handled_at = CURRENT_TIMESTAMP, handled_by = %s
            WHERE id = %s
        """, [data.handled, data.handled_by, alert_id])
        
        postgres.commit()
        return await get_alert(alert_id, postgres)
    except Exception as e:
        postgres.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()


class FlagTransactionRequest(BaseModel):
    txn_id: int
    account_id: int
    reason: Optional[str] = None

@router.post("/alerts/flag-transaction")
async def flag_transaction_as_fraud(
    data: FlagTransactionRequest,
    postgres: Connection = Depends(get_postgres),
    tenant_id: str = Depends(get_current_tenant)
):
    """Flag a transaction as fraud - creates a fraud alert"""
    cursor = postgres.cursor()
    try:
        # First, verify the transaction exists and get its account_id
        cursor.execute("""
            SELECT account_id, tenant_id FROM transactions WHERE id = %s
        """, (data.txn_id,))
        txn_result = cursor.fetchone()
        
        if not txn_result:
            raise HTTPException(status_code=404, detail=f"Transaction {data.txn_id} not found")
        
        txn_account_id = txn_result[0]
        txn_tenant_id = txn_result[1]
        
        # Verify tenant matches
        if txn_tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Transaction belongs to different tenant")
        
        # Ensure the account exists in the accounts table
        cursor.execute("""
            SELECT id FROM accounts WHERE id = %s AND tenant_id = %s
        """, (txn_account_id, tenant_id))
        
        if not cursor.fetchone():
            # Account doesn't exist - create it
            cursor.execute("""
                INSERT INTO accounts (id, customer_id, tenant_id, status)
                VALUES (%s, %s, %s, 'ACTIVE')
                ON CONFLICT (id) DO NOTHING
            """, (txn_account_id, f"CUST{txn_account_id}", tenant_id))
        
        # Check if tenant_id column exists in fraud_alerts
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fraud_alerts' AND column_name = 'tenant_id'
        """)
        has_tenant_id = cursor.fetchone() is not None
        
        # Insert fraud alert using the transaction's account_id
        if has_tenant_id:
            cursor.execute("""
                INSERT INTO fraud_alerts (
                    tenant_id, account_id, txn_id, rule_code, severity, reason, handled
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, FALSE
                ) RETURNING id
            """, (
                tenant_id,
                txn_account_id,
                data.txn_id,
                'MANUAL_FLAG',
                'HIGH',
                data.reason or f"Transaction {data.txn_id} manually flagged as fraud"
            ))
        else:
            cursor.execute("""
                INSERT INTO fraud_alerts (
                    account_id, txn_id, rule_code, severity, reason, handled
                ) VALUES (
                    %s, %s, %s, %s, %s, FALSE
                ) RETURNING id
            """, (
                txn_account_id,
                data.txn_id,
                'MANUAL_FLAG',
                'HIGH',
                data.reason or f"Transaction {data.txn_id} manually flagged as fraud"
            ))
        
        # Fetch alert_id and commit (OUTSIDE the if/else blocks)
        alert_id = cursor.fetchone()[0]
        postgres.commit()
        
        # Log audit event
        try:
            log_audit_sync(
                db=postgres,
                tenant_id=tenant_id,
                action="CREATE",
                resource_type="fraud_alerts",
                resource_id=str(alert_id),
                metadata={
                    "txn_id": data.txn_id,
                    "severity": "HIGH",
                    "reason": data.reason or "Manually flagged as fraud",
                    "details": f"Created fraud alert for transaction {data.txn_id}"
                }
            )
        except Exception as audit_err:
            logger.debug(f"Audit logging failed: {audit_err}")
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Transaction {data.txn_id} flagged as fraud"
        }
    except HTTPException:
        postgres.rollback()
        raise
    except Exception as e:
        postgres.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error flagging transaction: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()


@router.post("/alerts/mark-safe")
async def mark_transaction_as_safe(
    data: FlagTransactionRequest,
    postgres: Connection = Depends(get_postgres),
    tenant_id: str = Depends(get_current_tenant)
):
    """Mark a transaction as safe - dismisses any fraud alerts for this transaction"""
    cursor = postgres.cursor()
    try:
        # Check if tenant_id column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fraud_alerts' AND column_name = 'tenant_id'
        """)
        has_tenant_id = cursor.fetchone() is not None
        
        # Mark all alerts for this transaction as handled
        if has_tenant_id:
            cursor.execute("""
                UPDATE fraud_alerts
                SET handled = TRUE, handled_at = CURRENT_TIMESTAMP, handled_by = 'user'
                WHERE txn_id = %s AND tenant_id = %s AND handled = FALSE
            """, (data.txn_id, tenant_id))
        else:
            cursor.execute("""
                UPDATE fraud_alerts
                SET handled = TRUE, handled_at = CURRENT_TIMESTAMP, handled_by = 'user'
                WHERE txn_id = %s AND handled = FALSE
            """, (data.txn_id,))
        
        updated_count = cursor.rowcount
        postgres.commit()
        
        # Log audit event
        try:
            log_audit_sync(
                db=postgres,
                tenant_id=tenant_id,
                action="UPDATE",
                resource_type="fraud_alerts",
                resource_id=str(data.txn_id),
                metadata={
                    "txn_id": data.txn_id,
                    "alerts_dismissed": updated_count,
                    "details": f"Marked transaction {data.txn_id} as safe, dismissed {updated_count} alerts"
                }
            )
        except Exception as audit_err:
            logger.debug(f"Audit logging failed: {audit_err}")
        
        return {
            "success": True,
            "updated_alerts": updated_count,
            "message": f"Transaction {data.txn_id} marked as safe"
        }
    except Exception as e:
        postgres.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error marking transaction as safe: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()

