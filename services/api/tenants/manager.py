"""
Tenant Manager - Handles all tenant operations
"""
import secrets
import hashlib
from passlib.context import CryptContext
from typing import Optional, Dict, List
import json
from datetime import datetime, timedelta
import logging

from models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantUser, 
    TenantUserCreate, TenantUsage, TenantAPIKey, TenantAPIKeyCreate
)

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def row_to_dict(cursor, row):
    """Convert psycopg3 row tuple to dict"""
    if row is None:
        return None
    return dict(zip([desc[0] for desc in cursor.description], row))


class TenantManager:
    """Manages tenant operations"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def create_tenant(self, tenant_create: TenantCreate) -> Tenant:
        """
        Create new tenant with admin user
        
        Steps:
        1. Generate tenant ID and API key
        2. Hash admin password
        3. Create tenant record
        4. Create admin user
        5. Initialize usage tracking
        """
        # Generate tenant ID
        tenant_id = f"tenant_{secrets.token_urlsafe(16)}"
        
        # Generate API key
        api_key = self._generate_api_key()
        
        # Hash admin password (handle bcrypt 72-byte limit issue)
        try:
            import bcrypt
            # Use bcrypt directly to avoid passlib compatibility issues
            password_bytes = tenant_create.admin_password.encode('utf-8')
            # Bcrypt has a 72-byte limit, but our passwords are shorter
            password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
        except ImportError:
            # Fallback to passlib
            password_hash = pwd_context.hash(tenant_create.admin_password)
        except Exception as e:
            logger.error(f"Password hashing error: {e}, using passlib fallback")
            password_hash = pwd_context.hash(tenant_create.admin_password)
        
        cursor = self.db.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN")
            
            # Insert tenant
            cursor.execute("""
                INSERT INTO tenants (
                    tenant_id, organization_name, subdomain,
                    admin_name, admin_email, admin_phone,
                    plan, api_key
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                tenant_id,
                tenant_create.organization_name,
                tenant_create.subdomain,
                tenant_create.admin_name,
                tenant_create.admin_email,
                tenant_create.admin_phone,
                tenant_create.plan.value,
                api_key
            ))
            
            tenant_record = row_to_dict(cursor, cursor.fetchone())
            
            # Create admin user
            cursor.execute("""
                INSERT INTO tenant_users (
                    tenant_id, email, password_hash,
                    full_name, role, is_active, email_verified
                ) VALUES (%s, %s, %s, %s, 'ADMIN', true, false)
                RETURNING id
            """, (
                tenant_id,
                tenant_create.admin_email,
                password_hash,
                tenant_create.admin_name
            ))
            
            admin_user_id = row_to_dict(cursor, cursor.fetchone())['id']
            
            # Initialize usage tracking for current month
            cursor.execute("""
                INSERT INTO tenant_usage (
                    tenant_id,
                    period_start,
                    period_end
                ) VALUES (
                    %s,
                    DATE_TRUNC('month', CURRENT_DATE),
                    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day'
                )
            """, (tenant_id,))
            
            # Audit log
            cursor.execute("""
                INSERT INTO audit_logs (
                    tenant_id, user_id, action, resource_type,
                    new_value, severity
                ) VALUES (%s, %s, 'CREATE_TENANT', 'TENANT', %s::jsonb, 'INFO')
            """, (
                tenant_id,
                admin_user_id,
                json.dumps({'organization': tenant_create.organization_name})
            ))
            
            # Commit transaction
            cursor.execute("COMMIT")
            
            logger.info(f"Created tenant: {tenant_id} ({tenant_create.organization_name})")
            
            return Tenant(**tenant_record)
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Failed to create tenant: {str(e)}")
            raise Exception(f"Failed to create tenant: {str(e)}")
        finally:
            cursor.close()
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM tenants WHERE tenant_id = %s",
                (tenant_id,)
            )
            record = row_to_dict(cursor, cursor.fetchone())
            return Tenant(**record) if record else None
        finally:
            cursor.close()
    
    async def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """Get tenant by subdomain"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM tenants WHERE subdomain = %s",
                (subdomain,)
            )
            record = row_to_dict(cursor, cursor.fetchone())
            return Tenant(**record) if record else None
        finally:
            cursor.close()
    
    async def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM tenants WHERE api_key = %s AND status = 'ACTIVE'",
                (api_key,)
            )
            record = row_to_dict(cursor, cursor.fetchone())
            return Tenant(**record) if record else None
        finally:
            cursor.close()
    
    async def update_tenant(self, tenant_id: str, updates: TenantUpdate) -> Tenant:
        """Update tenant information"""
        cursor = self.db.cursor()
        
        try:
            # Build dynamic update query
            update_fields = []
            values = []
            
            for field, value in updates.dict(exclude_unset=True).items():
                if value is not None:
                    update_fields.append(f"{field} = %s")
                    values.append(value)
            
            if not update_fields:
                return await self.get_tenant_by_id(tenant_id)
            
            values.append(tenant_id)
            
            query = f"""
                UPDATE tenants 
                SET {', '.join(update_fields)}
                WHERE tenant_id = %s
                RETURNING *
            """
            
            cursor.execute(query, values)
            self.db.commit()
            
            record = row_to_dict(cursor, cursor.fetchone())
            return Tenant(**record)
        finally:
            cursor.close()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate tenant user"""
        cursor = self.db.cursor()
        
        try:
            # Optimized query with explicit column selection
            cursor.execute("""
                SELECT 
                    u.id, u.tenant_id, u.email, u.password_hash, u.full_name, u.role,
                    t.tenant_id, t.organization_name, t.plan, t.status
                FROM tenant_users u
                JOIN tenants t ON u.tenant_id = t.tenant_id
                WHERE u.email = %s AND u.is_active = true AND t.status IN ('ACTIVE', 'TRIAL')
                LIMIT 1
            """, (email,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return None
            
            # Convert row to dict manually for better performance
            user = {
                'id': row[0],
                'tenant_id': row[1],
                'email': row[2],
                'password_hash': row[3],
                'full_name': row[4],
                'role': row[5],
                'organization_name': row[7],
                'plan': row[8],
                'status': row[9]
            }
            
            # Verify password (handle bcrypt version compatibility)
            try:
                import bcrypt
                # Use bcrypt directly to avoid passlib compatibility issues
                password_bytes = password.encode('utf-8')
                hash_bytes = user['password_hash'].encode('utf-8')
                
                # Try bcrypt direct verification first
                if bcrypt.checkpw(password_bytes, hash_bytes):
                    pass  # Password is correct
                else:
                    logger.warning(f"Failed login attempt for user: {email}")
                    return None
            except ImportError:
                # Fallback to passlib if bcrypt not available directly
                try:
                    if not pwd_context.verify(password, user['password_hash']):
                        logger.warning(f"Failed login attempt for user: {email}")
                        return None
                except Exception as e:
                    logger.error(f"Password verification error for {email}: {e}")
                    return None
            except Exception as e:
                logger.error(f"Password verification error for {email}: {e}")
                # Last resort: try passlib with error handling
                try:
                    if not pwd_context.verify(password, user['password_hash']):
                        logger.warning(f"Failed login attempt for user: {email}")
                        return None
                except:
                    logger.error(f"All password verification methods failed for {email}")
                    return None
            
            # Update last login (non-blocking, don't wait for commit)
            try:
                cursor.execute("""
                    UPDATE tenant_users 
                    SET last_login = NOW(), login_count = COALESCE(login_count, 0) + 1
                    WHERE id = %s
                """, (user['id'],))
            except Exception as e:
                logger.warning(f"Failed to update last_login: {e}")
            
            # Audit log (non-blocking, optional - don't fail login if this fails)
            try:
                # Check if audit_logs table exists before inserting
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'audit_logs'
                    )
                """)
                audit_exists = cursor.fetchone()[0]
                
                if audit_exists:
                    cursor.execute("""
                        INSERT INTO audit_logs (
                            tenant_id, user_id, action, resource_type, severity
                        ) VALUES (%s, %s, 'USER_LOGIN', 'AUTH', 'INFO')
                    """, (user['tenant_id'], user['id']))
            except Exception as e:
                logger.debug(f"Audit log insert skipped: {e}")
            
            # Commit only the essential updates
            try:
                self.db.commit()
            except Exception as e:
                logger.warning(f"Commit warning (non-fatal): {e}")
            
            logger.info(f"Successful login: {email}")
            
            return {
                "user_id": user['id'],
                "tenant_id": user['tenant_id'],
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role'],
                "organization_name": user['organization_name'],
                "plan": user['plan'],
                "tenant_status": user['status']
            }
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            self.db.rollback()
            return None
        finally:
            cursor.close()
    
    async def get_tenant_usage(self, tenant_id: str) -> TenantUsage:
        """Get tenant usage statistics"""
        cursor = self.db.cursor()
        
        try:
            # Get current month's usage
            cursor.execute("""
                SELECT 
                    t.max_transactions_per_month,
                    t.max_users,
                    t.max_storage_gb,
                    t.max_api_calls_per_minute,
                    COALESCE(u.transaction_count, 0) as transaction_count
                FROM tenants t
                LEFT JOIN tenant_usage u ON t.tenant_id = u.tenant_id
                    AND u.period_start = DATE_TRUNC('month', CURRENT_DATE)
                WHERE t.tenant_id = %s
            """, (tenant_id,))
            
            limits = row_to_dict(cursor, cursor.fetchone())
            
            # Get active users count
            cursor.execute("""
                SELECT COUNT(*) as user_count
                FROM tenant_users
                WHERE tenant_id = %s AND is_active = true
            """, (tenant_id,))
            
            user_count = row_to_dict(cursor, cursor.fetchone())['user_count']
            
            return TenantUsage(
                tenant_id=tenant_id,
                transactions_this_month=limits['transaction_count'],
                transactions_limit=limits['max_transactions_per_month'],
                transactions_percentage=(limits['transaction_count'] / limits['max_transactions_per_month']) * 100,
                active_users=user_count,
                users_limit=limits['max_users'],
                storage_used_gb=0,  # TODO: Calculate actual storage
                storage_limit_gb=limits['max_storage_gb'],
                api_calls_this_minute=0,  # TODO: Implement rate limit tracking
                api_calls_limit=limits['max_api_calls_per_minute']
            )
        finally:
            cursor.close()
    
    async def create_api_key(self, tenant_id: str, key_create: TenantAPIKeyCreate, 
                           created_by_user_id: int) -> Dict:
        """Create new API key for tenant"""
        cursor = self.db.cursor()
        
        try:
            # Generate API key
            api_key = f"fgk_live_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            key_prefix = api_key[:12]
            
            # Calculate expiration
            expires_at = None
            if key_create.expires_days:
                expires_at = datetime.now() + timedelta(days=key_create.expires_days)
            
            cursor.execute("""
                INSERT INTO tenant_api_keys (
                    tenant_id, key_name, key_hash, key_prefix,
                    scopes, rate_limit_per_minute, expires_at, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                tenant_id,
                key_create.key_name,
                key_hash,
                key_prefix,
                key_create.scopes,
                key_create.rate_limit_per_minute,
                expires_at,
                created_by_user_id
            ))
            
            key_id = row_to_dict(cursor, cursor.fetchone())['id']
            self.db.commit()
            
            logger.info(f"Created API key for tenant {tenant_id}")
            
            # Return plain key ONCE
            return {
                "id": key_id,
                "api_key": api_key,  # ⚠️ Show only once!
                "key_prefix": key_prefix,
                "scopes": key_create.scopes,
                "expires_at": expires_at.isoformat() if expires_at else None
            }
        finally:
            cursor.close()
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"fgk_live_{secrets.token_urlsafe(32)}"
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

