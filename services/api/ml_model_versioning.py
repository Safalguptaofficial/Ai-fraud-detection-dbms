"""
ML Model Versioning and A/B Testing Support
Manages multiple model versions and enables gradual rollout
"""
from typing import Optional, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """Manage ML model versions and A/B testing"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.redis_enabled = redis_client is not None
        self.versions = {
            "1.0": {
                "name": "Production v1.0",
                "status": "active",
                "weight": 100,  # 100% traffic
                "created_at": "2025-01-01"
            },
            "1.1": {
                "name": "Improved v1.1",
                "status": "testing",
                "weight": 0,  # 0% traffic (A/B testing)
                "created_at": datetime.utcnow().isoformat()
            }
        }
    
    def get_model_version(self, tenant_id: Optional[str] = None) -> str:
        """
        Get active model version for tenant
        
        Supports A/B testing - can return different versions based on tenant
        """
        # If A/B testing enabled, check tenant assignment
        if tenant_id and self.redis_enabled:
            try:
                cached_version = self.redis.get(f"model_version:{tenant_id}")
                if cached_version:
                    version = cached_version.decode() if isinstance(cached_version, bytes) else cached_version
                    if version in self.versions:
                        return version
            except Exception as e:
                logger.warning(f"Failed to get cached model version: {e}")
        
        # Return active version (highest weight)
        active_version = "1.0"
        max_weight = 0
        for version, config in self.versions.items():
            if config["status"] == "active" and config["weight"] > max_weight:
                max_weight = config["weight"]
                active_version = version
        
        return active_version
    
    def set_model_version(self, tenant_id: str, version: str):
        """Set specific model version for tenant (A/B testing)"""
        if version not in self.versions:
            raise ValueError(f"Unknown model version: {version}")
        
        if self.redis_enabled:
            try:
                self.redis.setex(
                    f"model_version:{tenant_id}",
                    86400,  # 24 hours
                    version
                )
            except Exception as e:
                logger.warning(f"Failed to cache model version: {e}")
    
    def get_version_info(self, version: str) -> Dict:
        """Get information about a model version"""
        return self.versions.get(version, {})
    
    def list_versions(self) -> Dict:
        """List all available model versions"""
        return {
            "versions": self.versions,
            "active": self.get_model_version()
        }


# Global model version manager instance
_model_manager: Optional[ModelVersionManager] = None

def get_model_version_manager(redis_client=None) -> ModelVersionManager:
    """Get or create model version manager"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelVersionManager(redis_client)
    return _model_manager

