"""
ANALYTICA - Authentication Module
=================================
JWT-based authentication with user management and points system.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import json
import os
import re

# Simple JWT implementation (no external dependency)
import base64
import hmac

# ============================================================
# CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv("ANALYTICA_SECRET_KEY", "analytica-secret-key-change-in-production")
TOKEN_EXPIRE_HOURS = 24

# ============================================================
# MODELS
# ============================================================

class UserRegister(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=6)
    name: str = Field(min_length=2)
    company: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class UserLogin(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return v.lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    company: Optional[str]
    points_balance: int
    plan: str
    created_at: str


class PointsPurchase(BaseModel):
    amount: int = Field(ge=10, le=10000)
    payment_method: str = "card"


class PointsResponse(BaseModel):
    user_id: str
    points_balance: int
    transaction_id: str
    amount: int
    type: str


# ============================================================
# IN-MEMORY STORAGE (Replace with database in production)
# ============================================================

_users_db: Dict[str, Dict] = {}
_sessions_db: Dict[str, Dict] = {}


def _hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _generate_token(user_id: str, email: str) -> str:
    """Generate JWT-like token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": (datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)).isoformat(),
        "iat": datetime.utcnow().isoformat()
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload_b64}.{signature}"


def _verify_token(token: str) -> Optional[Dict]:
    """Verify and decode token"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        payload_b64, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()[:32]
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Check expiration
        exp = datetime.fromisoformat(payload["exp"])
        if datetime.utcnow() > exp:
            return None
        
        return payload
    except Exception:
        return None


# ============================================================
# SECURITY
# ============================================================

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = _verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = _users_db.get(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    payload = _verify_token(credentials.credentials)
    if not payload:
        return None
    
    return _users_db.get(payload["user_id"])


# ============================================================
# ROUTER
# ============================================================

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    """Register a new user"""
    # Check if email exists
    for user in _users_db.values():
        if user["email"] == data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create user
    user_id = secrets.token_hex(8)
    user = {
        "id": user_id,
        "email": data.email,
        "name": data.name,
        "company": data.company,
        "password_hash": _hash_password(data.password),
        "points_balance": 10,  # Free starter points
        "plan": "free",
        "created_at": datetime.utcnow().isoformat(),
        "transactions": []
    }
    _users_db[user_id] = user
    
    # Generate token
    token = _generate_token(user_id, data.email)
    
    return TokenResponse(
        access_token=token,
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
        user={
            "id": user_id,
            "email": data.email,
            "name": data.name,
            "company": data.company,
            "points_balance": 10,
            "plan": "free"
        }
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    """Login user"""
    # Find user by email
    user = None
    for u in _users_db.values():
        if u["email"] == data.email:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if user["password_hash"] != _hash_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = _generate_token(user["id"], user["email"])
    
    return TokenResponse(
        access_token=token,
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "company": user.get("company"),
            "points_balance": user["points_balance"],
            "plan": user["plan"]
        }
    )


@auth_router.get("/me", response_model=UserProfile)
async def get_profile(user: Dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        company=user.get("company"),
        points_balance=user["points_balance"],
        plan=user["plan"],
        created_at=user["created_at"]
    )


@auth_router.get("/points")
async def get_points(user: Dict = Depends(get_current_user)):
    """Get user points balance"""
    return {
        "user_id": user["id"],
        "points_balance": user["points_balance"],
        "plan": user["plan"],
        "transactions": user.get("transactions", [])[-10:]  # Last 10 transactions
    }


@auth_router.post("/points/purchase", response_model=PointsResponse)
async def purchase_points(data: PointsPurchase, user: Dict = Depends(get_current_user)):
    """Purchase points"""
    transaction_id = secrets.token_hex(8)
    
    # Add points
    user["points_balance"] += data.amount
    
    # Record transaction
    transaction = {
        "id": transaction_id,
        "type": "purchase",
        "amount": data.amount,
        "payment_method": data.payment_method,
        "timestamp": datetime.utcnow().isoformat()
    }
    user.setdefault("transactions", []).append(transaction)
    
    return PointsResponse(
        user_id=user["id"],
        points_balance=user["points_balance"],
        transaction_id=transaction_id,
        amount=data.amount,
        type="purchase"
    )


@auth_router.post("/points/use")
async def use_points(amount: int = 1, user: Dict = Depends(get_current_user)):
    """Use points for an operation"""
    if user["points_balance"] < amount:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient points. Need {amount}, have {user['points_balance']}"
        )
    
    # Deduct points
    user["points_balance"] -= amount
    
    transaction_id = secrets.token_hex(8)
    transaction = {
        "id": transaction_id,
        "type": "usage",
        "amount": -amount,
        "timestamp": datetime.utcnow().isoformat()
    }
    user.setdefault("transactions", []).append(transaction)
    
    return {
        "success": True,
        "points_used": amount,
        "points_balance": user["points_balance"],
        "transaction_id": transaction_id
    }


@auth_router.post("/logout")
async def logout(user: Dict = Depends(get_current_user)):
    """Logout user (invalidate session)"""
    return {"success": True, "message": "Logged out successfully"}


# ============================================================
# DEMO USER (for testing)
# ============================================================

def create_demo_user():
    """Create demo user for testing"""
    demo_id = "demo_user_001"
    if demo_id not in _users_db:
        _users_db[demo_id] = {
            "id": demo_id,
            "email": "demo@analytica.pl",
            "name": "Demo User",
            "company": "Analytica Demo",
            "password_hash": _hash_password("demo123"),
            "points_balance": 100,
            "plan": "pro",
            "created_at": datetime.utcnow().isoformat(),
            "transactions": []
        }

# Create demo user on module load
create_demo_user()
