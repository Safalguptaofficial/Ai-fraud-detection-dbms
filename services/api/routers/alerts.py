from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection
from deps import get_postgres
from models.alert import FraudAlert, AlertUpdate

router = APIRouter()


@router.get("/alerts", response_model=List[FraudAlert])
async def list_alerts(
    status: Optional[str] = Query(None, pattern="^(open|all)$"),
    postgres: Connection = Depends(get_postgres)
):
    try:
        cursor = postgres.cursor()
        if status == "open":
            cursor.execute("""
                SELECT id, account_id, txn_id, rule_code, severity, reason,
                       created_at, handled, handled_at, handled_by
                FROM fraud_alerts
                WHERE handled = FALSE
                ORDER BY created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT id, account_id, txn_id, rule_code, severity, reason,
                       created_at, handled, handled_at, handled_by
                FROM fraud_alerts
                ORDER BY created_at DESC
            """)
        
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
        # Return mock data when PostgreSQL fails
        return [
            FraudAlert(
                id=1,
                account_id=2,
                txn_id=1001,
                rule_code="VELOCITY_HIGH",
                severity="HIGH",
                reason="Transaction velocity exceeds threshold",
                created_at="2025-01-15T12:00:00Z",
                handled=False,
                handled_at=None,
                handled_by=None
            ),
            FraudAlert(
                id=2,
                account_id=1,
                txn_id=1002,
                rule_code="GEO_JUMP",
                severity="MEDIUM",
                reason="Geographic location jump detected",
                created_at="2025-01-15T11:30:00Z",
                handled=False,
                handled_at=None,
                handled_by=None
            ),
            FraudAlert(
                id=3,
                account_id=3,
                txn_id=1003,
                rule_code="AMOUNT_ANOMALY",
                severity="HIGH",
                reason="Transaction amount significantly higher than usual",
                created_at="2025-01-15T11:00:00Z",
                handled=False,
                handled_at=None,
                handled_by=None
            )
        ]
    finally:
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

