"""
Redis caching layer for improved performance
"""
import redis
import json
from typing import Any, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)

# Redis client
try:
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Caching disabled.")
    redis_client = None


class Cache:
    """Simple cache wrapper"""
    
    def __init__(self, client=None):
        self.client = client or redis_client
        self.enabled = self.client is not None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        if not self.enabled:
            return False
        
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        if not self.enabled:
            return False
        
        try:
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return False


# Singleton cache instance
cache = Cache()

