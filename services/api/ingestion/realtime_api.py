"""
Real-time Transaction Ingestion API
Accepts transactions via REST API for real-time processing
Production-ready with ML integration, rate limiting, and error handling
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import asyncio
from functools import wraps
import time
import re

# Import ML model
from ml_enhanced_model import predict_fraud

logger = logging.getLogger(__name__)

# Maximum retry attempts for transient failures
MAX_RETRIES = 3
RETRY_DELAY = 0.5  # seconds


class TransactionCreate(BaseModel):
    """Schema for creating a transaction via API"""
    account_id: str = Field(..., min_length=1, max_length=128)
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", max_length=3)
    merchant: str = Field(..., min_length=1, max_length=255)
    merchant_id: Optional[str] = Field(None, max_length=128)
    mcc: str = Field(default="0000", max_length=4)
    channel: str = Field(default="ONLINE", max_length=32)
    
    # Location
    city: Optional[str] = Field(None, max_length=128)
    country: Optional[str] = Field(None, max_length=3)
    ip_address: Optional[str] = Field(None, max_length=45)
    
    # Device
    device_id: Optional[str] = Field(None, max_length=128)
    device_type: Optional[str] = Field(None, max_length=32)
    
    # Metadata
    transaction_time: Optional[datetime] = None
    reference_id: Optional[str] = Field(None, max_length=128)
    metadata: Optional[dict] = None
    
    @validator('transaction_time', pre=True, always=True)
    def set_transaction_time(cls, v):
        return v or datetime.utcnow()
    
    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return v
    
    @validator('account_id')
    def validate_account_id(cls, v):
        """Sanitize and validate account ID"""
        if not v or len(v.strip()) == 0:
            raise ValueError('account_id cannot be empty')
        # Remove any potentially dangerous characters
        v = re.sub(r'[<>"\']', '', v.strip())
        if len(v) > 128:
            raise ValueError('account_id must be <= 128 characters')
        return v
    
    @validator('merchant')
    def validate_merchant(cls, v):
        """Sanitize merchant name"""
        if not v or len(v.strip()) == 0:
            raise ValueError('merchant cannot be empty')
        v = re.sub(r'[<>"\']', '', v.strip())
        if len(v) > 255:
            raise ValueError('merchant must be <= 255 characters')
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format"""
        if v is None:
            return v
        # Basic IP validation (IPv4 or IPv6)
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
        if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
            raise ValueError(f'Invalid IP address format: {v}')
        return v


def retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Decorator for retrying operations on transient failures"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying...")
                        await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator


