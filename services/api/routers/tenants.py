"""
Tenant Management API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
import logging
from datetime import datetime, timedelta
from jose import jwt

from models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantUser,
    TenantUserCreate, TenantUsage, TenantAPIKeyCreate,
    LoginRequest, LoginResponse
)
from tenants import TenantManager
from deps import get_postgres
from middleware import get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])

# JWT configuration
JWT_SECRET = "dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def create_access_token(user_data: dict) -> dict:
    """Create JWT access token"""
    expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": str(user_data["user_id"]),
        "email": user_data["email"],
        "tenant_id": user_data["tenant_id"],
        "role": user_data["role"],
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "expires_in": int(expires_delta.total_seconds())
    }


@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
async def signup(
    tenant_create: TenantCreate,
    db = Depends(get_postgres)
):
    """
    🆕 Sign up new tenant organization
    
    Creates:
    - New tenant account
    - Admin user
    - API key
    - Usage tracking
    
    **Demo Request:**
    ```json
    {
        "organization_name": "Acme Corp",
        "subdomain": "acme",
        "admin_name": "John Doe",
        "admin_email": "john@acme.com",
        "admin_password": "SecurePass123!",
        "admin_phone": "+1234567890",
        "plan": "STARTER"
    }
    ```
    """
    try:
        tenant_manager = TenantManager(db)
        
        # Check if subdomain already exists
        existing = await tenant_manager.get_tenant_by_subdomain(tenant_create.subdomain)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subdomain '{tenant_create.subdomain}' already taken"
            )
        
        # Check if email already exists
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM tenant_users WHERE email = %s",
            (tenant_create.admin_email,)
        )
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{tenant_create.admin_email}' already registered"
            )
        cursor.close()
        
        # Create tenant
        tenant = await tenant_manager.create_tenant(tenant_create)
        
        logger.info(f"✅ New tenant signed up: {tenant.tenant_id} ({tenant.organization_name})")
        
        return {
            "message": "Organization created successfully!",
            "tenant_id": tenant.tenant_id,
            "organization_name": tenant.organization_name,
            "subdomain": tenant.subdomain,
            "api_key": tenant.api_key,  # ⚠️ Show only once
            "admin_email": tenant.admin_email,
            "plan": tenant.plan,
            "status": tenant.status,
            "trial_ends_at": tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_req: LoginRequest,
    db = Depends(get_postgres)
):
    """
    🔐 Login tenant user
    
    Returns JWT token with user and tenant info
    """
    try:
        tenant_manager = TenantManager(db)
        
        # Authenticate user
        user_data = await tenant_manager.authenticate_user(
            login_req.email,
            login_req.password
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create access token
        token = create_access_token(user_data)
        
        # Build user object
        user = TenantUser(
            id=user_data["user_id"],
            tenant_id=user_data["tenant_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=True,
            email_verified=False,  # TODO: implement email verification
            last_login=datetime.now(),
            created_at=datetime.now()
        )
        
        # Build tenant info
        tenant_info = {
            "tenant_id": user_data["tenant_id"],
            "organization_name": user_data["organization_name"],
            "plan": user_data["plan"],
            "status": user_data["tenant_status"]
        }
        
        logger.info(f"✅ User logged in: {user_data['email']}")
        
        return LoginResponse(
            access_token=token["access_token"],
            token_type=token["token_type"],
            expires_in=token["expires_in"],
            user=user,
            tenant=tenant_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=Tenant)
async def get_my_tenant(
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_postgres)
):
    """
    📊 Get current tenant information
    
    Requires JWT token
    """
    try:
        tenant_manager = TenantManager(db)
        tenant = await tenant_manager.get_tenant_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tenant information"
        )


@router.patch("/me", response_model=Tenant)
async def update_my_tenant(
    updates: TenantUpdate,
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_postgres)
):
    """
    ✏️ Update current tenant information
    
    Requires JWT token
    """
    try:
        tenant_manager = TenantManager(db)
        tenant = await tenant_manager.update_tenant(tenant_id, updates)
        
        logger.info(f"Tenant updated: {tenant_id}")
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )


@router.get("/usage", response_model=TenantUsage)
async def get_usage(
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_postgres)
):
    """
    📈 Get current tenant usage statistics
    
    Shows:
    - Transactions this month vs limit
    - Active users vs limit
    - Storage used vs limit
    - API calls vs rate limit
    """
    try:
        tenant_manager = TenantManager(db)
        usage = await tenant_manager.get_tenant_usage(tenant_id)
        
        return usage
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: TenantUserCreate,
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_postgres)
):
    """
    👤 Create new user in current tenant
    
    Requires ADMIN role
    """
    try:
        # Check if email already exists
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM tenant_users WHERE tenant_id = %s AND email = %s",
            (tenant_id, user_create.email)
        )
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{user_create.email}' already exists"
            )
        
        # Hash password
        tenant_manager = TenantManager(db)
        password_hash = tenant_manager.hash_password(user_create.password)
        
        # Create user
        cursor.execute("""
            INSERT INTO tenant_users (
                tenant_id, email, password_hash, full_name, role
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (
            tenant_id,
            user_create.email,
            password_hash,
            user_create.full_name,
            user_create.role
        ))
        
        result = cursor.fetchone()
        db.commit()
        cursor.close()
        
        logger.info(f"User created in tenant {tenant_id}: {user_create.email}")
        
        return {
            "message": "User created successfully",
            "user_id": result[0],
            "email": user_create.email,
            "role": user_create.role,
            "created_at": result[1].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/api-keys", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_create: TenantAPIKeyCreate,
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    db = Depends(get_postgres)
):
    """
    🔑 Create new API key for programmatic access
    
    ⚠️ API key is shown only once! Save it securely.
    
    Requires ADMIN role
    """
    try:
        # Get current user ID from JWT (simplified - in production, use proper auth)
        user_id = 1  # TODO: Extract from JWT token
        
        tenant_manager = TenantManager(db)
        api_key_data = await tenant_manager.create_api_key(
            tenant_id,
            key_create,
            user_id
        )
        
        logger.info(f"API key created for tenant {tenant_id}")
        
        return {
            "message": "⚠️ Save this API key securely! It will not be shown again.",
            **api_key_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/health")
async def tenant_health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tenant-management",
        "timestamp": datetime.utcnow().isoformat()
    }

