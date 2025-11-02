"""
Tenant Middleware - Automatically extracts and sets tenant context
"""
from fastapi import Request, HTTPException, status
from typing import Optional
import logging
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

# JWT secret (should match your auth configuration)
JWT_SECRET = "dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"


class TenantMiddleware:
    """
    Middleware to extract and set current tenant
    
    Tenant can be identified by:
    1. API key header (X-API-Key)
    2. JWT token (Authorization: Bearer)
    3. Subdomain (tenant.fraudguard.com)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware"""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        request = Request(scope, receive=receive)
        method = scope.get("method", "")
        
        # Allow OPTIONS (CORS preflight) requests without authentication
        if method == "OPTIONS":
            return await self.app(scope, receive, send)
        
        # Extract tenant ID
        tenant_id = await self.extract_tenant_id(request)
        
        # Check if route requires tenant
        if not tenant_id and not self.is_public_route(request.url.path):
            # Return 401 Unauthorized
            response = {
                "type": "http.response.start",
                "status": 401,
                "headers": [[b"content-type", b"application/json"]],
            }
            await send(response)
            await send({
                "type": "http.response.body",
                "body": b'{"detail":"No tenant identified. Please provide X-API-Key header or valid JWT token."}'
            })
            return
        
        # Store tenant_id in scope for later access
        scope["tenant_id"] = tenant_id
        
        # Note: Database tenant context will be set in the route handlers via deps
        
        # Continue to next middleware/route
        await self.app(scope, receive, send)
    
    async def extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        
        # 1. Try API Key header
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if api_key:
            tenant_id = await self.get_tenant_from_api_key(request, api_key)
            if tenant_id:
                logger.debug(f"Tenant identified by API key: {tenant_id}")
                return tenant_id
        
        # 2. Try JWT token
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            tenant_id = await self.get_tenant_from_jwt(token)
            if tenant_id:
                logger.debug(f"Tenant identified by JWT: {tenant_id}")
                return tenant_id
        
        # 3. Try subdomain
        host = request.headers.get("Host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "admin", "localhost"]:
                tenant_id = await self.get_tenant_from_subdomain(request, subdomain)
                if tenant_id:
                    logger.debug(f"Tenant identified by subdomain: {tenant_id}")
                    return tenant_id
        
        return None
    
    async def get_tenant_from_api_key(self, request: Request, api_key: str) -> Optional[str]:
        """Get tenant ID from API key"""
        
        try:
            from deps import get_postgres
            # Get a database connection
            db_gen = get_postgres()
            db = next(db_gen)
            try:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT tenant_id FROM tenants WHERE api_key = %s AND status IN ('ACTIVE', 'TRIAL')",
                    (api_key,)
                )
                result = cursor.fetchone()
                cursor.close()
                if result:
                    logger.info(f"Found tenant_id for API key: {result[0]}")
                    return result[0]
                else:
                    logger.warning(f"No tenant found for API key: {api_key[:20]}...")
                    return None
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting tenant from API key: {e}")
            return None
    
    async def get_tenant_from_jwt(self, token: str) -> Optional[str]:
        """Get tenant ID from JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload.get("tenant_id")
        except JWTError as e:
            logger.debug(f"Invalid JWT token: {e}")
            return None
    
    async def get_tenant_from_subdomain(self, request: Request, subdomain: str) -> Optional[str]:
        """Get tenant ID from subdomain"""
        try:
            from deps import get_postgres
            # Get a database connection
            db_gen = get_postgres()
            db = next(db_gen)
            try:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT tenant_id FROM tenants WHERE subdomain = %s AND status IN ('ACTIVE', 'TRIAL')",
                    (subdomain,)
                )
                result = cursor.fetchone()
                cursor.close()
                return result[0] if result else None
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting tenant from subdomain: {e}")
            return None
    
    async def set_database_tenant(self, db, tenant_id: str):
        """Set PostgreSQL session variable for Row-Level Security"""
        try:
            cursor = db.cursor()
            cursor.execute("SELECT set_current_tenant(%s)", (tenant_id,))
            db.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to set database tenant: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to set tenant context"
            )
    
    def is_public_route(self, path: str) -> bool:
        """Check if route is public (no tenant required)"""
        public_routes = [
            "/",
            "/health",
            "/healthz",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/login",
            "/api/v1/tenants/signup",
            "/api/v1/tenants/login",
            "/api/v1/tenants/health",
            "/api/v1/auth/forgot-password"
        ]
        
        # Check exact matches
        if path in public_routes:
            return True
        
        # Check prefix matches
        public_prefixes = [
            "/static/",
            "/_next/",
            "/favicon.ico"
        ]
        
        for prefix in public_prefixes:
            if path.startswith(prefix):
                return True
        
        return False


def get_current_tenant(request: Request) -> str:
    """
    Dependency to get current tenant ID from request
    
    Usage:
        @router.get("/items")
        async def get_items(tenant_id: str = Depends(get_current_tenant)):
            # tenant_id is automatically injected
    """
    # Scope is a dict, so use .get() not hasattr
    tenant_id = request.scope.get('tenant_id')
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No tenant identified"
        )
    return tenant_id


def get_current_user_id(request: Request) -> int:
    """
    Dependency to get current user ID from request
    
    Usage:
        @router.get("/profile")
        async def get_profile(user_id: int = Depends(get_current_user_id)):
            # user_id is automatically injected
    """
    if not hasattr(request.scope, 'user_id') or not request.scope.get('user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.scope['user_id']


def require_role(required_role: str):
    """
    Dependency to require a specific role
    
    Usage:
        @router.post("/admin")
        async def admin_action(
            _: bool = Depends(require_role("ADMIN")),
            tenant_id: str = Depends(get_current_tenant)
        ):
            # Only ADMIN users can access this endpoint
    """
    def role_checker(request: Request) -> bool:
        user_role = request.scope.get('user_role', 'VIEWER')
        
        # Role hierarchy: ADMIN > MANAGER > ANALYST > VIEWER
        role_hierarchy = {'VIEWER': 0, 'ANALYST': 1, 'MANAGER': 2, 'ADMIN': 3}
        
        current_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if current_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return True
    
    return role_checker

