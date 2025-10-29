from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from models.user import (
    User, UserCreate, UserUpdate, UserWithPermissions,
    UserRole, Permission, get_user_permissions, has_permission
)

router = APIRouter()

# Mock database (in production, use real database)
mock_users_db = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@fraudguard.com",
        "full_name": "System Administrator",
        "role": UserRole.ADMIN,
        "department": "IT",
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": datetime.now()
    },
    {
        "id": 2,
        "username": "john_manager",
        "email": "john@fraudguard.com",
        "full_name": "John Manager",
        "role": UserRole.MANAGER,
        "department": "Fraud Prevention",
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": datetime.now()
    },
    {
        "id": 3,
        "username": "jane_analyst",
        "email": "jane@fraudguard.com",
        "full_name": "Jane Analyst",
        "role": UserRole.ANALYST,
        "department": "Fraud Prevention",
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": datetime.now()
    },
    {
        "id": 4,
        "username": "bob_viewer",
        "email": "bob@fraudguard.com",
        "full_name": "Bob Viewer",
        "role": UserRole.VIEWER,
        "department": "Compliance",
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": None
    }
]

next_user_id = 5

@router.get("/users", response_model=List[User])
async def list_users(
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = 100
):
    """List all users with optional filtering"""
    users = mock_users_db.copy()
    
    if role:
        users = [u for u in users if u["role"] == role]
    
    if is_active is not None:
        users = [u for u in users if u["is_active"] == is_active]
    
    return users[:limit]

@router.get("/users/{user_id}", response_model=UserWithPermissions)
async def get_user(user_id: int):
    """Get user by ID with permissions"""
    user = next((u for u in mock_users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = get_user_permissions(user["role"])
    return {**user, "permissions": permissions}

@router.post("/users", response_model=User, status_code=201)
async def create_user(user: UserCreate):
    """Create a new user"""
    global next_user_id
    
    # Check if username exists
    if any(u["username"] == user.username for u in mock_users_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    if any(u["email"] == user.email for u in mock_users_db):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_user = {
        "id": next_user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "department": user.department,
        "is_active": True,
        "created_at": datetime.now(),
        "last_login": None
    }
    
    mock_users_db.append(new_user)
    next_user_id += 1
    
    return new_user

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate):
    """Update user details"""
    user = next((u for u in mock_users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_update.email is not None:
        # Check if email is already taken by another user
        if any(u["email"] == user_update.email and u["id"] != user_id for u in mock_users_db):
            raise HTTPException(status_code=400, detail="Email already exists")
        user["email"] = user_update.email
    
    if user_update.full_name is not None:
        user["full_name"] = user_update.full_name
    
    if user_update.role is not None:
        user["role"] = user_update.role
    
    if user_update.department is not None:
        user["department"] = user_update.department
    
    if user_update.is_active is not None:
        user["is_active"] = user_update.is_active
    
    return user

@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """Delete a user"""
    global mock_users_db
    
    user = next((u for u in mock_users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting the last admin
    if user["role"] == UserRole.ADMIN:
        admin_count = sum(1 for u in mock_users_db if u["role"] == UserRole.ADMIN and u["is_active"])
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last active admin")
    
    mock_users_db = [u for u in mock_users_db if u["id"] != user_id]
    return None

@router.get("/users/{user_id}/permissions", response_model=List[Permission])
async def get_user_permissions_endpoint(user_id: int):
    """Get permissions for a specific user"""
    user = next((u for u in mock_users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return get_user_permissions(user["role"])

@router.get("/roles", response_model=List[str])
async def list_roles():
    """List all available roles"""
    return [role.value for role in UserRole]

@router.get("/roles/{role}/permissions", response_model=List[Permission])
async def get_role_permissions(role: UserRole):
    """Get permissions for a specific role"""
    return get_user_permissions(role)

@router.get("/permissions", response_model=List[str])
async def list_permissions():
    """List all available permissions"""
    return [perm.value for perm in Permission]

@router.post("/users/{user_id}/check-permission")
async def check_user_permission(user_id: int, permission: Permission):
    """Check if user has a specific permission"""
    user = next((u for u in mock_users_db if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_obj = User(**user)
    has_perm = has_permission(user_obj, permission)
    
    return {
        "user_id": user_id,
        "permission": permission,
        "has_permission": has_perm
    }

