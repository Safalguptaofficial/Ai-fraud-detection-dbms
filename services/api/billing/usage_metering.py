"""
Usage Metering for Billing
Tracks transaction usage, API calls, storage, etc.
"""
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class UsageMetering:
    """Track and meter usage for billing"""
    
    def __init__(self, db_connection, redis_client=None):
        self.db = db_connection
        self.redis = redis_client
        self.redis_enabled = redis_client is not None
    
    async def record_transaction(self, tenant_id: str, transaction_id: int):
        """Record a transaction for billing"""
        cursor = self.db.cursor()
        try:
            # Update usage counter
            cursor.execute("""
                INSERT INTO tenant_usage (
                    tenant_id,
                    period_start,
                    period_end,
                    transaction_count
                ) VALUES (
                    %s,
                    DATE_TRUNC('month', CURRENT_DATE),
                    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day',
                    1
                )
                ON CONFLICT (tenant_id, period_start)
                DO UPDATE SET
                    transaction_count = tenant_usage.transaction_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (tenant_id,))
            
            self.db.commit()
            logger.debug(f"Recorded transaction for tenant {tenant_id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record transaction: {e}")
            raise
        finally:
            cursor.close()
    
    async def record_api_call(self, tenant_id: str, endpoint: str):
        """Record an API call for rate limiting and billing"""
        cursor = self.db.cursor()
        try:
            cursor.execute("""
                INSERT INTO tenant_usage (
                    tenant_id,
                    period_start,
                    period_end,
                    api_call_count
                ) VALUES (
                    %s,
                    DATE_TRUNC('month', CURRENT_DATE),
                    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day',
                    1
                )
                ON CONFLICT (tenant_id, period_start)
                DO UPDATE SET
                    api_call_count = tenant_usage.api_call_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (tenant_id,))
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record API call: {e}")
        finally:
            cursor.close()
    
    async def check_limits(self, tenant_id: str) -> dict:
        """
        Check if tenant has exceeded usage limits
        
        Returns dict with limit status based on REAL transaction counts
        """
        cursor = self.db.cursor()
        try:
            # Get tenant limits
            cursor.execute("""
                SELECT 
                    t.max_transactions_per_month,
                    t.max_api_calls_per_minute
                FROM tenants t
                WHERE t.tenant_id = %s
            """, (tenant_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return {"error": "Tenant not found"}
            
            max_txns, max_api = result
            
            # Count REAL transactions from transactions table (all time for this tenant)
            cursor.execute("""
                SELECT COUNT(*) as total_transactions
                FROM transactions
                WHERE tenant_id = %s
            """, (tenant_id,))
            
            total_txns_result = cursor.fetchone()
            current_txns = total_txns_result[0] if total_txns_result else 0
            
            # Get this month's transactions for monthly limit tracking
            cursor.execute("""
                SELECT COUNT(*) as month_transactions
                FROM transactions
                WHERE tenant_id = %s
                  AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
            """, (tenant_id,))
            
            month_txns_result = cursor.fetchone()
            month_txns = month_txns_result[0] if month_txns_result else 0
            
            # Get API call count from usage tracking
            cursor.execute("""
                SELECT COALESCE(api_call_count, 0) as current_api_calls
                FROM tenant_usage
                WHERE tenant_id = %s
                  AND period_start = DATE_TRUNC('month', CURRENT_DATE)
            """, (tenant_id,))
            
            api_result = cursor.fetchone()
            current_api = api_result[0] if api_result else 0
            
            logger.info(f"Real-time usage for tenant {tenant_id}: Total={current_txns}, This month={month_txns}, Limit={max_txns}")
            
            return {
                "transactions": {
                    "limit": max_txns,
                    "used": current_txns,  # Use REAL transaction count
                    "month_used": month_txns,  # This month's count
                    "remaining": max(0, max_txns - month_txns) if max_txns else None,
                    "exceeded": month_txns > max_txns if max_txns else False
                },
                "api_calls": {
                    "limit": max_api,
                    "used": current_api,
                    "exceeded": self._check_per_minute_limit(tenant_id, max_api)
                }
            }
        finally:
            cursor.close()
    
    def _check_per_minute_limit(self, tenant_id: str, max_per_minute: int) -> bool:
        """Check if API calls exceeded per-minute limit using Redis"""
        if not self.redis_enabled or not max_per_minute:
            return False
        
        try:
            from datetime import datetime
            current_minute = datetime.utcnow().strftime("%Y%m%d%H%M")
            key = f"api_calls:{tenant_id}:{current_minute}"
            
            current_count = self.redis.get(key)
            if current_count:
                count = int(current_count) if isinstance(current_count, (bytes, str)) else int(current_count)
                return count >= max_per_minute
            
            return False
        except Exception as e:
            logger.warning(f"Per-minute limit check failed: {e}")
            return False
    
    async def record_api_call_minute(self, tenant_id: str, endpoint: str):
        """Record API call with per-minute tracking in Redis"""
        if self.redis_enabled:
            try:
                from datetime import datetime
                current_minute = datetime.utcnow().strftime("%Y%m%d%H%M")
                key = f"api_calls:{tenant_id}:{current_minute}"
                
                # Increment counter with 60 second TTL
                self.redis.incr(key)
                self.redis.expire(key, 60)
            except Exception as e:
                logger.warning(f"Failed to record per-minute API call: {e}")
        
        # Also record in database for monthly tracking
        await self.record_api_call(tenant_id, endpoint)
    
    async def calculate_overage_charges(self, tenant_id: str) -> float:
        """
        Calculate overage charges for the current period based on REAL transactions
        
        Returns amount in dollars
        """
        cursor = self.db.cursor()
        try:
            # Get tenant info
            cursor.execute("""
                SELECT 
                    t.max_transactions_per_month,
                    t.plan
                FROM tenants t
                WHERE t.tenant_id = %s
            """, (tenant_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return 0.0
            
            max_txns, plan = result
            
            # No overage for enterprise plan
            if plan == 'ENTERPRISE':
                return 0.0
            
            # Count REAL transactions from this month
            cursor.execute("""
                SELECT COUNT(*) as month_transactions
                FROM transactions
                WHERE tenant_id = %s
                  AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
            """, (tenant_id,))
            
            month_result = cursor.fetchone()
            current_txns = month_result[0] if month_result else 0
            
            # Calculate overage
            overage = max(0, current_txns - max_txns) if max_txns else 0
            
            # $0.002 per transaction over limit
            overage_charge = overage * 0.002
            
            logger.info(f"Overage calculation for {tenant_id}: {current_txns}/{max_txns} = ${overage_charge:.2f}")
            
            return overage_charge
        finally:
            cursor.close()
    
    async def get_usage_report(self, tenant_id: str, months: int = 3) -> list:
        """Get usage report for past N months"""
        cursor = self.db.cursor()
        try:
            cursor.execute("""
                SELECT 
                    period_start,
                    period_end,
                    transaction_count,
                    api_call_count,
                    storage_used_mb,
                    overage_charges
                FROM tenant_usage
                WHERE tenant_id = %s
                    AND period_start >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '%s months'
                ORDER BY period_start DESC
            """, (tenant_id, months))
            
            results = cursor.fetchall()
            
            return [
                {
                    "period_start": row[0],
                    "period_end": row[1],
                    "transactions": row[2],
                    "api_calls": row[3],
                    "storage_mb": row[4],
                    "overage_charges": float(row[5]) if row[5] else 0.0
                }
                for row in results
            ]
        finally:
            cursor.close()

