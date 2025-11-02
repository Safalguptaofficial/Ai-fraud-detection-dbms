from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    environment: str = "development"
    base_url: str = "http://localhost:8000"
    
    # Database URIs
    oracle_uri: str
    postgres_uri: str
    mongo_uri: str
    redis_uri: Optional[str] = None
    
    # Security
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_secret: str = "dev-secret-change-in-production"  # Backward compatibility
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # Encryption
    encryption_master_key: Optional[str] = None
    
    # API Keys
    api_key_worker: str = "dev-key"
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    
    # OAuth2 / SSO (Phase 2)
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None
    microsoft_oauth_client_id: Optional[str] = None
    microsoft_oauth_client_secret: Optional[str] = None
    okta_oauth_client_id: Optional[str] = None
    okta_oauth_client_secret: Optional[str] = None
    okta_domain: Optional[str] = None
    
    # Stripe (Phase 3)
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    
    # Email (Optional)
    sendgrid_api_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # SMS / Twilio (Optional)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    
    # Secrets Management
    secrets_backend: str = "env"  # 'env', 'aws', 'vault'
    vault_addr: Optional[str] = None
    vault_token: Optional[str] = None
    
    # Feature Flags
    enable_sso: bool = False
    enable_mfa: bool = True
    enable_billing: bool = True
    enable_data_ingestion: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

