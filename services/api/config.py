from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    environment: str = "development"
    
    # Database URIs
    oracle_uri: str
    postgres_uri: str
    mongo_uri: str
    redis_uri: Optional[str] = None
    
    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API Keys
    api_key_worker: str = "dev-key"
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

