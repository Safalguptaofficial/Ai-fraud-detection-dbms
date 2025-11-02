"""
Audit Logs API
Provides real-time audit trail and CRUD operation monitoring
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from psycopg import Connection
from deps import get_postgres
from middleware.tenant import get_current_tenant
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/audit/logs")
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    tenant_id: str = Depends(get_current_tenant),
    postgres: Connection = Depends(get_postgres)
):
    """
    📋 Get audit logs with filtering
    
    Returns real-time audit trail of all CRUD operations
    """
    cursor = postgres.cursor()
    try:
        # Build query with filters
        where_conditions = ["tenant_id = %s"]
        params = [tenant_id]
        
        if action:
            where_conditions.append("action = %s")
            params.append(action)
        
        if resource_type:
            where_conditions.append("resource_type = %s")
            params.append(resource_type)
        
        where_clause = " AND ".join(where_conditions)
        
        # Query audit logs
        query = f"""
            SELECT 
                id,
                action,
                resource_type,
                resource_id,
                user_id,
                metadata,
                ip_address,
                severity,
                created_at
            FROM audit_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        logs = []
        for row in cursor.fetchall():
            log = {
                "id": row[0],
                "action": row[1],
                "resource_type": row[2],
                "resource_id": row[3],
                "user_id": row[4],
                "metadata": row[5] or {},
                "ip_address": row[6],
                "severity": row[7],
                "created_at": row[8].isoformat() if row[8] else None
            }
            logs.append(log)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) FROM audit_logs WHERE {where_clause}
        """
        cursor.execute(count_query, params[:-2])  # Exclude limit and offset
        total = cursor.fetchone()[0]
        
        logger.info(f"Fetched {len(logs)} audit logs for tenant {tenant_id}")
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch audit logs: {e}")
        return {
            "logs": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
    finally:
        cursor.close()


@router.get("/audit/stats")
async def get_audit_stats(
    tenant_id: str = Depends(get_current_tenant),
    postgres: Connection = Depends(get_postgres)
):
    """
    📊 Get audit statistics
    
    Returns counts of CRUD operations
    """
    cursor = postgres.cursor()
    try:
        # Get operation counts
        cursor.execute("""
            SELECT 
                action,
                COUNT(*) as count
            FROM audit_logs
            WHERE tenant_id = %s
              AND created_at >= NOW() - INTERVAL '1 hour'
            GROUP BY action
        """, (tenant_id,))
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = row[1]
        
        return {
            "creates": stats.get("CREATE", 0),
            "reads": stats.get("READ", 0),
            "updates": stats.get("UPDATE", 0),
            "deletes": stats.get("DELETE", 0),
            "total": sum(stats.values())
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch audit stats: {e}")
        return {
            "creates": 0,
            "reads": 0,
            "updates": 0,
            "deletes": 0,
            "total": 0
        }
    finally:
        cursor.close()


@router.get("/audit/recent")
async def get_recent_operations(
    minutes: int = Query(5, ge=1, le=60),
    tenant_id: str = Depends(get_current_tenant),
    postgres: Connection = Depends(get_postgres)
):
    """
    ⚡ Get recent operations for real-time monitoring
    
    Returns operations from last N minutes
    """
    cursor = postgres.cursor()
    try:
        cursor.execute("""
            SELECT 
                id,
                action,
                resource_type,
                resource_id,
                metadata,
                created_at
            FROM audit_logs
            WHERE tenant_id = %s
              AND created_at >= NOW() - INTERVAL '%s minutes'
            ORDER BY created_at DESC
            LIMIT 50
        """, (tenant_id, minutes))
        
        operations = []
        for row in cursor.fetchall():
            op = {
                "id": str(row[0]),
                "operation": row[1],  # CREATE, READ, UPDATE, DELETE
                "table": row[2],       # resource_type
                "recordId": row[3],
                "details": row[4].get("details", "") if row[4] else "",
                "timestamp": row[5].isoformat() if row[5] else None
            }
            operations.append(op)
        
        return {
            "operations": operations,
            "count": len(operations)
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch recent operations: {e}")
        return {
            "operations": [],
            "count": 0
        }
    finally:
        cursor.close()

