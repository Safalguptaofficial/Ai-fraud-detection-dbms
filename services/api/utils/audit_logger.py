"""
Audit Logging Utility
Provides helper functions to log CRUD operations to audit_logs table
"""
from psycopg import Connection
from typing import Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


async def log_audit(
    db: Connection,
    tenant_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[int] = None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
) -> bool:
    """
    Log an audit event to the audit_logs table
    
    Args:
        db: Database connection
        tenant_id: Tenant ID
        action: Action performed (CREATE, READ, UPDATE, DELETE, USER_LOGIN, etc.)
        resource_type: Type of resource (transactions, alerts, accounts, etc.)
        resource_id: ID of the specific resource
        user_id: ID of the user who performed the action
        old_value: Previous state (for UPDATE/DELETE)
        new_value: New state (for CREATE/UPDATE)
        metadata: Additional metadata
        severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO audit_logs (
                tenant_id, user_id, action, resource_type, resource_id,
                old_value, new_value, metadata, severity
            ) VALUES (
                %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s
            )
        """, (
            tenant_id,
            user_id,
            action,
            resource_type,
            str(resource_id) if resource_id else None,
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None,
            json.dumps(metadata or {}),
            severity
        ))
        
        db.commit()
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        # Don't fail the main operation if audit logging fails
        return False


def log_audit_sync(
    db: Connection,
    tenant_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
) -> bool:
    """
    Synchronous version of log_audit (for non-async contexts)
    """
    try:
        logger.info(f"🔍 Logging audit: {action} on {resource_type} for tenant {tenant_id}")
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO audit_logs (
                tenant_id, user_id, action, resource_type, resource_id,
                metadata, severity
            ) VALUES (
                %s, %s, %s, %s, %s, %s::jsonb, %s
            )
        """, (
            tenant_id,
            user_id,
            action,
            resource_type,
            str(resource_id) if resource_id else None,
            json.dumps(metadata or {}),
            severity
        ))
        
        db.commit()
        cursor.close()
        logger.info(f"✅ Successfully logged audit: {action} on {resource_type}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to log audit event: {e}", exc_info=True)
        return False

