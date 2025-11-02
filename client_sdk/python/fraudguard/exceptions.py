"""
FraudGuard SDK Exceptions
"""
from typing import Optional


class FraudGuardError(Exception):
    """Base exception for FraudGuard SDK"""
    pass


class RateLimitError(FraudGuardError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ValidationError(FraudGuardError):
    """Raised when transaction data is invalid"""
    pass


class AuthenticationError(FraudGuardError):
    """Raised when authentication fails"""
    pass

