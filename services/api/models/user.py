from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

class Permission(str, Enum):
    # Alert permissions
    VIEW_ALERTS = "view_alerts"
    APPROVE_ALERTS = "approve_alerts"
    REJECT_ALERTS = "reject_alerts"
    DELETE_ALERTS = "delete_alerts"
    
    # Case permissions
    VIEW_CASES = "view_cases"
    CREATE_CASES = "create_cases"
    UPDATE_CASES = "update_cases"
    DELETE_CASES = "delete_cases"
    
    # User management
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    
    # System
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    MANAGE_SETTINGS = "manage_settings"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [p for p in Permission],  # All permissions
    UserRole.MANAGER: [
        Permission.VIEW_ALERTS, Permission.APPROVE_ALERTS, Permission.REJECT_ALERTS,
        Permission.VIEW_CASES, Permission.CREATE_CASES, Permission.UPDATE_CASES,
        Permission.VIEW_USERS, Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA
    ],
    UserRole.ANALYST: [
        Permission.VIEW_ALERTS, Permission.APPROVE_ALERTS, Permission.REJECT_ALERTS,
        Permission.VIEW_CASES, Permission.CREATE_CASES, Permission.UPDATE_CASES,
        Permission.VIEW_ANALYTICS
    ],
    UserRole.VIEWER: [
        Permission.VIEW_ALERTS, Permission.VIEW_CASES, Permission.VIEW_ANALYTICS
    ]
}

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: UserRole
    department: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None

class UserWithPermissions(User):
    permissions: List[Permission]

def get_user_permissions(role: UserRole) -> List[Permission]:
    return ROLE_PERMISSIONS.get(role, [])

def has_permission(user: User, permission: Permission) -> bool:
    user_perms = get_user_permissions(user.role)
    return permission in user_perms

