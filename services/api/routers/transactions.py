from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import redis
import json
from datetime import timedelta
from oracledb import Connection
from deps import get_oracle, get_redis
from models.transaction import Transaction, TransactionCreate
from config import settings

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
    oracle: Connection = Depends(get_oracle),
    redis_client: redis.Redis = Depends(get_redis)
):
    """List transactions with Redis caching"""
    # Try to get from cache
    cache_key = get_cache_key("/transactions", account_id=account_id, limit=limit, offset=offset)
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Query database
    cursor = oracle.cursor()
    try:
        query = """
            SELECT id, account_id, amount, currency, merchant, mcc, channel, device_id,
                   lat, lon, city, country, txn_time, auth_code, status, created_at
            FROM transactions
        """
        params = []
        
        if account_id:
            query += " WHERE account_id = :1"
            params.append(account_id)
        
        query += " ORDER BY txn_time DESC OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY"
        params.extend([offset, limit])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        transactions = [
            Transaction(
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
            ).dict()
            for row in rows
        ]
        
        # Cache the results
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(transactions, default=str))
        
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