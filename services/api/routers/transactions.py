from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
import redis
import json
import logging
from datetime import timedelta
from oracledb import Connection
from psycopg import Connection as PostgresConnection
from deps import get_oracle, get_redis, get_postgres
from models.transaction import Transaction, TransactionCreate
from config import settings
from middleware.tenant import get_current_tenant
from utils.audit_logger import log_audit_sync

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache TTL in seconds
CACHE_TTL = 300  # 5 minutes

def get_cache_key(endpoint: str, **kwargs) -> str:
    """Generate cache key from endpoint and parameters"""
    params = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()) if v)
    return f"api:{endpoint}:{params}" if params else f"api:{endpoint}"

@router.post("/transactions", response_model=Transaction)
async def create_transaction(
    data: TransactionCreate,
    oracle: Connection = Depends(get_oracle),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Create a new transaction with fraud detection"""
    cursor = oracle.cursor()
    try:
        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (
                id, account_id, amount, currency, merchant, mcc, channel,
                device_id, lat, lon, city, country, txn_time, auth_code
            )
            VALUES (
                seq_txns.NEXTVAL, :1, :2, :3, :4, :5, :6,
                :7, :8, :9, :10, :11, :12, :13
            )
        """, (
            data.account_id, data.amount, data.currency, data.merchant, data.mcc, data.channel,
            data.device_id, data.lat, data.lon, data.city, data.country, data.txn_time, data.auth_code
        ))
        
        oracle.commit()
        
        # Get the transaction ID
        cursor.execute("SELECT seq_txns.CURRVAL FROM dual")
        txn_id = cursor.fetchone()[0]
        
        # Fetch the inserted transaction
        cursor.execute("""
            SELECT id, account_id, amount, currency, merchant, mcc, channel, device_id,
                   lat, lon, city, country, txn_time, auth_code, status, created_at
            FROM transactions
            WHERE id = :1
        """, (txn_id,))
        
        row = cursor.fetchone()
        
        # Clear cache for transactions list
        redis_client.delete(f"api:/transactions:*")
        
        # Return transaction
        return Transaction(
            id=row[0],
            account_id=row[1],
            amount=float(row[2]),
            currency=row[3],
            merchant=row[4],
            mcc=row[5],
            channel=row[6],
            device_id=row[7],
            lat=float(row[8]) if row[8] else None,
            lon=float(row[9]) if row[9] else None,
            city=row[10],
            country=row[11],
            txn_time=row[12],
            auth_code=row[13],
            status=row[14],
            created_at=row[15]
        )
    except Exception as e:
        oracle.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()


