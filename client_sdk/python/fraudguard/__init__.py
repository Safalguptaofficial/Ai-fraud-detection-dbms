"""
FraudGuard Python SDK
Easy integration for fraud detection in Python applications
"""
from .client import FraudGuardClient
from .exceptions import FraudGuardError, RateLimitError, ValidationError

__version__ = "1.0.0"
__all__ = ["FraudGuardClient", "FraudGuardError", "RateLimitError", "ValidationError"]

