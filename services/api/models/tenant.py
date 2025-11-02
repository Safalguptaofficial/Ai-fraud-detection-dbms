"""
Tenant Models for Multi-Tenancy Support
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TenantPlan(str, Enum):
    """Subscription plan tiers"""
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class TenantStatus(str, Enum):
    """Tenant account status"""
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class Tenant(BaseModel):
    """Tenant information"""
    tenant_id: str
    organization_name: str
    subdomain: str
    plan: TenantPlan
    status: TenantStatus
    
    # Configuration
    settings: Dict[str, Any] = {}
    ml_config: Dict[str, Any] = {}
    
    # Limits
    max_users: int = 5
    max_transactions_per_month: int = 50000
    max_storage_gb: int = 10
    max_api_calls_per_minute: int = 100
    
    # Billing
    stripe_customer_id: Optional[str] = None
    billing_email: Optional[str] = None
    api_key: str
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    trial_ends_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    
    # Contact
    admin_name: Optional[str] = None
    admin_email: EmailStr
    admin_phone: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TenantCreate(BaseModel):
    """Schema for creating new tenant"""
    organization_name: str = Field(..., min_length=2, max_length=255)
    subdomain: str = Field(..., min_length=3, max_length=64, pattern=r'^[a-z0-9-]+$')
    admin_name: str
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_phone: Optional[str] = None
    plan: TenantPlan = TenantPlan.STARTER
    
    @validator('subdomain')
    def subdomain_must_be_lowercase(cls, v):
        """Ensure subdomain is lowercase"""
        return v.lower()
    
    @validator('admin_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class TenantUpdate(BaseModel):
    """Schema for updating tenant"""
    organization_name: Optional[str] = None
    admin_name: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    admin_phone: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    ml_config: Optional[Dict[str, Any]] = None


class TenantUser(BaseModel):
    """Tenant user information"""
    id: int
    tenant_id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    email_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TenantUserCreate(BaseModel):
    """Schema for creating tenant user"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: str = "ANALYST"
    
    @validator('role')
    def role_must_be_valid(cls, v):
        """Validate role"""
        valid_roles = ['ADMIN', 'MANAGER', 'ANALYST', 'VIEWER']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class TenantUsage(BaseModel):
    """Tenant usage statistics"""
    tenant_id: str
    transactions_this_month: int
    transactions_limit: int
    transactions_percentage: float
    active_users: int
    users_limit: int
    storage_used_gb: float
    storage_limit_gb: int
    api_calls_this_minute: int
    api_calls_limit: int


class TenantAPIKey(BaseModel):
    """API Key information"""
    id: int
    tenant_id: str
    key_name: str
    key_prefix: str
    scopes: List[str]
    rate_limit_per_minute: int
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TenantAPIKeyCreate(BaseModel):
    """Schema for creating API key"""
    key_name: str = Field(..., min_length=3, max_length=128)
    scopes: List[str] = [
        'read:transactions',
        'write:transactions',
        'read:alerts',
        'write:alerts'
    ]
    rate_limit_per_minute: int = 100
    expires_days: Optional[int] = 365


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: TenantUser
    tenant: dict