@router.get("/transactions", response_model=List[Transaction])
async def list_transactions(
    account_id: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    bypass_cache: bool = Query(False, description="Bypass Redis cache"),
    csv_only: bool = Query(False, description="Show only CSV-uploaded transactions"),
    tenant_id: str = Depends(get_current_tenant),
    postgres = Depends(get_postgres),
    redis_client: redis.Redis = Depends(get_redis)
):
    """List transactions with Redis caching - queries PostgreSQL"""
    from middleware.tenant import get_current_tenant
    
    # For real-time updates: Don't cache when csv_only=true (always fetch fresh)
    # Also respect bypass_cache flag for manual refreshes
    # Only cache when explicitly requested AND not filtering CSV-only
    should_cache = not bypass_cache and not csv_only
    
    if should_cache:
        cache_key = get_cache_key("/transactions", tenant_id=tenant_id, account_id=account_id, limit=limit, offset=offset)
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Returning cached transactions (key: {cache_key})")
                return json.loads(cached_data)
        except Exception as cache_err:
            logger.debug(f"Cache read failed: {cache_err}")
            pass  # Continue if Redis fails
    else:
        logger.debug(f"Bypassing cache: bypass_cache={bypass_cache}, csv_only={csv_only}")
    
    # Query PostgreSQL database (where CSV uploads store transactions)
    cursor = postgres.cursor()
    try:
        # Check which columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'transactions' 
            AND column_name IN ('tenant_id', 'status', 'risk_score', 'created_at')
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}
        has_tenant_id = 'tenant_id' in existing_columns
        has_status = 'status' in existing_columns
        has_risk_score = 'risk_score' in existing_columns
        has_created_at = 'created_at' in existing_columns
        
        # Build SELECT columns list
        select_cols = ['id', 'account_id', 'amount', 'currency', 'merchant', 'mcc', 'channel', 'city', 'country', 'txn_time']
        if has_status:
            select_cols.append('status')
        if has_risk_score:
            select_cols.append('risk_score')
        
        select_str = ', '.join(select_cols)
        
        # Build query with or without tenant_id filter
        params = []
        where_conditions = []
        
        # ALWAYS filter by tenant_id for security and data isolation
        if has_tenant_id:
            where_conditions.append("t.tenant_id = %s")
            params.append(tenant_id)
            logger.info(f"🔒 Filtering by tenant_id: {tenant_id}")
        
        # If csv_only is requested, filter to show only CSV-uploaded transactions
        if csv_only:
            try:
                # Get first CSV upload timestamp
                cursor.execute("""
                    SELECT MIN(created_at) as first_upload, COUNT(*) as upload_count
                    FROM file_uploads 
                    WHERE tenant_id = %s AND status = 'COMPLETED'
                """, (tenant_id,))
                upload_info = cursor.fetchone()
                
                logger.info(f"🔍 CSV filter: csv_only={csv_only}, upload_info={upload_info}, has_created_at={has_created_at}")
                
                if upload_info and upload_info[1] and upload_info[1] > 0:  # Has uploads
                    first_upload_time = upload_info[0]
                    from datetime import timedelta
                    # Filter from 1 minute before first upload to catch all CSV transactions
                    filter_start = first_upload_time - timedelta(minutes=1)
                    
                    if has_created_at:
                        # Check if created_at column has values
                        cursor.execute("SELECT COUNT(*) FROM transactions WHERE created_at IS NOT NULL LIMIT 1")
                        has_created_at_values = cursor.fetchone()[0] > 0
                        
                        if has_created_at_values:
                            where_conditions.append("t.created_at >= %s")
                            params.append(filter_start)
                            logger.info(f"✅ CSV filter: created_at >= {filter_start} (found {upload_info[1]} uploads)")
                        else:
                            # created_at column exists but is NULL, use txn_time instead
                            where_conditions.append("t.txn_time >= %s")
                            params.append(filter_start)
                            logger.warning(f"⚠️ CSV filter: created_at is NULL, using txn_time >= {filter_start}")
                    else:
                        # No created_at column, use txn_time
                        where_conditions.append("t.txn_time >= %s")
                        params.append(filter_start)
                        logger.warning(f"⚠️ CSV filter: created_at column missing, using txn_time >= {filter_start}")
                else:
                    logger.warning("❌ No CSV uploads found - returning empty list")
                    return []
            except Exception as e:
                logger.error(f"❌ CSV filter error: {e}", exc_info=True)
                return []
        
        # Add account_id filter if provided
        if account_id:
            where_conditions.append("t.account_id = %s")
            params.append(account_id)
        
        # Build the query
        query = f"""
            SELECT {select_str}
            FROM transactions t
        """
        
        # Add WHERE clause if we have conditions
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        logger.info(f"Showing transactions (csv_only={csv_only}, demo mode). Tenant was: {tenant_id}")
        
        query += " ORDER BY t.txn_time DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Debug logging
        logger.info(f"Executing query: {query[:200]}... with params: {params}")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        logger.info(f"Query returned {len(rows)} rows. First row ID: {rows[0][0] if rows else 'None'}")
        logger.info(f"Transactions query - tenant_id: {tenant_id}, has_tenant_id_col: {has_tenant_id}, rows: {len(rows)}")
        
        # Debug logging when no rows returned
        if len(rows) == 0:
            try:
                if has_tenant_id:
                    # Check what tenant_ids exist
                    cursor.execute("SELECT DISTINCT tenant_id, COUNT(*) FROM transactions GROUP BY tenant_id LIMIT 10")
                    tenant_counts = cursor.fetchall()
                    logger.warning(f"No transactions found for tenant_id={tenant_id}")
                    logger.info(f"Available tenant_ids and counts: {[(t[0], t[1]) for t in tenant_counts]}")
                
                # Check total transaction count
                cursor.execute("SELECT COUNT(*) FROM transactions")
                total_count = cursor.fetchone()[0]
                logger.info(f"Total transactions in database: {total_count}")
                
                # Check transactions for this specific tenant with exact match
                if has_tenant_id:
                    cursor.execute("SELECT COUNT(*) FROM transactions WHERE tenant_id = %s", (tenant_id,))
                    tenant_count = cursor.fetchone()[0]
                    logger.warning(f"Transactions for tenant '{tenant_id}': {tenant_count}")
                    
                    # Also check for NULL tenant_id
                    cursor.execute("SELECT COUNT(*) FROM transactions WHERE tenant_id IS NULL")
                    null_count = cursor.fetchone()[0]
                    if null_count > 0:
                        logger.warning(f"Found {null_count} transactions with NULL tenant_id")
            except Exception as debug_err:
                logger.error(f"Debug query failed: {debug_err}", exc_info=True)
        
        # Parse rows with dynamic column mapping
        transactions = []
        for row in rows:
            col_idx = 0
            txn = {
                "id": row[col_idx],
                "account_id": row[col_idx + 1],
                "amount": float(row[col_idx + 2]),
                "currency": row[col_idx + 3] or "USD",
                "merchant": row[col_idx + 4],
                "mcc": row[col_idx + 5] or "",
                "channel": row[col_idx + 6] or "ONLINE",
                "city": row[col_idx + 7],
                "country": row[col_idx + 8],
                "txn_time": row[col_idx + 9].isoformat() if row[col_idx + 9] else None,
                "created_at": row[col_idx + 9].isoformat() if row[col_idx + 9] else None
            }
            col_idx = 10
            
            # Add optional columns if they exist
            if has_status:
                txn["status"] = row[col_idx] or "APPROVED"
                col_idx += 1
            else:
                txn["status"] = "APPROVED"
                
            if has_risk_score:
                txn["risk_score"] = float(row[col_idx]) if row[col_idx] is not None else None
                col_idx += 1
            else:
                txn["risk_score"] = None
            
            # Add default fields
            txn["device_id"] = None
            txn["lat"] = None
            txn["lon"] = None
            txn["auth_code"] = None
            
            transactions.append(txn)
        
        # Log audit event for READ operation
        try:
            log_audit_sync(
                db=postgres,
                tenant_id=tenant_id,
                action="READ",
                resource_type="transactions",
                metadata={
                    "count": len(transactions),
                    "limit": limit,
                    "offset": offset,
                    "csv_only": csv_only,
                    "details": f"Fetched {len(transactions)} transactions"
                }
            )
        except Exception as audit_err:
            logger.debug(f"Audit logging failed: {audit_err}")
        
        # Cache the results only if we should cache (not for csv_only or bypass_cache)
        if should_cache:
            try:
                cache_key = get_cache_key("/transactions", tenant_id=tenant_id, account_id=account_id, limit=limit, offset=offset)
                redis_client.setex(cache_key, CACHE_TTL, json.dumps(transactions, default=str))
                logger.debug(f"Cached transactions (key: {cache_key}, TTL: {CACHE_TTL}s)")
            except Exception as cache_err:
                logger.debug(f"Cache write failed: {cache_err}")
                pass  # Continue if Redis fails
        else:
            logger.debug("Skipping cache write (csv_only or bypass_cache enabled)")
        
        return transactions
    finally:
        cursor.close()

@router.get("/cache/stats")
async def get_cache_stats(redis_client: redis.Redis = Depends(get_redis)):
    """Get Redis cache statistics"""
    try:
        info = redis_client.info()
        keys = redis_client.dbsize()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "keys": keys,
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": f"{info.get('keyspace_hits', 0) / (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100:.2f}%"
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/cache/clear")
async def clear_cache(redis_client: redis.Redis = Depends(get_redis)):
    """Clear all cache"""
    try:
        redis_client.flushdb()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))