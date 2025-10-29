from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from psycopg import Connection
from deps import get_postgres

router = APIRouter()


@router.get("/analytics/anomalies", response_model=List[dict])
async def get_anomalies(
    rule: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    account_id: Optional[int] = Query(None),
    postgres: Connection = Depends(get_postgres)
):
    query = """
        SELECT id, account_id, txn_id, rule, score, detected_at, severity, extra
        FROM anomaly_events
        WHERE 1=1
    """
    params = []
    
    if rule:
        query += " AND rule = %s"
        params.append(rule)
    
    if date_from:
        query += " AND detected_at >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND detected_at <= %s"
        params.append(date_to)
    
    if severity:
        query += " AND severity = %s"
        params.append(severity)
    
    if account_id:
        query += " AND account_id = %s"
        params.append(account_id)
    
    query += " ORDER BY detected_at DESC LIMIT 1000"
    
    with postgres.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            {
                "id": str(row[0]),
                "account_id": row[1],
                "txn_id": row[2],
                "rule": row[3],
                "score": float(row[4]) if row[4] else None,
                "detected_at": row[5].isoformat() if row[5] else None,
                "severity": row[6],
                "extra": row[7] if row[7] else {}
            }
            for row in rows
        ]


@router.get("/analytics/midnight-high-amount")
async def get_midnight_high_amount(days: int = Query(7, ge=1, le=30)):
    # This would call the analytics function
    return {"message": "Use Postgres function get_midnight_high_amount_txns"}


@router.get("/analytics/velocity-anomalies")
async def get_velocity_anomalies(hours: int = Query(24, ge=1, le=168)):
    # This would call the analytics function
    return {"message": "Use Postgres function get_velocity_anomalies"}


@router.get("/analytics/geo-jumps")
async def get_geo_jumps(postgres: Connection = Depends(get_postgres)):
    with postgres.cursor() as cursor:
        cursor.execute("SELECT * FROM get_geo_jump_anomalies()")
        rows = cursor.fetchall()
        
        return [
            {
                "account_id": row[0],
                "txn_id": row[1],
                "distance_meters": float(row[2]) if row[2] else None,
                "time_diff_hours": float(row[3]) if row[3] else None,
                "from_city": row[4],
                "to_city": row[5]
            }
            for row in rows
        ]

