"""
Secrets Management
Centralized management of API keys, database credentials, etc.
Integrates with environment variables, AWS Secrets Manager, HashiCorp Vault
"""
import os
import json
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages application secrets
    Supports: Environment variables, AWS Secrets Manager, HashiCorp Vault
    """
    
    def __init__(self, backend: str = 'env'):
        """
        Initialize secrets manager
        
        Args:
            backend: 'env' (environment variables), 'aws' (AWS Secrets Manager), 'vault' (HashiCorp Vault)
        """
        self.backend = backend
        
        if backend == 'aws':
            try:
                import boto3
                self.aws_client = boto3.client('secretsmanager')
            except ImportError:
                logger.error("boto3 not installed. Install with: pip install boto3")
                raise
        
        if backend == 'vault':
            try:
                import hvac
                vault_url = os.getenv('VAULT_ADDR', 'http://localhost:8200')
                vault_token = os.getenv('VAULT_TOKEN')
                self.vault_client = hvac.Client(url=vault_url, token=vault_token)
            except ImportError:
                logger.error("hvac not installed. Install with: pip install hvac")
                raise
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret
        
        Args:
            secret_name: Name of the secret
            default: Default value if secret not found
        
        Returns:
            Secret value or default
        """
        if self.backend == 'env':
            return self._get_from_env(secret_name, default)
        elif self.backend == 'aws':
            return self._get_from_aws(secret_name, default)
        elif self.backend == 'vault':
            return self._get_from_vault(secret_name, default)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def _get_from_env(self, secret_name: str, default: Optional[str]) -> Optional[str]:
        """Get secret from environment variable"""
        return os.getenv(secret_name, default)
    
    def _get_from_aws(self, secret_name: str, default: Optional[str]) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            response = self.aws_client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                return response['SecretString']
            else:
                # Binary secret
                import base64
                return base64.b64decode(response['SecretBinary']).decode('utf-8')
        
        except self.aws_client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret {secret_name} not found in AWS Secrets Manager")
            return default
        except Exception as e:
            logger.error(f"Error retrieving secret from AWS: {e}")
            return default
    
    def _get_from_vault(self, secret_name: str, default: Optional[str]) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        try:
            # Assuming KV v2 secrets engine mounted at 'secret/'
            secret_path = f"secret/data/{secret_name}"
            response = self.vault_client.secrets.kv.v2.read_secret_version(
                path=secret_name,
                mount_point='secret'
            )
            return response['data']['data'].get('value', default)
        
        except Exception as e:
            logger.error(f"Error retrieving secret from Vault: {e}")
            return default
    
    def get_database_credentials(self, db_name: str = 'postgres') -> Dict[str, str]:
        """
        Get database credentials
        
        Returns:
            Dict with host, port, database, user, password
        """
        prefix = f"{db_name.upper()}_"
        
        return {
            'host': self.get_secret(f'{prefix}HOST', 'localhost'),
            'port': int(self.get_secret(f'{prefix}PORT', '5432')),
            'database': self.get_secret(f'{prefix}DB', 'frauddb'),
            'user': self.get_secret(f'{prefix}USER', 'postgres'),
            'password': self.get_secret(f'{prefix}PASSWORD', '')
        }
    
    def get_encryption_key(self) -> str:
        """Get master encryption key"""
        key = self.get_secret('ENCRYPTION_MASTER_KEY')
        if not key:
            logger.warning("ENCRYPTION_MASTER_KEY not found! Using default (INSECURE)")
            # In production, this should raise an error
            from security.encryption import generate_master_key
            return generate_master_key()
        return key
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        secret = self.get_secret('JWT_SECRET_KEY')
        if not secret:
            logger.warning("JWT_SECRET_KEY not found! Using default (INSECURE)")
            return 'dev-secret-change-in-production'
        return secret
    
    def get_oauth_credentials(self, provider: str) -> Dict[str, str]:
        """
        Get OAuth credentials for a provider
        
        Args:
            provider: 'google', 'microsoft', 'okta'
        
        Returns:
            Dict with client_id and client_secret
        """
        prefix = f"{provider.upper()}_OAUTH_"
        
        return {
            'client_id': self.get_secret(f'{prefix}CLIENT_ID', ''),
            'client_secret': self.get_secret(f'{prefix}CLIENT_SECRET', ''),
            'redirect_uri': self.get_secret(f'{prefix}REDIRECT_URI', f'http://localhost:3000/auth/callback/{provider}')
        }
    
    def get_stripe_keys(self) -> Dict[str, str]:
        """Get Stripe API keys"""
        return {
            'api_key': self.get_secret('STRIPE_API_KEY', ''),
            'webhook_secret': self.get_secret('STRIPE_WEBHOOK_SECRET', ''),
            'publishable_key': self.get_secret('STRIPE_PUBLISHABLE_KEY', '')
        }


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(backend: str = 'env') -> SecretsManager:
    """Get or create global secrets manager instance"""
    global _secrets_manager
    
    if _secrets_manager is None:
        _secrets_manager = SecretsManager(backend=backend)
    
    return _secrets_manager


# Example usage:
"""
from security.secrets_manager import get_secrets_manager

# Get secrets manager
secrets = get_secrets_manager(backend='env')  # or 'aws', 'vault'

# Get individual secret
api_key = secrets.get_secret('API_KEY')

# Get database credentials
db_creds = secrets.get_database_credentials('postgres')

# Get OAuth credentials
google_oauth = secrets.get_oauth_credentials('google')

# Get Stripe keys
stripe_keys = secrets.get_stripe_keys()
"""

