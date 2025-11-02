"""
FraudGuard Client for Python
"""
import requests
from typing import Dict, List, Optional, Any
from .exceptions import FraudGuardError, RateLimitError, ValidationError


class FraudGuardClient:
    """
    Client for FraudGuard Fraud Detection API
    
    Usage:
        client = FraudGuardClient(api_key="fgk_live_xxx", base_url="https://api.fraudguard.com")
        
        # Analyze a transaction
        result = client.analyze_transaction({
            "amount": 150.00,
            "account_id": "ACC123",
            "merchant": "Example Store"
        })
        
        # Ingest transaction for monitoring
        result = client.ingest_transaction({
            "account_id": "ACC123",
            "amount": 150.00,
            "merchant": "Example Store",
            "currency": "USD"
        })
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        """
        Initialize FraudGuard client
        
        Args:
            api_key: Your FraudGuard API key
            base_url: API base URL (default: http://localhost:8000)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a transaction for fraud risk
        
        Args:
            transaction: Transaction data with keys:
                - amount: Transaction amount (float)
                - account_id: Account identifier (str)
                - merchant: Merchant name (str)
                - currency: Currency code (str, optional)
                - channel: Transaction channel (str, optional)
                - city, country: Location (str, optional)
                - ip_address: IP address (str, optional)
                - device_id: Device identifier (str, optional)
        
        Returns:
            Dict with fraud prediction:
            {
                'risk_score': float (0-100),
                'fraud_probability': float (0-1),
                'risk_level': str ('LOW', 'MEDIUM', 'HIGH'),
                'model_confidence': float,
                'triggered_rules': list,
                'recommendation': str
            }
        
        Raises:
            FraudGuardError: If API request fails
            RateLimitError: If rate limit exceeded
            ValidationError: If transaction data is invalid
        """
        try:
            response = self.session.post(
                f"{self.base_url}/v1/ml/predict",
                json=transaction,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {e.response.text}")
            elif e.response.status_code == 422:
                raise ValidationError(f"Invalid transaction data: {e.response.text}")
            else:
                raise FraudGuardError(f"API error: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise FraudGuardError(f"Network error: {str(e)}")
    
    def ingest_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest a transaction for real-time monitoring and fraud detection
        
        Args:
            transaction: Transaction data (see analyze_transaction for format)
        
        Returns:
            Dict with ingestion result:
            {
                'transaction_id': int,
                'status': str ('APPROVED', 'REVIEW', 'BLOCKED'),
                'fraud_score': float (0-1),
                'reference_id': str,
                'timestamp': str,
                'processing_time_ms': float
            }
        
        Raises:
            FraudGuardError: If ingestion fails
            RateLimitError: If rate limit exceeded
            ValidationError: If transaction data is invalid
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/ingestion/transactions",
                json=transaction,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = e.response.json().get('retry_after', 60)
                raise RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds",
                    retry_after=retry_after
                )
            elif e.response.status_code == 400:
                raise ValidationError(f"Invalid transaction: {e.response.text}")
            else:
                raise FraudGuardError(f"Ingestion failed: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise FraudGuardError(f"Network error: {str(e)}")
    
    def batch_ingest(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest multiple transactions at once (max 100)
        
        Args:
            transactions: List of transaction dicts
        
        Returns:
            Dict with batch results:
            {
                'total': int,
                'success': int,
                'failed': int,
                'transactions': list
            }
        """
        if len(transactions) > 100:
            raise ValidationError("Batch size cannot exceed 100 transactions")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/ingestion/transactions/batch",
                json=transactions,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {e.response.text}")
            else:
                raise FraudGuardError(f"Batch ingestion failed: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise FraudGuardError(f"Network error: {str(e)}")
    
    def get_alerts(self, account_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get fraud alerts
        
        Args:
            account_id: Filter by account ID (optional)
            limit: Maximum number of alerts to return
        
        Returns:
            List of alert dicts
        """
        params = {"limit": limit}
        if account_id:
            params["account_id"] = account_id
        
        try:
            response = self.session.get(
                f"{self.base_url}/v1/alerts",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise FraudGuardError(f"Failed to get alerts: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise FraudGuardError(f"Network error: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health
        
        Returns:
            Health status dict
        """
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise FraudGuardError(f"Health check failed: {str(e)}")

