from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from config import settings

router = APIRouter()
security = HTTPBearer()

# Simple JWT secret (in production, use environment variable)
JWT_SECRET = getattr(settings, 'jwt_secret', 'dev-secret-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Demo users (in production, use database)
DEMO_USERS = {
    "analyst@bank.com": {"password": "password123", "name": "Analyst User", "role": "analyst"},
    "admin@bank.com": {"password": "admin123", "name": "Admin User", "role": "admin"},
}

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict
    expires_at: str

class UserResponse(BaseModel):
    email: str
    name: str
    role: str

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Authorization header"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user_data = DEMO_USERS.get(request.email)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Simple password check (in production, use bcrypt)
    if request.password != user_data["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "email": request.email,
        "name": user_data["name"],
        "role": user_data["role"],
        "exp": expires_at
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "token": token,
        "user": {
            "email": request.email,
            "name": user_data["name"],
            "role": user_data["role"]
        },
        "expires_at": expires_at.isoformat()
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(payload: dict = Depends(verify_token)):
    """Get current authenticated user"""
    return {
        "email": payload["email"],
        "name": payload["name"],
        "role": payload["role"]
    }

@router.post("/verify")
async def verify(token: str):
    """Verify a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"valid": True, "payload": payload}
    except JWTError as e:
        return {"valid": False, "error": str(e)}