class RateLimiter:
    """Tenant-based rate limiter using Redis"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.enabled = redis_client is not None
    
    def check_rate_limit(self, tenant_id: str, max_requests: int = 100, window_seconds: int = 60) -> tuple[bool, Optional[int]]:
        """
        Check if tenant has exceeded rate limit (synchronous Redis operations)
        
        Returns: (allowed: bool, retry_after: Optional[int])
        """
        if not self.enabled:
            return True, None  # No rate limiting if Redis unavailable
        
        try:
            key = f"rate_limit:{tenant_id}"
            current = self.redis.get(key)
            
            if current is None:
                # First request in window
                self.redis.setex(key, window_seconds, "1")
                return True, None
            
            count = int(current) if isinstance(current, (bytes, str)) else int(current)
            if count >= max_requests:
                # Rate limit exceeded - get TTL for retry_after
                ttl = self.redis.ttl(key)
                return False, ttl if ttl > 0 else window_seconds
            
            # Increment counter
            self.redis.incr(key)
            return True, None
            
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}. Allowing request.")
            return True, None  # Fail open - allow request if rate limiting fails


class RealtimeTransactionAPI:
    """Handles real-time transaction ingestion with production-ready features"""
    
    def __init__(self, db_connection, redis_client=None):
        self.db = db_connection
        self.rate_limiter = RateLimiter(redis_client) if redis_client else None
        self.ml_cache_enabled = redis_client is not None
        self.ml_cache = redis_client if redis_client else None
        # Get model version from manager (supports A/B testing)
        from ml_model_versioning import get_model_version_manager
        model_manager = get_model_version_manager(redis_client)
        self.model_version = model_manager.get_model_version()
    
    async def ingest_transaction(
        self,
        tenant_id: str,
        transaction: TransactionCreate
    ) -> dict:
        """
        Ingest a single transaction in real-time with production-ready features
        
        Features:
        - Rate limiting per tenant
        - ML-based fraud detection
        - Comprehensive error handling
        - Retry logic for transient failures
        - Monitoring and metrics
        
        Returns: Transaction ID and fraud score
        """
        start_time = time.time()
        
        # Check rate limit (synchronous operation)
        if self.rate_limiter:
            allowed, retry_after = self.rate_limiter.check_rate_limit(
                tenant_id, 
                max_requests=100,  # Configurable per tenant
                window_seconds=60
            )
            if not allowed:
                logger.warning(f"Rate limit exceeded for tenant {tenant_id}")
                raise ValueError(f"Rate limit exceeded. Retry after {retry_after} seconds")
        
        # Validate tenant_id
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        
        tenant_id = tenant_id.strip()
        
        cursor = None
        transaction_id = None
        
        try:
            # Insert transaction with retry logic
            transaction_id = await self._insert_transaction_with_retry(
                tenant_id, transaction
            )
            
            # Calculate fraud score using REAL ML model
            fraud_score = await self._calculate_fraud_score(transaction_id, transaction, tenant_id)
            
            # Update transaction with fraud score and status
            await self._update_transaction_status_with_retry(
                transaction_id, fraud_score, tenant_id, transaction.account_id
            )
            
            # Log metrics
            processing_time = time.time() - start_time
            logger.info(
                f"Ingested transaction {transaction_id} for tenant {tenant_id} | "
                f"Fraud score: {fraud_score:.3f} | Processing time: {processing_time:.3f}s"
            )
            
            # Return result
            status = "APPROVED" if fraud_score <= 0.5 else "REVIEW" if fraud_score <= 0.8 else "BLOCKED"
            return {
                "transaction_id": transaction_id,
                "status": status,
                "fraud_score": round(fraud_score, 3),
                "reference_id": transaction.reference_id,
                "timestamp": transaction.transaction_time.isoformat(),
                "processing_time_ms": round(processing_time * 1000, 2)
            }
            
        except ValueError as e:
            # Rate limit or validation errors
            self.db.rollback()
            logger.warning(f"Transaction ingestion rejected: {e}")
            raise
        except Exception as e:
            # Rollback on any error
            if self.db:
                self.db.rollback()
            logger.error(
                f"Transaction ingestion failed for tenant {tenant_id}: {e}",
                exc_info=True
            )
            # Re-raise with more context
            raise ValueError(f"Transaction ingestion failed: {str(e)}") from e
        finally:
            if cursor:
                cursor.close()
    
    @retry_on_failure(max_retries=3, delay=0.5)
    async def _insert_transaction_with_retry(
        self, tenant_id: str, transaction: TransactionCreate
    ) -> int:
        """Insert transaction with retry logic for transient database failures"""
        cursor = self.db.cursor()
        try:
            cursor.execute("""
                INSERT INTO transactions (
                    tenant_id, account_id, amount, currency,
                    merchant, merchant_id, mcc, channel,
                    city, country, ip_address,
                    device_id, device_type,
                    txn_time, reference_id, status,
                    metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, 'PENDING', %s
                )
                RETURNING id
            """, (
                tenant_id,
                transaction.account_id,
                float(transaction.amount),
                transaction.currency,
                transaction.merchant,
                transaction.merchant_id,
                transaction.mcc,
                transaction.channel,
                transaction.city,
                transaction.country,
                transaction.ip_address,
                transaction.device_id,
                transaction.device_type,
                transaction.transaction_time,
                transaction.reference_id,
                transaction.metadata
            ))
            
            result = cursor.fetchone()
            if not result:
                raise ValueError("Failed to insert transaction - no ID returned")
            
            self.db.commit()
            return result[0]
            
        except Exception as e:
            self.db.rollback()
            raise
        finally:
            cursor.close()
    
    @retry_on_failure(max_retries=3, delay=0.5)
    async def _update_transaction_status_with_retry(
        self, transaction_id: int, fraud_score: float,
        tenant_id: str, account_id: str
    ):
        """Update transaction status and create alerts with retry logic"""
        cursor = self.db.cursor()
        try:
            # Update transaction
            cursor.execute("""
                UPDATE transactions
                SET risk_score = %s,
                    status = CASE
                        WHEN %s > 0.8 THEN 'BLOCKED'
                        WHEN %s > 0.5 THEN 'REVIEW'
                        ELSE 'APPROVED'
                    END
                WHERE id = %s AND tenant_id = %s
            """, (fraud_score, fraud_score, fraud_score, transaction_id, tenant_id))
            
            # Create alert if high risk
            if fraud_score > 0.5:
                cursor.execute("""
                    INSERT INTO fraud_alerts (
                        tenant_id, account_id, transaction_id,
                        rule_code, severity, reason, status
                    ) VALUES (
                        %s, %s, %s, 'HIGH_RISK_SCORE',
                        CASE WHEN %s > 0.8 THEN 'HIGH' ELSE 'MEDIUM' END,
                        'Fraud score: ' || %s::text,
                        'OPEN'
                    )
                    ON CONFLICT DO NOTHING
                """, (
                    tenant_id,
                    account_id,
                    transaction_id,
                    fraud_score,
                    fraud_score
                ))
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise
        finally:
            cursor.close()
    
    async def _calculate_fraud_score(
        self,
        transaction_id: int,
        transaction: TransactionCreate,
        tenant_id: str
    ) -> float:
        """
        Calculate fraud score using REAL ML model (not simple rules!)
        
        This method:
        1. Fetches historical data for ML features
        2. Formats transaction for ML model
        3. Calls predict_fraud() from ml_enhanced_model
        4. Returns fraud probability (0-1)
        
        Falls back to rule-based scoring if ML model fails.
        """
        try:
            # Get historical data for ML features
            historical_data = await self._get_account_historical_data(
                tenant_id, transaction.account_id, transaction_id
            )
            
            # Prepare transaction dict for ML model
            ml_transaction = {
                'amount': float(transaction.amount),
                'transactions_last_hour': historical_data['velocity'],
                'historical_avg_amount': historical_data['avg_amount'],
                'historical_std_amount': historical_data['std_amount'],
                'minutes_since_last_transaction': historical_data['minutes_since_last'],
                'location_changed': historical_data['location_changed'],
                'merchant_risk_score': historical_data['merchant_risk'],
                'device_changed': historical_data['device_changed'],
                'ip_reputation_score': historical_data['ip_reputation']
            }
            
            # Check cache for ML prediction (cache key based on transaction features)
            cache_key = None
            cached_prediction = None
            if self.ml_cache_enabled:
                import hashlib
                import json
                from typing import Dict, Any
                # Create cache key from transaction features
                cache_data = json.dumps(ml_transaction, sort_keys=True, default=str)
                cache_key = f"ml_prediction:{hashlib.md5(cache_data.encode()).hexdigest()}"
                try:
                    cached = self.ml_cache.get(cache_key)
                    if cached:
                        cached_prediction = json.loads(cached)
                        logger.debug(f"ML prediction cache hit for transaction {transaction_id}")
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")
            
            # Call REAL ML model (not rules!) - use cache if available
            if cached_prediction:
                prediction = cached_prediction
            else:
                prediction = predict_fraud(ml_transaction)
                
                # Cache prediction for 5 minutes (similar transactions get instant results)
                if self.ml_cache_enabled and cache_key:
                    try:
                        self.ml_cache.setex(
                            cache_key,
                            300,  # 5 minutes TTL
                            json.dumps(prediction, default=str)
                        )
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")
                
                # Store model version in prediction metadata
                if isinstance(prediction, dict):
                    prediction['model_version'] = self.model_version
            
            # Extract fraud probability
            fraud_probability = prediction.get('fraud_probability', 0.0)
            
            # Validate result
            if not isinstance(fraud_probability, (int, float)):
                raise ValueError(f"Invalid ML model output: {fraud_probability}")
            
            # Ensure between 0 and 1
            fraud_probability = max(0.0, min(1.0, float(fraud_probability)))
            
            logger.debug(
                f"ML prediction for transaction {transaction_id}: "
                f"fraud_probability={fraud_probability:.3f}, "
                f"risk_level={prediction.get('risk_level', 'UNKNOWN')}"
            )
            
            return fraud_probability
            
        except Exception as e:
            logger.error(
                f"ML model scoring failed for transaction {transaction_id}: {e}. "
                f"Falling back to rule-based scoring.",
                exc_info=True
            )
            # Fallback to rule-based scoring
            return await self._fallback_risk_score(transaction)
    
    async def _get_account_historical_data(
        self, tenant_id: str, account_id: str, current_transaction_id: int
    ) -> Dict[str, Any]:
        """Get historical account data for ML features"""
        cursor = self.db.cursor()
        try:
            # Get velocity (transactions in last hour)
            cursor.execute("""
                SELECT COUNT(*) as velocity
                FROM transactions
                WHERE account_id = %s 
                AND tenant_id = %s
                AND txn_time > NOW() - INTERVAL '1 hour'
                AND id != %s
            """, (account_id, tenant_id, current_transaction_id))
            velocity_row = cursor.fetchone()
            velocity = int(velocity_row[0]) if velocity_row and velocity_row[0] else 1
            
            # Get historical average and std deviation
            cursor.execute("""
                SELECT 
                    COALESCE(AVG(amount), 150) as avg_amount,
                    COALESCE(STDDEV(amount), 50) as std_amount
                FROM transactions
                WHERE account_id = %s 
                AND tenant_id = %s
                AND txn_time > NOW() - INTERVAL '30 days'
                AND id != %s
            """, (account_id, tenant_id, current_transaction_id))
            stats_row = cursor.fetchone()
            avg_amount = float(stats_row[0]) if stats_row and stats_row[0] else 150.0
            std_amount = float(stats_row[1]) if stats_row and stats_row[1] else 50.0
            
            # Get time since last transaction
            cursor.execute("""
                SELECT EXTRACT(EPOCH FROM (NOW() - MAX(txn_time))) / 60 as minutes
                FROM transactions
                WHERE account_id = %s 
                AND tenant_id = %s
                AND id != %s
            """, (account_id, tenant_id, current_transaction_id))
            time_row = cursor.fetchone()
            minutes_since_last = float(time_row[0]) if time_row and time_row[0] is not None else 60.0
            
            # Check location change
            cursor.execute("""
                SELECT city, country
                FROM transactions
                WHERE account_id = %s 
                AND tenant_id = %s
                AND id != %s
                ORDER BY txn_time DESC
                LIMIT 1
            """, (account_id, tenant_id, current_transaction_id))
            last_txn = cursor.fetchone()
            location_changed = False
            
            # Get current transaction location (need to query it)
            cursor.execute("""
                SELECT city, country
                FROM transactions
                WHERE id = %s
            """, (current_transaction_id,))
            current_txn = cursor.fetchone()
            
            if last_txn and current_txn:
                last_city = last_txn[0] if last_txn[0] else ""
                last_country = last_txn[1] if last_txn[1] else ""
                current_city = current_txn[0] if current_txn[0] else ""
                current_country = current_txn[1] if current_txn[1] else ""
                location_changed = (
                    (last_city and current_city and last_city != current_city) or
                    (last_country and current_country and last_country != current_country)
                )
            
            # Check device change
            cursor.execute("""
                SELECT device_id
                FROM transactions
                WHERE account_id = %s 
                AND tenant_id = %s
                AND id != %s
                ORDER BY txn_time DESC
                LIMIT 1
            """, (account_id, tenant_id, current_transaction_id))
            last_device = cursor.fetchone()
            
            cursor.execute("""
                SELECT device_id
                FROM transactions
                WHERE id = %s
            """, (current_transaction_id,))
            current_device = cursor.fetchone()
            
            device_changed = False
            if last_device and current_device:
                last_did = last_device[0] if last_device[0] else ""
                current_did = current_device[0] if current_device[0] else ""
                device_changed = (last_did and current_did and last_did != current_did)
            
            # Get merchant risk (default to 0.2 if unknown)
            merchant_risk = 0.2  # TODO: Implement merchant risk scoring from historical data
            
            # Get IP reputation (default to 0.8 if unknown)
            ip_reputation = 0.8  # TODO: Implement IP reputation check
            
            return {
                'velocity': velocity,
                'avg_amount': avg_amount,
                'std_amount': std_amount,
                'minutes_since_last': minutes_since_last,
                'location_changed': location_changed,
                'device_changed': device_changed,
                'merchant_risk': merchant_risk,
                'ip_reputation': ip_reputation
            }
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            # Return defaults if query fails
            return {
                'velocity': 1,
                'avg_amount': 150.0,
                'std_amount': 50.0,
                'minutes_since_last': 60.0,
                'location_changed': False,
                'device_changed': False,
                'merchant_risk': 0.2,
                'ip_reputation': 0.8
            }
        finally:
            cursor.close()
    
    async def _fallback_risk_score(self, transaction: TransactionCreate) -> float:
        """Fallback rule-based scoring if ML model fails"""
        score = 0.0
        if transaction.amount > 5000:
            score += 0.5
        elif transaction.amount > 1000:
            score += 0.3
        if transaction.country and transaction.country not in ['USA', 'CAN', 'US']:
            score += 0.2
        if transaction.channel == 'ONLINE':
            score += 0.1
        return min(score, 1.0)
    
    async def ingest_batch(
        self,
        tenant_id: str,
        transactions: list[TransactionCreate],
        max_batch_size: int = 100
    ) -> dict:
        """
        Ingest multiple transactions at once
        
        Returns: Batch processing results
        """
        if len(transactions) > max_batch_size:
            return {
                "success": False,
                "error": f"Batch size {len(transactions)} exceeds maximum {max_batch_size}"
            }
        
        results = {
            "total": len(transactions),
            "success": 0,
            "failed": 0,
            "transactions": []
        }
        
        for transaction in transactions:
            try:
                result = await self.ingest_transaction(tenant_id, transaction)
                results["transactions"].append(result)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["transactions"].append({
                    "error": str(e),
                    "reference_id": transaction.reference_id
                })
        
        return results

